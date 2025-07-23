from fastapi import APIRouter, Request, HTTPException
from fastapi.responses import JSONResponse
import asyncio
from typing import List, Dict, Optional
from agent import registry
from agent.models import ChatRequest, UnifiedChatResponse

chat = APIRouter()

@chat.post("/chat", response_model=UnifiedChatResponse)
async def get_chat(request: Request, body: ChatRequest):
    agent_name = request.headers.get("agent", "").lower()
    
    if not agent_name:
        return JSONResponse(content={
            "error": "Missing agent header"
        }, status_code=400)
    
    agent = registry.get(agent_name)
    if not agent:
        return JSONResponse(content={
            "error": f"Unknown agent: {agent_name}"
        }, status_code=400)
    
    request_data = body.model_dump()  # 使用 model_dump() 替代 dict()
    if not agent.validate_request(request_data):
        return JSONResponse(content={
            "error": f"Invalid request for agent: {agent_name}"
        }, status_code=400)
    
    try:
        loop = asyncio.get_event_loop()
        response_data = await loop.run_in_executor(
            None,
            lambda: agent.process_request(request_data)
        )
        result = agent.format_response(response_data)
        # 将 Pydantic 模型转换为字典，用于 JSON 序列化
        return JSONResponse(content=result.model_dump(exclude_none=True))
    except Exception as e:
        import traceback
        traceback.print_exc()
        return JSONResponse(content={
            "error": str(e)
        }, status_code=500)