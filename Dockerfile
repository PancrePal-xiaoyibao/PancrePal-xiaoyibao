# syntax=docker/dockerfile:1.7

ARG PYTHON_VERSION=3.12
FROM python:${PYTHON_VERSION}-slim AS base

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    PIP_DEFAULT_TIMEOUT=100

# 安装系统依赖
RUN apt-get update \
    && DEBIAN_FRONTEND=noninteractive apt-get install -y --no-install-recommends \
       build-essential \
       curl \
       ca-certificates \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# 仅复制依赖清单，加速缓存
COPY requirements.txt ./

# 安装依赖：移除本地可编辑安装行(-e .)，以兼容哈希校验
RUN python -m pip install --upgrade pip \
    && grep -vE '^-e[[:space:]]*\.$' requirements.txt > requirements.lock \
    && pip install -r requirements.lock

# 复制源码
COPY . .

# 创建非 root 用户
RUN useradd --create-home --shell /bin/bash appuser \
    && chown -R appuser:appuser /app
USER appuser

# 运行端口
EXPOSE 8000

# 默认启动命令（生产禁用 reload）
CMD ["python", "-m", "uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000", "--log-level", "info"]


