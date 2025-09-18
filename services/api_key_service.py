from datetime import datetime, timedelta, timezone
from typing import Optional, List
from bson import ObjectId
import secrets
import hashlib
import logging
from database.connection import get_database
from models.user import (
    APIKeyCreate, APIKeyResponse, APIKeyFullResponse, 
    APIKeyUpdate, APIKeyUsage, UserRole
)

logger = logging.getLogger(__name__)


class APIKeyService:
    """API Key管理服务"""
    
    def __init__(self):
        self.db = get_database()
        self.api_keys_collection = self.db.api_keys
        self.api_key_usage_collection = self.db.api_key_usage
    
    def _generate_api_key(self) -> str:
        """生成安全的API Key"""
        # 生成64字节的随机数据
        random_bytes = secrets.token_bytes(64)
        # 使用SHA-256哈希生成最终的API Key
        api_key = hashlib.sha256(random_bytes).hexdigest()
        return api_key
    
    def _get_key_prefix(self, api_key: str) -> str:
        """获取API Key的前缀（前8位）"""
        return api_key[:8]
    
    async def create_api_key(
        self, 
        user_id: str, 
        user_role: UserRole,
        api_key_create: APIKeyCreate
    ) -> APIKeyFullResponse:
        """创建新的API Key"""
        try:
            # 检查用户权限
            if user_role not in [UserRole.ADMIN, UserRole.PREMIUM]:
                raise ValueError("只有管理员和高级用户才能创建API Key")
            
            # 生成API Key
            full_key = self._generate_api_key()
            key_prefix = self._get_key_prefix(full_key)
            
            # 检查前缀是否已存在（极小概率）
            while self.api_keys_collection.find_one({"key_prefix": key_prefix}):
                full_key = self._generate_api_key()
                key_prefix = self._get_key_prefix(full_key)
            
            # 创建API Key文档
            now = datetime.now()

            # 处理并校验过期时间：必须晚于当前时间；统一存储为UTC无时区
            normalized_expires_at = None
            if api_key_create.expires_at is not None:
                exp = api_key_create.expires_at
                try:
                    if getattr(exp, "tzinfo", None) is not None:
                        exp_utc = exp.astimezone(timezone.utc).replace(tzinfo=None)
                    else:
                        exp_utc = exp
                except Exception:
                    exp_utc = exp
                if exp_utc <= now:
                    raise ValueError("过期时间必须晚于当前时间")
                normalized_expires_at = exp_utc
            api_key_doc = {
                "name": api_key_create.name,
                "description": api_key_create.description,
                "key_hash": hashlib.sha256(full_key.encode()).hexdigest(),
                "key_prefix": key_prefix,
                "created_at": now,
                "expires_at": normalized_expires_at,
                "last_used_at": None,
                "permissions": api_key_create.permissions or [],
                "is_active": True,
                "created_by": user_id
            }
            
            # 插入数据库
            result = self.api_keys_collection.insert_one(api_key_doc)
            api_key_doc["_id"] = str(result.inserted_id)
            api_key_doc["id"] = api_key_doc["_id"]
            
            # 初始化使用统计
            usage_doc = {
                "api_key_id": str(result.inserted_id),
                "total_calls": 0,
                "last_used_at": None,
                "calls_today": 0,
                "calls_this_month": 0,
                "last_reset_date": now.date().isoformat(),
                "last_reset_month": now.strftime("%Y-%m")
            }
            self.api_key_usage_collection.insert_one(usage_doc)
            
            logger.info(f"✅ API Key创建成功: {api_key_create.name} (用户: {user_id})")
            
            return APIKeyFullResponse(
                **api_key_doc,
                full_key=full_key
            )
            
        except Exception as e:
            logger.error(f"❌ 创建API Key失败: {str(e)}")
            raise
    
    async def verify_api_key(self, api_key: str) -> Optional[APIKeyResponse]:
        """验证API Key"""
        try:
            # 计算API Key的哈希值
            key_hash = hashlib.sha256(api_key.encode()).hexdigest()
            
            # 查找API Key
            api_key_doc = self.api_keys_collection.find_one({"key_hash": key_hash})
            if not api_key_doc:
                return None
            
            # 检查是否激活
            if not api_key_doc.get("is_active", True):
                logger.warning(f"API Key已停用: {api_key_doc['key_prefix']}")
                return None
            
            # 检查是否过期
            if api_key_doc.get("expires_at") and datetime.now() > api_key_doc["expires_at"]:
                logger.warning(f"API Key已过期: {api_key_doc['key_prefix']}")
                return None
            
            # 更新最后使用时间
            self.api_keys_collection.update_one(
                {"_id": api_key_doc["_id"]},
                {"$set": {"last_used_at": datetime.now()}}
            )
            
            # 更新使用统计
            await self._increment_usage(api_key_doc["_id"])
            
            api_key_doc["_id"] = str(api_key_doc["_id"])
            api_key_doc["id"] = api_key_doc["_id"]
            
            return APIKeyResponse(**api_key_doc)
            
        except Exception as e:
            logger.error(f"❌ 验证API Key失败: {str(e)}")
            return None
    
    async def get_api_key_by_id(self, api_key_id: str) -> Optional[APIKeyResponse]:
        """根据ID获取API Key信息"""
        try:
            api_key_doc = self.api_keys_collection.find_one({"_id": ObjectId(api_key_id)})
            if api_key_doc:
                api_key_doc["_id"] = str(api_key_doc["_id"])
                api_key_doc["id"] = api_key_doc["_id"]
                return APIKeyResponse(**api_key_doc)
            return None
        except Exception as e:
            logger.error(f"❌ 获取API Key失败: {str(e)}")
            return None
    
    async def list_user_api_keys(self, user_id: str) -> List[APIKeyResponse]:
        """获取用户的所有API Key"""
        try:
            cursor = self.api_keys_collection.find({"created_by": user_id})
            api_keys = []
            
            for api_key_doc in cursor:
                api_key_doc["_id"] = str(api_key_doc["_id"])
                api_key_doc["id"] = api_key_doc["_id"]
                api_keys.append(APIKeyResponse(**api_key_doc))
            
            return api_keys
            
        except Exception as e:
            logger.error(f"❌ 获取用户API Key列表失败: {str(e)}")
            return []
    
    async def list_all_api_keys(self, skip: int = 0, limit: int = 100) -> List[APIKeyResponse]:
        """获取所有API Key（管理员专用）"""
        try:
            cursor = self.api_keys_collection.find({}).skip(skip).limit(limit)
            api_keys = []
            
            for api_key_doc in cursor:
                api_key_doc["_id"] = str(api_key_doc["_id"])
                api_key_doc["id"] = api_key_doc["_id"]
                api_keys.append(APIKeyResponse(**api_key_doc))
            
            return api_keys
            
        except Exception as e:
            logger.error(f"❌ 获取所有API Key失败: {str(e)}")
            return []
    
    async def update_api_key(
        self, 
        api_key_id: str, 
        user_id: str,
        user_role: UserRole,
        api_key_update: APIKeyUpdate
    ) -> Optional[APIKeyResponse]:
        """更新API Key"""
        try:
            # 检查权限
            api_key = await self.get_api_key_by_id(api_key_id)
            if not api_key:
                raise ValueError("API Key不存在")
            
            # 只有创建者和管理员可以更新
            if api_key.created_by != user_id and user_role != UserRole.ADMIN:
                raise ValueError("权限不足，只能更新自己创建的API Key")
            
            # 构建更新数据
            update_data = {}
            if api_key_update.name is not None:
                update_data["name"] = api_key_update.name
            if api_key_update.description is not None:
                update_data["description"] = api_key_update.description
            if api_key_update.expires_at is not None:
                update_data["expires_at"] = api_key_update.expires_at
            if api_key_update.permissions is not None:
                update_data["permissions"] = api_key_update.permissions
            if api_key_update.is_active is not None:
                update_data["is_active"] = api_key_update.is_active
            
            if update_data:
                update_data["updated_at"] = datetime.now()
                
                result = self.api_keys_collection.update_one(
                    {"_id": ObjectId(api_key_id)},
                    {"$set": update_data}
                )
                
                if result.modified_count > 0:
                    logger.info(f"✅ API Key更新成功: {api_key_id}")
                    return await self.get_api_key_by_id(api_key_id)
            
            return None
            
        except Exception as e:
            logger.error(f"❌ 更新API Key失败: {str(e)}")
            raise
    
    async def delete_api_key(
        self, 
        api_key_id: str, 
        user_id: str,
        user_role: UserRole
    ) -> bool:
        """删除API Key"""
        try:
            # 检查权限
            api_key = await self.get_api_key_by_id(api_key_id)
            if not api_key:
                return False
            
            # 只有创建者和管理员可以删除
            if api_key.created_by != user_id and user_role != UserRole.ADMIN:
                raise ValueError("权限不足，只能删除自己创建的API Key")
            
            # 删除API Key
            result = self.api_keys_collection.delete_one({"_id": ObjectId(api_key_id)})
            if result.deleted_count > 0:
                # 删除使用统计
                self.api_key_usage_collection.delete_one({"api_key_id": api_key_id})
                logger.info(f"✅ API Key删除成功: {api_key_id}")
                return True
            return False
            
        except Exception as e:
            logger.error(f"❌ 删除API Key失败: {str(e)}")
            raise
    
    async def revoke_api_key(
        self, 
        api_key_id: str, 
        user_id: str,
        user_role: UserRole
    ) -> bool:
        """撤销API Key（停用但不删除）"""
        try:
            # 检查权限
            api_key = await self.get_api_key_by_id(api_key_id)
            if not api_key:
                return False
            
            # 只有创建者和管理员可以撤销
            if api_key.created_by != user_id and user_role != UserRole.ADMIN:
                raise ValueError("权限不足，只能撤销自己创建的API Key")
            
            # 停用API Key
            result = self.api_keys_collection.update_one(
                {"_id": ObjectId(api_key_id)},
                {"$set": {"is_active": False, "updated_at": datetime.now()}}
            )
            
            if result.modified_count > 0:
                logger.info(f"✅ API Key撤销成功: {api_key_id}")
                return True
            return False
            
        except Exception as e:
            logger.error(f"❌ 撤销API Key失败: {str(e)}")
            raise
    
    async def get_api_key_usage(self, api_key_id: str) -> Optional[APIKeyUsage]:
        """获取API Key使用统计"""
        try:
            usage_doc = self.api_key_usage_collection.find_one({"api_key_id": api_key_id})
            if usage_doc:
                return APIKeyUsage(**usage_doc)
            return None
        except Exception as e:
            logger.error(f"❌ 获取API Key使用统计失败: {str(e)}")
            return None
    
    async def _increment_usage(self, api_key_id: str):
        """增加API Key使用次数"""
        try:
            now = datetime.now()
            today = now.date().isoformat()
            this_month = now.strftime("%Y-%m")
            
            # 更新使用统计
            update_data = {
                "$inc": {"total_calls": 1},
                "$set": {"last_used_at": now}
            }
            
            # 检查是否需要重置今日和本月计数
            usage_doc = self.api_key_usage_collection.find_one({"api_key_id": api_key_id})
            if usage_doc:
                if usage_doc.get("last_reset_date") != today:
                    update_data["$set"]["calls_today"] = 1
                    update_data["$set"]["last_reset_date"] = today
                else:
                    update_data["$inc"]["calls_today"] = 1
                
                if usage_doc.get("last_reset_month") != this_month:
                    update_data["$set"]["calls_this_month"] = 1
                    update_data["$set"]["last_reset_month"] = this_month
                else:
                    update_data["$inc"]["calls_this_month"] = 1
            else:
                # 如果不存在，创建新的使用统计
                update_data = {
                    "$set": {
                        "api_key_id": api_key_id,
                        "total_calls": 1,
                        "last_used_at": now,
                        "calls_today": 1,
                        "calls_this_month": 1,
                        "last_reset_date": today,
                        "last_reset_month": this_month
                    }
                }
                self.api_key_usage_collection.insert_one(update_data["$set"])
                return
            
            self.api_key_usage_collection.update_one(
                {"api_key_id": api_key_id},
                update_data
            )
            
        except Exception as e:
            logger.error(f"❌ 更新API Key使用统计失败: {str(e)}")
    
    async def cleanup_expired_keys(self) -> int:
        """清理过期的API Key"""
        try:
            now = datetime.now()
            result = self.api_keys_collection.update_many(
                {
                    "expires_at": {"$lt": now},
                    "is_active": True
                },
                {"$set": {"is_active": False, "updated_at": now}}
            )
            
            if result.modified_count > 0:
                logger.info(f"✅ 清理过期API Key: {result.modified_count} 个")
            
            return result.modified_count
            
        except Exception as e:
            logger.error(f"❌ 清理过期API Key失败: {str(e)}")
            return 0


# 全局API Key服务实例
api_key_service = APIKeyService()
