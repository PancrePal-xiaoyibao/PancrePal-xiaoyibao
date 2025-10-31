import sys
import os
import json
import requests

# 添加项目根目录到Python路径
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '../../../..'))
sys.path.insert(0, project_root)

# 简化版的FastGPT LLMProvider实现，参考OpenAI API方式
class LLMProvider:
    def __init__(self, config):
        self.api_key = config["api_key"]
        # 确保base_url以/v1结尾，与OpenAI API兼容
        self.base_url = config.get("base_url", "").rstrip('/')
        self.detail = config.get("detail", False)
        self.variables = config.get("variables", {})

    def response(self, session_id, dialogue, **kwargs):
        try:
            # 准备消息历史，将所有对话消息传递给API
            messages = []
            for msg in dialogue:
                # 只传递role和content字段
                if "role" in msg and "content" in msg:
                    messages.append({
                        "role": msg["role"],
                        "content": msg["content"]
                    })

            # 发起流式请求
            response = requests.post(
                f"{self.base_url}/",
                headers={"Authorization": f"Bearer {self.api_key}"},  # 使用Bearer认证方式
                json={
                    "stream": True,
                    "chatId": session_id,
                    "appId": "68872fe412268e8142f66d25",
                    "detail": self.detail,
                    "variables": self.variables,
                    "messages": messages,  # 传递完整对话历史
                },
                stream=True,
            )
            
            response.raise_for_status()
            
            for line in response.iter_lines():
                if line:
                    try:
                        if line.startswith(b"data: "):
                            if line[6:].decode("utf-8") == "[DONE]":
                                break

                            data = json.loads(line[6:])
                            if "choices" in data and len(data["choices"]) > 0:
                                delta = data["choices"][0].get("delta", {})
                                if (
                                    delta
                                    and "content" in delta
                                    and delta["content"] is not None
                                ):
                                    content = delta["content"]
                                    # 不过滤特殊字符，让API返回内容更准确
                                    yield content

                    except json.JSONDecodeError as e:
                        continue
                    except Exception as e:
                        continue

        except Exception as e:
            print(f"Error in response generation: {e}")
            yield "【服务响应异常】"

    def response_with_functions(self, session_id, dialogue, functions=None):
        print("fastgpt暂未实现完整的工具调用（function call），建议使用其他意图识别")

# 配置信息，参考OpenAI示例
config = {
    # "api_key": "openapi-vemBbC4MJO01GJBOoxtDXYE0X4ATDR5aCuBDCGDUEXdggpFX4YMwQRkNEB",
    "api_key": "openapi-pkUdgWhqX9v95fk9xAy0MFMrZUm2LMroHz3NhObMJujpxKtpTQCxi",
    "base_url": "https://admin.xiaoyibao.com.cn/api/v1",  # 注意：代码会自动添加/v1后缀
    "detail": False,
    "variables": {}
}

# 创建LLMProvider实例
llm = LLMProvider(config)

# 测试对话数据
test_dialogue = [
    {"role": "user", "content": "你是谁"}
]

# 调用response方法并打印结果
print("开始测试FastGPT API调用:")
try:
    response_generator = llm.response("test_session_id", test_dialogue)
    full_response = ""
    for chunk in response_generator:
        print(chunk, end="", flush=True)
        full_response += chunk
    print("\n\n完整响应:")
    print(full_response)
except Exception as e:
    print(f"调用出错: {e}")

# 测试多轮对话
print("\n\n开始测试多轮对话:")
multi_turn_dialogue = [
    {"role": "user", "content": "你好"},
    {"role": "assistant", "content": "你好！有什么我可以帮你的吗？"},
    {"role": "user", "content": "你是谁？"}
]

try:
    response_generator = llm.response("test_session_id_2", multi_turn_dialogue)
    full_response = ""
    for chunk in response_generator:
        print(chunk, end="", flush=True)
        full_response += chunk
    print("\n\n完整响应:")
    print(full_response)
except Exception as e:
    print(f"调用出错: {e}")

# 测试response_with_functions方法
# print("\n测试response_with_functions方法:")
# try:
#     response_generator = llm.response_with_functions("test_session_id", test_dialogue)
#     print("该方法暂未实现完整的工具调用")
# except Exception as e:
#     print(f"调用出错: {e}")