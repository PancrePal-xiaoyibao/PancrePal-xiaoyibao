import os
from typing import Dict, Any, List, Optional
from .base import BaseAgent
from .registry import registry
from .models import ChatRequest, UnifiedChatResponse, Message, Choice, Usage
from dotenv import load_dotenv
from cozepy import Coze, TokenAuth, COZE_CN_BASE_URL, AsyncCoze, AsyncTokenAuth, Message as CozeMessage, ChatEventType
import traceback

load_dotenv()

# 环境变量配置 - 使用与测试文件一致的变量名
coze_api_token = os.getenv("COZE_API_TOKEN")
coze_base_url = os.getenv("COZE_BASE_URL", COZE_CN_BASE_URL)
coze_bot_id = os.getenv("COZE_BOT_ID")

# 初始化扣子客户端
if coze_api_token:
    coze = Coze(auth=TokenAuth(coze_api_token), base_url=coze_base_url)
    async_coze = AsyncCoze(auth=AsyncTokenAuth(coze_api_token), base_url=coze_base_url)
else:
    coze = None
    async_coze = None

class CozeAgent(BaseAgent):
    """Agent for Coze API."""

    def __init__(self):
        # 可在此初始化所需的环境变量或配置
        self.api_token = coze_api_token
        self.base_url = coze_base_url
        self.bot_id = coze_bot_id
        
        # 验证必要的环境变量
        if not self.api_token:
            raise ValueError("COZE_API_TOKEN not found in environment variables")
        if not self.bot_id:
            raise ValueError("COZE_BOT_ID not found in environment variables")

    def validate_request(self, request_data: Dict[str, Any]) -> bool:
        """
        校验请求数据是否合法。
        子类可根据实际需求自定义校验逻辑。
        需要先检验 ChatRequest 模型是否能通过，
        以确保前端传入的参数符合预期。

        参数:
            request_data (Dict[str, Any]): 需要校验的请求数据

        返回:
            bool: 如果请求数据合法返回 True，否则返回 False
        """
        # 示例：检查 query 字段是否存在且非空
        try:
            ChatRequest(**request_data)
        except Exception as e:
            print(f"Validation error: {e}")
            return False
        return 'query' in request_data and bool(request_data['query'])

    def process_request(self, request_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        处理请求并返回原始响应。
        使用 Coze SDK 进行聊天对话。

        参数:
            request_data (Dict[str, Any]): 需要处理的请求数据

        返回:
            Dict[str, Any]: Coze API 响应数据
        """
        try:
            if not coze:
                raise ValueError("Coze client not initialized. Please check COZE_API_TOKEN.")
            
            # 获取用户输入
            query = request_data.get('query', '')
            user_id = request_data.get('user', 'default_user')
            conversation_id = request_data.get('conversation_id')
            stream = request_data.get('stream', False)
            
            # 构建消息
            additional_messages = [CozeMessage.build_user_question_text(query)]
            
            if stream:
                # 流式响应
                return self._handle_stream_response(user_id, additional_messages, conversation_id)
            else:
                # 非流式响应
                return self._handle_blocking_response(user_id, additional_messages, conversation_id)
                
        except Exception as e:
            print(f"Error in process_request: {e}")
            traceback.print_exc()
            return {"error": str(e)}

    def _handle_blocking_response(self, user_id: str, additional_messages: List[CozeMessage], conversation_id: Optional[str] = None) -> Dict[str, Any]:
        """处理非流式响应"""
        try:
            # 发送聊天请求
            kwargs = {
                "bot_id": self.bot_id,
                "user_id": user_id,
                "additional_messages": additional_messages
            }
            
            if conversation_id:
                kwargs["conversation_id"] = conversation_id
                
            chat_result = coze.chat.create_and_poll(**kwargs)
            
            # 构建响应
            response = {
                "id": getattr(chat_result, 'id', ''),
                "conversation_id": getattr(chat_result, 'conversation_id', ''),
                "model": "coze",  # Coze 作为模型名称
                "choices": [],
                "usage": {
                    "prompt_tokens": 0,
                    "completion_tokens": 0,
                    "total_tokens": 0
                }
            }
            
            # 获取消息内容 - 改进的消息处理逻辑
            if hasattr(chat_result, 'messages') and chat_result.messages:
                content_parts = []
                for message in chat_result.messages:
                    # 只处理 assistant 角色的消息
                    if hasattr(message, 'role') and message.role == 'assistant':
                        if hasattr(message, 'content') and message.content:
                            # 过滤掉系统控制信息
                            content = message.content.strip()
                            if content and not content.startswith('{"msg_type":'):
                                content_parts.append(content)
                
                final_content = '\n'.join(content_parts) if content_parts else "响应为空"
                
                response["choices"] = [{
                    "message": {
                        "role": "assistant",
                        "content": final_content
                    },
                    "finish_reason": "stop",
                    "index": 0
                }]
            else:
                # 如果没有消息，提供默认响应
                response["choices"] = [{
                    "message": {
                        "role": "assistant",
                        "content": "抱歉，没有收到有效响应"
                    },
                    "finish_reason": "stop",
                    "index": 0
                }]
            
            # 如果有使用量信息，更新usage
            if hasattr(chat_result, 'usage') and chat_result.usage:
                usage = chat_result.usage
                response["usage"] = {
                    "prompt_tokens": getattr(usage, 'input_count', 0),
                    "completion_tokens": getattr(usage, 'output_count', 0),
                    "total_tokens": getattr(usage, 'token_count', 0)
                }
                
            return response
            
        except Exception as e:
            print(f"Error in _handle_blocking_response: {e}")
            traceback.print_exc()
            return {"error": str(e)}

    def _handle_stream_response(self, user_id: str, additional_messages: List[CozeMessage], conversation_id: Optional[str] = None) -> Dict[str, Any]:
        """处理流式响应"""
        try:
            kwargs = {
                "bot_id": self.bot_id,
                "user_id": user_id,
                "additional_messages": additional_messages
            }
            
            if conversation_id:
                kwargs["conversation_id"] = conversation_id
            
            content_parts = []
            usage_info = {}
            conversation_id_result = ""
            
            # 流式处理
            for event in coze.chat.stream(**kwargs):
                if event.event == ChatEventType.CONVERSATION_MESSAGE_DELTA:
                    if hasattr(event.message, 'content') and event.message.content:
                        # 过滤掉系统控制信息
                        content_chunk = event.message.content
                        if content_chunk and not content_chunk.startswith('{"msg_type":'):
                            content_parts.append(content_chunk)
                        
                if event.event == ChatEventType.CONVERSATION_CHAT_COMPLETED:
                    if hasattr(event.chat, 'usage') and event.chat.usage:
                        usage = event.chat.usage
                        usage_info = {
                            "prompt_tokens": getattr(usage, 'input_count', 0),
                            "completion_tokens": getattr(usage, 'output_count', 0),
                            "total_tokens": getattr(usage, 'token_count', 0)
                        }
                    if hasattr(event.chat, 'conversation_id'):
                        conversation_id_result = event.chat.conversation_id
            
            # 构建最终响应
            final_content = ''.join(content_parts) if content_parts else "响应为空"
            response = {
                "id": "",  # 流式响应可能没有明确的ID
                "conversation_id": conversation_id_result,
                "model": "coze",
                "choices": [{
                    "message": {
                        "role": "assistant",
                        "content": final_content
                    },
                    "finish_reason": "stop",
                    "index": 0
                }],
                "usage": usage_info if usage_info else {
                    "prompt_tokens": 0,
                    "completion_tokens": 0,
                    "total_tokens": 0
                }
            }
            
            return response
            
        except Exception as e:
            print(f"Error in _handle_stream_response: {e}")
            traceback.print_exc()
            return {"error": str(e)}

    def format_response(self, response_data: Dict[str, Any]) -> UnifiedChatResponse:
        """
        将原始响应数据格式化为标准结构。
        将 Coze 的响应格式转换为统一的响应格式。

        参数:
            response_data (Dict[str, Any]): 原始响应数据

        返回:
            UnifiedChatResponse: 标准化后的响应字典
        """
        try:
            # 检查是否有错误
            if "error" in response_data:
                # 返回错误响应
                return UnifiedChatResponse(
                    id="error",
                    model="coze",
                    usage=Usage(prompt_tokens=0, completion_tokens=0, total_tokens=0),
                    choices=[Choice(
                        message=Message(role="assistant", content=f"Error: {response_data['error']}"),
                        finish_reason="error",
                        index=0
                    )]
                )
            
            # 构建标准响应格式
            choices = []
            if response_data.get("choices"):
                for idx, choice in enumerate(response_data["choices"]):
                    message_data = choice.get("message", {})
                    choices.append(Choice(
                        message=Message(
                            role=message_data.get("role", "assistant"),
                            content=message_data.get("content", "")
                        ),
                        finish_reason=choice.get("finish_reason", "stop"),
                        index=idx
                    ))
            
            usage_data = response_data.get("usage", {})
            usage = Usage(
                prompt_tokens=usage_data.get("prompt_tokens", 0),
                completion_tokens=usage_data.get("completion_tokens", 0),
                total_tokens=usage_data.get("total_tokens", 0)
            )
            
            return UnifiedChatResponse(
                id=response_data.get("id", ""),
                model=response_data.get("model", "coze"),
                usage=usage,
                choices=choices
            )
            
        except Exception as e:
            print(f"Error in format_response: {e}")
            traceback.print_exc()
            # 返回错误响应
            return UnifiedChatResponse(
                id="error",
                model="coze",
                usage=Usage(prompt_tokens=0, completion_tokens=0, total_tokens=0),
                choices=[Choice(
                    message=Message(role="assistant", content=f"Format error: {str(e)}"),
                    finish_reason="error",
                    index=0
                )]
            )

# 注册 Coze Agent
registry.register("coze", CozeAgent())