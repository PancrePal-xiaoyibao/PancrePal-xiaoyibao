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
    
    @staticmethod
    def _is_valid_object_id(value: Optional[str]) -> bool:
        if not value or not isinstance(value, str):
            return False
        if len(value) != 24:
            return False
        try:
            int(value, 16)
            return True
        except Exception:
            return False
    
    def validate_request(self, request_data: Dict[str, Any]) -> bool:
        """Validate if the request data is valid for FastGPT."""
        # FastGPT requires a query or files
        try:
            # 用 ChatRequest 模型来验证请求数据
            ChatRequest(**request_data)
        except Exception as e:
            print(f"Validation error: {e}")
            return False
        
        # 至少需要有 query 或 files 其中一个
        has_query = 'query' in request_data and bool(request_data['query'])
        has_files = 'files' in request_data and request_data['files'] and len(request_data['files']) > 0
        
        if not (has_query or has_files):
            return False

        # 校验 appId（请求级或环境变量）
        used_app_id = request_data.get('app_id') or fastgpt_app_id
        if not self._is_valid_object_id(used_app_id):
            print(f"Invalid app_id provided or missing. Got: {used_app_id}")
            return False

        return True
    
    def process_request(self, request_data: Dict[str, Any]) -> Dict[str, Any]:
        """Process the request using FastGPT API."""
        # 构建消息内容，支持文件上传
        message_content = []
        
        # 添加文本内容
        text_content = request_data.get('query', '')
        if text_content:
            message_content.append({
                "type": "text",
                "text": text_content
            })
        
        # 处理文件上传
        files = request_data.get('files', [])
        if files:
            for file_url in files:
                if isinstance(file_url, str):
                    # 判断文件类型
                    if self._is_image_file(file_url):
                        # 图片文件
                        message_content.append({
                            "type": "image_url",
                            "image_url": {
                                "url": file_url
                            }
                        })
                    else:
                        # 文档文件
                        # 从URL中提取文件名
                        file_name = self._extract_filename_from_url(file_url)
                        message_content.append({
                            "type": "file_url",
                            "name": file_name,
                            "url": file_url
                        })
        
        # 如果有多个内容类型，使用复合格式；否则使用简单字符串格式
        if len(message_content) > 1 or (len(message_content) == 1 and message_content[0]["type"] != "text"):
            messages = [
                {"role": "user", "content": message_content}
            ]
        else:
            # 只有文本内容时，保持原有格式
            messages = [
                {"role": "user", "content": text_content}
            ]
        
        variables = {}
        if 'uid' in request_data and request_data['uid']:
            variables["uid"] = request_data['uid']
        if 'user' in request_data and request_data['user']:
            variables["user"] = request_data['user']
        # 请求体参数
        response = self.chat_completions(
            messages=messages,
            app_id=request_data.get('app_id'),
            chat_id=request_data.get('chat_id'),
            stream=request_data.get('stream', False),
            detail=request_data.get('detail', False),  # 支持通过请求参数控制 detail
            variables=variables
        )
        
        return response
    
    def _is_image_file(self, url: str) -> bool:
        """判断URL是否为图片文件"""
        image_extensions = ['.jpg', '.jpeg', '.png', '.gif', '.bmp', '.webp', '.svg']
        url_lower = url.lower()
        return any(url_lower.endswith(ext) for ext in image_extensions)
    
    def _extract_filename_from_url(self, url: str) -> str:
        """从URL中提取文件名"""
        try:
            # 从URL中提取文件名
            import urllib.parse
            parsed_url = urllib.parse.urlparse(url)
            filename = parsed_url.path.split('/')[-1]
            if filename:
                return filename
            else:
                # 如果无法提取文件名，返回默认名称
                return "uploaded_file"
        except Exception:
            return "uploaded_file"
    
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
        messages: List[Dict[str, Union[str, List[Dict[str, Any]]]]],
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
        if not self._is_valid_object_id(used_app_id):
            raise ValueError(f"Invalid app_id format. Expect 24-char hex ObjectId, got: {used_app_id}")

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

    def stream_chat(self, request_data: Dict[str, Any]):
        """
        以 SSE 形式流式转发 FastGPT 的响应（detail=false, stream=true）。
        """
        if not fastgpt_api_key:
            raise ValueError("FASTGPT_API_KEY not found in environment variables")

        used_app_id = request_data.get('app_id') or fastgpt_app_id
        if not used_app_id:
            raise ValueError("app_id is required. Please provide it as parameter or set FASTGPT_APP_ID in environment variables")
        if not self._is_valid_object_id(used_app_id):
            raise ValueError(f"Invalid app_id format. Expect 24-char hex ObjectId, got: {used_app_id}")

        if not fastgpt_base_url:
            raise ValueError("FASTGPT_BASE_URL not found in environment variables")

        # 组装消息（与 process_request 保持一致）
        message_content = []
        text_content = request_data.get('query', '')
        if text_content:
            message_content.append({
                "type": "text",
                "text": text_content
            })
        files = request_data.get('files', [])
        if files:
            for file_url in files:
                if isinstance(file_url, str):
                    if self._is_image_file(file_url):
                        message_content.append({
                            "type": "image_url",
                            "image_url": {"url": file_url}
                        })
                    else:
                        file_name = self._extract_filename_from_url(file_url)
                        message_content.append({
                            "type": "file_url",
                            "name": file_name,
                            "url": file_url
                        })

        if len(message_content) > 1 or (len(message_content) == 1 and message_content[0]["type"] != "text"):
            messages = [{"role": "user", "content": message_content}]
        else:
            messages = [{"role": "user", "content": text_content}]

        variables: Dict[str, str] = {}
        if 'uid' in request_data and request_data['uid']:
            variables["uid"] = request_data['uid']
        if 'user' in request_data and request_data['user']:
            variables["user"] = request_data['user']

        url = f"{fastgpt_base_url}/v1/chat/completions"
        headers = {
            "Authorization": f"Bearer {fastgpt_api_key}",
            "Content-Type": "application/json"
        }
        data = {
            "appId": used_app_id,
            "stream": True,
            "detail": False,
            "messages": messages
        }
        if request_data.get('chat_id') is not None:
            data["chatId"] = request_data.get('chat_id')
        if request_data.get('variables') is not None:
            data["variables"] = request_data.get('variables')
        elif variables:
            data["variables"] = variables

        def event_generator():
            with httpx.Client(timeout=None) as client:
                with client.stream("POST", url, headers=headers, json=data) as response:
                    response.raise_for_status()
                    for line in response.iter_lines():
                        if not line:
                            continue
                        # FastGPT 通常已带有 'data: ' 前缀，这里原样透传
                        yield (line + "\n\n")

        return event_generator()

# Register the agent
registry.register("fastgpt", FastGPTAgent())