from fastapi import FastAPI, Request
from fastapi.responses import StreamingResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from api.chat import chat
from api.upload import upload
from api.agents import agents
from api.mcp import mcp_router
from api.auth import router as auth
from api.api_keys import router as api_keys
from agent.loader import load_agents
from database.connection import db_manager
from dotenv import load_dotenv
import os
import logging
from contextlib import asynccontextmanager
from datetime import datetime
import time
import json
from fastapi.openapi.utils import get_openapi

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# 有条件加载 .env：存在则加载，否则依赖系统环境变量
if os.path.exists('.env'):
    load_dotenv('.env')
    logger.info("加载 .env 环境变量文件")
else:
    logger.info("未找到 .env 文件，使用系统环境变量")

# 环境变量配置
dify_base_url = os.getenv("DIFY_BASE_URL")
dify_api_key = os.getenv("DIFY_API_KEY")
print(f"DIFY_BASE_URL: {dify_base_url}")

fastgpt_base_url = os.getenv("FASTGPT_BASE_URL")
fastgpt_api_key = os.getenv("FASTGPT_API_KEY")
print(f"FASTGPT_BASE_URL: {fastgpt_base_url}")


@asynccontextmanager
async def lifespan(app: FastAPI):
    """应用生命周期管理：启动时连接DB并加载智能体，关闭时断开DB。"""
    try:
        # 连接MongoDB数据库
        db_manager.connect()
        logger.info("✅ 数据库连接成功")

        # 加载智能体
        load_agents()
        logger.info("✅ 智能体加载完成")

        yield
    finally:
        try:
            db_manager.close()
            logger.info("✅ 数据库连接已关闭")
        except Exception as e:
            logger.error(f"❌ 关闭数据库连接失败: {str(e)}")


# 创建FastAPI应用
app = FastAPI(
    title="小胰宝智能助手平台",
    description="基于多AI平台的智能体系统，支持用户认证和权限管理",
    version="0.2.0",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan
)

# 请求/响应日志中间件
@app.middleware("http")
async def request_logging_middleware(request: Request, call_next):
    start_time = time.time()
    client_ip = request.headers.get("x-forwarded-for") or request.client.host if request.client else "unknown"
    # 兼容多级代理，取第一个IP
    if isinstance(client_ip, str) and "," in client_ip:
        client_ip = client_ip.split(",")[0].strip()

    # 提取agent（多种header/参数变体）
    agent_name = (
        request.headers.get("agent")
        or request.headers.get("Agent")
        or request.headers.get("x-agent")
        or request.headers.get("X-Agent")
        or request.query_params.get("agent")
        or ""
    )
    agent_name = agent_name.lower() if isinstance(agent_name, str) else ""

    # 从 request.state 获取认证信息（由依赖注入）
    user_id = None
    username = None
    auth_type = None
    api_key_id = None
    try:
        if hasattr(request.state, "current_user") and request.state.current_user:
            user_id = getattr(request.state.current_user, "id", None)
            username = getattr(request.state.current_user, "username", None)
        auth_type = getattr(request.state, "auth_type", None)
        api_key_data = getattr(request.state, "api_key_data", None)
        if api_key_data:
            api_key_id = getattr(api_key_data, "id", None) or getattr(api_key_data, "_id", None)
    except Exception:
        pass

    # 先执行实际处理，拿到响应
    response = await call_next(request)

    # 计算耗时
    duration_ms = int((time.time() - start_time) * 1000)

    # 尝试获取响应体（JSON完整记录，其他类型记录文本，流式标记）
    response_body = None
    is_streaming = False
    try:
        if getattr(response, "media_type", None) == "text/event-stream":
            is_streaming = True
        if isinstance(response, JSONResponse):
            # JSONResponse 在 render 后有 body 可读
            body_bytes = getattr(response, "body", None)
            if body_bytes is not None:
                max_bytes = int(os.getenv("RESPONSE_LOG_MAX_BYTES", "65536"))
                trimmed = body_bytes[:max_bytes]
                try:
                    response_body = json.loads(trimmed.decode("utf-8", errors="ignore"))
                except Exception:
                    response_body = trimmed.decode("utf-8", errors="ignore")
        else:
            # 非 JSON 的响应（如纯文本）尽力记录
            body_bytes = getattr(response, "body", None)
            if body_bytes is not None:
                max_bytes = int(os.getenv("RESPONSE_LOG_MAX_BYTES", "65536"))
                response_body = body_bytes[:max_bytes].decode("utf-8", errors="ignore")
    except Exception:
        response_body = None

    # 组织日志文档
    log_doc = {
        "timestamp": datetime.now(),
        "method": request.method,
        "path": request.url.path,
        "query": dict(request.query_params) if request.query_params else {},
        "ip": client_ip,
        "agent": agent_name,
        "user_id": user_id,
        "username": username,
        "auth_type": auth_type,
        "api_key_id": api_key_id,
        "status_code": response.status_code,
        "duration_ms": duration_ms,
        "user_agent": request.headers.get("user-agent"),
        "content_length": request.headers.get("content-length"),
        "response": response_body,
        "is_streaming": is_streaming,
        "trace_id": request.headers.get("x-request-id") or request.headers.get("x-trace-id"),
    }

    try:
        db = db_manager.get_database()
        db.request_logs.insert_one(log_doc)
    except Exception as e:
        logger.error(f"写入请求日志失败: {str(e)}")

    return response

