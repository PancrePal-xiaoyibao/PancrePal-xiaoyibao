#!/usr/bin/env python3
"""
增强的 CozeAgent 测试脚本
验证改进的响应处理和错误处理逻辑
"""
import os
import sys
from dotenv import load_dotenv

# 添加项目根目录到路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from agent.coze import CozeAgent
from agent.models import ChatRequest

load_dotenv()

def test_enhanced_coze_agent():
    """测试增强的 CozeAgent 功能"""
    print("开始测试增强的 CozeAgent...")
    print("=" * 50)
    
    try:
        # 初始化 CozeAgent
        agent = CozeAgent()
        print("✓ CozeAgent 初始化成功")
        
        # 测试不同类型的请求
        test_cases = [
            {
                "name": "基础问答测试",
                "request": {
                    "query": "你好，请介绍一下你自己",
                    "user": "test_user_001",
                    "stream": False
                }
            },
            {
                "name": "胰腺癌相关问题测试",
                "request": {
                    "query": "胰腺癌的早期症状有哪些？如何早期发现？",
                    "user": "test_user_002",
                    "stream": False
                }
            },
            {
                "name": "流式请求测试（应该转为非流式）",
                "request": {
                    "query": "请详细解释胰腺癌的治疗方法",
                    "user": "test_user_003",
                    "stream": True  # 应该被转为非流式
                }
            }
        ]
        
        # 检查环境变量配置
        coze_api_token = os.getenv("COZE_API_TOKEN")
        coze_bot_id = os.getenv("COZE_BOT_ID")
        
        if not coze_api_token or not coze_bot_id:
            print("⚠️ 未检测到完整的 Coze 配置，只进行基础验证测试")
            test_basic_validation_only(agent)
            return
        
        print(f"✓ 检测到 Coze 配置，Bot ID: {coze_bot_id}")
        print()
        
        # 执行测试用例
        for i, test_case in enumerate(test_cases, 1):
            print(f"测试 {i}: {test_case['name']}")
            print("-" * 30)
            
            request_data = test_case['request']
            
            # 验证请求
            if not agent.validate_request(request_data):
                print(f"❌ 请求验证失败: {request_data}")
                continue
            
            print(f"用户问题: {request_data['query']}")
            if request_data.get('stream'):
                print("(注: 流式请求将转为非流式处理)")
            
            # 处理请求
            print("正在处理请求...")
            response = agent.process_request(request_data)
            
            # 显示原始响应的关键信息
            print(f"响应状态: {'成功' if 'error' not in response else '失败'}")
            if 'error' in response:
                print(f"错误信息: {response['error']}")
                print(f"错误类型: {response.get('error_type', 'unknown')}")
            else:
                print(f"对话ID: {response.get('id', 'N/A')}")
                print(f"会话ID: {response.get('conversation_id', 'N/A')}")
                print(f"状态: {response.get('status', 'N/A')}")
                
                # 显示元数据
                if 'metadata' in response:
                    metadata = response['metadata']
                    print(f"消息统计: 回答={metadata.get('answer_count', 0)}, "
                          f"推荐问题={metadata.get('follow_up_count', 0)}, "
                          f"总消息数={metadata.get('total_messages', 0)}")
                
                # 显示使用量
                usage = response.get('usage', {})
                print(f"Token使用: 输入={usage.get('prompt_tokens', 0)}, "
                      f"输出={usage.get('completion_tokens', 0)}, "
                      f"总计={usage.get('total_tokens', 0)}")
            
            # 格式化响应
            print("正在格式化响应...")
            formatted_response = agent.format_response(response)
            
            print(f"格式化后响应:")
            print(f"  模型: {formatted_response.model}")
            print(f"  选择数: {len(formatted_response.choices)}")
            
            if formatted_response.choices:
                choice = formatted_response.choices[0]
                content = choice.message.content
                # 截取内容进行显示
                display_content = content[:200] + "..." if len(content) > 200 else content
                print(f"  AI回复: {display_content}")
                print(f"  完成原因: {choice.finish_reason}")
            
            # 显示额外变量（如果有）
            if formatted_response.newVariables:
                print(f"  额外信息: {list(formatted_response.newVariables.keys())}")
            
            print()
            
    except Exception as e:
        print(f"❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()

def test_basic_validation_only(agent):
    """只进行基础验证测试（当没有API配置时）"""
    print("进行基础验证测试...")
    
    # 测试请求验证
    valid_requests = [
        {"query": "测试问题", "user": "test_user"},
        {"query": "胰腺癌的症状", "user": "user123", "stream": False},
    ]
    
    invalid_requests = [
        {},  # 缺少必需字段
        {"user": "test"},  # 缺少query
        {"query": ""},  # 空query
        {"query": "测试", "user": ""},  # 空user
    ]
    
    print("测试有效请求验证:")
    for i, req in enumerate(valid_requests, 1):
        result = agent.validate_request(req)
        print(f"  {i}. {req} -> {'✓ 通过' if result else '❌ 失败'}")
    
    print("测试无效请求验证:")
    for i, req in enumerate(invalid_requests, 1):
        result = agent.validate_request(req)
        print(f"  {i}. {req} -> {'❌ 应该失败但通过了' if result else '✓ 正确拒绝'}")

def test_error_handling():
    """测试错误处理机制"""
    print("\n测试错误处理机制...")
    print("-" * 30)
    
    try:
        # 创建一个没有有效配置的agent来测试错误处理
        os.environ.pop("COZE_API_TOKEN", None)  # 临时移除token
        
        from agent.coze import CozeAgent
        
        # 这应该会失败
        try:
            agent = CozeAgent()
            print("❌ 应该因为缺少token而失败，但没有")
        except ValueError as e:
            print(f"✓ 正确捕获了配置错误: {e}")
        
    except Exception as e:
        print(f"错误处理测试异常: {e}")

if __name__ == "__main__":
    test_enhanced_coze_agent()
    test_error_handling()
