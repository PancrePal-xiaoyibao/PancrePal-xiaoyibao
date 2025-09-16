import os
import httpx
from dotenv import load_dotenv
import json
from typing import List, Dict, Optional, Union, Any
import traceback
import uuid
import mimetypes
from datetime import datetime
from .base import BaseAgent
from .registry import registry
from .models import ChatRequest, UnifiedChatResponse, StandardChatResponse, DetailedChatResponse

if os.path.exists('.env'):
    load_dotenv('.env')

fastgpt_api_key = os.getenv("FASTGPT_API_KEY")
fastgpt_base_url = os.getenv("FASTGPT_BASE_URL")
fastgpt_app_id = os.getenv("FASTGPT_APP_ID")

# S3 / MinIO 配置（用于文件上传）
s3_endpoint = os.getenv("S3_ENDPOINT")  # 例如: https://minio.example.com 或 http://127.0.0.1:9000
s3_access_key = os.getenv("S3_ACCESS_KEY")
s3_secret_key = os.getenv("S3_SECRET_KEY")
s3_bucket = os.getenv("S3_BUCKET")
s3_region = os.getenv("S3_REGION")  # 可选
s3_key_prefix = os.getenv("S3_KEY_PREFIX", "uploads")  # 可选，默认 uploads
s3_acl = os.getenv("S3_ACL")  # 可选，例如 public-read（部分 MinIO 可无 ACL，依赖桶策略）
s3_public_base_url = os.getenv("S3_PUBLIC_BASE_URL")  # 可选，外网访问基准，如 https://cdn.example.com

