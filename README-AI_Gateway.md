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