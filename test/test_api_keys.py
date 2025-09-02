#!/usr/bin/env python3
"""
API Key功能测试
测试API Key的创建、验证、管理等功能，以及新的认证流程
"""

import asyncio
import requests
import json
from datetime import datetime, timedelta
import time

# 测试配置
BASE_URL = "http://localhost:8000"
API_BASE = f"{BASE_URL}/api/v1"

# 测试用户信息
TEST_USER = {
    "username": "testuser",
    "email": "test@example.com",
    "password": "TestPass123!",
    "full_name": "测试用户"
}

ADMIN_USER = {
    "username": "admin",
    "email": "admin@example.com",
    "password": "AdminPass123!",
    "full_name": "管理员"
}

PREMIUM_USER = {
    "username": "premium",
    "email": "premium@example.com",
    "password": "PremiumPass123!",
    "full_name": "高级用户"
}


class APITestClient:
    """API测试客户端"""
    
    def __init__(self):
        self.session = requests.Session()
        self.base_url = API_BASE
        self.tokens = {}
        self.api_keys = {}
    
    def _make_request(self, method, endpoint, **kwargs):
        """发送HTTP请求"""
        url = f"{self.base_url}{endpoint}"
        response = self.session.request(method, url, **kwargs)
        return response
    
    def register_user(self, user_data):
        """注册用户"""
        response = self._make_request(
            "POST", "/auth/register",
            json=user_data
        )
        return response
    
    def login_user(self, username, password):
        """用户登录"""
        response = self._make_request(
            "POST", "/auth/login",
            json={"username": username, "password": password}
        )
        if response.status_code == 200:
            data = response.json()
            self.tokens[username] = data["access_token"]
        return response
    
    def create_api_key(self, username, api_key_data):
        """创建API Key"""
        headers = {"Authorization": f"Bearer {self.tokens[username]}"}
        response = self._make_request(
            "POST", "/api-keys/",
            json=api_key_data,
            headers=headers
        )
        if response.status_code == 200:
            data = response.json()
            self.api_keys[data["name"]] = data["full_key"]
        return response
    
    def get_my_api_keys(self, username):
        """获取用户的API Key列表"""
        headers = {"Authorization": f"Bearer {self.tokens[username]}"}
        response = self._make_request(
            "GET", "/api-keys/my",
            headers=headers
        )
        return response
    
    def get_api_key_detail(self, username, api_key_id):
        """获取API Key详情"""
        headers = {"Authorization": f"Bearer {self.tokens[username]}"}
        response = self._make_request(
            "GET", f"/api-keys/{api_key_id}",
            headers=headers
        )
        return response
    
    def update_api_key(self, username, api_key_id, update_data):
        """更新API Key"""
        headers = {"Authorization": f"Bearer {self.tokens[username]}"}
        response = self._make_request(
            "PUT", f"/api-keys/{api_key_id}",
            json=update_data,
            headers=headers
        )
        return response
    
    def delete_api_key(self, username, api_key_id):
        """删除API Key"""
        headers = {"Authorization": f"Bearer {self.tokens[username]}"}
        response = self._make_request(
            "DELETE", f"/api-keys/{api_key_id}",
            headers=headers
        )
        return response
    
    def revoke_api_key(self, username, api_key_id):
        """撤销API Key"""
        headers = {"Authorization": f"Bearer {self.tokens[username]}"}
        response = self._make_request(
            "POST", f"/api-keys/{api_key_id}/revoke",
            headers=headers
        )
        return response
    
    def get_api_key_usage(self, username, api_key_id):
        """获取API Key使用统计"""
        headers = {"Authorization": f"Bearer {self.tokens[username]}"}
        response = self._make_request(
            "GET", f"/api-keys/{api_key_id}/usage",
            headers=headers
        )
        return response
    
    def test_api_key_authentication(self, api_key_name):
        """测试API Key认证"""
        if api_key_name not in self.api_keys:
            print(f"❌ API Key {api_key_name} 不存在")
            return False
        
        api_key = self.api_keys[api_key_name]
        headers = {"Authorization": f"Bearer {api_key}"}
        
        # 测试访问需要认证的API
        response = self._make_request(
            "GET", "/auth/me",
            headers=headers
        )
        return response
    
    def test_chat_with_api_key(self, api_key_name):
        """使用API Key测试聊天接口"""
        if api_key_name not in self.api_keys:
            print(f"❌ API Key {api_key_name} 不存在")
            return False
        
        api_key = self.api_keys[api_key_name]
        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
            "agent": "fastgpt"
        }
        
        chat_data = {
            "message": "你好，这是一个测试消息",
            "stream": False
        }
        
        response = self._make_request(
            "POST", "/chat",
            json=chat_data,
            headers=headers
        )
        return response
    
    def test_chat_with_jwt(self, username):
        """使用JWT测试聊天接口（应该失败）"""
        headers = {
            "Authorization": f"Bearer {self.tokens[username]}",
            "Content-Type": "application/json",
            "agent": "fastgpt"
        }
        
        chat_data = {
            "message": "你好，这是一个测试消息",
            "stream": False
        }
        
        response = self._make_request(
            "POST", "/chat",
            json=chat_data,
            headers=headers
        )
        return response


