from fastapi import APIRouter, HTTPException
from fastapi.responses import JSONResponse
from typing import Dict, Any
from agent import registry
from agent.base import BaseAgent

agents = APIRouter()

@agents.get("/")
async def list_available_agents():
    """
    获取所有可用的智能体列表
    
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
    获取指定智能体的详细信息
    
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
    检查指定智能体的健康状态
    
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
        health_status = {
            "name": agent_name.lower(),
            "status": "healthy",
            "timestamp": __import__("time").time(),
            "capabilities": {
                "streaming": hasattr(agent, 'stream_chat') and callable(getattr(agent, 'stream_chat')),
                "file_upload": hasattr(agent, 'upload_file') and callable(getattr(agent, 'upload_file')),
            }
        }
        
        return JSONResponse(content={
            "success": True,
            "data": health_status
        })
    except HTTPException:
        raise
    except Exception as e:
        return JSONResponse(content={
            "success": False,
            "error": str(e)
        }, status_code=500)
