#!/usr/bin/env python3
"""
测试 FastGPT Agent 的完整功能，包括文件上传
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from agent.fastgpt import FastGPTAgent
from agent.models import ChatRequest
import json

def test_comprehensive_fastgpt():
    """全面测试 FastGPT Agent 的功能"""
    
    agent = FastGPTAgent()
    
    print("=== FastGPT Agent 综合功能测试 ===\n")
    
    # 测试各种请求格式
    test_cases = [
        {
            "name": "纯文本请求",
            "data": {
                "query": "你好，请介绍一下自己",
                "user": "test_user",
                "stream": False,
                "detail": False
            }
        },
        {
            "name": "文本 + 单个图片",
            "data": {
                "query": "请分析这张图片",
                "user": "test_user",
                "files": ["https://example.com/test.jpg"],
                "stream": False,
                "detail": False
            }
        },
        {
            "name": "文本 + 单个文档",
            "data": {
                "query": "请总结这个文档的内容",
                "user": "test_user",
                "files": ["https://example.com/document.pdf"],
                "stream": False,
                "detail": False
            }
        },
        {
            "name": "文本 + 多个文件（图片+文档）",
            "data": {
                "query": "请分析这些文件",
                "user": "test_user",
                "files": [
                    "https://example.com/image.png",
                    "https://example.com/report.docx"
                ],
                "stream": False,
                "detail": True
            }
        },
        {
            "name": "只有文件，无文本",
            "data": {
                "query": "",
                "user": "test_user",
                "files": ["https://example.com/data.xlsx"],
                "stream": False,
                "detail": False
            }
        },
        {
            "name": "带 chat_id 的对话",
            "data": {
                "query": "继续我们之前的对话",
                "user": "test_user",
                "chat_id": "test_chat_123",
                "stream": False,
                "detail": False
            }
        },
        {
            "name": "带变量的请求",
            "data": {
                "query": "用户{{user}}想要了解信息",
                "user": "张三",
                "uid": "user_123",
                "stream": False,
                "detail": False
            }
        }
    ]
    
    for i, test_case in enumerate(test_cases, 1):
        print(f"=== 测试案例 {i}: {test_case['name']} ===")
        
        # 验证请求
        is_valid = agent.validate_request(test_case['data'])
        print(f"请求验证: {'✓ 通过' if is_valid else '✗ 失败'}")
        
        if is_valid:
            try:
                # 构建请求（不实际发送API）
                print("构建的请求数据:")
                
                # 模拟 process_request 的消息构建逻辑
                message_content = []
                
                # 添加文本内容
                text_content = test_case['data'].get('query', '')
                if text_content:
                    message_content.append({
                        "type": "text",
                        "text": text_content
                    })
                
                # 处理文件上传
                files = test_case['data'].get('files', [])
                if files:
                    for file_url in files:
                        if isinstance(file_url, str):
                            # 判断文件类型
                            if agent._is_image_file(file_url):
                                # 图片文件
                                message_content.append({
                                    "type": "image_url",
                                    "image_url": {
                                        "url": file_url
                                    }
                                })
                            else:
                                # 文档文件
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
                    # 只有文本内容时，保持原有格式
                    messages = [
                        {"role": "user", "content": text_content}
                    ]
                
                # 构建变量
                variables = {}
                if 'uid' in test_case['data'] and test_case['data']['uid']:
                    variables["uid"] = test_case['data']['uid']
                if 'user' in test_case['data'] and test_case['data']['user']:
                    variables["user"] = test_case['data']['user']
                
                # 构建完整的请求数据
                request_payload = {
                    "appId": "test_app_id",
                    "stream": test_case['data'].get('stream', False),
                    "detail": test_case['data'].get('detail', False),
                    "messages": messages
                }
                
                if test_case['data'].get('chat_id'):
                    request_payload["chatId"] = test_case['data']['chat_id']
                if variables:
                    request_payload["variables"] = variables
                
                print(json.dumps(request_payload, ensure_ascii=False, indent=2))
                print("✓ 请求构建成功")
                
            except Exception as e:
                print(f"✗ 构建请求时出错: {e}")
        
        print("-" * 50)
        print()
    
    # 测试边界情况
    print("=== 边界情况测试 ===")
    
    edge_cases = [
        {
            "name": "空请求",
            "data": {}
        },
        {
            "name": "空查询和空文件",
            "data": {
                "query": "",
                "files": [],
                "user": "test_user"
            }
        },
        {
            "name": "None 文件列表",
            "data": {
                "query": "测试",
                "files": None,
                "user": "test_user"
            }
        },
        {
            "name": "无效文件格式",
            "data": {
                "query": "测试",
                "files": [123, {"invalid": "format"}],
                "user": "test_user"
            }
        }
    ]
    
    for edge_case in edge_cases:
        print(f"测试: {edge_case['name']}")
        try:
            is_valid = agent.validate_request(edge_case['data'])
            print(f"验证结果: {'✓ 通过' if is_valid else '✗ 失败'}")
        except Exception as e:
            print(f"验证出错: {e}")
        print()
    
    print("=== 测试完成 ===")

if __name__ == "__main__":
    test_comprehensive_fastgpt()
