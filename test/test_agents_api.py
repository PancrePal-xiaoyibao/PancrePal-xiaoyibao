#!/usr/bin/env python3
"""
测试智能体管理API接口的脚本
"""

import requests
import json
import time

# 配置
BASE_URL = "http://localhost:8000"
API_PREFIX = "/api/v1/agents"

def test_list_agents():
    """测试获取所有智能体列表"""
    print("=== 测试获取所有智能体列表 ===")
    try:
        response = requests.get(f"{BASE_URL}{API_PREFIX}/")
        print(f"状态码: {response.status_code}")
        print(f"响应内容: {json.dumps(response.json(), indent=2, ensure_ascii=False)}")
        return response.status_code == 200
    except Exception as e:
        print(f"请求失败: {e}")
        return False

def test_get_agent_info(agent_name):
    """测试获取指定智能体信息"""
    print(f"\n=== 测试获取智能体 '{agent_name}' 信息 ===")
    try:
        response = requests.get(f"{BASE_URL}{API_PREFIX}/{agent_name}")
        print(f"状态码: {response.status_code}")
        print(f"响应内容: {json.dumps(response.json(), indent=2, ensure_ascii=False)}")
        return response.status_code == 200
    except Exception as e:
        print(f"请求失败: {e}")
        return False

def test_agent_health(agent_name):
    """测试检查智能体健康状态"""
    print(f"\n=== 测试智能体 '{agent_name}' 健康状态 ===")
    try:
        response = requests.get(f"{BASE_URL}{API_PREFIX}/{agent_name}/health")
        print(f"状态码: {response.status_code}")
        print(f"响应内容: {json.dumps(response.json(), indent=2, ensure_ascii=False)}")
        return response.status_code == 200
    except Exception as e:
        print(f"请求失败: {e}")
        return False

def test_nonexistent_agent():
    """测试查询不存在的智能体"""
    print(f"\n=== 测试查询不存在的智能体 ===")
    try:
        response = requests.get(f"{BASE_URL}{API_PREFIX}/nonexistent_agent")
        print(f"状态码: {response.status_code}")
        print(f"响应内容: {json.dumps(response.json(), indent=2, ensure_ascii=False)}")
        return response.status_code == 404
    except Exception as e:
        print(f"请求失败: {e}")
        return False

def main():
    """主测试函数"""
    print("开始测试智能体管理API接口...")
    print(f"测试地址: {BASE_URL}{API_PREFIX}")
    
    # 等待服务启动
    print("等待服务启动...")
    time.sleep(2)
    
    # 测试用例
    tests = [
        ("获取所有智能体列表", test_list_agents),
        ("查询不存在的智能体", test_nonexistent_agent),
    ]
    
    # 如果第一个测试成功，继续测试其他功能
    if test_list_agents():
        # 获取可用的智能体名称
        try:
            response = requests.get(f"{BASE_URL}{API_PREFIX}/")
            if response.status_code == 200:
                data = response.json()
                if data.get("success") and data.get("data", {}).get("agents"):
                    agents = data["data"]["agents"]
                    if agents:
                        # 测试第一个可用的智能体
                        first_agent = agents[0]["name"]
                        tests.extend([
                            (f"获取智能体 '{first_agent}' 信息", lambda: test_get_agent_info(first_agent)),
                            (f"检查智能体 '{first_agent}' 健康状态", lambda: test_agent_health(first_agent)),
                        ])
        except Exception as e:
            print(f"获取智能体列表失败: {e}")
    
    # 执行所有测试
    passed = 0
    total = len(tests)
    
    for test_name, test_func in tests:
        print(f"\n{'='*50}")
        print(f"执行测试: {test_name}")
        print('='*50)
        
        try:
            if test_func():
                print(f"✅ {test_name} - 通过")
                passed += 1
            else:
                print(f"❌ {test_name} - 失败")
        except Exception as e:
            print(f"❌ {test_name} - 异常: {e}")
    
    print(f"\n{'='*50}")
    print(f"测试完成: {passed}/{total} 通过")
    print('='*50)

if __name__ == "__main__":
    main()
