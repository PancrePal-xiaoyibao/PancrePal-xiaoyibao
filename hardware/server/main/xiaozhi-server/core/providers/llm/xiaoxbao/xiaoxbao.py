import json
from config.logger import setup_logging
import requests
from core.providers.llm.base import LLMProviderBase
from core.utils.util import check_model_key

TAG = __name__
logger = setup_logging()


class LLMProvider(LLMProviderBase):
    def __init__(self, config):
        self.api_key = config["api_key"]
        self.base_url = config.get("base_url")
        self.detail = config.get("detail", False)
        self.variables = config.get("variables", {})
        model_key_msg = check_model_key("XiaoXBaoLLM", self.api_key)
        if model_key_msg:
            logger.bind(tag=TAG).error(model_key_msg)

    def response(self, session_id, dialogue, **kwargs):
        try:
            # 取最后一条用户消息
            last_msg = next(m for m in reversed(dialogue) if m["role"] == "user")

            # 构造请求URL
            url = f"{self.base_url}/api/v1/chat/completions"
            
            headers = {"Authorization": f"Bearer {self.api_key}"}
            payload = {
                "stream": True,
                "chatId": session_id,
                "detail": self.detail,
                "variables": self.variables,
                "messages": [{"role": "user", "content": last_msg["content"]}],
            }

            # 发起请求
            response = requests.post(
                url,
                headers=headers,
                json=payload,
                stream=True,
                timeout=30
            )
            
            if response.status_code != 200:
                raise Exception(f"请求失败，状态码: {response.status_code}")

            # 处理流式响应
            for line in response.iter_lines():
                if line:
                    try:
                        if line.startswith(b"data: "):
                            if line[6:].decode("utf-8") == "[DONE]":
                                break

                            data = json.loads(line[6:])
                            if "choices" in data and len(data["choices"]) > 0:
                                delta = data["choices"][0].get("delta", {})
                                if (
                                    delta
                                    and "content" in delta
                                    and delta["content"] is not None
                                ):
                                    content = delta["content"]
                                    # 过滤特殊字符
                                    if "\u001f" in content or "\u001e" in content:
                                        continue
                                    yield content

                    except json.JSONDecodeError as e:
                        logger.bind(tag=TAG).warning(f"JSON解析错误: {e}")
                        continue
                    except Exception as e:
                        logger.bind(tag=TAG).warning(f"处理响应时出错: {e}")
                        continue

        except Exception as e:
            logger.bind(tag=TAG).error(f"Error in response generation: {e}")
            yield "【服务响应异常】"

    def response_with_functions(self, session_id, dialogue, functions=None):
        logger.bind(tag=TAG).error(
            f"xiao_x_bao暂未实现完整的工具调用（function call），建议使用其他意图识别"
        )