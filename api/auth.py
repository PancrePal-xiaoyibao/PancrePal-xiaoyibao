from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import HTTPBearer
from typing import List, Optional
import logging

from models.user import (
    UserCreate, UserUpdate, UserResponse, LoginRequest, 
    Token, PasswordChangeRequest, UserStats, UserRole
)
from services.user_service import user_service
from auth.dependencies import (
    get_current_user, get_current_active_user, 
    get_admin_user, get_premium_user
)

logger = logging.getLogger(__name__)

router = APIRouter()


@router.post("/register", response_model=UserResponse, summary="用户注册")
async def register(user_create: UserCreate):
    """用户注册"""
    try:
        user = await user_service.create_user(user_create)
        logger.info(f"新用户注册成功: {user.username}")
        return user
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"用户注册失败: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="注册失败，请稍后重试"
        )


@router.post("/login", response_model=Token, summary="用户登录")
async def login(login_request: LoginRequest):
    """用户登录"""
    try:
        user = await user_service.authenticate_user(
            login_request.username, 
            login_request.password
        )
        
        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="用户名或密码错误",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        # 创建访问令牌
        access_token = user_service.create_access_token(
            data={"sub": user.username, "role": user.role}
        )
        
        logger.info(f"用户登录成功: {user.username}")
        
        return Token(
            access_token=access_token,
            token_type="bearer",
            expires_in=30 * 60,  # 30分钟
            user=user
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"用户登录失败: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="登录失败，请稍后重试"
        )


@router.get("/me", response_model=UserResponse, summary="获取当前用户信息")
async def get_current_user_info(current_user: UserResponse = Depends(get_current_active_user)):
    """获取当前用户信息"""
    return current_user


@router.put("/me", response_model=UserResponse, summary="更新当前用户信息")
async def update_current_user(
    user_update: UserUpdate,
    current_user: UserResponse = Depends(get_current_active_user)
):
    """更新当前用户信息"""
    try:
        # 普通用户不能修改角色和状态
        if user_update.role is not None:
            user_update.role = None
        if user_update.status is not None:
            user_update.status = None
            
        updated_user = await user_service.update_user(current_user.id, user_update)
        if updated_user:
            logger.info(f"用户信息更新成功: {current_user.username}")
            return updated_user
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="更新失败，请检查输入数据"
            )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"更新用户信息失败: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="更新失败，请稍后重试"
        )


@router.post("/change-password", summary="修改密码")
async def change_password(
    password_change: PasswordChangeRequest,
    current_user: UserResponse = Depends(get_current_active_user)
):
    """修改密码"""
    try:
        # 验证当前密码
        if not user_service.verify_password(
            password_change.current_password, 
            current_user.hashed_password
        ):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="当前密码错误"
            )
        
        # 更新密码
        user_update = UserUpdate(password=password_change.new_password)
        updated_user = await user_service.update_user(current_user.id, user_update)
        
        if updated_user:
            logger.info(f"用户密码修改成功: {current_user.username}")
            return {"message": "密码修改成功"}
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="密码修改失败"
            )
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"修改密码失败: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="密码修改失败，请稍后重试"
        )


# 管理员专用API
@router.get("/users", response_model=List[UserResponse], summary="获取用户列表")
async def list_users(
    skip: int = 0,
    limit: int = 100,
    role: Optional[UserRole] = None,
    current_user: UserResponse = Depends(get_admin_user)
):
    """获取用户列表（管理员专用）"""
    try:
        users = await user_service.list_users(skip=skip, limit=limit, role=role)
        return users
    except Exception as e:
        logger.error(f"获取用户列表失败: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="获取用户列表失败"
        )


@router.get("/users/{user_id}", response_model=UserResponse, summary="获取指定用户信息")
async def get_user(
    user_id: str,
    current_user: UserResponse = Depends(get_admin_user)
):
    """获取指定用户信息（管理员专用）"""
    try:
        user = await user_service.get_user_by_id(user_id)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="用户不存在"
            )
        return user
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取用户信息失败: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="获取用户信息失败"
        )


@router.put("/users/{user_id}", response_model=UserResponse, summary="更新指定用户信息")
async def update_user(
    user_id: str,
    user_update: UserUpdate,
    current_user: UserResponse = Depends(get_admin_user)
):
    """更新指定用户信息（管理员专用）"""
    try:
        updated_user = await user_service.update_user(user_id, user_update)
        if updated_user:
            logger.info(f"管理员 {current_user.username} 更新用户 {user_id} 成功")
            return updated_user
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="更新失败，请检查输入数据"
            )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"更新用户信息失败: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="更新失败，请稍后重试"
        )


@router.delete("/users/{user_id}", summary="删除指定用户")
async def delete_user(
    user_id: str,
    current_user: UserResponse = Depends(get_admin_user)
):
    """删除指定用户（管理员专用）"""
    try:
        # 不能删除自己
        if user_id == current_user.id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="不能删除自己的账户"
            )
        
        success = await user_service.delete_user(user_id)
        if success:
            logger.info(f"管理员 {current_user.username} 删除用户 {user_id} 成功")
            return {"message": "用户删除成功"}
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="删除失败，用户可能不存在"
            )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"删除用户失败: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="删除失败，请稍后重试"
        )


@router.get("/stats", response_model=UserStats, summary="获取用户统计信息")
async def get_user_stats(current_user: UserResponse = Depends(get_admin_user)):
    """获取用户统计信息（管理员专用）"""
    try:
        stats = await user_service.get_user_stats()
        return UserStats(**stats)
    except Exception as e:
        logger.error(f"获取用户统计失败: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="获取统计信息失败"
        )
