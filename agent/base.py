from abc import ABC, abstractmethod
from typing import Dict, Any, Optional

class BaseAgent(ABC):
    """
    所有智能体（Agent）必须实现的基类。

    该类定义了智能体的基本接口，包括请求校验、请求处理和响应格式化三个核心方法。
    子类需实现这些抽象方法，以保证统一的接口规范。
    """

    @abstractmethod
    def validate_request(self, request_data: Dict[str, Any]) -> bool:
        """
        校验请求数据是否合法。

        参数:
            request_data (Dict[str, Any]): 需要校验的请求数据

        返回:
            bool: 如果请求数据合法返回 True，否则返回 False
        """
        pass

    @abstractmethod
    def process_request(self, request_data: Dict[str, Any]) -> Any:
        """
        处理请求并返回原始响应。

        参数:
            request_data (Dict[str, Any]): 需要处理的请求数据

        返回:
            Any: 原始响应数据，具体类型由子类决定
        """
        pass

    @abstractmethod
    def format_response(self, response_data: Any) -> Dict[str, Any]:
        """
        将原始响应数据格式化为标准结构。

        参数:
            response_data (Any): 原始响应数据

        返回:
            Dict[str, Any]: 标准化后的响应字典
        """
        pass