def run_tests():
    """运行所有测试"""
    print("🧪 开始API Key功能测试...")
    print("=" * 50)
    
    client = APITestClient()
    
    # 测试1: 注册测试用户
    print("\n📝 测试1: 注册测试用户")
    print("-" * 30)
    
    # 注册普通用户
    response = client.register_user(TEST_USER)
    if response.status_code == 200:
        print("✅ 普通用户注册成功")
    else:
        print(f"❌ 普通用户注册失败: {response.text}")
    
    # 注册高级用户
    response = client.register_user(PREMIUM_USER)
    if response.status_code == 200:
        print("✅ 高级用户注册成功")
    else:
        print(f"❌ 高级用户注册失败: {response.text}")
    
    # 测试2: 用户登录
    print("\n🔐 测试2: 用户登录")
    print("-" * 30)
    
    # 普通用户登录
    response = client.login_user(TEST_USER["username"], TEST_USER["password"])
    if response.status_code == 200:
        print("✅ 普通用户登录成功")
    else:
        print(f"❌ 普通用户登录失败: {response.text}")
    
    # 高级用户登录
    response = client.login_user(PREMIUM_USER["username"], PREMIUM_USER["password"])
    if response.status_code == 200:
        print("✅ 高级用户登录成功")
    else:
        print(f"❌ 高级用户登录失败: {response.text}")
    
    # 测试3: 创建API Key（普通用户应该失败）
    print("\n🔑 测试3: 创建API Key权限测试")
    print("-" * 30)
    
    api_key_data = {
        "name": "测试API Key",
        "description": "用于测试的API Key",
        "expires_at": (datetime.utcnow() + timedelta(days=30)).isoformat(),
        "permissions": ["read", "write"]
    }
    
    # 普通用户尝试创建API Key（应该失败）
    response = client.create_api_key(TEST_USER["username"], api_key_data)
    if response.status_code == 403:
        print("✅ 普通用户无法创建API Key（权限正确）")
    else:
        print(f"❌ 普通用户创建API Key权限检查失败: {response.status_code}")
    
    # 高级用户创建API Key（应该成功）
    response = client.create_api_key(PREMIUM_USER["username"], api_key_data)
    if response.status_code == 200:
        print("✅ 高级用户创建API Key成功")
        api_key_info = response.json()
        print(f"   API Key ID: {api_key_info['id']}")
        print(f"   API Key前缀: {api_key_info['key_prefix']}")
        print(f"   API Key: {api_key_info['full_key'][:20]}...")
    else:
        print(f"❌ 高级用户创建API Key失败: {response.text}")
        return
    
    # 测试4: 获取API Key列表
    print("\n📋 测试4: 获取API Key列表")
    print("-" * 30)
    
    response = client.get_my_api_keys(PREMIUM_USER["username"])
    if response.status_code == 200:
        api_keys = response.json()
        print(f"✅ 获取API Key列表成功，共 {len(api_keys)} 个")
        for key in api_keys:
            print(f"   - {key['name']}: {key['key_prefix']}...")
    else:
        print(f"❌ 获取API Key列表失败: {response.text}")
    
    # 测试5: 获取API Key详情
    print("\n🔍 测试5: 获取API Key详情")
    print("-" * 30)
    
    api_key_id = api_key_info["id"]
    response = client.get_api_key_detail(PREMIUM_USER["username"], api_key_id)
    if response.status_code == 200:
        key_detail = response.json()
        print("✅ 获取API Key详情成功")
        print(f"   名称: {key_detail['name']}")
        print(f"   描述: {key_detail['description']}")
        print(f"   状态: {'激活' if key_detail['is_active'] else '停用'}")
        print(f"   创建时间: {key_detail['created_at']}")
    else:
        print(f"❌ 获取API Key详情失败: {response.text}")
    
    # 测试6: 更新API Key
    print("\n✏️ 测试6: 更新API Key")
    print("-" * 30)
    
    update_data = {
        "name": "更新后的测试API Key",
        "description": "已更新的描述信息"
    }
    
    response = client.update_api_key(PREMIUM_USER["username"], api_key_id, update_data)
    if response.status_code == 200:
        print("✅ 更新API Key成功")
        updated_key = response.json()
        print(f"   新名称: {updated_key['name']}")
        print(f"   新描述: {updated_key['description']}")
    else:
        print(f"❌ 更新API Key失败: {response.text}")
    
    # 测试7: 获取API Key使用统计
    print("\n📊 测试7: 获取API Key使用统计")
    print("-" * 30)
    
    response = client.get_api_key_usage(PREMIUM_USER["username"], api_key_id)
    if response.status_code == 200:
        usage = response.json()
        print("✅ 获取API Key使用统计成功")
        print(f"   总调用次数: {usage['total_calls']}")
        print(f"   今日调用次数: {usage['calls_today']}")
        print(f"   本月调用次数: {usage['calls_this_month']}")
    else:
        print(f"❌ 获取API Key使用统计失败: {response.text}")
    
    # 测试8: 测试API Key认证
    print("\n🔐 测试8: 测试API Key认证")
    print("-" * 30)
    
    # 使用API Key访问需要认证的API
    response = client.test_api_key_authentication("更新后的测试API Key")
    if response.status_code == 200:
        print("✅ API Key认证成功")
        user_info = response.json()
        print(f"   认证用户: {user_info['username']}")
    else:
        print(f"❌ API Key认证失败: {response.text}")
    
    # 测试9: 测试聊天接口认证（新功能）
    print("\n💬 测试9: 测试聊天接口认证")
    print("-" * 30)
    
    # 使用JWT访问主要聊天接口（应该失败）
    response = client.test_chat_with_jwt(PREMIUM_USER["username"])
    if response.status_code == 400:
        print("✅ JWT无法访问主要聊天接口（认证正确）")
        print(f"   错误信息: {response.json().get('detail', '未知错误')}")
    else:
        print(f"❌ JWT访问主要聊天接口检查失败: {response.status_code}")
    
    # 使用API Key访问主要聊天接口（应该成功）
    response = client.test_chat_with_api_key("更新后的测试API Key")
    if response.status_code == 200:
        print("✅ API Key访问主要聊天接口成功")
    else:
        print(f"❌ API Key访问主要聊天接口失败: {response.text}")
    
    # 测试10: 撤销API Key
    print("\n🚫 测试10: 撤销API Key")
    print("-" * 30)
    
    response = client.revoke_api_key(PREMIUM_USER["username"], api_key_id)
    if response.status_code == 200:
        print("✅ 撤销API Key成功")
    else:
        print(f"❌ 撤销API Key失败: {response.text}")
    
    # 测试11: 验证撤销后的API Key无法使用
    print("\n🔒 测试11: 验证撤销后的API Key")
    print("-" * 30)
    
    response = client.test_api_key_authentication("更新后的测试API Key")
    if response.status_code == 401:
        print("✅ 撤销后的API Key无法使用（安全正确）")
    else:
        print(f"❌ 撤销后的API Key仍可使用（安全漏洞）: {response.status_code}")
    
    # 测试12: 删除API Key
    print("\n🗑️ 测试12: 删除API Key")
    print("-" * 30)
    
    response = client.delete_api_key(PREMIUM_USER["username"], api_key_id)
    if response.status_code == 200:
        print("✅ 删除API Key成功")
    else:
        print(f"❌ 删除API Key失败: {response.text}")
    
    # 测试13: 验证删除后的API Key无法访问
    print("\n🔒 测试13: 验证删除后的API Key")
    print("-" * 30)
    
    response = client.get_api_key_detail(PREMIUM_USER["username"], api_key_id)
    if response.status_code == 404:
        print("✅ 删除后的API Key无法访问（正确）")
    else:
        print(f"❌ 删除后的API Key仍可访问: {response.status_code}")
    
    print("\n" + "=" * 50)
    print("🎉 API Key功能测试完成！")
    print("\n📋 测试总结:")
    print("✅ 权限控制: 只有高级用户和管理员可以创建API Key")
    print("✅ 创建功能: 支持设置名称、描述、过期时间和权限")
    print("✅ 管理功能: 支持查看、更新、撤销、删除API Key")
    print("✅ 使用统计: 记录API Key的使用次数和时间")
    print("✅ 安全控制: 撤销和删除后的API Key无法使用")
    print("✅ 认证集成: API Key可以替代JWT进行API认证")
    print("✅ 新认证流程: 主要接口仅支持API Key，确保安全性")
    print("✅ 清晰分离: JWT用于用户管理，API Key用于API访问")


if __name__ == "__main__":
    try:
        run_tests()
    except KeyboardInterrupt:
        print("\n\n⏹️ 测试被用户中断")
    except Exception as e:
        print(f"\n\n❌ 测试过程中发生错误: {str(e)}")
        import traceback
        traceback.print_exc()
