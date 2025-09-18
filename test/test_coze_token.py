#!/usr/bin/env python3
"""
测试Coze API Token是否有效
"""

import os
import requests
from dotenv import load_dotenv

def test_coze_token():
    """测试Coze API Token"""
    load_dotenv()
    
    token = os.getenv("COZE_API_TOKEN")
    base_url = os.getenv("COZE_BASE_URL", "https://api.coze.cn")
    
    print(f"COZE_API_TOKEN: {token[:10]}...{token[-10:] if token else 'None'}")
    print(f"COZE_BASE_URL: {base_url}")
    
    if not token:
        print("❌ COZE_API_TOKEN not found!")
        return
    
    # 测试API连通性 - 使用文件上传接口来验证
    test_url = f"{base_url}/v1/files/upload"
    headers = {
        "Authorization": f"Bearer {token}"
    }
    
    # 创建一个简单的测试文件
    test_content = "Test file content"
    
    try:
        # 这里只是测试请求头是否正确，不实际上传文件
        files = {
            'file': ('test.txt', test_content, 'text/plain')
        }
        
        print(f"正在测试Coze API连通性: {test_url}")
        response = requests.post(test_url, headers=headers, files=files)
        
        print(f"响应状态码: {response.status_code}")
        print(f"响应内容: {response.text}")
        
        if response.status_code == 200:
            print("✅ Coze API Token有效，文件上传成功!")
        elif response.status_code == 401:
            print("❌ Coze API Token无效或已过期!")
        elif response.status_code == 403:
            print("❌ Coze API Token权限不足!")
        else:
            print(f"⚠️  Coze API响应异常: {response.status_code}")
            
    except Exception as e:
        print(f"❌ 请求失败: {e}")

if __name__ == "__main__":
    test_coze_token()
