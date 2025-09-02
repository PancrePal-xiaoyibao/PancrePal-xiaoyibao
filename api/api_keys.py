from fastapi import APIRouter, Depends, HTTPException, status, Query
from typing import List, Optional
import logging

from models.user import (
    APIKeyCreate, APIKeyResponse, APIKeyFullResponse, 
    APIKeyUpdate, APIKeyUsage, UserResponse
)
from services.api_key_service import api_key_service
from auth.dependencies import (
    get_current_active_user, get_admin_user, get_premium_user
)

logger = logging.getLogger(__name__)

router = APIRouter()


@router.post("/", response_model=APIKeyFullResponse, summary="创建API Key")
async def create_api_key(
    api_key_create: APIKeyCreate,
    current_user: UserResponse = Depends(get_premium_user)
):
    """创建新的API Key（需要高级用户权限）"""
    try:
        api_key = await api_key_service.create_api_key(
            user_id=current_user.id,
            user_role=current_user.role,
            api_key_create=api_key_create
        )
        logger.info(f"用户 {current_user.username} 创建API Key成功: {api_key_create.name}")
        return api_key
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"创建API Key失败: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="创建API Key失败，请稍后重试"
        )


@router.get("/my", response_model=List[APIKeyResponse], summary="获取我的API Key")
async def get_my_api_keys(
    current_user: UserResponse = Depends(get_current_active_user)
):
    """获取当前用户的所有API Key"""
    try:
        api_keys = await api_key_service.list_user_api_keys(current_user.id)
        return api_keys
    except Exception as e:
        logger.error(f"获取用户API Key失败: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="获取API Key失败"
        )


@router.get("/{api_key_id}", response_model=APIKeyResponse, summary="获取API Key详情")
async def get_api_key(
    api_key_id: str,
    current_user: UserResponse = Depends(get_current_active_user)
):
    """获取指定API Key的详细信息"""
    try:
        api_key = await api_key_service.get_api_key_by_id(api_key_id)
        if not api_key:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="API Key不存在"
            )
        
        # 检查权限：只能查看自己创建的或管理员可以查看所有
        if api_key.created_by != current_user.id and current_user.role != "admin":
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="权限不足，只能查看自己创建的API Key"
            )
        
        return api_key
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取API Key详情失败: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="获取API Key详情失败"
        )


@router.put("/{api_key_id}", response_model=APIKeyResponse, summary="更新API Key")
async def update_api_key(
    api_key_id: str,
    api_key_update: APIKeyUpdate,
    current_user: UserResponse = Depends(get_current_active_user)
):
    """更新API Key信息"""
    try:
        updated_api_key = await api_key_service.update_api_key(
            api_key_id=api_key_id,
            user_id=current_user.id,
            user_role=current_user.role,
            api_key_update=api_key_update
        )
        
        if updated_api_key:
            logger.info(f"用户 {current_user.username} 更新API Key成功: {api_key_id}")
            return updated_api_key
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
        logger.error(f"更新API Key失败: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="更新API Key失败"
        )


@router.delete("/{api_key_id}", summary="删除API Key")
async def delete_api_key(
    api_key_id: str,
    current_user: UserResponse = Depends(get_current_active_user)
):
    """删除API Key"""
    try:
        success = await api_key_service.delete_api_key(
            api_key_id=api_key_id,
            user_id=current_user.id,
            user_role=current_user.role
        )
        
        if success:
            logger.info(f"用户 {current_user.username} 删除API Key成功: {api_key_id}")
            return {"message": "API Key删除成功"}
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="删除失败，API Key可能不存在"
            )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"删除API Key失败: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="删除API Key失败"
        )


@router.post("/{api_key_id}/revoke", summary="撤销API Key")
async def revoke_api_key(
    api_key_id: str,
    current_user: UserResponse = Depends(get_current_active_user)
):
    """撤销API Key（停用但不删除）"""
    try:
        success = await api_key_service.revoke_api_key(
            api_key_id=api_key_id,
            user_id=current_user.id,
            user_role=current_user.role
        )
        
        if success:
            logger.info(f"用户 {current_user.username} 撤销API Key成功: {api_key_id}")
            return {"message": "API Key撤销成功"}
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="撤销失败，API Key可能不存在"
            )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"撤销API Key失败: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="撤销API Key失败"
        )


@router.get("/{api_key_id}/usage", response_model=APIKeyUsage, summary="获取API Key使用统计")
async def get_api_key_usage(
    api_key_id: str,
    current_user: UserResponse = Depends(get_current_active_user)
):
    """获取API Key的使用统计信息"""
    try:
        # 首先检查API Key是否存在且属于当前用户
        api_key = await api_key_service.get_api_key_by_id(api_key_id)
        if not api_key:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="API Key不存在"
            )
        
        # 检查权限：只能查看自己创建的或管理员可以查看所有
        if api_key.created_by != current_user.id and current_user.role != "admin":
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="权限不足，只能查看自己创建的API Key使用统计"
            )
        
        usage = await api_key_service.get_api_key_usage(api_key_id)
        if usage:
            return usage
        else:
            # 如果没有使用统计，返回默认值
            return APIKeyUsage(
                total_calls=0,
                last_used_at=None,
                calls_today=0,
                calls_this_month=0
            )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取API Key使用统计失败: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="获取使用统计失败"
        )


# 管理员专用API
@router.get("/admin/all", response_model=List[APIKeyResponse], summary="获取所有API Key")
async def get_all_api_keys(
    skip: int = Query(0, ge=0, description="跳过记录数"),
    limit: int = Query(100, ge=1, le=1000, description="返回记录数"),
    current_user: UserResponse = Depends(get_admin_user)
):
    """获取所有API Key（管理员专用）"""
    try:
        api_keys = await api_key_service.list_all_api_keys(skip=skip, limit=limit)
        return api_keys
    except Exception as e:
        logger.error(f"获取所有API Key失败: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="获取所有API Key失败"
        )


@router.post("/admin/cleanup", summary="清理过期API Key")
async def cleanup_expired_api_keys(
    current_user: UserResponse = Depends(get_admin_user)
):
    """清理过期的API Key（管理员专用）"""
    try:
        cleaned_count = await api_key_service.cleanup_expired_keys()
        logger.info(f"管理员 {current_user.username} 清理过期API Key: {cleaned_count} 个")
        return {
            "message": f"清理完成，共清理 {cleaned_count} 个过期API Key",
            "cleaned_count": cleaned_count
        }
    except Exception as e:
        logger.error(f"清理过期API Key失败: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="清理过期API Key失败"
        )
