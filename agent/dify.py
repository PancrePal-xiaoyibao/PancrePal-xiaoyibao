import os
import httpx
from dotenv import load_dotenv
from .base import BaseAgent
from .registry import registry
from typing import Dict, Any, Optional
import json
import mimetypes
from .models import ChatRequest, UnifiedChatResponse, Usage, Choice, Message

if os.path.exists('.env'):
    load_dotenv('.env')

dify_api_key = os.getenv("DIFY_API_KEY")
dify_base_url = os.getenv("DIFY_BASE_URL")

class DifyAPIError(Exception):
    """自定义异常类，用于处理Dify API的错误响应"""
    def __init__(self, status_code, message):
        self.status_code = status_code
        self.message = message
        super().__init__(f"HTTP {status_code}: {message}")

class DifyAgent(BaseAgent):
    """Agent for Dify API."""

    def validate_request(self, request_data: Dict[str, Any]) -> bool:
        """
        校验请求数据是否合法，只需保证 user 字段存在且非空。
        """
        try:
            # 只校验统一模型能否通过，具体字段由各 Agent 自行提取
            ChatRequest(**request_data)
        except Exception:
            return False
        return 'user' in request_data and bool(request_data['user'])

    def process_request(self, request_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        处理请求，只提取自己关心的字段。
        """
        # 只提取 Dify 需要的字段
        user = request_data.get('user', '')
        query = request_data.get('query', '')
        response_mode = "streaming" if request_data.get('stream', False) else "blocking"
        conversation_id = request_data.get('conversation_id', '')
        files = request_data.get('files', None)

        try:
            response = self.send_chat_message(
                api_key=dify_api_key,
                user=user,
                base_url=dify_base_url,
                query=query,
                response_mode=response_mode,
                conversation_id=conversation_id,
                files=files
            )

            if response_mode == "blocking":
                print("Dify response:", response.text)
                return response.json()
            return response
        except DifyAPIError as e:
            print(f"Dify API error: {e.status_code} - {e.message}")
            return {"error": f"Dify API error: {e.status_code} - {e.message}"}
        except httpx.HTTPStatusError as e:
            print(f"HTTP error from Dify: {e.response.status_code} - {e.response.text}")
            return {"error": f"HTTP error from Dify: {e.response.status_code} - {e.response.text}"}
        except httpx.RequestError as e:
            print(f"Request error from Dify: {e}")
            return {"error": f"Request error from Dify: {e}"}
        except Exception as e:
            print(f"Unexpected error from Dify: {e}")
            return {"error": f"Unexpected error from Dify: {e}"}

    def stream_chat(self, request_data: Dict[str, Any]):
        """
        将 Dify 的流式响应转换为统一的 SSE 增量格式：
        data: {"id":"","object":"","created":0,"choices":[{"delta":{"content":"..."},"index":0,"finish_reason":null}]}
        """
        user = request_data.get('user', '')
        query = request_data.get('query', '')
        conversation_id = request_data.get('conversation_id', '')
        files = request_data.get('files', None)

        if not dify_api_key or not dify_base_url:
            raise ValueError("DIFY_BASE_URL or DIFY_API_KEY not found in environment variables")

        # 先发一个空增量，保持与 FastGPT/OpenAI 风格一致
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
            prev = ""
            # 发送初始空片段
            yield sse_wrap(build_delta(""))

            # 直接在此方法内部管理 httpx.Client，避免返回已关闭的流
            url = f"{dify_base_url}/chat-messages"
            headers = {
                "Authorization": f"Bearer {dify_api_key}",
                "Content-Type": "application/json",
                "Accept": "text/event-stream"
            }
            data = {
                "inputs": {},
                "query": query,
                "response_mode": "streaming",
                "conversation_id": conversation_id,
                "user": user,
                "files": files
            }

            try:
                with httpx.Client(timeout=None) as client:
                    with client.stream("POST", url, headers=headers, json=data) as response:
                        response.raise_for_status()
                        for raw_line in response.iter_lines():
                            if not raw_line:
                                continue
                            # 统一为 str
                            try:
                                line = raw_line.decode('utf-8') if isinstance(raw_line, (bytes, bytearray)) else str(raw_line)
                            except Exception:
                                continue
                            line = line.strip()
                            if not line:
                                continue
                            # 忽略注释行（SSE keepalive）
                            if line.startswith(":"):
                                continue

                            if line.startswith("data:"):
                                data_text = line[len("data:"):].strip()
                            else:
                                data_text = line

                            # Dify 结束标识
                            if data_text == "[DONE]":
                                done_payload = {
                                    "id": "",
                                    "object": "",
                                    "created": 0,
                                    "choices": [
                                        {
                                            "delta": {},
                                            "index": 0,
                                            "finish_reason": "stop"
                                        }
                                    ]
                                }
                                yield sse_wrap(done_payload)
                                break

                            # 解析 JSON，取 answer 累计文本，计算增量
                            try:
                                obj = json.loads(data_text)
                            except Exception:
                                continue

                            answer = obj.get("answer") or obj.get("data", {}).get("answer") or ""
                            if not isinstance(answer, str):
                                continue

                            if not answer.startswith(prev):
                                delta_text = answer
                            else:
                                delta_text = answer[len(prev):]

                            if delta_text:
                                yield sse_wrap(build_delta(delta_text))
                                prev = answer
            except httpx.HTTPError as e:
                err_payload = build_delta(f"[stream error] {e}")
                yield sse_wrap(err_payload)

        return event_generator()

    def upload_file(self, file_path: str) -> Any:
        """
        将本地临时文件上传到 Dify，并返回统一文件信息 FastGPTFileInfo。
        使用 Dify 的 /files/upload 接口。
        """
        if not dify_api_key or not dify_base_url:
            raise ValueError("DIFY_BASE_URL or DIFY_API_KEY not found in environment variables")

        # 提取原始文件名（upload.py 会以 _{filename} 作为后缀创建临时文件）
        original_name = os.path.basename(file_path)
        if "_" in original_name:
            original_name = original_name.split("_", 1)[1] or original_name

        # 猜测 MIME 类型
        mime_type = mimetypes.guess_type(original_name)[0] or "application/octet-stream"
        file_size = os.path.getsize(file_path)

        # 智能处理 base_url，避免重复的 /v1
        base = dify_base_url.rstrip('/')
        if base.endswith('/v1'):
            url = f"{base}/files/upload"
        else:
            url = f"{base}/v1/files/upload"
        headers = {
            "Authorization": f"Bearer {dify_api_key}"
        }

        # 使用 multipart/form-data 上传文件
        with open(file_path, 'rb') as f:
            files = {
                'file': (original_name, f, mime_type)
            }
            data = {
                'user': 'uploader'  # Dify 要求的用户标识
            }
            
            with httpx.Client(timeout=60.0) as client:
                response = client.post(url, headers=headers, files=files, data=data)
                
                if response.status_code not in [200, 201]:  # 200 OK 或 201 Created 都是成功
                    error_msg = f"HTTP {response.status_code}"
                    try:
                        error_data = response.json()
                        if "message" in error_data:
                            error_msg = error_data["message"]
                    except:
                        error_msg = response.text or error_msg
                    raise DifyAPIError(response.status_code, error_msg)
                
                # 解析 Dify 返回的文件信息
                dify_file_info = response.json()
                
                # 转换为统一格式
                file_info = self.build_file_info(
                    file_id=dify_file_info.get("id", ""),
                    file_name=dify_file_info.get("name", original_name),
                    size_bytes=dify_file_info.get("size", file_size),
                    mime_type=dify_file_info.get("mime_type", mime_type),
                    created_by=str(dify_file_info.get("created_by", "uploader")),
                    created_at=dify_file_info.get("created_at")
                )
                
                return file_info

    def format_response(self, response_data: Any) -> UnifiedChatResponse:
        """
        格式化 Dify 响应为统一结构，遵循 FastGPT 的响应格式。
        """
        # 检查是否是错误响应
        if isinstance(response_data, dict) and "error" in response_data:
            # 错误情况，返回包含错误信息的响应
            error_message = Message(
                role="assistant",
                content=f"抱歉，请求处理失败：{response_data['error']}"
            )
            
            choice = Choice(
                message=error_message,
                finish_reason="stop",
                index=0
            )
            
            return UnifiedChatResponse(
                id="",
                model="dify",
                usage=Usage(prompt_tokens=0, completion_tokens=0, total_tokens=0),
                choices=[choice]
            )
        
        if isinstance(response_data, dict):
            usage_data = response_data.get("metadata", {}).get("usage", {})
            # 兼容 Dify 价格等多余字段，只取 tokens 相关
            usage = Usage(
                prompt_tokens=usage_data.get("prompt_tokens", 0),
                completion_tokens=usage_data.get("completion_tokens", 0),
                total_tokens=usage_data.get("total_tokens", 0)
            )
            
            message = Message(
                role="assistant",
                content=response_data.get("answer", "")
            )
            
            choice = Choice(
                message=message,
                finish_reason="stop",
                index=0
            )
            
            # Dify 只支持标准模式，不支持 detail=true
            return UnifiedChatResponse(
                id=response_data.get("conversation_id", ""),
                model=response_data.get("mode", ""),
                usage=usage,
                choices=[choice]
            )
        else:
            # 其他错误情况，返回空的标准响应
            return UnifiedChatResponse(
                id="",
                model="",
                usage=Usage(prompt_tokens=0, completion_tokens=0, total_tokens=0),
                choices=[]
            )

    def send_chat_message(self, api_key: str, user: str, base_url: str, query: str, response_mode: str = "blocking", conversation_id: str = "", files: list = None):
        """
        向 Dify 服务发送聊天消息请求。
        """
        url = f"{base_url}/chat-messages"
        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }
        data = {
            "inputs": {},
            "query": query,
            "response_mode": response_mode,
            "conversation_id": conversation_id,
            "user": user,
            "files": files
        }
        with httpx.Client(timeout=60.0) as client:
            if response_mode == "streaming":
                return client.stream("POST", url, headers=headers, json=data)
            else:
                response = client.post(url, headers=headers, json=data)
                # 检查HTTP状态码
                if response.status_code != 200:
                    error_msg = f"HTTP {response.status_code}"
                    try:
                        error_data = response.json()
                        if "message" in error_data:
                            error_msg = error_data["message"]
                        if "code" in error_data:
                            error_msg = f"{error_data['code']}: {error_data.get('message', 'Unknown error')}"
                    except:
                        pass
                    raise DifyAPIError(response.status_code, error_msg)
                return response

    def get_history(self, api_key: str, user: str, base_url: str, conversation_id: str = ""):
        """
        获取 Dify 聊天历史记录。
        """
        url = f"{base_url}/conversations?user={user}&conversation_id={conversation_id}"

        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }
        
        with httpx.Client(timeout=60.0) as client:
            response = client.get(url, headers=headers)
            return response
        

# 注册 Dify Agent
registry.register("dify", DifyAgent())