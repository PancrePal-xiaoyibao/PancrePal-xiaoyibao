from fastapi import APIRouter, Request, HTTPException
from pydantic import BaseModel
from fastapi.responses import JSONResponse
import asyncio
from typing import List, Dict, Optional
from agent import registry  # Import the registry instead of individual agents

# 定义请求体模型
class ChatRequest(BaseModel):
    app_id: Optional[str] = None
    chat_id: Optional[str] = None
    stream: bool = False
    detail: bool = False
    query: str
    conversation_id: str = ""
    files: list = []
    user: Optional[str] = None

chat = APIRouter()

@chat.post("/chat")
async def get_chat(request: Request, body: ChatRequest):
    agent_name = request.headers.get("agent", "").lower()
    
    if not agent_name:
        return JSONResponse(content={
            "error": "Missing agent header"
        }, status_code=400)
    
    # Get the agent from the registry
    agent = registry.get(agent_name)
    
    if not agent:
        return JSONResponse(content={
            "error": f"Unknown agent: {agent_name}"
        }, status_code=400)
    
    # Convert the request body to a dictionary
    request_data = body.dict()
    
    # Validate the request
    if not agent.validate_request(request_data):
        return JSONResponse(content={
            "error": f"Invalid request for agent: {agent_name}"
        }, status_code=400)
    
    try:
        # Process the request (handle both sync and async agents)
        loop = asyncio.get_event_loop()
        response_data = await loop.run_in_executor(
            None,
            lambda: agent.process_request(request_data)
        )
        
        # Format the response
        result = agent.format_response(response_data)
        
        return JSONResponse(content=result)
        
    except Exception as e:
        import traceback
        traceback.print_exc()
        return JSONResponse(content={
            "error": str(e)
        }, status_code=500)