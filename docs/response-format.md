# 统一响应格式说明

## 概述

AI Gateway 现在采用基于 FastGPT 的统一响应格式，所有 Agent 都遵循相同的响应结构，确保前端调用的一致性。

## 响应格式

### 标准格式（detail=false 或不支持 detail 的 Agent）

```json
{
  "id": "conversation_id",
  "model": "model_name",
  "usage": {
    "prompt_tokens": 10,
    "completion_tokens": 20,
    "total_tokens": 30
  },
  "choices": [
    {
      "message": {
        "role": "assistant",
        "content": "AI 回复内容"
      },
      "finish_reason": "stop",
      "index": 0
    }
  ]
}
```

### 详细格式（detail=true，仅 FastGPT 支持）

```json
{
  "responseData": [
    {
      "moduleName": "Dataset Search",
      "price": 1.2,
      "model": "Embedding-2",
      "tokens": 6,
      "similarity": 0.61,
      "limit": 3
    },
    {
      "moduleName": "AI Chat",
      "price": 454.5,
      "model": "FastAI-4k",
      "tokens": 303,
      "question": "用户问题",
      "answer": "AI回答",
      "maxToken": 2050,
      "quoteList": [
        {
          "dataset_id": "xxx",
          "id": "xxx",
          "q": "问题",
          "a": "答案",
          "source": "来源"
        }
      ],
      "completeMessages": [
        {
          "obj": "System",
          "value": "系统消息"
        },
        {
          "obj": "Human",
          "value": "用户消息"
        },
        {
          "obj": "AI",
          "value": "AI回复"
        }
      ]
    }
  ],
  "newVariables": {
    "user": "test_user"
  }
}
```

## Agent 支持情况

| Agent | 标准格式 | 详细格式 | 说明 |
|-------|----------|----------|------|
| FastGPT | ✅ | ✅ | 完全支持两种格式 |
| Dify | ✅ | ❌ | 只支持标准格式 |

## 数据模型

### 核心模型

- `UnifiedChatResponse`: 统一响应模型，支持两种格式
- `StandardChatResponse`: 标准响应格式（别名：`ChatResponse`）
- `DetailedChatResponse`: 详细响应格式
- `ResponseDataModule`: 响应数据模块（detail=true 时使用）

### 辅助模型

- `Message`: 消息模型
- `Choice`: 选择项模型
- `Usage`: 使用情况模型
- `QuoteItem`: 引用项模型
- `CompleteMessage`: 完整消息模型

## 向后兼容性

- 原有的 `ChatResponse` 模型保持可用，作为 `StandardChatResponse` 的别名
- 所有现有的 API 调用和响应格式保持不变
- 新增的 `detail` 参数向后兼容，默认为 `false`

## 实现要点

1. **统一接口**: 所有 Agent 的 `format_response` 方法必须返回 `UnifiedChatResponse`
2. **灵活性**: `UnifiedChatResponse` 支持可选字段，Agent 可根据需要填充
3. **类型安全**: 使用 Pydantic 模型确保数据验证和类型安全
4. **JSON 序列化**: API 层自动处理模型到 JSON 的转换

## 示例代码

### Agent 实现

```python
def format_response(self, response_data: Dict[str, Any]) -> UnifiedChatResponse:
    if "responseData" in response_data:
        # 详细模式
        return UnifiedChatResponse(
            responseData=response_data.get("responseData", []),
            newVariables=response_data.get("newVariables", {})
        )
    else:
        # 标准模式
        return UnifiedChatResponse(
            id=response_data.get("id", ""),
            model=response_data.get("model", ""),
            usage=response_data.get("usage", {}),
            choices=response_data.get("choices", [])
        )
```

### API 使用

```python
# 标准格式请求
{
  "query": "你好",
  "user": "test_user",
  "detail": false  # 可选，默认 false
}

# 详细格式请求（仅 FastGPT）
{
  "query": "你好", 
  "user": "test_user",
  "detail": true
}
```
