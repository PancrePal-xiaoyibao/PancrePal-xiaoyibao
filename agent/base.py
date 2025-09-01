from abc import ABC, abstractmethod
from typing import Dict, Any, Optional
from .models import UnifiedChatResponse, FileUploadResponse, FastGPTFileInfo

class BaseAgent(ABC):
    """
    所有智能体（Agent）必须实现的基类。

    该类定义了智能体的基本接口，包括请求校验、请求处理和响应格式化三个核心方法。
    子类需实现这些抽象方法，以保证统一的接口规范。
    所有 Agent 必须遵循 FastGPT 的响应格式，返回 UnifiedChatResponse 模型。
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
    def format_response(self, response_data: Any) -> UnifiedChatResponse:
        """
        将原始响应数据格式化为统一的标准结构。
        所有 Agent 必须遵循 FastGPT 的响应格式。

        参数:
            response_data (Any): 原始响应数据

        返回:
            UnifiedChatResponse: 统一的响应模型，支持标准模式和详细模式
        """
        pass

    def stream_chat(self, request_data: Dict[str, Any]):
        """
        流式对话接口（SSE）。

        参数:
            request_data (Dict[str, Any]): 请求数据，需包含 detail=false 且 stream=true

        返回:
            迭代器/生成器: 逐条产出 SSE 文本数据（以 "data: {json}" 形式，使用 \"\n\n\" 分隔）
        """
        raise NotImplementedError("This agent does not support streaming chat")

    def upload_file(self, file_path: str) -> str:
        """
        上传文件的默认实现（返回文件可访问 URL/ID）。
        子类可以重写以使用各自平台的对象存储。

        参数:
            file_path (str): 本地文件路径

        返回:
            str: 文件的访问 URL 或 ID

        异常:
            NotImplementedError: 如果子类没有实现此方法
        """
        raise NotImplementedError("File upload not supported by this agent")

    def build_file_info(self, *, file_id: str, file_name: str, size_bytes: int, mime_type: str, created_by: str = "", created_at: Optional[int] = None) -> FastGPTFileInfo:
        """
        构建统一文件信息（用于返回统一响应）。
        """
        import time
        from pathlib import Path
        ext = Path(file_name).suffix.lstrip('.')
        ts = created_at if created_at is not None else int(time.time())
        return FastGPTFileInfo(
            id=file_id,
            name=file_name,
            size=size_bytes,
            extension=ext,
            mime_type=mime_type,
            created_by=created_by or "unknown",
            created_at=ts
        )