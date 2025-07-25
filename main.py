from fastapi import FastAPI, Request
from fastapi.responses import StreamingResponse, JSONResponse
from api.chat import chat
from api.upload import upload
from agent.loader import load_agents
from dotenv import load_dotenv
import os

load_dotenv()
dify_base_url = os.getenv("DIFY_BASE_URL")
dify_api_key = os.getenv("DIFY_API_KEY")
print(f"DIFY_BASE_URL: {dify_base_url}")

fastgpt_base_url = os.getenv("FASTGPT_BASE_URL")
fastgpt_api_key = os.getenv("FASTGPT_API_KEY")
print(f"FASTGPT_BASE_URL: {fastgpt_base_url}")

# 加载智能体
load_agents()

app = FastAPI()

app.include_router(chat, prefix="/api/v1", tags=["聊天"])
app.include_router(upload, prefix="/api/v1", tags=["文件上传"])