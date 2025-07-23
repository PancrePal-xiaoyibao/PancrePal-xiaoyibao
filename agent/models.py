from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any

class Message(BaseModel):
    role: str = Field(..., description="消息角色，如 assistant 或 user")
    content: str = Field(..., description="消息内容")

class Choice(BaseModel):
    message: Message = Field(..., description="消息对象")
    finish_reason: Optional[str] = Field(None, description="结束原因")
    index: int = Field(..., description="选项索引")

class Usage(BaseModel):
    prompt_tokens: int = Field(..., description="提示词 tokens 数")
    completion_tokens: int = Field(..., description="生成 tokens 数")
    total_tokens: int = Field(..., description="总 tokens 数")

class ChatResponse(BaseModel):
    """
    统一响应数据模型
    """
    id: str = Field(..., description="会话ID")
    model: str = Field(..., description="使用的模型名称")
    usage: Usage = Field(..., description="tokens 使用情况")
    choices: List[Choice] = Field(..., description="响应选项列表")

class ChatRequest(BaseModel):
    """
    前端请求统一数据模型

    说明:
        - query: 所有 Agent 必须要求前端传递，表示用户输入的对话内容（必填）
        - 其他字段为可选，各 Agent 可按需提取，在 Agent 中需要对该必填字段进行校验
    """
    query: str = Field(..., description="用户输入的对话内容，所有Agent必填")
    user: Optional[str] = Field(None, description="用户标识")
    uid: Optional[str] = Field(None, description="用户ID")
    stream: Optional[bool] = Field(False, description="是否流式返回")
    app_id: Optional[str] = Field(None, description="应用ID")
    chat_id: Optional[str] = Field(None, description="会话ID")
    files: Optional[List[Any]] = Field(None, description="上传的文件列表")
    conversation_id: Optional[str] = Field("", description="会话标识，用于多轮对话")
    detail: Optional[bool] = Field(False, description="是否返回详细信息（模块状态等）")