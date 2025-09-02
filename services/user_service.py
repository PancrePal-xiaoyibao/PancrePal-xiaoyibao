from datetime import datetime, timedelta
from typing import Optional, List
from passlib.context import CryptContext
from jose import JWTError, jwt
from bson import ObjectId
import logging
import os

from database.connection import get_database
from models.user import (
    UserCreate, UserUpdate, UserInDB, UserResponse, 
    UserRole, UserStatus, TokenData
)

logger = logging.getLogger(__name__)

# 密码加密上下文 - 使用更兼容的加密方案
try:
    pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
    logger.info("✅ 使用bcrypt进行密码加密")
except Exception as e:
    # 如果bcrypt有问题，使用sha256_crypt作为备选
    pwd_context = CryptContext(schemes=["sha256_crypt"], deprecated="auto")
    logger.warning(f"⚠️  bcrypt不可用，使用sha256_crypt作为备选方案: {str(e)}")

# JWT配置 - 从环境变量读取，如果没有配置则自动生成安全的密钥
SECRET_KEY = os.getenv("JWT_SECRET_KEY")
if not SECRET_KEY:
    import secrets
    import hashlib
    import time
    
    # 自动生成安全的SECRET_KEY
    # 使用系统随机数 + 时间戳 + 进程ID生成
    random_bytes = secrets.token_bytes(32)
    timestamp = str(int(time.time()))
    pid = str(os.getpid())
    
    # 组合并哈希生成最终密钥
    combined = random_bytes + timestamp.encode() + pid.encode()
    SECRET_KEY = hashlib.sha256(combined).hexdigest()
    
    logger.info("🔐 自动生成JWT_SECRET_KEY，如需固定密钥请设置环境变量")

ALGORITHM = os.getenv("JWT_ALGORITHM", "HS256")
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("JWT_ACCESS_TOKEN_EXPIRE_MINUTES", "30"))

logger.info(f"✅ JWT配置完成 - 算法: {ALGORITHM}, 过期时间: {ACCESS_TOKEN_EXPIRE_MINUTES}分钟")


