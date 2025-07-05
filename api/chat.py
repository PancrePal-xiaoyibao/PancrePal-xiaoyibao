from fastapi import APIRouter
from pydantic import BaseModel
from fastapi.responses import StreamingResponse, JSONResponse
import agent.dify as dify
import asyncio

# 定义前端传入的请求体格式
class ChatRequest(BaseModel):
    agent: str # 需要指定后端使用的 agent 名称
    user: str # 用户标识，用来定义终端用户的身份
    query: str # 用户问题
    response_mode: str = "streaming"  # 默认值为 "streaming"
    conversation_id: str = ""  # 可选参数
    files: list = []  # 可选参数，文件列表

chat = APIRouter()

@chat.post("/chat")
async def get_chat(response: ChatRequest):
    if response.agent == "dify":
        if response.response_mode == "streaming":
            # 异步流式返回
            async def event_stream():
                async with await dify.send_chat_message(
                    api_key=dify.dify_api_key,
                    user=response.user,
                    base_url=dify.dify_base_url,
                    query=response.query,
                    response_mode=response.response_mode,
                    conversation_id=response.conversation_id,
                    files=response.files
                ) as resp:
                    async for line in resp.aiter_lines():
                        if line:
                            yield line + "\n"
            return StreamingResponse(event_stream(), media_type="text/plain")
        else:
            resp = await dify.send_chat_message(
                api_key=dify.dify_api_key,
                user=response.user,
                base_url=dify.dify_base_url,
                query=response.query,
                response_mode=response.response_mode,
                conversation_id=response.conversation_id,
                files=response.files
            )
            return JSONResponse(content=resp.json())
    return {"message": "Hello, this is a test chat response!"}