import os
import httpx
from dotenv import load_dotenv
import json
from typing import List, Dict, Optional, Union, Any
import traceback
from .base import BaseAgent
from .registry import registry
from .models import ChatRequest, UnifiedChatResponse, StandardChatResponse, DetailedChatResponse

load_dotenv()
fastgpt_api_key = os.getenv("FASTGPT_API_KEY")
fastgpt_base_url = os.getenv("FASTGPT_BASE_URL")
fastgpt_app_id = os.getenv("FASTGPT_APP_ID")

class FastGPTAgent(BaseAgent):
    """Agent for FastGPT API."""
    
    def validate_request(self, request_data: Dict[str, Any]) -> bool:
        """Validate if the request data is valid for FastGPT."""
        # FastGPT requires a query
        try:
            # 用 ChatRequest 模型来验证请求数据
            ChatRequest(**request_data)
        except Exception as e:
            print(f"Validation error: {e}")
            return False
        return 'query' in request_data and bool(request_data['query'])
    
    def process_request(self, request_data: Dict[str, Any]) -> Dict[str, Any]:
        """Process the request using FastGPT API."""
        messages = [
            {"role": "user", "content": request_data.get('query', '')}
        ]
        
        variables = {}
        if 'uid' in request_data and request_data['uid']:
            variables["uid"] = request_data['uid']
        if 'user' in request_data and request_data['user']:
            variables["user"] = request_data['user']
        response = self.chat_completions(
            messages=messages,
            app_id=request_data.get('app_id'),
            chat_id=request_data.get('chat_id'),
            stream=request_data.get('stream', False),
            detail=request_data.get('detail', False),  # 支持通过请求参数控制 detail
            variables=variables
        )
        
        return response
    
    # 规范来自 FastGPT 的响应格式
    def format_response(self, response_data: Dict[str, Any]) -> UnifiedChatResponse:
        """Format the FastGPT response into a standardized format using UnifiedChatResponse model."""
        # 检查是否为 detail=true 的响应格式
        if "responseData" in response_data:
            # detail=true 的响应格式，返回详细模式
            return UnifiedChatResponse(
                responseData=response_data.get("responseData", []),
                newVariables=response_data.get("newVariables", {})
            )
        else:
            # detail=false 的响应格式，返回标准模式
            return UnifiedChatResponse(
                id=response_data.get("id", ""),
                model=response_data.get("model", ""),
                usage=response_data.get("usage", {}),
                choices=response_data.get("choices", [])
            )
    
    def chat_completions(
        self,
        messages: List[Dict[str, str]],
        app_id: Optional[str] = None,
        chat_id: Optional[str] = None,
        stream: bool = False,
        detail: bool = False,
        response_chat_item_id: Optional[str] = None,
        variables: Optional[Dict[str, str]] = None
    ) -> Dict:
        """
        发送聊天请求到FastGPT API

        Args:
            messages: 消息列表，格式为 [{"content": "消息内容", "role": "user"}]
                    当chat_id为None时，使用完整messages构建上下文
                    当chat_id不为None时，只使用messages最后一个作为用户问题
            app_id: 应用ID，可选，优先使用参数，其次使用环境变量
            chat_id: 聊天ID，可选
                    为None时，不使用FastGPT上下文功能，完全通过messages构建上下文
                    为非空字符串时，使用chatId进行对话，自动从FastGPT数据库取历史记录
            stream: 是否流式输出，默认为False
            detail: 是否返回中间值（模块状态，响应的完整结果等），默认为False
            response_chat_item_id: 响应聊天项ID，如果传入会作为本次对话响应消息的ID存入数据库
            variables: 模块变量，会替换模块中输入框内容里的{{key}}

        Returns:
            API响应的JSON数据
        """
        if not fastgpt_api_key:
            raise ValueError("FASTGPT_API_KEY not found in environment variables")

        used_app_id = app_id or fastgpt_app_id
        if not used_app_id:
            raise ValueError("app_id is required. Please provide it as parameter or set FASTGPT_APP_ID in environment variables")

        if not fastgpt_base_url:
            raise ValueError("FASTGPT_BASE_URL not found in environment variables")

        url = f"{fastgpt_base_url}/v1/chat/completions"

        headers = {
            "Authorization": f"Bearer {fastgpt_api_key}",
            "Content-Type": "application/json"
        }

        data = {
            "appId": used_app_id,
            "stream": stream,
            "detail": detail,
            "messages": messages
        }

        if chat_id is not None:
            data["chatId"] = chat_id
        if response_chat_item_id is not None:
            data["responseChatItemId"] = response_chat_item_id
        if variables is not None:
            data["variables"] = variables

        with httpx.Client(timeout=30.0) as client:
            response = client.post(url, headers=headers, json=data)
            print("Raw response status:", response.status_code)
            print("Raw response text:", response.text)
            response.raise_for_status()
            return response.json()

# Register the agent
registry.register("fastgpt", FastGPTAgent())