from fastapi import APIRouter, Request, HTTPException
from pydantic import BaseModel
from fastapi.responses import StreamingResponse, JSONResponse
import agent.dify as dify
import agent.fastgpt as fastgpt
import asyncio
from typing import List, Dict, Optional

"""
 messages: List[Dict[str, str]],
    app_id: Optional[str] = None,
    chat_id: Optional[str] = None,
    stream: bool = False,
    detail: bool = False,
    response_chat_item_id: Optional[str] = None,
    variables: Optional[Dict[str, str]] = None
"""

# 定义请求体模型
class ChatRequest(BaseModel):
    app_id: Optional[str] = None
    chat_id: Optional[str] = None
    stream: bool = False
    detail: bool = False
    query: str
    conversation_id: str = ""
    files: list = []
    user: Optional[str] = None

# 定义响应格式化类
class ChatResponseFormatter:
    @staticmethod
    def from_dify(data):
        return {
            "responseData": [
                # 可根据 data["metadata"]["retriever_resources"] 填充
            ],
            "id": data.get("id", ""),
            "model": "",
            "usage": data.get("metadata", {}).get("usage", {}),
            "choices": [
                {
                    "message": {
                        "role": "assistant",
                        "content": data.get("answer", "")
                    },
                    "finish_reason": "stop",
                    "index": 0
                }
            ]
        }

    @staticmethod
    def from_fastgpt(data):
        return {
            "responseData": data.get("responseData", []),
            "id": data.get("id", ""),
            "model": data.get("model", ""),
            "usage": data.get("usage", {}),
            "choices": data.get("choices", [])
        }

chat = APIRouter()

@chat.post("/chat")
async def get_chat(request: Request, body: ChatRequest):
    agent = request.headers.get("agent", "").lower()
    # 断言 user 字段必须存在且非空
    if agent == "dify":
        # Dify 的请求体必须包含 user 字段
        if not body.user:
            raise HTTPException(
                status_code=400, detail="Missing required field: user"
                )
        print(body)
        print(header := request.headers)
        files = body.files if body.files else None
        resp = dify.send_chat_message(
            api_key=dify.dify_api_key,
            user=body.user,
            base_url=dify.dify_base_url,
            query=body.query,
            response_mode="streaming" if body.stream else "blocking",
            conversation_id=body.conversation_id,
            files=files
        )
        print("Response status:", resp.status_code)
        print("Response text:", resp.text)
        data = resp.json()
        result = ChatResponseFormatter.from_dify(data)
        return JSONResponse(content=result)

    if agent == "fastgpt":
        messages = [
            {"role": "user", "content": body.query}
        ]
        variables = {
            "uid": body.user
        }
        loop = asyncio.get_event_loop()
        data = await loop.run_in_executor(
            None,
            lambda: fastgpt.chat_completions(
                messages=messages,
                app_id=body.app_id,             
                chat_id=body.chat_id,         
                variables=variables,
                stream=False,
                detail=body.detail
            )
        )
        result = ChatResponseFormatter.from_fastgpt(data)
        return JSONResponse(content=result)

    return JSONResponse(content={
        "id": "",
        "model": "",
        "usage": {},
        "choices": []
    })