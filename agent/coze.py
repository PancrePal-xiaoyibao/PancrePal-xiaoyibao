import os
import json
from typing import Dict, Any, List, Optional
from .base import BaseAgent
from .registry import registry
from .models import ChatRequest, UnifiedChatResponse, Message, Choice, Usage
from dotenv import load_dotenv
from cozepy import Coze, TokenAuth, COZE_CN_BASE_URL, Message as CozeMessage, ChatEventType, ChatStatus, MessageType
import traceback

if os.path.exists('.env'):
    load_dotenv('.env')

# 环境变量配置 - 使用与测试文件一致的变量名
coze_api_token = os.getenv("COZE_API_TOKEN")
coze_base_url = os.getenv("COZE_BASE_URL", COZE_CN_BASE_URL)
coze_bot_id = os.getenv("COZE_BOT_ID")

# 初始化扣子客户端
if coze_api_token:
    coze = Coze(auth=TokenAuth(coze_api_token), base_url=coze_base_url)
else:
    coze = None

class CozeAgent(BaseAgent):
    """Agent for Coze API."""

    def __init__(self):
        # 可在此初始化所需的环境变量或配置
        self.api_token = coze_api_token
        self.base_url = coze_base_url
        self.bot_id = coze_bot_id
        
        # 验证必要的环境变量（但不抛出异常，让 loader 处理）
        if not self.api_token:
            print("Warning: COZE_API_TOKEN not found in environment variables")
        if not self.bot_id:
            print("Warning: COZE_BOT_ID not found in environment variables")

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
            
            # 根据 stream 参数选择处理方式
            if stream:
                return self._handle_stream_response(user_id, additional_messages, conversation_id)
            else:
                return self._handle_blocking_response(user_id, additional_messages, conversation_id)
            
        except Exception as e:
            print(f"Error in process_request: {e}")
            traceback.print_exc()
            return {"error": str(e), "error_type": "process_error"}

    def _handle_blocking_response(self, user_id: str, additional_messages: List[CozeMessage], conversation_id: Optional[str] = None) -> Dict[str, Any]:
        """处理非流式响应，基于实际的Coze响应结构优化"""
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
            
            # 检查聊天状态
            if not hasattr(chat_result, 'chat') or not chat_result.chat:
                return {"error": "No chat object in response", "error_type": "response_error"}
            
            chat = chat_result.chat
            
            # 检查聊天是否完成
            if chat.status != ChatStatus.COMPLETED:
                error_msg = f"Chat not completed. Status: {chat.status}"
                if chat.last_error:
                    error_msg += f", Error: {chat.last_error}"
                return {"error": error_msg, "error_type": "chat_status_error"}
            
            # 构建基础响应结构
            response = {
                "id": chat.id,
                "conversation_id": chat.conversation_id,
                "model": "coze",
                "status": str(chat.status),
                "created_at": getattr(chat, 'created_at', None),
                "completed_at": getattr(chat, 'completed_at', None),
                "choices": [],
                "usage": {
                    "prompt_tokens": 0,
                    "completion_tokens": 0,
                    "total_tokens": 0
                }
            }
            
            # 处理使用量信息
            if hasattr(chat, 'usage') and chat.usage:
                usage = chat.usage
                response["usage"] = {
                    "prompt_tokens": getattr(usage, 'input_count', 0),
                    "completion_tokens": getattr(usage, 'output_count', 0),
                    "total_tokens": getattr(usage, 'token_count', 0)
                }
            
            # 处理消息内容
            if hasattr(chat_result, 'messages') and chat_result.messages:
                # 分类处理不同类型的消息
                answer_content = []
                follow_up_questions = []
                verbose_info = []
                
                for message in chat_result.messages:
                    if not hasattr(message, 'role') or not hasattr(message, 'type'):
                        continue
                    
                    # 只处理 assistant 角色的消息
                    if message.role.value == 'assistant':
                        content = getattr(message, 'content', '')
                        
                        if message.type == MessageType.ANSWER:
                            # 主要回答内容
                            answer_content.append(content)
                        elif message.type == MessageType.FOLLOW_UP:
                            # 跟进问题
                            follow_up_questions.append(content)
                        elif message.type == MessageType.VERBOSE:
                            # 详细信息（通常是系统信息）
                            verbose_info.append(content)
                
                # 构建最终回答内容
                final_content = '\n'.join(answer_content) if answer_content else ""
                
                # 如果没有主要回答，但有其他内容，使用它们
                if not final_content and (follow_up_questions or verbose_info):
                    final_content = "抱歉，没有收到有效的回答内容。"
                
                # 添加跟进问题（可选）
                if follow_up_questions:
                    final_content += f"\n\n相关问题推荐：\n" + '\n'.join(f"• {q}" for q in follow_up_questions[:3])
                
                response["choices"] = [{
                    "message": {
                        "role": "assistant",
                        "content": final_content or "抱歉，没有收到有效响应"
                    },
                    "finish_reason": "stop",
                    "index": 0
                }]
                
                # 添加额外的消息元数据
                response["metadata"] = {
                    "answer_count": len(answer_content),
                    "follow_up_count": len(follow_up_questions),
                    "verbose_count": len(verbose_info),
                    "total_messages": len(list(chat_result.messages))
                }
                
            else:
                # 没有消息的情况
                response["choices"] = [{
                    "message": {
                        "role": "assistant",
                        "content": "抱歉，没有收到任何响应消息"
                    },
                    "finish_reason": "no_content",
                    "index": 0
                }]
                response["metadata"] = {
                    "answer_count": 0,
                    "follow_up_count": 0,
                    "verbose_count": 0,
                    "total_messages": 0
                }
                
            return response
            
        except Exception as e:
            print(f"Error in _handle_blocking_response: {e}")
            traceback.print_exc()
            return {"error": str(e), "error_type": "api_error"}

    def stream_chat(self, request_data: Dict[str, Any]):
        """
        以 SSE 形式流式转发 Coze 的响应（stream=true）。
        """
        if not coze:
            raise ValueError("Coze client not initialized. Please check COZE_API_TOKEN.")

        # 获取用户输入
        query = request_data.get('query', '')
        user_id = request_data.get('user', 'default_user')
        conversation_id = request_data.get('conversation_id')
        
        # 构建消息
        additional_messages = [CozeMessage.build_user_question_text(query)]
        
        kwargs = {
            "bot_id": self.bot_id,
            "user_id": user_id,
            "additional_messages": additional_messages
        }
        
        if conversation_id:
            kwargs["conversation_id"] = conversation_id

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

            try:
                # 流式处理
                for event in coze.chat.stream(**kwargs):
                    if event.event == ChatEventType.CONVERSATION_MESSAGE_DELTA:
                        if hasattr(event.message, 'content') and event.message.content:
                            # 过滤掉系统控制信息
                            content_chunk = event.message.content
                            if content_chunk and not content_chunk.startswith('{"msg_type":'):
                                yield sse_wrap(build_delta(content_chunk))
                                prev += content_chunk
                        
                    if event.event == ChatEventType.CONVERSATION_CHAT_COMPLETED:
                        # 发送结束片段（finish_reason=stop）
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
            except Exception as e:
                err_payload = build_delta(f"[stream error] {e}")
                yield sse_wrap(err_payload)

        return event_generator()

    def upload_file(self, file_path: str) -> Any:
        """
        将本地临时文件上传到 Coze，并返回统一文件信息 FastGPTFileInfo。
        使用 Coze 的文件上传接口。
        """
        if not self.api_token:
            raise ValueError("Coze client not initialized. Please check COZE_API_TOKEN.")
        
        try:
            import requests
            import mimetypes
            import time
            
            # 提取原始文件名（upload.py 会以 _{filename} 作为后缀创建临时文件）
            original_name = os.path.basename(file_path)
            if "_" in original_name:
                original_name = original_name.split("_", 1)[1] or original_name

            # 猜测 MIME 类型
            mime_type = mimetypes.guess_type(original_name)[0] or "application/octet-stream"
            file_size = os.path.getsize(file_path)
            
            # 构建请求URL
            upload_url = f"{self.base_url}/v1/files/upload"
            
            # 构建请求头 - 按照 Coze 文档格式
            headers = {
                "Authorization": f"Bearer {self.api_token}",
                "Content-Type": "multipart/form-data"
            }
            
            # 打开文件并上传
            with open(file_path, 'rb') as file:
                files = {
                    'file': (original_name, file, mime_type)
                }
                
                # 发送POST请求
                response = requests.post(upload_url, headers=headers, files=files)
                response.raise_for_status()
                
                # 解析响应
                result = response.json()
                
                # 构造统一文件信息（Coze 可能返回简单的文件信息）
                file_info = self.build_file_info(
                    file_id=result.get("id", ""),
                    file_name=result.get("name", original_name),
                    size_bytes=result.get("size", file_size),
                    mime_type=result.get("mime_type", mime_type),
                    created_by=result.get("created_by", "uploader"),
                    created_at=result.get("created_at", int(time.time()))
                )
                return file_info
                
        except requests.exceptions.RequestException as e:
            print(f"HTTP request error: {e}")
            traceback.print_exc()
            raise e
        except Exception as e:
            print(f"Error uploading file: {e}")
            traceback.print_exc()
            raise e
        
    def format_response(self, response_data: Dict[str, Any]) -> UnifiedChatResponse:
        """
        将原始响应数据格式化为标准结构。
        将 Coze 的响应格式转换为统一的响应格式，增强错误处理。

        参数:
            response_data (Dict[str, Any]): 原始响应数据

        返回:
            UnifiedChatResponse: 标准化后的响应字典
        """
        try:
            # 检查是否有错误
            if "error" in response_data:
                error_type = response_data.get("error_type", "unknown_error")
                error_msg = response_data["error"]
                
                # 根据错误类型提供更友好的错误信息
                user_friendly_errors = {
                    "process_error": "处理请求时发生错误",
                    "response_error": "响应格式异常",
                    "chat_status_error": "对话状态异常",
                    "api_error": "API调用失败",
                    "unknown_error": "未知错误"
                }
                
                friendly_msg = user_friendly_errors.get(error_type, "系统错误")
                
                return UnifiedChatResponse(
                    id="error",
                    model="coze",
                    usage=Usage(prompt_tokens=0, completion_tokens=0, total_tokens=0),
                    choices=[Choice(
                        message=Message(
                            role="assistant", 
                            content=f"{friendly_msg}: {error_msg}"
                        ),
                        finish_reason="error",
                        index=0
                    )]
                )
            
            # 构建标准响应格式
            choices = []
            if response_data.get("choices"):
                for idx, choice in enumerate(response_data["choices"]):
                    message_data = choice.get("message", {})
                    finish_reason = choice.get("finish_reason", "stop")
                    
                    # 确保finish_reason的有效性
                    valid_finish_reasons = ["stop", "length", "content_filter", "error", "no_content"]
                    if finish_reason not in valid_finish_reasons:
                        finish_reason = "stop"
                    
                    choices.append(Choice(
                        message=Message(
                            role=message_data.get("role", "assistant"),
                            content=message_data.get("content", "")
                        ),
                        finish_reason=finish_reason,
                        index=idx
                    ))
            else:
                # 如果没有choices，创建默认的空响应
                choices.append(Choice(
                    message=Message(role="assistant", content="没有可用的响应内容"),
                    finish_reason="no_content",
                    index=0
                ))
            
            # 处理使用量信息
            usage_data = response_data.get("usage", {})
            usage = Usage(
                prompt_tokens=usage_data.get("prompt_tokens", 0),
                completion_tokens=usage_data.get("completion_tokens", 0),
                total_tokens=usage_data.get("total_tokens", 0)
            )
            
            # 构建响应，包含额外的元数据
            unified_response = UnifiedChatResponse(
                id=response_data.get("id", ""),
                model=response_data.get("model", "coze"),
                usage=usage,
                choices=choices
            )
            
            # 如果有元数据，可以添加到newVariables中（用于调试和监控）
            if "metadata" in response_data:
                unified_response.newVariables = {
                    "coze_metadata": response_data["metadata"],
                    "conversation_id": response_data.get("conversation_id", ""),
                    "status": response_data.get("status", ""),
                    "created_at": response_data.get("created_at"),
                    "completed_at": response_data.get("completed_at")
                }
            
            return unified_response
            
        except Exception as e:
            print(f"Error in format_response: {e}")
            traceback.print_exc()
            # 返回错误响应
            return UnifiedChatResponse(
                id="format_error",
                model="coze",
                usage=Usage(prompt_tokens=0, completion_tokens=0, total_tokens=0),
                choices=[Choice(
                    message=Message(
                        role="assistant", 
                        content=f"响应格式化失败: {str(e)}"
                    ),
                    finish_reason="error",
                    index=0
                )]
            )

# 注册 Coze Agent（只有在环境变量配置完整时才注册）
if coze_api_token and coze_bot_id:
    registry.register("coze", CozeAgent())