class UserService:
    """用户管理服务"""
    
    def __init__(self):
        self.db = get_database()
        self.users_collection = self.db.users
    
    def verify_password(self, plain_password: str, hashed_password: str) -> bool:
        """验证密码"""
        return pwd_context.verify(plain_password, hashed_password)
    
    def get_password_hash(self, password: str) -> str:
        """获取密码哈希"""
        # 验证密码强度
        if len(password) < 8:
            raise ValueError("密码长度至少8位")
        
        # 检查密码复杂度
        has_upper = any(c.isupper() for c in password)
        has_lower = any(c.islower() for c in password)
        has_digit = any(c.isdigit() for c in password)
        has_special = any(c in "!@#$%^&*()_+-=[]{}|;:,.<>?" for c in password)
        
        if not (has_upper and has_lower and has_digit):
            raise ValueError("密码必须包含大小写字母和数字")
        
        return pwd_context.hash(password)
    
    def create_access_token(self, data: dict, expires_delta: Optional[timedelta] = None):
        """创建访问令牌"""
        to_encode = data.copy()
        if expires_delta:
            expire = datetime.utcnow() + expires_delta
        else:
            expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
        
        to_encode.update({"exp": expire})
        encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
        return encoded_jwt
    
    def verify_token(self, token: str) -> Optional[TokenData]:
        """验证令牌"""
        try:
            payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
            username: str = payload.get("sub")
            role: str = payload.get("role")
            
            if username is None:
                return None
            
            return TokenData(username=username, role=role)
        except JWTError:
            return None
    
    async def create_user(self, user_create: UserCreate) -> UserResponse:
        """创建新用户"""
        try:
            # 检查用户名是否已存在
            if self.users_collection.find_one({"username": user_create.username}):
                raise ValueError("用户名已存在")
            
            # 检查邮箱是否已存在
            if self.users_collection.find_one({"email": user_create.email}):
                raise ValueError("邮箱已存在")
            
            # 创建用户文档
            now = datetime.utcnow()
            user_doc = {
                "username": user_create.username,
                "email": user_create.email,
                "full_name": user_create.full_name,
                "role": user_create.role,
                "status": user_create.status,
                "hashed_password": self.get_password_hash(user_create.password),
                "created_at": now,
                "updated_at": now,
                "last_login": None,
                "api_calls_count": 0,
                "max_api_calls": 1000
            }
            
            # 插入用户
            result = self.users_collection.insert_one(user_doc)
            user_doc["_id"] = str(result.inserted_id)
            user_doc["id"] = user_doc["_id"]  # 确保id字段存在
            
            logger.info(f"✅ 用户创建成功: {user_create.username}")
            return UserResponse(**user_doc)
            
        except Exception as e:
            logger.error(f"❌ 创建用户失败: {str(e)}")
            raise
    
    async def authenticate_user(self, username: str, password: str) -> Optional[UserResponse]:
        """用户认证"""
        try:
            # 查找用户
            user_doc = self.users_collection.find_one({"username": username})
            if not user_doc:
                return None
            
            # 验证密码
            if not self.verify_password(password, user_doc["hashed_password"]):
                return None
            
            # 检查用户状态
            if user_doc["status"] != UserStatus.ACTIVE:
                logger.warning(f"用户 {username} 状态异常: {user_doc['status']}")
                return None
            
            # 更新最后登录时间
            self.users_collection.update_one(
                {"_id": user_doc["_id"]},
                {"$set": {"last_login": datetime.utcnow()}}
            )
            
            user_doc["_id"] = str(user_doc["_id"])
            logger.info(f"✅ 用户认证成功: {username}")
            return UserResponse(**user_doc)
            
        except Exception as e:
            logger.error(f"❌ 用户认证失败: {str(e)}")
            return None
    
    async def get_user_by_id(self, user_id: str) -> Optional[UserResponse]:
        """根据ID获取用户"""
        try:
            user_doc = self.users_collection.find_one({"_id": ObjectId(user_id)})
            if user_doc:
                user_doc["_id"] = str(user_doc["_id"])
                return UserResponse(**user_doc)
            return None
        except Exception as e:
            logger.error(f"❌ 获取用户失败: {str(e)}")
            return None
    
    async def get_user_by_username(self, username: str) -> Optional[UserResponse]:
        """根据用户名获取用户"""
        try:
            user_doc = self.users_collection.find_one({"username": username})
            if user_doc:
                user_doc["_id"] = str(user_doc["_id"])
                return UserResponse(**user_doc)
            return None
        except Exception as e:
            logger.error(f"❌ 获取用户失败: {str(e)}")
            return None
    
    async def update_user(self, user_id: str, user_update: UserUpdate) -> Optional[UserResponse]:
        """更新用户信息"""
        try:
            update_data = {}
            
            # 构建更新数据
            if user_update.username is not None:
                # 检查用户名是否已被其他用户使用
                existing_user = self.users_collection.find_one({
                    "username": user_update.username,
                    "_id": {"$ne": ObjectId(user_id)}
                })
                if existing_user:
                    raise ValueError("用户名已被使用")
                update_data["username"] = user_update.username
            
            if user_update.email is not None:
                # 检查邮箱是否已被其他用户使用
                existing_user = self.users_collection.find_one({
                    "email": user_update.email,
                    "_id": {"$ne": ObjectId(user_id)}
                })
                if existing_user:
                    raise ValueError("邮箱已被使用")
                update_data["email"] = user_update.email
            
            if user_update.full_name is not None:
                update_data["full_name"] = user_update.full_name
            
            if user_update.role is not None:
                update_data["role"] = user_update.role
            
            if user_update.status is not None:
                update_data["status"] = user_update.status
            
            if user_update.password is not None:
                update_data["hashed_password"] = self.get_password_hash(user_update.password)
            
            if update_data:
                update_data["updated_at"] = datetime.utcnow()
                
                result = self.users_collection.update_one(
                    {"_id": ObjectId(user_id)},
                    {"$set": update_data}
                )
                
                if result.modified_count > 0:
                    logger.info(f"✅ 用户更新成功: {user_id}")
                    return await self.get_user_by_id(user_id)
            
            return None
            
        except Exception as e:
            logger.error(f"❌ 更新用户失败: {str(e)}")
            raise
    
    async def delete_user(self, user_id: str) -> bool:
        """删除用户"""
        try:
            result = self.users_collection.delete_one({"_id": ObjectId(user_id)})
            if result.deleted_count > 0:
                logger.info(f"✅ 用户删除成功: {user_id}")
                return True
            return False
        except Exception as e:
            logger.error(f"❌ 删除用户失败: {str(e)}")
            return False
    
    async def list_users(self, skip: int = 0, limit: int = 100, role: Optional[UserRole] = None) -> List[UserResponse]:
        """获取用户列表"""
        try:
            filter_query = {}
            if role:
                filter_query["role"] = role
            
            cursor = self.users_collection.find(filter_query).skip(skip).limit(limit)
            users = []
            
            for user_doc in cursor:
                user_doc["_id"] = str(user_doc["_id"])
                users.append(UserResponse(**user_doc))
            
            return users
            
        except Exception as e:
            logger.error(f"❌ 获取用户列表失败: {str(e)}")
            return []
    
    async def get_user_stats(self) -> dict:
        """获取用户统计信息"""
        try:
            total_users = self.users_collection.count_documents({})
            active_users = self.users_collection.count_documents({"status": UserStatus.ACTIVE})
            admin_users = self.users_collection.count_documents({"role": UserRole.ADMIN})
            premium_users = self.users_collection.count_documents({"role": UserRole.PREMIUM})
            
            return {
                "total_users": total_users,
                "active_users": active_users,
                "admin_users": admin_users,
                "premium_users": premium_users
            }
            
        except Exception as e:
            logger.error(f"❌ 获取用户统计失败: {str(e)}")
            return {
                "total_users": 0,
                "active_users": 0,
                "admin_users": 0,
                "premium_users": 0
            }
    
    async def increment_api_calls(self, user_id: str) -> bool:
        """增加用户API调用次数"""
        try:
            result = self.users_collection.update_one(
                {"_id": ObjectId(user_id)},
                {"$inc": {"api_calls_count": 1}}
            )
            return result.modified_count > 0
        except Exception as e:
            logger.error(f"❌ 增加API调用次数失败: {str(e)}")
            return False
    
    async def check_api_limit(self, user_id: str) -> bool:
        """检查用户API调用限制"""
        try:
            user = await self.get_user_by_id(user_id)
            if user:
                return user.api_calls_count < user.max_api_calls
            return False
        except Exception as e:
            logger.error(f"❌ 检查API限制失败: {str(e)}")
            return False


# 全局用户服务实例
user_service = UserService()
