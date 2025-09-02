#!/usr/bin/env python3
"""
用户认证系统测试脚本
用于测试认证功能的各个组件
"""

import asyncio
import sys
import os
import requests
import json
from datetime import datetime

# 添加项目根目录到Python路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# 测试配置
BASE_URL = "http://localhost:8000"
API_BASE = f"{BASE_URL}/api/v1/auth"

# 测试用户数据
TEST_USERS = [
    {
        "username": "testuser1",
        "email": "test1@example.com",
        "full_name": "测试用户1",
        "password": "testpass123"
    },
    {
        "username": "testuser2",
        "email": "test2@example.com",
        "full_name": "测试用户2",
        "password": "testpass456"
    }
]


class AuthSystemTester:
    """认证系统测试器"""
    
    def __init__(self):
        self.session = requests.Session()
        self.access_tokens = {}
        self.test_results = []
    
    def log_test(self, test_name: str, success: bool, message: str = ""):
        """记录测试结果"""
        status = "✅ 通过" if success else "❌ 失败"
        timestamp = datetime.now().strftime("%H:%M:%S")
        result = f"[{timestamp}] {test_name}: {status}"
        if message:
            result += f" - {message}"
        
        print(result)
        self.test_results.append({
            "test": test_name,
            "success": success,
            "message": message,
            "timestamp": timestamp
        })
    
    def test_health_check(self):
        """测试健康检查端点"""
        try:
            response = self.session.get(f"{BASE_URL}/health")
            if response.status_code == 200:
                data = response.json()
                self.log_test("健康检查", True, f"状态: {data.get('status')}")
                return True
            else:
                self.log_test("健康检查", False, f"状态码: {response.status_code}")
                return False
        except Exception as e:
            self.log_test("健康检查", False, f"异常: {str(e)}")
            return False
    
    def test_user_registration(self):
        """测试用户注册"""
        success_count = 0
        
        for i, user_data in enumerate(TEST_USERS):
            try:
                response = self.session.post(
                    f"{API_BASE}/register",
                    json=user_data,
                    headers={"Content-Type": "application/json"}
                )
                
                if response.status_code == 200:
                    data = response.json()
                    self.log_test(f"用户注册 {i+1}", True, f"用户: {data.get('username')}")
                    success_count += 1
                else:
                    error_msg = response.json().get('detail', '未知错误')
                    self.log_test(f"用户注册 {i+1}", False, f"错误: {error_msg}")
                    
            except Exception as e:
                self.log_test(f"用户注册 {i+1}", False, f"异常: {str(e)}")
        
        return success_count > 0
    
    def test_user_login(self):
        """测试用户登录"""
        success_count = 0
        
        for i, user_data in enumerate(TEST_USERS):
            try:
                login_data = {
                    "username": user_data["username"],
                    "password": user_data["password"]
                }
                
                response = self.session.post(
                    f"{API_BASE}/login",
                    json=login_data,
                    headers={"Content-Type": "application/json"}
                )
                
                if response.status_code == 200:
                    data = response.json()
                    token = data.get('access_token')
                    if token:
                        self.access_tokens[user_data["username"]] = token
                        self.log_test(f"用户登录 {i+1}", True, f"用户: {data['user']['username']}")
                        success_count += 1
                    else:
                        self.log_test(f"用户登录 {i+1}", False, "未获取到访问令牌")
                else:
                    error_msg = response.json().get('detail', '未知错误')
                    self.log_test(f"用户登录 {i+1}", False, f"错误: {error_msg}")
                    
            except Exception as e:
                self.log_test(f"用户登录 {i+1}", False, f"异常: {str(e)}")
        
        return success_count > 0
    
    def test_protected_endpoints(self):
        """测试受保护的端点"""
        if not self.access_tokens:
            self.log_test("受保护端点测试", False, "没有可用的访问令牌")
            return False
        
        success_count = 0
        test_user = list(self.access_tokens.keys())[0]
        token = self.access_tokens[test_user]
        
        # 测试获取当前用户信息
        try:
            response = self.session.get(
                f"{API_BASE}/me",
                headers={"Authorization": f"Bearer {token}"}
            )
            
            if response.status_code == 200:
                data = response.json()
                self.log_test("获取用户信息", True, f"用户: {data.get('username')}")
                success_count += 1
            else:
                error_msg = response.json().get('detail', '未知错误')
                self.log_test("获取用户信息", False, f"错误: {error_msg}")
                
        except Exception as e:
            self.log_test("获取用户信息", False, f"异常: {str(e)}")
        
        # 测试更新用户信息
        try:
            update_data = {
                "full_name": f"{test_user}_updated"
            }
            
            response = self.session.put(
                f"{API_BASE}/me",
                json=update_data,
                headers={
                    "Authorization": f"Bearer {token}",
                    "Content-Type": "application/json"
                }
            )
            
            if response.status_code == 200:
                data = response.json()
                self.log_test("更新用户信息", True, f"全名: {data.get('full_name')}")
                success_count += 1
            else:
                error_msg = response.json().get('detail', '未知错误')
                self.log_test("更新用户信息", False, f"错误: {error_msg}")
                
        except Exception as e:
            self.log_test("更新用户信息", False, f"异常: {str(e)}")
        
        return success_count > 0
    
    def test_admin_endpoints(self):
        """测试管理员端点（需要管理员权限）"""
        # 尝试访问管理员端点
        try:
            response = self.session.get(f"{API_BASE}/users")
            
            if response.status_code == 401:
                self.log_test("管理员端点权限检查", True, "正确拒绝未认证访问")
                return True
            elif response.status_code == 403:
                self.log_test("管理员端点权限检查", True, "正确拒绝非管理员访问")
                return True
            else:
                self.log_test("管理员端点权限检查", False, f"意外的状态码: {response.status_code}")
                return False
                
        except Exception as e:
            self.log_test("管理员端点权限检查", False, f"异常: {str(e)}")
            return False
    
    def test_invalid_token(self):
        """测试无效令牌"""
        try:
            invalid_token = "invalid_token_here"
            response = self.session.get(
                f"{API_BASE}/me",
                headers={"Authorization": f"Bearer {invalid_token}"}
            )
            
            if response.status_code == 401:
                self.log_test("无效令牌检查", True, "正确拒绝无效令牌")
                return True
            else:
                self.log_test("无效令牌检查", False, f"意外的状态码: {response.status_code}")
                return False
                
        except Exception as e:
            self.log_test("无效令牌检查", False, f"异常: {str(e)}")
            return False
    
    def run_all_tests(self):
        """运行所有测试"""
        print("🚀 开始认证系统测试...")
        print("=" * 60)
        
        # 基础连接测试
        if not self.test_health_check():
            print("❌ 基础连接失败，停止测试")
            return False
        
        print()
        
        # 功能测试
        self.test_user_registration()
        print()
        
        self.test_user_login()
        print()
        
        self.test_protected_endpoints()
        print()
        
        self.test_admin_endpoints()
        print()
        
        self.test_invalid_token()
        print()
        
        # 测试结果统计
        self.print_test_summary()
        
        return True
    
    def print_test_summary(self):
        """打印测试结果摘要"""
        print("=" * 60)
        print("📊 测试结果摘要")
        print("=" * 60)
        
        total_tests = len(self.test_results)
        passed_tests = sum(1 for result in self.test_results if result["success"])
        failed_tests = total_tests - passed_tests
        
        print(f"总测试数: {total_tests}")
        print(f"通过: {passed_tests} ✅")
        print(f"失败: {failed_tests} ❌")
        print(f"成功率: {(passed_tests/total_tests)*100:.1f}%")
        
        if failed_tests > 0:
            print("\n❌ 失败的测试:")
            for result in self.test_results:
                if not result["success"]:
                    print(f"  - {result['test']}: {result['message']}")
        
        print("\n🎯 建议:")
        if failed_tests == 0:
            print("  所有测试通过！认证系统工作正常。")
        else:
            print("  请检查失败的测试项，确保系统配置正确。")
            print("  常见问题：")
            print("    - MongoDB服务未启动")
            print("    - 环境变量配置错误")
            print("    - 依赖包未正确安装")


async def main():
    """主函数"""
    print("🔐 小胰宝智能助手平台 - 认证系统测试")
    print("=" * 60)
    
    # 检查服务是否运行
    try:
        response = requests.get(f"{BASE_URL}/health", timeout=5)
        if response.status_code != 200:
            print("❌ 服务未运行或无法访问")
            print(f"请确保服务在 {BASE_URL} 上运行")
            return
    except requests.exceptions.RequestException:
        print("❌ 无法连接到服务")
        print(f"请确保服务在 {BASE_URL} 上运行")
        return
    
    # 运行测试
    tester = AuthSystemTester()
    tester.run_all_tests()


if __name__ == "__main__":
    asyncio.run(main())
