from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any

class ChatRequest(BaseModel):
    """
    前端请求统一数据模型

    说明:
        - query: 所有 Agent 必须要求前端传递，表示用户输入的对话内容（必填）
        - 其他字段为可选，各 Agent 可按需提取，在 Agent 中需要对该必填字段进行校验
    """
    query: str = Field(..., description="用户输入的对话内容，所有Agent必填")
    user: Optional[str] = Field(None, description="用户标识")
    stream: Optional[bool] = Field(False, description="是否流式返回")
    app_id: Optional[str] = Field(None, description="应用ID")
    chat_id: Optional[str] = Field(None, description="会话ID")
    files: Optional[List[Any]] = Field(None, description="上传的文件列表")
    conversation_id: Optional[str] = Field("", description="会话标识，用于多轮对话")
