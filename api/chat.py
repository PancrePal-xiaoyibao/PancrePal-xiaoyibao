from fastapi import APIRouter, Request, HTTPException, Depends
from fastapi.responses import JSONResponse, StreamingResponse
import asyncio
from typing import List, Dict, Optional
from agent import registry
from agent.models import ChatRequest, UnifiedChatResponse
from auth.dependencies import get_api_key_user, check_api_limit, increment_api_calls
from models.user import UserResponse

chat = APIRouter()


@chat.post("/chat", response_model=UnifiedChatResponse)
async def get_chat(
    request: Request, 
    body: ChatRequest,
    current_user: UserResponse = Depends(get_api_key_user)
):
    """
    聊天API（仅支持API Key认证）
    
    此端点专门为API Key用户设计，提供稳定的聊天服务。
    用户需要先登录获取JWT令牌，然后使用JWT创建API Key，最后使用API Key访问此接口。
    """
    # 检查API调用限制
    if not check_api_limit(current_user.id):
        raise HTTPException(
            status_code=429, 
            detail="API调用次数超限，请稍后重试或联系管理员"
        )
    
    agent_name = (
        request.headers.get("agent")
        or request.headers.get("Agent")
        or request.headers.get("x-agent")
        or request.headers.get("X-Agent")
        or request.query_params.get("agent")
        or ""
    ).lower()
    
    if not agent_name:
        return JSONResponse(content={
            "error": "Missing agent header. Please set 'agent: fastgpt' or 'x-agent: fastgpt'"
        }, status_code=400)
    
    agent = registry.get(agent_name)
    if not agent:
        return JSONResponse(content={
            "error": f"Unknown agent: {agent_name}"
        }, status_code=400)
    
    # 调试信息：打印 agent 类型和名称
    print(f"Debug: Agent type: {type(agent)}, Agent name: {agent_name}")
    print(f"Debug: Available agents: {list(registry.list_agents().keys())}")
    
    request_data = body.model_dump()  # 使用 model_dump() 替代 dict()
    if not agent.validate_request(request_data):
        return JSONResponse(content={
            "error": f"Invalid request for agent: {agent_name}"
        }, status_code=400)
    
    try:
        # 增加API调用次数
        await increment_api_calls(current_user.id)
        
        # 如果是流式且非 detail 模式，使用 SSE
        if request_data.get("stream") and not request_data.get("detail"):
            print(f"Debug: Using streaming mode for agent: {type(agent)}")
            loop = asyncio.get_event_loop()
            generator = await loop.run_in_executor(
                None,
                lambda: agent.stream_chat(request_data)
            )
            return StreamingResponse(generator, media_type="text/event-stream")

        loop = asyncio.get_event_loop()
        response_data = await loop.run_in_executor(
            None,
            lambda: agent.process_request(request_data)
        )
        result = agent.format_response(response_data)
        return JSONResponse(content=result.model_dump(exclude_none=True))
    except Exception as e:
        import traceback
        traceback.print_exc()
        return JSONResponse(content={
            "error": str(e)
        }, status_code=500)