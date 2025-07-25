#!/usr/bin/env python3
"""
测试文件上传功能
"""

import requests
import os
from pathlib import Path

def test_coze_file_upload():
    """测试 Coze 智能体的文件上传功能"""
    
    # 服务器URL
    base_url = "http://localhost:8000"  # 根据实际服务器地址调整
    upload_url = f"{base_url}/api/v1/upload"
    
    # 创建一个测试文件
    test_file_path = "test_upload.txt"
    test_content = "这是一个测试文件内容\nThis is a test file content."
    
    with open(test_file_path, "w", encoding="utf-8") as f:
        f.write(test_content)
    
    try:
        # 准备上传文件
        with open(test_file_path, "rb") as f:
            files = {
                "file": (test_file_path, f, "text/plain")
            }
            data = {
                "agent": "coze"
            }
            
            print(f"正在上传文件到: {upload_url}")
            print(f"文件名: {test_file_path}")
            print(f"智能体: coze")
            
            # 发送上传请求
            response = requests.post(upload_url, files=files, data=data)
            
            print(f"响应状态码: {response.status_code}")
            print(f"响应内容: {response.text}")
            
            if response.status_code == 200:
                result = response.json()
                if result.get("code") == 0:
                    print("✅ 文件上传成功!")
                    print(f"文件信息: {result.get('data')}")
                else:
                    print(f"❌ 上传失败: {result.get('msg')}")
            else:
                print(f"❌ HTTP错误: {response.status_code}")
                
    except Exception as e:
        print(f"❌ 测试失败: {e}")
    finally:
        # 清理测试文件
        if os.path.exists(test_file_path):
            os.remove(test_file_path)
            print(f"已清理测试文件: {test_file_path}")

def test_get_supported_agents():
    """测试获取支持文件上传的智能体列表"""
    
    base_url = "http://localhost:8000"
    agents_url = f"{base_url}/api/v1/upload/agents"
    
    try:
        print(f"正在获取支持文件上传的智能体列表: {agents_url}")
        response = requests.get(agents_url)
        
        print(f"响应状态码: {response.status_code}")
        print(f"响应内容: {response.text}")
        
        if response.status_code == 200:
            result = response.json()
            if result.get("code") == 0:
                data = result.get("data", {})
                agents = data.get("supported_agents", [])
                count = data.get("count", 0)
                print(f"✅ 成功获取智能体列表!")
                print(f"支持文件上传的智能体数量: {count}")
                print(f"智能体列表: {agents}")
            else:
                print(f"❌ 获取失败: {result.get('msg')}")
        else:
            print(f"❌ HTTP错误: {response.status_code}")
            
    except Exception as e:
        print(f"❌ 测试失败: {e}")

def test_header_based_upload():
    """测试通过Header指定智能体的文件上传"""
    
    base_url = "http://localhost:8000"
    upload_url = f"{base_url}/api/v1/upload"
    
    # 创建一个测试文件
    test_file_path = "test_header_upload.txt"
    test_content = "Header方式上传测试文件\nHeader-based upload test file."
    
    with open(test_file_path, "w", encoding="utf-8") as f:
        f.write(test_content)
    
    try:
        # 准备上传文件
        with open(test_file_path, "rb") as f:
            files = {
                "file": (test_file_path, f, "text/plain")
            }
            headers = {
                "agent": "coze"
            }
            
            print(f"正在通过Header方式上传文件到: {upload_url}")
            print(f"文件名: {test_file_path}")
            print(f"Header中的智能体: coze")
            
            # 发送上传请求
            response = requests.post(upload_url, files=files, headers=headers)
            
            print(f"响应状态码: {response.status_code}")
            print(f"响应内容: {response.text}")
            
            if response.status_code == 200:
                result = response.json()
                if result.get("code") == 0:
                    print("✅ 通过Header的文件上传成功!")
                    print(f"文件信息: {result.get('data')}")
                else:
                    print(f"❌ 上传失败: {result.get('msg')}")
            else:
                print(f"❌ HTTP错误: {response.status_code}")
                
    except Exception as e:
        print(f"❌ 测试失败: {e}")
    finally:
        # 清理测试文件
        if os.path.exists(test_file_path):
            os.remove(test_file_path)
            print(f"已清理测试文件: {test_file_path}")

if __name__ == "__main__":
    print("开始测试文件上传功能...")
    print("=" * 50)
    
    print("\n1. 测试获取支持文件上传的智能体列表")
    test_get_supported_agents()
    
    print("\n" + "=" * 50)
    print("\n2. 测试Coze智能体文件上传（Form方式）")
    test_coze_file_upload()
    
    print("\n" + "=" * 50)
    print("\n3. 测试Coze智能体文件上传（Header方式）")
    test_header_based_upload()
    
    print("\n" + "=" * 50)
    print("测试完成!")
