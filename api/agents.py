from fastapi import APIRouter, HTTPException, Depends
from fastapi.responses import JSONResponse
from typing import Dict, Any
from agent import registry
from agent.base import BaseAgent
from auth.dependencies import get_current_active_user, get_admin_user
from models.user import UserResponse

agents = APIRouter()

@agents.get("/")
async def list_available_agents():
    """
    获取所有可用的智能体列表（公开端点）
    
    返回:
        JSON: 包含智能体名称和基本信息的列表
    """
    try:
        agents_dict = registry.list_agents()
        agent_list = []
        
        for name, agent in agents_dict.items():
            agent_info = {
                "name": name,
                "type": agent.__class__.__name__,
                "module": agent.__class__.__module__,
                "capabilities": {
                    "streaming": hasattr(agent, 'stream_chat') and callable(getattr(agent, 'stream_chat')),
                    "file_upload": hasattr(agent, 'upload_file') and callable(getattr(agent, 'upload_file')),
                }
            }
            agent_list.append(agent_info)
        
        return JSONResponse(content={
            "success": True,
            "data": {
                "total": len(agent_list),
                "agents": agent_list
            }
        })
    except Exception as e:
        return JSONResponse(content={
            "success": False,
            "error": str(e)
        }, status_code=500)

@agents.get("/{agent_name}")
async def get_agent_info(agent_name: str):
    """
    获取指定智能体的详细信息（公开端点）
    
    参数:
        agent_name (str): 智能体名称
    
    返回:
        JSON: 智能体的详细信息
    """
    try:
        agent = registry.get(agent_name.lower())
        if not agent:
            raise HTTPException(status_code=404, detail=f"智能体 '{agent_name}' 未找到")
        
        agent_info = {
            "name": agent_name.lower(),
            "type": agent.__class__.__name__,
            "module": agent.__class__.__module__,
            "capabilities": {
                "streaming": hasattr(agent, 'stream_chat') and callable(getattr(agent, 'stream_chat')),
                "file_upload": hasattr(agent, 'upload_file') and callable(getattr(agent, 'upload_file')),
            }
        }
        
        return JSONResponse(content={
            "success": True,
            "data": agent_info
        })
    except HTTPException:
        raise
    except Exception as e:
        return JSONResponse(content={
            "success": False,
            "error": str(e)
        }, status_code=500)

@agents.get("/{agent_name}/health")
async def check_agent_health(agent_name: str):
    """
    检查指定智能体的健康状态（公开端点）
    
    参数:
        agent_name (str): 智能体名称
    
    返回:
        JSON: 智能体的健康状态
    """
    try:
        agent = registry.get(agent_name.lower())
        if not agent:
            raise HTTPException(status_code=404, detail=f"智能体 '{agent_name}' 未找到")
        
        # 检查智能体是否可用（这里可以根据具体需求添加更多检查）
        health_status = "healthy"
        try:
            # 可以添加一些基本的健康检查逻辑
            if hasattr(agent, 'check_health'):
                health_status = agent.check_health()
            elif hasattr(agent, 'health_check'):
                health_status = agent.health_check()
        except Exception:
            health_status = "unhealthy"
        
        return JSONResponse(content={
            "success": True,
            "data": {
                "agent": agent_name.lower(),
                "status": health_status,
                "timestamp": "2024-01-01T00:00:00Z"
            }
        })
    except HTTPException:
        raise
    except Exception as e:
        return JSONResponse(content={
            "success": False,
            "error": str(e)
        }, status_code=500)

# 以下端点为管理员专用
@agents.post("/{agent_name}/reload")
async def reload_agent(
    agent_name: str,
    current_user: UserResponse = Depends(get_admin_user)
):
    """
    重新加载指定智能体（管理员专用）
    
    参数:
        agent_name (str): 智能体名称
    
    返回:
        JSON: 重新加载结果
    """
    try:
        # 这里可以添加重新加载智能体的逻辑
        # 例如：重新初始化配置、重新加载模型等
        
        return JSONResponse(content={
            "success": True,
            "data": {
                "agent": agent_name.lower(),
                "action": "reloaded",
                "timestamp": "2024-01-01T00:00:00Z"
            }
        })
    except Exception as e:
        return JSONResponse(content={
            "success": False,
            "error": str(e)
        }, status_code=500)

@agents.delete("/{agent_name}")
async def remove_agent(
    agent_name: str,
    current_user: UserResponse = Depends(get_admin_user)
):
    """
    移除指定智能体（管理员专用）
    
    参数:
        agent_name (str): 智能体名称
    
    返回:
        JSON: 移除结果
    """
    try:
        # 这里可以添加移除智能体的逻辑
        # 例如：从注册表中移除、清理资源等
        
        return JSONResponse(content={
            "success": True,
            "data": {
                "agent": agent_name.lower(),
                "action": "removed",
                "timestamp": "2024-01-01T00:00:00Z"
            }
        })
    except Exception as e:
        return JSONResponse(content={
            "success": False,
            "error": str(e)
        }, status_code=500)
