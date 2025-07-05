import os
import httpx
from dotenv import load_dotenv

load_dotenv()
dify_api_key = os.getenv("DIFY_API_KEY")
dify_base_url = os.getenv("DIFY_BASE_URL")

def send_chat_message(api_key, user, base_url, query, response_mode="blocking", conversation_id="", files=None):
    """
    向 Dify 服务发送聊天消息请求。

    参数:
        api_key (str): Dify API 密钥，用于身份验证，从环境变量 DIFY_API_KEY 获取。
        user (str): 用户标识符，用于标识发送消息的用户。
        files (list): 附加的文件列表，默认为 None。
        base_url (str): Dify 服务的基础 URL，例如 http://localhost/v1。
        query (str): 用户输入的提问内容。
        response_mode (str): 响应模式，"blocking" 为同步，"streaming" 为流式（默认为 "blocking"）。
        conversation_id (str): 会话 ID，用于多轮对话（可选）。

    返回:
        httpx.Response: Dify 服务的 HTTP 响应对象。
    """
    url = f"{base_url}/chat-messages"
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }
    data = {
        "inputs": {},
        "query": query,
        "response_mode": response_mode,
        "conversation_id": conversation_id,
        "user": user,
        "files": files
    }
    with httpx.Client() as client:
        if response_mode == "streaming":
            # 返回同步流式响应
            return client.stream("POST", url, headers=headers, json=data)
        else:
            response = client.post(url, headers=headers, json=data)
            return response