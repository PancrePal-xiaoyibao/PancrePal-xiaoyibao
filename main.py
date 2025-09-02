from fastapi import FastAPI, Request
from fastapi.responses import StreamingResponse, JSONResponse
from api.chat import chat
from api.upload import upload
from api.agents import agents
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

app = FastAPI(
    title="小胰宝智能助手平台",
    description="基于多AI平台的智能体系统",
    version="0.1.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

app.include_router(chat, prefix="/api/v1", tags=["聊天"])
app.include_router(upload, prefix="/api/v1", tags=["文件上传"])
app.include_router(agents, prefix="/api/v1/agents", tags=["智能体管理"])

if __name__ == "__main__":
    import uvicorn
    print("🚀 启动小胰宝智能助手平台...")
    print("📖 API文档: http://localhost:8000/docs")
    print("🔍 智能体管理: http://localhost:8000/api/v1/agents/")
    print("\n按 Ctrl+C 停止服务")
    
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )