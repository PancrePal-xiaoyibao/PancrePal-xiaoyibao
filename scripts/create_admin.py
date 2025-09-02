#!/usr/bin/env python3
"""
管理员用户创建脚本
用于初始化系统管理员账户
"""

import asyncio
import sys
import os
from datetime import datetime

# 添加项目根目录到Python路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database.connection import db_manager
from services.user_service import user_service
from models.user import UserCreate, UserRole, UserStatus


async def create_admin_user():
    """创建管理员用户"""
    try:
        # 连接数据库
        db_manager.connect()
        
        # 检查是否已存在管理员用户
        existing_admin = await user_service.get_user_by_username("admin")
        if existing_admin:
            print("⚠️  管理员用户已存在，跳过创建")
            return existing_admin
        
        # 创建管理员用户
        admin_user = UserCreate(
            username="admin",
            email="admin@pancrepal.com",
            full_name="系统管理员",
            password="admin123456",  # 默认密码，建议首次登录后修改
            role=UserRole.ADMIN,
            status=UserStatus.ACTIVE
        )
        
        created_admin = await user_service.create_user(admin_user)
        
        print("✅ 管理员用户创建成功!")
        print(f"   用户名: {created_admin.username}")
        print(f"   邮箱: {created_admin.email}")
        print(f"   角色: {created_admin.role}")
        print(f"   状态: {created_admin.status}")
        print(f"   创建时间: {created_admin.created_at}")
        print("\n⚠️  请及时修改默认密码: admin123456")
        
        return created_admin
        
    except Exception as e:
        print(f"❌ 创建管理员用户失败: {str(e)}")
        return None
    
    finally:
        # 关闭数据库连接
        db_manager.close()


async def create_demo_users():
    """创建演示用户"""
    try:
        # 连接数据库
        db_manager.connect()
        
        # 演示用户列表
        demo_users = [
            {
                "username": "demo_user",
                "email": "demo@pancrepal.com",
                "full_name": "演示用户",
                "password": "demo123456",
                "role": UserRole.USER,
                "status": UserStatus.ACTIVE
            },
            {
                "username": "premium_user",
                "email": "premium@pancrepal.com",
                "full_name": "高级用户",
                "password": "premium123456",
                "role": UserRole.PREMIUM,
                "status": UserStatus.ACTIVE
            }
        ]
        
        created_users = []
        
        for user_data in demo_users:
            # 检查用户是否已存在
            existing_user = await user_service.get_user_by_username(user_data["username"])
            if existing_user:
                print(f"⚠️  用户 {user_data['username']} 已存在，跳过创建")
                continue
            
            # 创建用户
            user_create = UserCreate(**user_data)
            created_user = await user_service.create_user(user_create)
            created_users.append(created_user)
            
            print(f"✅ 演示用户创建成功: {created_user.username}")
        
        if created_users:
            print(f"\n✅ 共创建了 {len(created_users)} 个演示用户")
        
        return created_users
        
    except Exception as e:
        print(f"❌ 创建演示用户失败: {str(e)}")
        return []
    
    finally:
        # 关闭数据库连接
        db_manager.close()


async def main():
    """主函数"""
    print("🚀 开始创建系统用户...")
    print("=" * 50)
    
    # 创建管理员用户
    print("\n📝 创建管理员用户...")
    admin_user = await create_admin_user()
    
    if not admin_user:
        print("❌ 管理员用户创建失败，程序退出")
        return
    
    # 创建演示用户
    print("\n📝 创建演示用户...")
    demo_users = await create_demo_users()
    
    print("\n" + "=" * 50)
    print("🎉 系统用户创建完成!")
    
    if admin_user:
        print(f"👑 管理员账户: {admin_user.username}")
        print(f"   默认密码: Admin123456!")
        print(f"   请及时修改密码!")
    
    if demo_users:
        print(f"\n👥 演示用户账户:")
        for user in demo_users:
            print(f"   {user['username']} (密码: {user['password']})")
    
    print("\n🔐 用户可以通过以下API进行登录:")
    print("   POST /api/v1/auth/login")
    print("\n📖 完整API文档: http://localhost:8000/docs")


if __name__ == "__main__":
    asyncio.run(main())
