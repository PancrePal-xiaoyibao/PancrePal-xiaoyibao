import os
import httpx
from dotenv import load_dotenv
from .base import BaseAgent
from .registry import registry
from typing import Dict, Any
from .models import ChatRequest

load_dotenv()
dify_api_key = os.getenv("DIFY_API_KEY")
dify_base_url = os.getenv("DIFY_BASE_URL")

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
            return response.json()
        return response

    def format_response(self, response_data: Any) -> Dict[str, Any]:
        """
        格式化 Dify 响应为统一结构。
        """
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
                return response

# 注册 Dify Agent
registry.register("dify", DifyAgent())