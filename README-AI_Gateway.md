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

需要调用 `/v1/api/chat` 接口，在请求头中加入 `Agent: dify`，请求体内容为：

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

