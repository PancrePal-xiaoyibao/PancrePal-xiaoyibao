from fastapi import FastAPI
from fastapi.responses import StreamingResponse, JSONResponse
from dotenv import load_dotenv
import os
from agent.dify import send_chat_message

load_dotenv()
dify_base_url = os.getenv("DIFY_BASE_URL")
dify_api_key = os.getenv("DIFY_API_KEY")
print(f"DIFY_BASE_URL: {dify_base_url}")

app = FastAPI()

@app.get("/chat")
def chat(query: str, response_mode: str = "blocking", conversation_id: str = ""):
    """
    处理聊天请求，调用 Dify 服务。
    
    参数:
        query (str): 用户输入的提问内容。
        response_mode (str): 响应模式，默认为 "blocking"。
        conversation_id (str): 会话 ID，用于多轮对话（可选）。
    
    返回:
        str: Dify 服务的响应内容。
    """
    response = send_chat_message(
        dify_api_key,
        dify_base_url,
        query=query,
        response_mode=response_mode,
        conversation_id=conversation_id
    )
    if response_mode == "streaming":
        # 流式返回
        def event_stream():
            for line in response.iter_lines(decode_unicode=True):
                if line:
                    yield line + "\n"
        return StreamingResponse(event_stream(), media_type="text/plain")
    else:
        # 普通返回
        return JSONResponse(content=response.json())