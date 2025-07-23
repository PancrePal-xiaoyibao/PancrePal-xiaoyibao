import os
from typing import Dict, Any
from .base import BaseAgent
from .registry import registry
from .models import ChatRequest

class AgentTemplate(BaseAgent):
    """
    AgentTemplate 模板类，定义接入新 Agent 的标准实现方式。
    开发者可基于此模板快速实现自定义 Agent。
    """

    def __init__(self):
        # 可在此初始化所需的环境变量或配置
        self.api_key = os.getenv("YOUR_AGENT_API_KEY")
        self.base_url = os.getenv("YOUR_AGENT_BASE_URL")

    def validate_request(self, request_data: Dict[str, Any]) -> bool:
        """
        校验请求数据是否合法。
        子类可根据实际需求自定义校验逻辑。
        需要先检验 ChatRequest 模型是否能通过，
        以确保前端传入的参数符合预期。

        参数:
            request_data (Dict[str, Any]): 需要校验的请求数据

        返回:
            bool: 如果请求数据合法返回 True，否则返回 False
        """
        # 示例：检查 query 字段是否存在且非空
        try:
            ChatRequest(**request_data)
        except Exception:
            return False
        return 'query' in request_data and bool(request_data['query'])

    def process_request(self, request_data: Dict[str, Any]) -> Any:
        """
        处理请求并返回原始响应。
        子类需实现具体的 API 调用逻辑。

        参数:
            request_data (Dict[str, Any]): 需要处理的请求数据

        返回:
            Any: 原始响应数据
        """
        # 示例：伪代码，实际应调用第三方 API
        # response = requests.post(self.base_url, headers=..., json=request_data)
        # return response.json()
        return {"result": "This is a mock response from AgentTemplate."}

    def format_response(self, response_data: Any) -> Dict[str, Any]:
        """
        将原始响应数据格式化为标准结构。
        子类可根据实际返回结构自定义格式化逻辑。

        参数:
            response_data (Any): 原始响应数据

        返回:
            Dict[str, Any]: 标准化后的响应字典
        """
        # 示例：统一输出格式
        return {
            "status": "success"
        }

# 注册模板 Agent（实际使用时请更换名称和实现）
# registry.register("template", AgentTemplate())