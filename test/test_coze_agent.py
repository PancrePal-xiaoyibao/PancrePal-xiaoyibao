#!/usr/bin/env python3
"""
测试 CozeAgent 实现
"""
import os
import sys
from dotenv import load_dotenv

# 添加项目根目录到路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from agent.coze import CozeAgent
from agent.models import ChatRequest

load_dotenv()

def test_coze_agent():
    """测试 CozeAgent 基本功能"""
    print("开始测试 CozeAgent...")
    
    try:
        # 初始化 CozeAgent
        agent = CozeAgent()
        print("✓ CozeAgent 初始化成功")
        
        # 测试请求验证
        valid_request = {
            "query": "你好，请介绍一下胰腺癌的基本知识",
            "user": "test_user",
            "stream": False
        }
        
        invalid_request = {
            "user": "test_user"
            # 缺少 query 字段
        }
        
        # 测试有效请求验证
        if agent.validate_request(valid_request):
            print("✓ 有效请求验证通过")
        else:
            print("✗ 有效请求验证失败")
            
        # 测试无效请求验证
        if not agent.validate_request(invalid_request):
            print("✓ 无效请求验证通过")
        else:
            print("✗ 无效请求验证失败")
        
        # 测试实际请求处理（如果环境变量配置正确）
        coze_api_token = os.getenv("COZE_API_TOKEN")
        coze_bot_id = os.getenv("COZE_BOT_ID")
        
        if coze_api_token and coze_bot_id:
            print("检测到 Coze 配置，开始测试实际请求...")
            
            # 测试非流式请求
            response = agent.process_request(valid_request)
            print(f"非流式响应: {response}")
            
            # 格式化响应
            formatted_response = agent.format_response(response)
            print(f"格式化响应: {formatted_response}")
            
            # 测试流式请求
            stream_request = valid_request.copy()
            stream_request["stream"] = True
            
            print("测试流式请求...")
            stream_response = agent.process_request(stream_request)
            print(f"流式响应: {stream_response}")
            
            formatted_stream_response = agent.format_response(stream_response)
            print(f"格式化流式响应: {formatted_stream_response}")
            
        else:
            print("⚠️ 未检测到 COZE_API_TOKEN 或 COZE_BOT_ID 环境变量，跳过实际请求测试")
            print("请确保 .env 文件中包含以下配置:")
            print("COZE_API_TOKEN=your_token_here")
            print("COZE_BOT_ID=your_bot_id_here")
            print("COZE_BASE_URL=https://api.coze.cn (可选，默认为国内版)")
            
    except Exception as e:
        print(f"✗ 测试失败: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_coze_agent()
