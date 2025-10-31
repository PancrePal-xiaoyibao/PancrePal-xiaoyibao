import sys
import os

# 添加项目根目录到Python路径
# 修复路径问题，正确添加项目根目录
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '../../../..'))
sys.path.insert(0, project_root)

from core.providers.llm.fastgpt.fastgpt import LLMProvider

# 配置信息
config = {
    # "api_key": "fastgpt-pkUdgWhqX9v95fk9xAy0MFMrZUm2LMroHz3NhObMJujpxKtpTQCxi",
    "api_key": "openapi-bLuna5VmKYqR7IXAfRt0taKmld0Oxq90xnUEdiNk3PyoSsekPaaRi1DlVG82U",
    "base_url": "https://admin.xiaoyibao.com.cn",  # 例如: "http://localhost:3000/api"
    "detail": False,
    "variables": {}
}

# 创建LLMProvider实例
llm = LLMProvider(config)

# 测试对话数据
test_dialogue = [
    {"role": "user", "content": "你好，介绍一下你自己"}
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

# # 测试response_with_functions方法
# print("\n测试response_with_functions方法:")
# try:
#     response_generator = llm.response_with_functions("test_session_id", test_dialogue)
#     # 这个方法目前只是记录错误日志，不会产生实际输出
#     print("该方法暂未实现完整的工具调用")
# except Exception as e:
#     print(f"调用出错: {e}")
