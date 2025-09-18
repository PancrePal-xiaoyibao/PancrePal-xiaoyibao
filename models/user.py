from pydantic import BaseModel, EmailStr, Field
from typing import Optional, List
from datetime import datetime
from enum import Enum


class UserRole(str, Enum):
    """用户角色枚举"""
    ADMIN = "admin"
    USER = "user"
    PREMIUM = "premium"


class UserStatus(str, Enum):
    """用户状态枚举"""
    ACTIVE = "active"
    INACTIVE = "inactive"
    SUSPENDED = "suspended"


class UserBase(BaseModel):
    """用户基础模型"""
    username: str = Field(..., min_length=3, max_length=50, description="用户名")
    email: EmailStr = Field(..., description="邮箱地址")
    full_name: Optional[str] = Field(None, max_length=100, description="全名")
    role: UserRole = Field(default=UserRole.USER, description="用户角色")
    status: UserStatus = Field(default=UserStatus.ACTIVE, description="用户状态")


class UserCreate(UserBase):
    """创建用户模型"""
    password: str = Field(..., min_length=6, description="密码")


class UserUpdate(BaseModel):
    """更新用户模型"""
    username: Optional[str] = Field(None, min_length=3, max_length=50)
    email: Optional[EmailStr] = None
    full_name: Optional[str] = Field(None, max_length=100)
    role: Optional[UserRole] = None
    status: Optional[UserStatus] = None
    password: Optional[str] = Field(None, min_length=6)


class UserInDB(UserBase):
    """数据库中的用户模型"""
    id: str = Field(..., alias="_id")
    hashed_password: str
    created_at: datetime
    updated_at: datetime
    last_login: Optional[datetime] = None
    api_calls_count: int = Field(default=0, description="API调用次数")
    max_api_calls: int = Field(default=1000, description="最大API调用次数")


class UserResponse(UserBase):
    """用户响应模型"""
    id: str
    created_at: datetime
    updated_at: datetime
    last_login: Optional[datetime] = None
    api_calls_count: int
    max_api_calls: int


class Token(BaseModel):
    """JWT令牌模型"""
    access_token: str
    token_type: str = "bearer"
    expires_in: int
    user: UserResponse


class TokenData(BaseModel):
    """令牌数据模型"""
    username: Optional[str] = None
    role: Optional[str] = None


class LoginRequest(BaseModel):
    """登录请求模型"""
    username: str
    password: str


class PasswordChangeRequest(BaseModel):
    """密码修改请求模型"""
    current_password: str
    new_password: str


class UserStats(BaseModel):
    """用户统计信息"""
    total_users: int
    active_users: int
    admin_users: int
    premium_users: int


# API Key相关模型
class APIKeyCreate(BaseModel):
    """创建API Key请求模型"""
    name: str = Field(..., min_length=1, max_length=100, description="API Key名称")
    description: Optional[str] = Field(None, max_length=500, description="API Key描述")
    expires_at: Optional[datetime] = Field(None, description="过期时间，为空表示永不过期")
    permissions: List[str] = Field(default=[], description="权限列表")


class APIKeyResponse(BaseModel):
    """API Key响应模型"""
    id: str
    name: str
    description: Optional[str]
    key_prefix: str = Field(..., description="API Key前缀（用于识别）")
    created_at: datetime
    expires_at: Optional[datetime]
    last_used_at: Optional[datetime]
    permissions: List[str]
    is_active: bool
    created_by: str = Field(..., description="创建者用户ID")


class APIKeyFullResponse(APIKeyResponse):
    """API Key完整响应模型（包含完整密钥）"""
    full_key: str = Field(..., description="完整的API Key")


class APIKeyUpdate(BaseModel):
    """更新API Key请求模型"""
    name: Optional[str] = Field(None, min_length=1, max_length=100)
    description: Optional[str] = Field(None, max_length=500)
    expires_at: Optional[datetime] = None
    permissions: Optional[List[str]] = None
    is_active: Optional[bool] = None


class APIKeyUsage(BaseModel):
    """API Key使用统计"""
    total_calls: int = Field(default=0, description="总调用次数")
    last_used_at: Optional[datetime] = Field(None, description="最后使用时间")
    calls_today: int = Field(default=0, description="今日调用次数")
    calls_this_month: int = Field(default=0, description="本月调用次数")
