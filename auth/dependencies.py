from fastapi import Depends, HTTPException, status, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from typing import Optional
import logging

from services.user_service import user_service
from services.api_key_service import api_key_service
from models.user import UserRole, TokenData

logger = logging.getLogger(__name__)

# HTTP Bearer认证方案
security = HTTPBearer()


async def get_current_user(request: Request, credentials: HTTPAuthorizationCredentials = Depends(security)):
    """获取当前认证用户（支持JWT和API Key）"""
    try:
        token = credentials.credentials
        
        # 首先尝试作为JWT令牌验证
        token_data = user_service.verify_token(token)
        if token_data:
            user = await user_service.get_user_by_username(token_data.username)
            if user:
                # 将认证信息注入 request.state
                try:
                    request.state.current_user = user
                    request.state.auth_type = "jwt"
                except Exception:
                    pass
                return user
        
        # 如果不是JWT，尝试作为API Key验证
        api_key_data = await api_key_service.verify_api_key(token)
        if api_key_data:
            # 获取API Key创建者信息
            user = await user_service.get_user_by_id(api_key_data.created_by)
            if user:
                # 将API Key信息附加到用户对象上，用于权限检查
                user.api_key_data = api_key_data
                # 将认证信息注入 request.state
                try:
                    request.state.current_user = user
                    request.state.auth_type = "api_key"
                    request.state.api_key_data = api_key_data
                except Exception:
                    pass
                return user
        
        # 如果都验证失败，抛出认证错误
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="无效的认证令牌或API Key",
            headers={"WWW-Authenticate": "Bearer"},
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"认证失败: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="认证失败",
            headers={"WWW-Authenticate": "Bearer"},
        )


async def get_current_active_user(current_user = Depends(get_current_user)):
    """获取当前活跃用户"""
    if current_user.status != "active":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="用户账户未激活"
        )
    return current_user


async def get_admin_user(current_user = Depends(get_current_user)):
    """获取管理员用户"""
    if current_user.role != UserRole.ADMIN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="权限不足，需要管理员权限"
        )
    return current_user


async def get_premium_user(current_user = Depends(get_current_user)):
    """获取高级用户"""
    if current_user.role not in [UserRole.ADMIN, UserRole.PREMIUM]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="权限不足，需要高级用户权限"
        )
    return current_user


async def get_api_key_user(current_user = Depends(get_current_user)):
    """获取通过API Key认证的用户"""
    # 检查是否通过API Key认证
    if not hasattr(current_user, 'api_key_data'):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="此操作需要API Key认证"
        )
    return current_user


async def get_jwt_user(current_user = Depends(get_current_user)):
    """获取通过JWT认证的用户"""
    # 检查是否通过JWT认证
    if hasattr(current_user, 'api_key_data'):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="此操作需要JWT认证，不支持API Key"
        )
    return current_user


def check_api_limit(user_id: str) -> bool:
    """检查用户API调用限制"""
    return user_service.check_api_limit(user_id)


async def increment_api_calls(user_id: str):
    """增加用户API调用次数"""
    await user_service.increment_api_calls(user_id)
