from fastapi import APIRouter, Request, HTTPException, UploadFile, File, Form
from fastapi.responses import JSONResponse
import asyncio
import os
import tempfile
from typing import Optional
from agent import registry
from agent.models import FileUploadResponse, FastGPTFileInfo

upload = APIRouter()

@upload.post("/upload", response_model=FileUploadResponse)
async def upload_file(
    request: Request,
    file: UploadFile = File(...),
    agent: Optional[str] = Form(None),
    created_by: Optional[str] = Form(None)
):
    """
    文件上传API
    
    参数:
        file: 上传的文件
        agent: 指定的智能体名称（可选，也可通过header传递）
    
    返回:
        FileUploadResponse: 包含文件信息的响应
    """
    # 获取智能体名称，优先使用Form参数，其次使用Header（兼容大小写/变体）
    agent_name = agent or (
        request.headers.get("agent")
        or request.headers.get("Agent")
        or request.headers.get("x-agent")
        or request.headers.get("X-Agent")
        or ""
    )
    agent_name = agent_name.lower()
    
    if not agent_name:
        return JSONResponse(content={
            "code": 400,
            "msg": "Missing agent parameter or header",
            "data": None
        }, status_code=400)
    
    # 获取智能体实例
    agent_instance = registry.get(agent_name)
    if not agent_instance:
        return JSONResponse(content={
            "code": 400,
            "msg": f"Unknown agent: {agent_name}",
            "data": None
        }, status_code=400)
    
    # 检查智能体是否支持文件上传
    if not hasattr(agent_instance, 'upload_file') or not callable(getattr(agent_instance, 'upload_file')):
        return JSONResponse(content={
            "code": 400,
            "msg": f"Agent {agent_name} does not support file upload",
            "data": None
        }, status_code=400)
    
    try:
        # 创建临时文件
        with tempfile.NamedTemporaryFile(delete=False, suffix=f"_{file.filename}") as temp_file:
            # 读取上传文件内容并写入临时文件
            contents = await file.read()
            temp_file.write(contents)
            temp_file_path = temp_file.name
        
        try:
            # 调用智能体的文件上传方法
            loop = asyncio.get_event_loop()
            result = await loop.run_in_executor(
                None,
                lambda: agent_instance.upload_file(temp_file_path)
            )

            # 统一响应：如果 agent 返回 FastGPTFileInfo，直接使用；否则做最小包装
            if isinstance(result, FastGPTFileInfo):
                # 覆盖 created_by（优先使用表单 created_by，次之 header: user）
                cb = created_by or request.headers.get("user") or "unknown"
                try:
                    result.created_by = cb
                except Exception:
                    pass
                return JSONResponse(content={
                    "code": 0,
                    "msg": "File uploaded successfully",
                    "data": result.model_dump()
                })
            elif isinstance(result, dict):
                # 尝试从 dict 中映射到规范字段
                return JSONResponse(content={
                    "code": 0,
                    "msg": result.get("msg", "File uploaded successfully"),
                    "data": result.get("data", result)
                })
            else:
                # 字符串或其他 → 当作 URL/ID 返回，并补齐必要字段
                cb = created_by or request.headers.get("user") or "unknown"
                info = FastGPTFileInfo(
                    id=str(result),
                    name=file.filename,
                    size=len(contents),
                    extension=(os.path.splitext(file.filename)[1].lstrip('.') or ''),
                    mime_type=file.content_type or "application/octet-stream",
                    created_by=cb,
                    created_at=int(__import__('time').time())
                )
                return JSONResponse(content={
                    "code": 0,
                    "msg": "File uploaded successfully",
                    "data": info.model_dump()
                })
                
        finally:
            # 清理临时文件
            if os.path.exists(temp_file_path):
                os.unlink(temp_file_path)
                
    except NotImplementedError as e:
        return JSONResponse(content={
            "code": 400,
            "msg": f"Agent {agent_name} does not support file upload: {str(e)}",
            "data": None
        }, status_code=400)
    except Exception as e:
        import traceback
        traceback.print_exc()
        return JSONResponse(content={
            "code": 500,
            "msg": f"File upload failed: {str(e)}",
            "data": None
        }, status_code=500)

@upload.get("/upload/agents")
async def get_upload_supported_agents():
    """
    获取支持文件上传的智能体列表
    
    返回:
        dict: 包含支持文件上传的智能体列表
    """
    supported_agents = []
    
    for agent_name, agent_instance in registry.list_agents().items():
        # 检查智能体是否实现了upload_file方法，且不是BaseAgent的默认实现
        if hasattr(agent_instance, 'upload_file') and callable(getattr(agent_instance, 'upload_file')):
            # 通过检查方法的定义位置来判断是否是自定义实现
            upload_method = getattr(agent_instance, 'upload_file')
            # 如果方法在agent实例的类中定义，而不是在BaseAgent中，则认为支持上传
            if upload_method.__qualname__.startswith(agent_instance.__class__.__name__):
                supported_agents.append(agent_name)
    
    return JSONResponse(content={
        "code": 0,
        "msg": "Success",
        "data": {
            "supported_agents": supported_agents,
            "count": len(supported_agents)
        }
    })
