.PHONY: help install install-dev install-test install-docs clean test test-cov lint format check-deps sync-deps run build docs setup-auth create-admin test-auth test-api-keys

# 默认目标
help:
	@echo "小胰宝 - AI Gateway项目 - 可用命令:"
	@echo ""
	@echo "环境管理:"
	@echo "  install       安装生产依赖"
	@echo "  install-dev   安装开发依赖"
	@echo "  install-test  安装测试依赖"
	@echo "  install-docs  安装文档依赖"
	@echo "  sync-deps     同步依赖到虚拟环境"
	@echo "  clean         清理构建文件"
	@echo ""
	@echo "认证系统:"
	@echo "  setup-auth    设置认证系统环境"
	@echo "  create-admin  创建管理员用户"
	@echo "  test-auth     测试认证系统"
	@echo "  test-api-keys 测试API Key功能"
	@echo ""
	@echo "代码质量:"
	@echo "  lint          运行代码检查"
	@echo "  format        格式化代码"
	@echo "  check-deps    检查依赖"
	@echo ""
	@echo "测试:"
	@echo "  test          运行测试"
	@echo "  test-cov      运行测试并生成覆盖率报告"
	@echo ""
	@echo "开发:"
	@echo "  run           运行开发服务器"
	@echo "  run-prod      运行生产服务器"
	@echo "  build         构建项目"
	@echo "  docs          构建文档"
	@echo ""

# 安装生产依赖
install:
	uv pip install -e .

# 安装开发依赖
install-dev:
	uv pip install -e ".[dev]"

# 安装测试依赖
install-test:
	uv pip install -e ".[test]"

# 安装文档依赖
install-docs:
	uv pip install -e ".[docs]"

# 同步依赖到虚拟环境
sync-deps:
	uv sync

# 清理构建文件
clean:
	rm -rf build/
	rm -rf dist/
	rm -rf *.egg-info/
	rm -rf .pytest_cache/
	rm -rf .coverage
	rm -rf htmlcov/
	rm -rf .mypy_cache/
	find . -type d -name __pycache__ -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete

# 设置认证系统环境
setup-auth:
	@echo "🔐 设置认证系统环境..."
	@if [ ! -f .env ]; then \
		echo "📝 创建 .env 文件..."; \
		cp env.example .env; \
		echo "✅ .env 文件已创建，请根据需要编辑配置信息"; \
		echo "💡 JWT_SECRET_KEY 是可选的，系统会自动生成安全密钥"; \
		echo "💡 如需固定密钥，请取消注释并设置 JWT_SECRET_KEY"; \
	else \
		echo "✅ .env 文件已存在"; \
	fi
	@echo "📦 安装认证系统依赖..."
	uv sync
	@echo "🔄 更新依赖以解决兼容性问题..."
	uv add bcrypt>=4.0.0
	uv sync
	@echo "🔍 检查MongoDB服务..."
	@if command -v mongod >/dev/null 2>&1; then \
		echo "✅ MongoDB 已安装"; \
		echo "💡 启动MongoDB: brew services start mongodb-community (macOS)"; \
		echo "💡 启动MongoDB: sudo systemctl start mongod (Linux)"; \
	else \
		echo "❌ MongoDB 未安装"; \
		echo "💡 安装MongoDB: brew install mongodb-community (macOS)"; \
		echo "💡 安装MongoDB: sudo apt install mongodb (Ubuntu)"; \
	fi

# 创建管理员用户
create-admin:
	@echo "👑 创建管理员用户..."
	@if [ ! -f .env ]; then \
		echo "❌ 请先运行 'make setup-auth' 设置环境"; \
		exit 1; \
	fi
	uv run python scripts/create_admin.py

# 测试认证系统
test-auth:
	@echo "🧪 测试认证系统..."
	@if [ ! -f .env ]; then \
		echo "❌ 请先运行 'make setup-auth' 设置环境"; \
		exit 1; \
	fi
	@echo "🚀 启动服务进行测试..."
	@echo "💡 在另一个终端运行: make run"
	@echo "⏳ 等待服务启动后按任意键继续..."
	@read -n 1 -s
	uv run python test/test_auth_system.py

# 测试API Key功能
test-api-keys:
	@echo "🔑 测试API Key功能..."
	@if [ ! -f .env ]; then \
		echo "❌ 请先运行 'make setup-auth' 设置环境"; \
		exit 1; \
	fi
	@echo "🚀 启动服务进行测试..."
	@echo "💡 在另一个终端运行: make run"
	@echo "⏳ 等待服务启动后按任意键继续..."
	@read -n 1 -s
	uv run python test/test_api_keys.py

# 运行代码检查
lint:
	uv run flake8 agent/ api/ auth/ services/ database/ models/ test/
	uv run mypy agent/ api/ auth/ services/ database/ models/

# 格式化代码
format:
	uv run black agent/ api/ auth/ services/ database/ models/ test/
	uv run isort agent/ api/ auth/ services/ database/ models/ test/

# 检查依赖
check-deps:
	uv pip list --outdated

# 运行测试
test:
	uv run pytest test/ -v

# 运行测试并生成覆盖率报告
test-cov:
	uv run pytest test/ --cov=agent --cov=api --cov=auth --cov=services --cov=database --cov=models --cov-report=html --cov-report=term

# 运行开发服务器
run:
	uvicorn main:app --reload

# 运行生产服务器
run-prod:
	uv run uvicorn main:app --host 0.0.0.0 --port 8000

# 测试智能体管理API
test-agents:
	uv run python test/test_agents_api.py

# 构建项目
build:
	uv build

# 构建文档
docs:
	uv run mkdocs build

# 预提交检查
pre-commit:
	uv run pre-commit run --all-files

# 安装预提交钩子
install-hooks:
	uv run pre-commit install

# 更新依赖
update-deps:
	uv lock --upgrade
	uv sync

# 显示项目信息
info:
	@echo "项目名称: $(shell uv run python -c 'import tomllib; print(tomllib.load(open("pyproject.toml", "rb"))["project"]["name"])')"
	@echo "项目版本: $(shell uv run python -c 'import tomllib.load(open("pyproject.toml", "rb"))["project"]["version"])')"
	@echo "Python版本: $(shell uv run python --version)"
	@echo "uv版本: $(shell uv --version)"
	@echo "认证系统: 已集成 ✅"
	@echo "API Key系统: 已集成 ✅"
	@echo "数据库: MongoDB ✅"
