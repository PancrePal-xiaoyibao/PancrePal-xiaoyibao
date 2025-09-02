from fastapi import FastAPI, Request
from fastapi.responses import StreamingResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from api.chat import chat
from api.upload import upload
from api.agents import agents
from api.auth import auth
from agent.loader import load_agents
from database.connection import db_manager
from dotenv import load_dotenv
import os
import logging

# 加载环境变量
load_dotenv()

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# 环境变量配置
dify_base_url = os.getenv("DIFY_BASE_URL")
dify_api_key = os.getenv("DIFY_API_KEY")
print(f"DIFY_BASE_URL: {dify_base_url}")

fastgpt_base_url = os.getenv("FASTGPT_BASE_URL")
fastgpt_api_key = os.getenv("FASTGPT_API_KEY")
print(f"FASTGPT_BASE_URL: {fastgpt_base_url}")

# 加载智能体
load_agents()

# 创建FastAPI应用
app = FastAPI(
    title="小胰宝智能助手平台",
    description="基于多AI平台的智能体系统，支持用户认证和权限管理",
    version="0.2.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# 添加CORS中间件
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 在生产环境中应该限制具体域名
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 启动事件：连接数据库
@app.on_event("startup")
async def startup_event():
    """应用启动时执行"""
    try:
        # 连接MongoDB数据库
        db_manager.connect()
        logger.info("✅ 数据库连接成功")
        
        # 加载智能体
        logger.info("✅ 智能体加载完成")
        
    except Exception as e:
        logger.error(f"❌ 应用启动失败: {str(e)}")
        raise

# 关闭事件：关闭数据库连接
@app.on_event("shutdown")
async def shutdown_event():
    """应用关闭时执行"""
    try:
        # 关闭数据库连接
        db_manager.close()
        logger.info("✅ 数据库连接已关闭")
    except Exception as e:
        logger.error(f"❌ 关闭数据库连接失败: {str(e)}")

# 健康检查端点
@app.get("/health", tags=["系统"])
async def health_check():
    """健康检查"""
    return {
        "status": "healthy",
        "timestamp": "2024-01-01T00:00:00Z",
        "version": "0.2.0",
        "database": "connected" if db_manager.db else "disconnected"
    }

# 包含路由
app.include_router(auth, prefix="/api/v1/auth", tags=["用户认证"])
app.include_router(chat, prefix="/api/v1", tags=["聊天"])
app.include_router(upload, prefix="/api/v1", tags=["文件上传"])
app.include_router(agents, prefix="/api/v1/agents", tags=["智能体管理"])

if __name__ == "__main__":
    import uvicorn
    print("🚀 启动小胰宝智能助手平台...")
    print("📖 API文档: http://localhost:8000/docs")
    print("🔐 用户认证: http://localhost:8000/api/v1/auth/")
    print("🔍 智能体管理: http://localhost:8000/api/v1/agents/")
    print("💚 健康检查: http://localhost:8000/health")
    print("\n按 Ctrl+C 停止服务")
    
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )