# 智能体管理API接口文档

## 概述

智能体管理API提供了查询和管理已注册智能体的功能，包括获取智能体列表、查询智能体详情和检查智能体健康状态。

## 基础信息

- **基础路径**: `/api/v1/agents`
- **内容类型**: `application/json`
- **认证**: 目前无需认证

## API接口

### 1. 获取所有智能体列表

获取系统中所有已注册的智能体信息。

**请求**
```http
GET /api/v1/agents/
```

**响应**
```json
{
  "success": true,
  "data": {
    "total": 2,
    "agents": [
      {
        "name": "fastgpt",
        "type": "FastGPTAgent",
        "module": "agent.fastgpt",
        "capabilities": {
          "streaming": true,
          "file_upload": true
        }
      },
      {
        "name": "dify",
        "type": "DifyAgent",
        "module": "agent.dify",
        "capabilities": {
          "streaming": false,
          "file_upload": false
        }
      }
    ]
  }
}
```

**响应字段说明**
- `success`: 请求是否成功
- `data.total`: 智能体总数
- `data.agents`: 智能体列表
  - `name`: 智能体名称
  - `type`: 智能体类型
  - `module`: 智能体模块路径
  - `capabilities`: 功能特性
    - `streaming`: 是否支持流式对话
    - `file_upload`: 是否支持文件上传

### 2. 获取指定智能体信息

获取特定智能体的详细信息。

**请求**
```http
GET /api/v1/agents/{agent_name}
```

**路径参数**
- `agent_name`: 智能体名称（不区分大小写）

**响应**
```json
{
  "success": true,
  "data": {
    "name": "fastgpt",
    "type": "FastGPTAgent",
    "module": "agent.fastgpt",
    "capabilities": {
      "streaming": true,
      "file_upload": true
    }
  }
}
```

**错误响应** (404)
```json
{
  "detail": "智能体 'nonexistent' 未找到"
}
```

### 3. 检查智能体健康状态

检查指定智能体的健康状态和可用性。

**请求**
```http
GET /api/v1/agents/{agent_name}/health
```

**路径参数**
- `agent_name`: 智能体名称（不区分大小写）

**响应**
```json
{
  "success": true,
  "data": {
    "name": "fastgpt",
    "status": "healthy",
    "timestamp": 1703123456.789,
    "capabilities": {
      "streaming": true,
      "file_upload": true
    }
  }
}
```

**响应字段说明**
- `status`: 智能体状态（目前固定为 "healthy"）
- `timestamp`: 检查时间戳（Unix时间戳）

## 使用示例

### Python示例

```python
import requests

# 获取所有智能体
response = requests.get("http://localhost:8000/api/v1/agents/")
agents = response.json()
print(f"可用智能体数量: {agents['data']['total']}")

# 获取特定智能体信息
fastgpt_info = requests.get("http://localhost:8000/api/v1/agents/fastgpt")
print(f"FastGPT信息: {fastgpt_info.json()}")

# 检查智能体健康状态
health = requests.get("http://localhost:8000/api/v1/agents/fastgpt/health")
print(f"健康状态: {health.json()}")
```

### cURL示例

```bash
# 获取所有智能体
curl -X GET "http://localhost:8000/api/v1/agents/"

# 获取特定智能体信息
curl -X GET "http://localhost:8000/api/v1/agents/fastgpt"

# 检查智能体健康状态
curl -X GET "http://localhost:8000/api/v1/agents/fastgpt/health"
```

## 错误处理

所有接口都遵循统一的错误响应格式：

```json
{
  "success": false,
  "error": "错误描述信息"
}
```

常见HTTP状态码：
- `200`: 请求成功
- `404`: 智能体未找到
- `500`: 服务器内部错误

## 注意事项

1. 智能体名称不区分大小写
2. 所有接口都是只读的，不会修改智能体状态
3. 健康检查接口目前只返回基本信息，未来可能会添加更详细的健康检查逻辑
4. 接口响应中的时间戳使用Unix时间戳格式

## 测试

可以使用提供的测试脚本进行接口测试：

```bash
cd test
python test_agents_api.py
```

确保在运行测试前启动主服务：

```bash
python main.py
```
