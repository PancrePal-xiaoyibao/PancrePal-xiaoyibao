import os
import httpx
from dotenv import load_dotenv
from .base import BaseAgent
from .registry import registry
from typing import Dict, Any

load_dotenv()
dify_api_key = os.getenv("DIFY_API_KEY")
dify_base_url = os.getenv("DIFY_BASE_URL")

class DifyAgent(BaseAgent):
    """Agent for Dify API."""
    
    def validate_request(self, request_data: Dict[str, Any]) -> bool:
        """Validate if the request data is valid for Dify."""
        # Dify requires a user field
        return 'user' in request_data and bool(request_data['user'])
    
    def process_request(self, request_data: Dict[str, Any]) -> Dict[str, Any]:
        """Process the request using Dify API."""
        api_key = dify_api_key
        base_url = dify_base_url
        query = request_data.get('query', '')
        user = request_data.get('user', '')
        response_mode = "streaming" if request_data.get('stream', False) else "blocking"
        conversation_id = request_data.get('conversation_id', '')
        files = request_data.get('files', None)
        
        response = self.send_chat_message(
            api_key=api_key,
            user=user,
            base_url=base_url,
            query=query,
            response_mode=response_mode,
            conversation_id=conversation_id,
            files=files
        )
        
        if response_mode == "blocking":
            return response.json()
        return response
    
    def format_response(self, response_data: Any) -> Dict[str, Any]:
        """Format the Dify response into a standardized format."""
        if isinstance(response_data, dict):
            return {
                "responseData": [],
                "id": response_data.get("id", ""),
                "model": "",
                "usage": response_data.get("metadata", {}).get("usage", {}),
                "choices": [
                    {
                        "message": {
                            "role": "assistant",
                            "content": response_data.get("answer", "")
                        },
                        "finish_reason": "stop",
                        "index": 0
                    }
                ]
            }
        return {
            "error": "Invalid response format"
        }
    
    def send_chat_message(self, api_key, user, base_url, query, response_mode="blocking", conversation_id="", files=None):
        """
        向 Dify 服务发送聊天消息请求。

        参数:
            api_key (str): Dify API 密钥，用于身份验证，从环境变量 DIFY_API_KEY 获取。
            user (str): 用户标识符，用于标识发送消息的用户。
            files (list): 附加的文件列表，默认为 None。
            base_url (str): Dify 服务的基础 URL，例如 http://localhost/v1。
            query (str): 用户输入的提问内容。
            response_mode (str): 响应模式，"blocking" 为同步，"streaming" 为流式（默认为 "blocking"）。
            conversation_id (str): 会话 ID，用于多轮对话（可选）。

        返回:
            httpx.Response: Dify 服务的 HTTP 响应对象。
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
        # 后端相应可能过慢
        with httpx.Client(timeout=60.0) as client:
            if response_mode == "streaming":
                # 返回同步流式响应
                return client.stream("POST", url, headers=headers, json=data)
            else:
                response = client.post(url, headers=headers, json=data)
                return response

# Register the agent
registry.register("dify", DifyAgent())