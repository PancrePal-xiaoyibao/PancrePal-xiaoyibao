import os
from pymongo import MongoClient
from pymongo.database import Database
from dotenv import load_dotenv
import logging

load_dotenv()

logger = logging.getLogger(__name__)


class DatabaseManager:
    """数据库管理器"""
    
    def __init__(self):
        self.client: MongoClient = None
        self.db: Database = None
        
    def connect(self):
        """连接到MongoDB"""
        try:
            # 从环境变量获取MongoDB连接信息
            mongo_uri = os.getenv("MONGO_URI", "mongodb://localhost:27017")
            database_name = os.getenv("MONGO_DATABASE", "ai-gateway")
            
            # 创建MongoDB客户端
            self.client = MongoClient(mongo_uri)
            
            # 测试连接
            self.client.admin.command('ping')
            
            # 获取数据库
            self.db = self.client[database_name]
            
            logger.info(f"✅ 成功连接到MongoDB数据库: {database_name}")
            
            # 创建索引
            self._create_indexes()
            
        except Exception as e:
            logger.error(f"❌ 连接MongoDB失败: {str(e)}")
            raise
    
    def _create_indexes(self):
        """创建数据库索引"""
        try:
            # 用户集合索引
            users_collection = self.db.users
            
            # 用户名唯一索引
            users_collection.create_index("username", unique=True)
            
            # 邮箱唯一索引
            users_collection.create_index("email", unique=True)
            
            # 角色索引
            users_collection.create_index("role")
            
            # 状态索引
            users_collection.create_index("status")
            
            # 创建时间索引
            users_collection.create_index("created_at")
            
            # 请求日志集合索引
            request_logs = self.db.request_logs
            request_logs.create_index("timestamp")
            request_logs.create_index([("user_id", 1), ("timestamp", -1)])
            request_logs.create_index([("ip", 1), ("timestamp", -1)])
            request_logs.create_index([("agent", 1), ("timestamp", -1)])
            request_logs.create_index("status_code")

            logger.info("✅ 数据库索引创建成功")
            
        except Exception as e:
            logger.error(f"❌ 创建索引失败: {str(e)}")
    
    def get_database(self) -> Database:
        """获取数据库实例"""
        if self.db is None:
            self.connect()
        return self.db
    
    def close(self):
        """关闭数据库连接"""
        if self.client:
            self.client.close()
            logger.info("✅ MongoDB连接已关闭")


# 全局数据库管理器实例
db_manager = DatabaseManager()


def get_database() -> Database:
    """获取数据库实例的便捷函数"""
    return db_manager.get_database()


def close_database():
    """关闭数据库连接的便捷函数"""
    db_manager.close()
