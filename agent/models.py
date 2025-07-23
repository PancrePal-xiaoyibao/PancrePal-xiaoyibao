from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any, Union

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

# FastGPT Detail 模式的数据模型
class QuoteItem(BaseModel):
    """引用项"""
    dataset_id: str = Field(..., description="数据集ID")
    id: str = Field(..., description="项目ID")
    q: str = Field(..., description="问题")
    a: str = Field(..., description="答案")
    source: str = Field(..., description="来源")

class CompleteMessage(BaseModel):
    """完整消息"""
    obj: str = Field(..., description="消息对象类型，如 System, Human, AI")
    value: str = Field(..., description="消息内容")

class ResponseDataModule(BaseModel):
    """响应数据模块 - FastGPT detail=true 时的模块信息"""
    moduleName: str = Field(..., description="模块名称")
    price: Optional[float] = Field(None, description="模块价格")
    model: Optional[str] = Field(None, description="使用的模型")
    tokens: Optional[int] = Field(None, description="tokens 数量")
    
    # Dataset Search 模块特有字段
    similarity: Optional[float] = Field(None, description="相似度")
    limit: Optional[int] = Field(None, description="限制数量")
    
    # AI Chat 模块特有字段
    question: Optional[str] = Field(None, description="问题")
    answer: Optional[str] = Field(None, description="答案")
    maxToken: Optional[int] = Field(None, description="最大 token 数")
    quoteList: Optional[List[QuoteItem]] = Field(None, description="引用列表")
    completeMessages: Optional[List[CompleteMessage]] = Field(None, description="完整消息列表")
    
    # 其他可能的字段
    runningTime: Optional[float] = Field(None, description="运行时间")
    totalPoints: Optional[float] = Field(None, description="总点数")
    inputTokens: Optional[int] = Field(None, description="输入 tokens")
    outputTokens: Optional[int] = Field(None, description="输出 tokens")
    reasoningText: Optional[str] = Field(None, description="推理文本")
    historyPreview: Optional[List[Dict[str, str]]] = Field(None, description="历史预览")
    contextTotalLen: Optional[int] = Field(None, description="上下文总长度")
    finishReason: Optional[str] = Field(None, description="完成原因")
    nodeId: Optional[str] = Field(None, description="节点ID")
    moduleType: Optional[str] = Field(None, description="模块类型")
    id: Optional[str] = Field(None, description="模块ID")

class StandardChatResponse(BaseModel):
    """
    标准聊天响应格式 (detail=false)
    """
    id: str = Field(..., description="会话ID")
    model: str = Field(..., description="使用的模型名称")
    usage: Usage = Field(..., description="tokens 使用情况")
    choices: List[Choice] = Field(..., description="响应选项列表")

class DetailedChatResponse(BaseModel):
    """
    详细聊天响应格式 (detail=true)
    """
    responseData: List[ResponseDataModule] = Field(..., description="详细的模块响应数据")

class UnifiedChatResponse(BaseModel):
    """
    统一聊天响应格式 - 支持两种模式
    """
    # 标准模式字段 (detail=false)
    id: Optional[str] = Field(None, description="会话ID")
    model: Optional[str] = Field(None, description="使用的模型名称")
    usage: Optional[Usage] = Field(None, description="tokens 使用情况")
    choices: Optional[List[Choice]] = Field(None, description="响应选项列表")
    
    # 详细模式字段 (detail=true)
    responseData: Optional[List[ResponseDataModule]] = Field(None, description="详细的模块响应数据")
    
    # 其他可能的通用字段
    newVariables: Optional[Dict[str, Any]] = Field(None, description="新变量")

# 保持原有的 ChatResponse 作为别名，确保向后兼容
ChatResponse = StandardChatResponse

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