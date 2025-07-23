#!/usr/bin/env python3
"""
测试 FastGPT Agent 的 detail 功能
"""

import json
from agent.fastgpt import FastGPTAgent
from agent.models import ChatRequest

def test_format_response():
    """测试 format_response 方法处理 detail=true 和 detail=false 的响应"""
    
    agent = FastGPTAgent()
    
    # 测试 detail=false 的响应格式（原有格式）
    detail_false_response = {
        "id": "test_id",
        "model": "FastAI-4k",
        "usage": {
            "prompt_tokens": 10,
            "completion_tokens": 20,
            "total_tokens": 30
        },
        "choices": [
            {
                "message": {
                    "role": "assistant",
                    "content": "这是一个测试回复"
                },
                "finish_reason": "stop",
                "index": 0
            }
        ]
    }
    
    # 测试 detail=true 的响应格式（包含 responseData）
    detail_true_response = {
        "responseData": [
            {
                "moduleName": "Dataset Search",
                "price": 1.2000000000000002,
                "model": "Embedding-2",
                "tokens": 6,
                "similarity": 0.61,
                "limit": 3
            },
            {
                "moduleName": "AI Chat",
                "price": 454.5,
                "model": "FastAI-4k",
                "tokens": 303,
                "question": "测试问题",
                "answer": "测试回答",
                "maxToken": 2050,
                "quoteList": [],
                "completeMessages": []
            }
        ],
        "id": "detail_test_id",
        "model": "FastAI-4k",
        "usage": {
            "prompt_tokens": 1,
            "completion_tokens": 1,
            "total_tokens": 2
        },
        "choices": [
            {
                "message": {
                    "role": "assistant",
                    "content": "测试回答"
                },
                "finish_reason": "stop",
                "index": 0
            }
        ]
    }
    
    # 测试 detail=false 格式化
    formatted_false = agent.format_response(detail_false_response)
    print("Detail=false 格式化结果:")
    print(json.dumps(formatted_false, indent=2, ensure_ascii=False))
    print()
    
    # 测试 detail=true 格式化
    formatted_true = agent.format_response(detail_true_response)
    print("Detail=true 格式化结果:")
    print(json.dumps(formatted_true, indent=2, ensure_ascii=False))
    print()
    
    # 验证结果
    assert "responseData" not in formatted_false, "detail=false 时不应包含 responseData"
    assert "responseData" in formatted_true, "detail=true 时应包含 responseData"
    assert len(formatted_true["responseData"]) == 2, "responseData 应包含 2 个模块"
    
    print("✅ 所有测试通过！")

def test_request_validation():
    """测试请求验证是否支持 detail 参数"""
    
    agent = FastGPTAgent()
    
    # 测试包含 detail 参数的请求
    request_data = {
        "query": "测试查询",
        "user": "test_user",
        "detail": True
    }
    
    is_valid = agent.validate_request(request_data)
    print(f"包含 detail=True 的请求验证结果: {is_valid}")
    assert is_valid, "包含 detail 参数的请求应该通过验证"
    
    print("✅ 请求验证测试通过！")

if __name__ == "__main__":
    print("开始测试 FastGPT Agent 的 detail 功能...")
    print("=" * 50)
    
    test_format_response()
    print()
    test_request_validation()
    
    print("=" * 50)
    print("🎉 所有测试完成！")