class FastGPTAgent(BaseAgent):
    """Agent for FastGPT API."""
    
    @staticmethod
    def _is_valid_object_id(value: Optional[str]) -> bool:
        if not value or not isinstance(value, str):
            return False
        if len(value) != 24:
            return False
        try:
            int(value, 16)
            return True
        except Exception:
            return False
    
    def validate_request(self, request_data: Dict[str, Any]) -> bool:
        """Validate if the request data is valid for FastGPT."""
        # FastGPT requires a query or files
        try:
            # 用 ChatRequest 模型来验证请求数据
            ChatRequest(**request_data)
        except Exception as e:
            print(f"Validation error: {e}")
            return False
        
        # 至少需要有 query 或 files 其中一个
        has_query = 'query' in request_data and bool(request_data['query'])
        has_files = 'files' in request_data and request_data['files'] and len(request_data['files']) > 0
        
        if not (has_query or has_files):
            return False

        # 校验 appId（请求级或环境变量）
        used_app_id = request_data.get('app_id') or fastgpt_app_id
        if not self._is_valid_object_id(used_app_id):
            print(f"Invalid app_id provided or missing. Got: {used_app_id}")
            return False

        return True
    
    def process_request(self, request_data: Dict[str, Any]) -> Dict[str, Any]:
        """Process the request using FastGPT API."""
        # 构建消息内容，支持文件上传
        message_content = []
        
        # 添加文本内容
        text_content = request_data.get('query', '')
        if text_content:
            message_content.append({
                "type": "text",
                "text": text_content
            })
        
        # 处理文件上传
        files = request_data.get('files', [])
        if files:
            for file_url in files:
                if isinstance(file_url, str):
                    # 判断文件类型
                    if self._is_image_file(file_url):
                        # 图片文件
                        message_content.append({
                            "type": "image_url",
                            "image_url": {
                                "url": file_url
                            }
                        })
                    else:
                        # 文档文件
                        # 从URL中提取文件名
                        file_name = self._extract_filename_from_url(file_url)
                        message_content.append({
                            "type": "file_url",
                            "name": file_name,
                            "url": file_url
                        })
        
        # 如果有多个内容类型，使用复合格式；否则使用简单字符串格式
        if len(message_content) > 1 or (len(message_content) == 1 and message_content[0]["type"] != "text"):
            messages = [
                {"role": "user", "content": message_content}
            ]
        else:
            # 只有文本内容时，保持原有格式
            messages = [
                {"role": "user", "content": text_content}
            ]
        
        variables = {}
        if 'uid' in request_data and request_data['uid']:
            variables["uid"] = request_data['uid']
        if 'user' in request_data and request_data['user']:
            variables["user"] = request_data['user']
        # 请求体参数
        response = self.chat_completions(
            messages=messages,
            app_id=request_data.get('app_id'),
            chat_id=request_data.get('chat_id'),
            stream=request_data.get('stream', False),
            detail=request_data.get('detail', False),  # 支持通过请求参数控制 detail
            variables=variables
        )
        
        return response
    
    def _is_image_file(self, url: str) -> bool:
        """判断URL是否为图片文件"""
        image_extensions = ['.jpg', '.jpeg', '.png', '.gif', '.bmp', '.webp', '.svg']
        url_lower = url.lower()
        return any(url_lower.endswith(ext) for ext in image_extensions)
    
    def _extract_filename_from_url(self, url: str) -> str:
        """从URL中提取文件名"""
        try:
            # 从URL中提取文件名
            import urllib.parse
            parsed_url = urllib.parse.urlparse(url)
            filename = parsed_url.path.split('/')[-1]
            if filename:
                return filename
            else:
                # 如果无法提取文件名，返回默认名称
                return "uploaded_file"
        except Exception:
            return "uploaded_file"
    
    # 规范来自 FastGPT 的响应格式
    def format_response(self, response_data: Dict[str, Any]) -> UnifiedChatResponse:
        """Format the FastGPT response into a standardized format using UnifiedChatResponse model."""
        # 检查是否为 detail=true 的响应格式
        if "responseData" in response_data:
            # detail=true 的响应格式，返回详细模式
            return UnifiedChatResponse(
                responseData=response_data.get("responseData", []),
                newVariables=response_data.get("newVariables", {})
            )
        else:
            # detail=false 的响应格式，返回标准模式
            return UnifiedChatResponse(
                id=response_data.get("id", ""),
                model=response_data.get("model", ""),
                usage=response_data.get("usage", {}),
                choices=response_data.get("choices", [])
            )
    
    def chat_completions(
        self,
        messages: List[Dict[str, Union[str, List[Dict[str, Any]]]]],
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
        if not self._is_valid_object_id(used_app_id):
            raise ValueError(f"Invalid app_id format. Expect 24-char hex ObjectId, got: {used_app_id}")

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

        with httpx.Client(timeout=30.0) as client:
            response = client.post(url, headers=headers, json=data)
            print("Raw response status:", response.status_code)
            print("Raw response text:", response.text)
            response.raise_for_status()
            return response.json()

    def stream_chat(self, request_data: Dict[str, Any]):
        """
        以 SSE 形式流式转发 FastGPT 的响应（detail=false, stream=true）。
        """
        if not fastgpt_api_key:
            raise ValueError("FASTGPT_API_KEY not found in environment variables")

        used_app_id = request_data.get('app_id') or fastgpt_app_id
        if not used_app_id:
            raise ValueError("app_id is required. Please provide it as parameter or set FASTGPT_APP_ID in environment variables")
        if not self._is_valid_object_id(used_app_id):
            raise ValueError(f"Invalid app_id format. Expect 24-char hex ObjectId, got: {used_app_id}")

        if not fastgpt_base_url:
            raise ValueError("FASTGPT_BASE_URL not found in environment variables")

        # 组装消息（与 process_request 保持一致）
        message_content = []
        text_content = request_data.get('query', '')
        if text_content:
            message_content.append({
                "type": "text",
                "text": text_content
            })
        files = request_data.get('files', [])
        if files:
            for file_url in files:
                if isinstance(file_url, str):
                    if self._is_image_file(file_url):
                        message_content.append({
                            "type": "image_url",
                            "image_url": {"url": file_url}
                        })
                    else:
                        file_name = self._extract_filename_from_url(file_url)
                        message_content.append({
                            "type": "file_url",
                            "name": file_name,
                            "url": file_url
                        })

        if len(message_content) > 1 or (len(message_content) == 1 and message_content[0]["type"] != "text"):
            messages = [{"role": "user", "content": message_content}]
        else:
            messages = [{"role": "user", "content": text_content}]

        variables: Dict[str, str] = {}
        if 'uid' in request_data and request_data['uid']:
            variables["uid"] = request_data['uid']
        if 'user' in request_data and request_data['user']:
            variables["user"] = request_data['user']

        url = f"{fastgpt_base_url}/v1/chat/completions"
        headers = {
            "Authorization": f"Bearer {fastgpt_api_key}",
            "Content-Type": "application/json"
        }
        data = {
            "appId": used_app_id,
            "stream": True,
            "detail": False,
            "messages": messages
        }
        if request_data.get('chat_id') is not None:
            data["chatId"] = request_data.get('chat_id')
        if request_data.get('variables') is not None:
            data["variables"] = request_data.get('variables')
        elif variables:
            data["variables"] = variables

        def event_generator():
            with httpx.Client(timeout=None) as client:
                with client.stream("POST", url, headers=headers, json=data) as response:
                    response.raise_for_status()
                    for line in response.iter_lines():
                        if not line:
                            continue
                        # FastGPT 通常已带有 'data: ' 前缀，这里原样透传
                        yield (line + "\n\n")

        return event_generator()

    def upload_file(self, file_path: str) -> Any:
        """
        将本地临时文件上传到 S3/MinIO，并返回统一文件信息 FastGPTFileInfo。
        需要以下环境变量：
        - S3_ENDPOINT: 形如 https://minio.example.com 或 http://127.0.0.1:9000
        - S3_ACCESS_KEY, S3_SECRET_KEY
        - S3_BUCKET
        可选：S3_REGION, S3_KEY_PREFIX, S3_ACL, S3_PUBLIC_BASE_URL
        """
        if not all([s3_endpoint, s3_access_key, s3_secret_key, s3_bucket]):
            raise ValueError("Missing S3 configs. Please set S3_ENDPOINT,S3_ACCESS_KEY,S3_SECRET_KEY,S3_BUCKET")

        # 延迟导入 boto3，避免未使用文件上传功能时强依赖
        try:
            import boto3  # type: ignore
        except ImportError as e:
            raise ImportError("boto3 未安装。请运行: pip install boto3 或将其加入 requirements.txt") from e

        # 提取原始文件名（upload.py 会以 _{filename} 作为后缀创建临时文件）
        original_name = os.path.basename(file_path)
        if "_" in original_name:
            original_name = original_name.split("_", 1)[1] or original_name

        # 猜测 MIME
        mime_type = mimetypes.guess_type(original_name)[0] or "application/octet-stream"
        file_size = os.path.getsize(file_path)
        ext = os.path.splitext(original_name)[1]
        object_key = f"{s3_key_prefix}/{datetime.now().strftime('%Y/%m/%d')}/{uuid.uuid4().hex}{ext}"

        client = boto3.client(
            "s3",
            endpoint_url=s3_endpoint,
            aws_access_key_id=s3_access_key,
            aws_secret_access_key=s3_secret_key,
            region_name=s3_region if s3_region else None
        )

        extra_args = {"ContentType": mime_type}
        if s3_acl:
            extra_args["ACL"] = s3_acl

        with open(file_path, "rb") as f:
            client.upload_fileobj(
                f,
                s3_bucket,
                object_key,
                ExtraArgs=extra_args
            )

        # 生成可访问 URL：优先使用 S3_PUBLIC_BASE_URL，其次使用预签名 URL
        public_url: Optional[str] = None
        if s3_public_base_url:
            base = s3_public_base_url.rstrip('/')
            try:
                # 支持 {bucket} 占位符、虚拟主机式(bucket.example.com) 与路径式(/bucket/...)
                from urllib.parse import urlparse
                parsed = urlparse(base)
                host_has_bucket = parsed.netloc.startswith(f"{s3_bucket}.") if parsed.netloc else False
                path = (parsed.path or '').strip('/')
                path_has_bucket = (path == s3_bucket) or path.startswith(f"{s3_bucket}/")

                if '{bucket}' in base:
                    base = base.replace('{bucket}', s3_bucket)
                    public_url = f"{base}/{object_key}"
                elif host_has_bucket or path_has_bucket:
                    public_url = f"{base}/{object_key}"
                else:
                    public_url = f"{base}/{s3_bucket}/{object_key}"
            except Exception:
                public_url = f"{base}/{s3_bucket}/{object_key}"
        else:
            try:
                public_url = client.generate_presigned_url(
                    'get_object',
                    Params={'Bucket': s3_bucket, 'Key': object_key},
                    ExpiresIn=3600
                )
            except Exception:
                public_url = None

        # 构造统一文件信息；将 id 设为可访问 URL（若有），否则为对象键
        file_info = self.build_file_info(
            file_id=public_url or object_key,
            file_name=original_name,
            size_bytes=file_size,
            mime_type=mime_type,
            created_by="uploader"
        )

        return file_info

# Register the agent
registry.register("fastgpt", FastGPTAgent())