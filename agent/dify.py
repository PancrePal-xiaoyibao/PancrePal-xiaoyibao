import os
import httpx
from dotenv import load_dotenv
from .base import BaseAgent
from .registry import registry
from typing import Dict, Any
from .models import ChatRequest, UnifiedChatResponse, Usage, Choice, Message

load_dotenv()
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