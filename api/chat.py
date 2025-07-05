from fastapi import APIRouter
from pydantic import BaseModel
import agent.dify as dify

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
        resp = dify.send_chat_message(
            api_key=dify.dify_api_key,
            user=response.user,
            base_url=dify.dify_base_url,
            query=response.query,
            response_mode=response.response_mode,
            conversation_id=response.conversation_id,
            files=response.files
        )
        if response.response_mode == "streaming":
            # 流式返回
            from fastapi.responses import StreamingResponse
            def event_stream():
                for line in resp.iter_lines(decode_unicode=True):
                    if line:
                        yield line + "\n"
            return StreamingResponse(event_stream(), media_type="text/plain")
        else:
            # 普通 JSON 返回
            return resp.json()
    return {"message": "Hello, this is a test chat response!"}