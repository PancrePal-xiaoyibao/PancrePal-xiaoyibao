from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from typing import Optional
import logging

from services.user_service import user_service
from models.user import UserRole, TokenData

logger = logging.getLogger(__name__)

# HTTP Bearer认证方案
security = HTTPBearer()


async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)):
    """获取当前认证用户"""
    try:
        token = credentials.credentials
        token_data = user_service.verify_token(token)
        
        if token_data is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="无效的认证令牌",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        user = await user_service.get_user_by_username(token_data.username)
        if user is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="用户不存在",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        return user
        
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


def check_api_limit(user_id: str) -> bool:
    """检查用户API调用限制"""
    return user_service.check_api_limit(user_id)


async def increment_api_calls(user_id: str):
    """增加用户API调用次数"""
    await user_service.increment_api_calls(user_id)
