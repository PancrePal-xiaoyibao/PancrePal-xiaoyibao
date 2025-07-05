import os
import httpx
from dotenv import load_dotenv
import json
from typing import List, Dict, Optional, Union
import traceback

load_dotenv()
fastgpt_api_key = os.getenv("FASTGPT_API_KEY")
fastgpt_base_url = os.getenv("FASTGPT_BASE_URL")
fastgpt_app_id = os.getenv("FASTGPT_APP_ID")

def chat_completions(
    messages: List[Dict[str, str]],
    app_id: Optional[str] = None,
    chat_id: Optional[str] = None,
    stream: bool = False,
    detail: bool = False,
    response_chat_item_id: Optional[str] = None,
    variables: Optional[Dict[str, str]] = None
) -> Dict:
    """
    发送聊天请求到FastGPT API

    Args:
        messages: 消息列表，格式为 [{"content": "消息内容", "role": "user"}]
                 当chat_id为None时，使用完整messages构建上下文
                 当chat_id不为None时，只使用messages最后一个作为用户问题
        app_id: 应用ID，可选，优先使用参数，其次使用环境变量
        chat_id: 聊天ID，可选
                为None时，不使用FastGPT上下文功能，完全通过messages构建上下文
                为非空字符串时，使用chatId进行对话，自动从FastGPT数据库取历史记录
        stream: 是否流式输出，默认为False
        detail: 是否返回中间值（模块状态，响应的完整结果等），默认为False
        response_chat_item_id: 响应聊天项ID，如果传入会作为本次对话响应消息的ID存入数据库
        variables: 模块变量，会替换模块中输入框内容里的{{key}}

    Returns:
        API响应的JSON数据
    """
    if not fastgpt_api_key:
        raise ValueError("FASTGPT_API_KEY not found in environment variables")

    used_app_id = app_id or fastgpt_app_id
    if not used_app_id:
        raise ValueError("app_id is required. Please provide it as parameter or set FASTGPT_APP_ID in environment variables")

    if not fastgpt_base_url:
        raise ValueError("FASTGPT_BASE_URL not found in environment variables")

    url = f"{fastgpt_base_url}/v1/chat/completions"

    headers = {
        "Authorization": f"Bearer {fastgpt_api_key}",
        "Content-Type": "application/json"
    }

    data = {
        "appId": used_app_id,
        "stream": stream,
        "detail": detail,
        "messages": messages
    }

    if chat_id is not None:
        data["chatId"] = chat_id
    if response_chat_item_id is not None:
        data["responseChatItemId"] = response_chat_item_id
    if variables is not None:
        data["variables"] = variables

    # 打印最终请求的URL和数据
    print("Request URL:", url)
    print("Request headers:", headers)
    print("Request data:", json.dumps(data, ensure_ascii=False, indent=2))

    with httpx.Client(timeout=30.0) as client:
        response = client.post(url, headers=headers, json=data)
        print("Raw response status:", response.status_code)
        print("Raw response text:", response.text)
        response.raise_for_status()
        return response.json()