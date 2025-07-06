from fastapi import APIRouter, Request, HTTPException
from fastapi.responses import JSONResponse
import asyncio
from typing import List, Dict, Optional
from agent import registry
from agent.models import ChatRequest

chat = APIRouter()

@chat.post("/chat")
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
    
    request_data = body.dict()
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
        return JSONResponse(content=result)
    except Exception as e:
        import traceback
        traceback.print_exc()
        return JSONResponse(content={
            "error": str(e)
        }, status_code=500)