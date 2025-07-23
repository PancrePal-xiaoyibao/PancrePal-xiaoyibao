# AI Gateway

将多个 Agent 后端整合成为一个接口，方便前端调用，API基本设计可参考[FastGPT | OpenAPI介绍](https://doc.tryfastgpt.ai/docs/development/openapi/intro/)

## 开发

先克隆仓库到本地

```bash
git clone https://github.com/liueic/PancrePal-xiaoyibao.git
cd PancrePal-xiaoyibao
```

使用 uv 作为包管理器，你需要先安装 uv

```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```

安装依赖：

```bash
uv pip install -r requirements.txt
```

如需导出依赖（方便他人部署）：

```bash
uv pip freeze > requirements.txt
```

### 运行项目

```bash
uvicorn main:app --reload
```

### 文档

本项目基于 FastAPI，启动后自动生成交互式 API 文档，访问地址：

- Swagger UI: [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs)
- Redoc: [http://127.0.0.1:8000/redoc](http://127.0.0.1:8000/redoc)

同时本项目提供 APIFox 文档：[AI Gateway | APIFox](https://ai-gateway.apifox.cn/)

## 目前已兼容的 Agent 平台有

- [x] FastGPT
- [x] Dify
- [ ] 腾讯混元
- [ ] 扣子

## 请求方法

前端需要按照统一的格式发起请求，有些字段对于某些 Agent 是必需的，如果发送的时候没有提供对应的字段，后端会返回错误，对于哪些字段是必须的，会在后续文档中提及，并且提供发送成功的参考案例

### Dify

**Chat**：

需要调用 `/api/v1/chat` 接口，在请求头中加入 `Agent: dify`，请求体内容为：

```json
{
  "app_id": "", // 可选
  "chat_id": "", // 可选
  "user": "lihua", // 必填
  "stream": false, // 可选，默认为false，即阻塞模式
  "query": "你好，我需要你的帮助", // 用户输入/提问内容
  "conversation_id": "31c9fdb6-6dcc-4216-b1b9-592eea874d0c", // 会话ID。需要基于之前的聊天记录继续对话，则必须传入之前消息的ID
  "files": [] // 文件列表，适用于传入文件结合文本理解并回答问题，仅当模型支持 Vision 能力时可用
}
```

### FastGPT

**Chat**：

需要调用 `/api/v1/chat` 接口，在请求头中加入 `Agent: fastgpt`，请求体内容为：

```json
{
  "app_id": "", // 可选，应用ID，优先使用参数，其次使用环境变量 FASTGPT_APP_ID
  "chat_id": "", // 可选，聊天ID。为空时不使用FastGPT上下文功能；为非空时使用chatId进行对话
  "query": "你好，我需要你的帮助", // 必填，用户输入/提问内容
  "user": "user123", // 可选，用户标识
  "uid": "uid123", // 可选，用户ID
  "stream": false, // 可选，默认为false，即阻塞模式
  "detail": false // 可选，默认为false。为true时返回模块详细信息（价格、tokens、引用等）
}
```

**响应格式**：

- **detail=false**（默认）：返回标准格式
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
        "content": "回复内容"
      },
      "finish_reason": "stop",
      "index": 0
    }
  ]
}
```

- **detail=true**：返回详细信息，包含各模块执行详情
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
  ]
}
```

