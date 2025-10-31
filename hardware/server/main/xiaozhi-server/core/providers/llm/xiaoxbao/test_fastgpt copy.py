import requests
import json

def test_fastgpt_api():
    # 配置参数（根据你的实际配置修改）
    base_url = "https://admin.xiaoyibao.com.cn"  # FastGPT服务地址
    api_key = "openapi-pkUdgWhqX9v95fk9xAy0MFMrZUm2LMroHz3NhObMJujpxKtpTQCxi"  # 应用特定的API Key
    app_id = "68872fe412268e8142f66d25"  # 应用ID
    chat_id = "test-chat-id"  # 对话窗口ID（随机生成或固定值）

    # 请求头设置
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }

    # 尝试两种可能的URL路径（带v1和不带v1）
    url_options = [
        f"{base_url}/api/v1/chat/completions",  # 带v1的路径
        f"{base_url}/api/chat/completions"      # 不带v1的路径
    ]

    # ===== 测试普通对话模式 =====
    print("\n===== 测试普通对话模式 =====")
    payload = {
        "stream": False,
        "appId": app_id,
        "chatId": chat_id,
        "messages": [
            {"role": "user", "content": "你好，请介绍一下你自己"}
        ],
        "detail": True  # 获取详细返回信息
    }

    for url in url_options:
        try:
            response = requests.post(url, headers=headers, data=json.dumps(payload))
            if response.status_code == 200:
                print("普通对话成功！")
                print("url:", url)
                print("响应内容:", json.dumps(response.json(), indent=2, ensure_ascii=False))
                break
            elif response.status_code == 404:
                print(f"URL {url} 返回404，尝试备用路径...")
            else:
                print(f"请求失败，状态码: {response.status_code}, 响应: {response.text}")
        except Exception as e:
            print(f"请求异常: {str(e)}")

    # ===== 测试插件模式 =====
    print("\n===== 测试插件模式 =====")
    plugin_payload = {
        "stream": False,
        "detail": True,  # 插件模式强制detail=true
        "variables": {
            "query": "需要处理的查询内容"  # 插件输入参数
        }
    }

    for url in url_options:
        try:
            response = requests.post(url, headers=headers, data=json.dumps(plugin_payload))
            if response.status_code == 200:
                print("插件调用成功！")
                print("响应内容:", json.dumps(response.json(), indent=2, ensure_ascii=False))
                
                # 提取插件输出
                response_data = response.json()
                if 'pluginData' in response_data:
                    print("插件输出:", response_data['pluginData'])
                break
            elif response.status_code == 404:
                print(f"URL {url} 返回404，尝试备用路径...")
            else:
                print(f"请求失败，状态码: {response.status_code}, 响应: {response.text}")
        except Exception as e:
            print(f"请求异常: {str(e)}")

if __name__ == "__main__":
    test_fastgpt_api()