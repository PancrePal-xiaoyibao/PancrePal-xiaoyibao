from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse
from typing import Dict, Any
from agent import registry

mcp_router = APIRouter()


@mcp_router.post("/mcp")
async def mcp_entry(request: Request) -> JSONResponse:
    """
    约定：
    - 通过 Header 传入 `agent`/`x-agent` 指定目标 Agent。
    - 请求体为任意 JSON，推荐包含 {"method": str, "params": dict}。
    - 仅做简单演示：handshake/capabilities/echo。
    """
    agent_name = (
        request.headers.get("agent")
        or request.headers.get("Agent")
        or request.headers.get("x-agent")
        or request.headers.get("X-Agent")
        or request.query_params.get("agent")
        or ""
    ).lower()

    if not agent_name:
        return JSONResponse(content={
            "ok": False,
            "error": "Missing agent header. Please set 'agent: fastgpt' or 'x-agent: fastgpt'"
        }, status_code=400)

    agent = registry.get(agent_name)
    if not agent:
        return JSONResponse(content={
            "ok": False,
            "error": f"Unknown agent: {agent_name}"
        }, status_code=400)

    try:
        payload: Dict[str, Any] = await request.json()
    except Exception:
        payload = {}

    try:
        result = agent.handle_mcp(payload)
        return JSONResponse(content=result)
    except Exception as e:
        return JSONResponse(content={
            "ok": False,
            "error": str(e)
        }, status_code=500)