# 添加CORS中间件
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 在生产环境中应该限制具体域名
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 健康检查端点
@app.get("/health", tags=["系统"])
async def health_check():
    """健康检查"""
    return {
        "status": "healthy",
        "timestamp": "2024-01-01T00:00:00Z",
        "version": "0.2.0",
        "database": "connected" if db_manager.db is not None else "disconnected"
    }

# 包含路由
app.include_router(auth, prefix="/api/v1/auth", tags=["用户认证"])
app.include_router(api_keys, prefix="/api/v1/api-keys", tags=["API Key管理"])
app.include_router(chat, prefix="/api/v1", tags=["聊天"])
app.include_router(upload, prefix="/api/v1", tags=["文件上传"])
app.include_router(agents, prefix="/api/v1/agents", tags=["智能体管理"])
app.include_router(mcp_router, prefix="/api/v1", tags=["MCP"])

# 自定义 OpenAPI：为实际使用的 Header 补充到文档

def custom_openapi():
    if getattr(app, "openapi_schema", None):
        return app.openapi_schema

    openapi_schema = get_openapi(
        title=app.title,
        version=app.version,
        description=app.description,
        routes=app.routes,
    )

    paths = openapi_schema.get("paths", {})

    # 为 /api/v1/chat POST 增加必填 Header: agent
    chat_path = paths.get("/api/v1/chat")
    if chat_path and "post" in chat_path:
        post_op = chat_path["post"]
        parameters = post_op.get("parameters", [])
        # 避免重复添加
        has_agent = any(p.get("in") == "header" and p.get("name") == "agent" for p in parameters)
        if not has_agent:
            parameters.append({
                "name": "agent",
                "in": "header",
                "required": True,
                "schema": {"type": "string"},
                "description": "指定智能体名称。也支持 'Agent'/'x-agent' 变体。示例: fastgpt",
            })
            post_op["parameters"] = parameters

    # 为 /api/v1/upload POST 增加可选 Header: agent（form 参数已支持，这里补充 header 方式）
    upload_path = paths.get("/api/v1/upload")
    if upload_path and "post" in upload_path:
        post_op = upload_path["post"]
        parameters = post_op.get("parameters", [])
        has_agent = any(p.get("in") == "header" and p.get("name") == "agent" for p in parameters)
        if not has_agent:
            parameters.append({
                "name": "agent",
                "in": "header",
                "required": False,
                "schema": {"type": "string"},
                "description": "可选智能体名称（也支持表单字段 'agent'，以及 'Agent'/'x-agent' 变体）",
            })
            post_op["parameters"] = parameters

    app.openapi_schema = openapi_schema
    return app.openapi_schema

app.openapi = custom_openapi

if __name__ == "__main__":
    import uvicorn
    print("🚀 启动小胰宝智能助手平台...")
    print("📖 API文档: http://localhost:8000/docs")
    print("🔐 用户认证: http://localhost:8000/api/v1/auth/")
    print("🔑 API Key管理: http://localhost:8000/api/v1/api-keys/")
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