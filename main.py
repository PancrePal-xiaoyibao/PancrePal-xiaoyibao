from fastapi import FastAPI, Request
from fastapi.responses import StreamingResponse, JSONResponse
from api.chat import chat
from dotenv import load_dotenv
import os

load_dotenv()
dify_base_url = os.getenv("DIFY_BASE_URL")
dify_api_key = os.getenv("DIFY_API_KEY")
print(f"DIFY_BASE_URL: {dify_base_url}")

app = FastAPI()

app.include_router(chat, prefix="/api/v1", tags=["聊天"])