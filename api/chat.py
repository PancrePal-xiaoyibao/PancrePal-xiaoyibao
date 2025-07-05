from fastapi import APIRouter, Request
from pydantic import BaseModel
from fastapi.responses import StreamingResponse, JSONResponse
import agent.dify as dify
import agent.fastgpt as fastgpt
import asyncio
from typing import List, Dict, Optional

"""
 messages: List[Dict[str, str]],
    app_id: Optional[str] = None,
    chat_id: Optional[str] = None,
    stream: bool = False,
    detail: bool = False,
    response_chat_item_id: Optional[str] = None,
    variables: Optional[Dict[str, str]] = None
"""

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
    agent = request.headers.get("agent", "").lower()
    if agent == "dify":
        # ...existing dify code...
        pass

    if agent == "fastgpt":
        messages = [
            {"role": "user", "content": body.query}
        ]
        variables = {
            "uid": body.user
        }
        loop = asyncio.get_event_loop()
        result = await loop.run_in_executor(
            None,
            lambda: fastgpt.chat_completions(
                messages=messages,
                app_id=body.app_id,             
                chat_id=body.chat_id,         
                variables=variables,
                stream=body.stream,
                detail=body.detail
            )
        )
        return JSONResponse(content=result)

    return {"message": "Hello, this is a test chat response!"}