import os
import json
from typing import Dict, Any, List, Optional
from dotenv import load_dotenv
from .base import BaseAgent
from .registry import registry
from .models import ChatRequest, UnifiedChatResponse, Usage, Choice, Message

load_dotenv()

# 环境变量
zhipu_api_key = os.getenv("ZHIPUAI_API_KEY")
zhipu_base_url = os.getenv("ZHIPUAI_BASE_URL")  # 可选


class ZhipuAgent(BaseAgent):
    """Agent for ZhipuAI (智谱清言) chat.completions API."""

    def __init__(self):
        self.api_key = zhipu_api_key
        self.base_url = zhipu_base_url

        if not self.api_key:
            print("Warning: ZHIPUAI_API_KEY not found in environment variables")

    def validate_request(self, request_data: Dict[str, Any]) -> bool:
        try:
            ChatRequest(**request_data)
        except Exception:
            return False
        return 'query' in request_data and bool(request_data['query'])

    def process_request(self, request_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        非流式请求：调用 zhipuai.chat.completions.create 并返回其 JSON 结果。
        仅使用最小必要字段：messages、model、extra_body。
        """
        if not self.api_key:
            return {"error": "ZHIPUAI_API_KEY not configured"}

        # 延迟导入，避免未用到时报错
        try:
            from zhipuai import ZhipuAI  # type: ignore
        except Exception as e:
            return {"error": f"zhipuai SDK import failed: {e}"}

        query = request_data.get('query', '')
        model_name = request_data.get('model') or "glm-4"
        temperature = request_data.get('temperature', 0.7)
        max_tokens = request_data.get('max_tokens', 1024)

        # 构造 messages（仅文本）
        messages: List[Dict[str, Any]] = [
            {"role": "user", "content": query}
        ]

        client_kwargs: Dict[str, Any] = {"api_key": self.api_key}
        if self.base_url:
            client_kwargs["base_url"] = self.base_url

        client = ZhipuAI(**client_kwargs)

        try:
            resp = client.chat.completions.create(
                model=model_name,
                messages=messages,
                extra_body={"temperature": temperature, "max_tokens": max_tokens}
            )
        except Exception as e:
            return {"error": f"Zhipu API error: {e}"}

        # zhipuai SDK 返回对象可被 dict() / json 序列化，这里统一转 dict
        try:
            if hasattr(resp, "model_dump"):
                return resp.model_dump()
            if hasattr(resp, "to_dict"):
                return resp.to_dict()
            # 兜底：尝试通过 JSON
            return json.loads(json.dumps(resp, default=lambda o: getattr(o, "__dict__", str(o))))
        except Exception:
            # 最小化可用字段
            return {
                "id": getattr(resp, "id", ""),
                "model": model_name,
                "choices": getattr(resp, "choices", []),
                "usage": getattr(resp, "usage", {}),
            }

    def stream_chat(self, request_data: Dict[str, Any]):
        """
        流式对话：将智谱的增量结果转换为统一的 SSE Delta 结构。
        data: {"id":"","object":"","created":0,"choices":[{"delta":{"content":"..."},"index":0,"finish_reason":null}]}
        """
        if not self.api_key:
            raise ValueError("ZHIPUAI_API_KEY not configured")

        try:
            from zhipuai import ZhipuAI  # type: ignore
        except Exception as e:
            raise ImportError(f"zhipuai SDK import failed: {e}")

        query = request_data.get('query', '')
        model_name = request_data.get('model') or "glm-4"
        temperature = request_data.get('temperature', 0.7)
        max_tokens = request_data.get('max_tokens', 1024)

        client_kwargs: Dict[str, Any] = {"api_key": self.api_key}
        if self.base_url:
            client_kwargs["base_url"] = self.base_url

        client = ZhipuAI(**client_kwargs)

        def sse_wrap(payload: Dict[str, Any]) -> str:
            return f"data: {json.dumps(payload, ensure_ascii=False)}\n\n"

        def build_delta(content: Optional[str]):
            return {
                "id": "",
                "object": "",
                "created": 0,
                "choices": [
                    {
                        "delta": {"content": content or ""},
                        "index": 0,
                        "finish_reason": None
                    }
                ]
            }

        def event_generator():
            # 先发一个空增量，兼容前端渲染器
            yield sse_wrap(build_delta(""))
            try:
                stream = client.chat.completions.create(
                    model=model_name,
                    messages=[{"role": "user", "content": query}],
                    stream=True,
                    extra_body={"temperature": temperature, "max_tokens": max_tokens}
                )
                for chunk in stream:
                    try:
                        delta = None
                        # SDK chunk 结构：chunk.choices[0].delta.content
                        if hasattr(chunk, "choices") and chunk.choices:
                            choice0 = chunk.choices[0]
                            delta_obj = getattr(choice0, "delta", None)
                            if delta_obj and getattr(delta_obj, "content", None):
                                delta = delta_obj.content
                        if delta:
                            yield sse_wrap(build_delta(delta))
                    except Exception:
                        continue
                # 结束片段
                done_payload = {
                    "id": "",
                    "object": "",
                    "created": 0,
                    "choices": [
                        {"delta": {}, "index": 0, "finish_reason": "stop"}
                    ]
                }
                yield sse_wrap(done_payload)
            except Exception as e:
                yield sse_wrap(build_delta(f"[stream error] {e}"))

        return event_generator()

    def format_response(self, response_data: Dict[str, Any]) -> UnifiedChatResponse:
        # 错误处理
        if isinstance(response_data, dict) and response_data.get("error"):
            return UnifiedChatResponse(
                id="",
                model="zhipu",
                usage=Usage(prompt_tokens=0, completion_tokens=0, total_tokens=0),
                choices=[Choice(
                    message=Message(role="assistant", content=f"请求失败：{response_data.get('error')}"),
                    finish_reason="error",
                    index=0
                )]
            )

        # 标准模式（detail=false）
        usage_dict = (response_data or {}).get("usage", {}) if isinstance(response_data, dict) else {}
        usage = Usage(
            prompt_tokens=usage_dict.get("prompt_tokens", 0) or usage_dict.get("input_tokens", 0) or 0,
            completion_tokens=usage_dict.get("completion_tokens", 0) or usage_dict.get("output_tokens", 0) or 0,
            total_tokens=usage_dict.get("total_tokens", 0) or (usage_dict.get("prompt_tokens", 0) or 0) + (usage_dict.get("completion_tokens", 0) or 0)
        )

        # choices
        choices_src = (response_data or {}).get("choices", []) if isinstance(response_data, dict) else []
        choices: List[Choice] = []
        for idx, ch in enumerate(choices_src):
            msg = ch.get("message", {}) if isinstance(ch, dict) else {}
            content = msg.get("content", "")
            role = msg.get("role", "assistant")
            choices.append(Choice(
                message=Message(role=role, content=content),
                finish_reason=ch.get("finish_reason", "stop") if isinstance(ch, dict) else "stop",
                index=idx
            ))

        return UnifiedChatResponse(
            id=(response_data or {}).get("id", "") if isinstance(response_data, dict) else "",
            model=(response_data or {}).get("model", "glm-4") if isinstance(response_data, dict) else "glm-4",
            usage=usage,
            choices=choices or [Choice(message=Message(role="assistant", content=""), finish_reason="stop", index=0)]
        )


# 注册 Zhipu Agent（当存在 API Key 时）
if zhipu_api_key:
    registry.register("zhipu", ZhipuAgent())


