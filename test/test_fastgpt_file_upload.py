#!/usr/bin/env python3
"""
测试 FastGPT Agent 文件上传功能
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from agent.fastgpt import FastGPTAgent
from agent.models import ChatRequest

def test_fastgpt_file_upload():
    """测试 FastGPT Agent 的文件上传功能"""
    
    agent = FastGPTAgent()
    
    # 测试案例1: 只有文本
    print("=== 测试案例1: 只有文本 ===")
    request_data_text_only = {
        "query": "你好",
        "user": "test_user",
        "stream": False,
        "detail": False
    }
    
    print("验证请求:", agent.validate_request(request_data_text_only))
    print()
    
    # 测试案例2: 文本 + 图片文件
    print("=== 测试案例2: 文本 + 图片文件 ===")
    request_data_with_image = {
        "query": "这张图片里有什么？",
        "user": "test_user",
        "stream": False,
        "detail": False,
        "files": ["https://example.com/image.jpg"]
    }
    
    print("验证请求:", agent.validate_request(request_data_with_image))
    
    # 模拟处理请求（不实际发送到API）
    try:
        # 获取处理后的消息格式
        messages = []
        message_content = []
        
        # 添加文本内容
        text_content = request_data_with_image.get('query', '')
        if text_content:
            message_content.append({
                "type": "text",
                "text": text_content
            })
        
        # 处理文件上传
        files = request_data_with_image.get('files', [])
        if files:
            for file_url in files:
                if isinstance(file_url, str):
                    if agent._is_image_file(file_url):
                        message_content.append({
                            "type": "image_url",
                            "image_url": {
                                "url": file_url
                            }
                        })
        
        # 构建最终消息
        if len(message_content) > 1 or (len(message_content) == 1 and message_content[0]["type"] != "text"):
            messages = [
                {"role": "user", "content": message_content}
            ]
        else:
            messages = [
                {"role": "user", "content": text_content}
            ]
        
        print("生成的消息格式:")
        import json
        print(json.dumps(messages, ensure_ascii=False, indent=2))
        print()
        
    except Exception as e:
        print(f"处理请求时出错: {e}")
        print()
    
    # 测试案例3: 文本 + 文档文件
    print("=== 测试案例3: 文本 + 文档文件 ===")
    request_data_with_doc = {
        "query": "请分析这个文档",
        "user": "test_user",
        "stream": False,
        "detail": False,
        "files": ["https://s3.juniortree.com/pic/static/with-docker.md"]
    }
    
    print("验证请求:", agent.validate_request(request_data_with_doc))
    
    # 模拟处理请求
    try:
        messages = []
        message_content = []
        
        # 添加文本内容
        text_content = request_data_with_doc.get('query', '')
        if text_content:
            message_content.append({
                "type": "text",
                "text": text_content
            })
        
        # 处理文件上传
        files = request_data_with_doc.get('files', [])
        if files:
            for file_url in files:
                if isinstance(file_url, str):
                    if agent._is_image_file(file_url):
                        message_content.append({
                            "type": "image_url",
                            "image_url": {
                                "url": file_url
                            }
                        })
                    else:
                        file_name = agent._extract_filename_from_url(file_url)
                        message_content.append({
                            "type": "file_url",
                            "name": file_name,
                            "url": file_url
                        })
        
        # 构建最终消息
        if len(message_content) > 1 or (len(message_content) == 1 and message_content[0]["type"] != "text"):
            messages = [
                {"role": "user", "content": message_content}
            ]
        else:
            messages = [
                {"role": "user", "content": text_content}
            ]
        
        print("生成的消息格式:")
        import json
        print(json.dumps(messages, ensure_ascii=False, indent=2))
        print()
        
    except Exception as e:
        print(f"处理请求时出错: {e}")
        print()
    
    # 测试案例4: 只有文件（无文本）
    print("=== 测试案例4: 只有文件（无文本） ===")
    request_data_file_only = {
        "query": "",
        "user": "test_user",
        "stream": False,
        "detail": False,
        "files": ["https://example.com/document.pdf"]
    }
    
    print("验证请求:", agent.validate_request(request_data_file_only))
    print()
    
    # 测试辅助方法
    print("=== 测试辅助方法 ===")
    test_urls = [
        "https://example.com/image.jpg",
        "https://example.com/image.PNG",
        "https://example.com/document.pdf",
        "https://s3.juniortree.com/pic/static/with-docker.md",
        "https://example.com/file.txt"
    ]
    
    for url in test_urls:
        is_image = agent._is_image_file(url)
        filename = agent._extract_filename_from_url(url)
        print(f"URL: {url}")
        print(f"  是否为图片: {is_image}")
        print(f"  提取的文件名: {filename}")
        print()

if __name__ == "__main__":
    test_fastgpt_file_upload()
