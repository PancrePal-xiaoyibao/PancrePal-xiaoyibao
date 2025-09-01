.PHONY: help install install-dev install-test install-docs clean test test-cov lint format check-deps sync-deps run build docs

# 默认目标
help:
	@echo "小胰宝项目 - 可用命令:"
	@echo ""
	@echo "环境管理:"
	@echo "  install       安装生产依赖"
	@echo "  install-dev   安装开发依赖"
	@echo "  install-test  安装测试依赖"
	@echo "  install-docs  安装文档依赖"
	@echo "  sync-deps     同步依赖到虚拟环境"
	@echo "  clean         清理构建文件"
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

# 运行代码检查
lint:
	uv run flake8 agent/ api/ src/ test/
	uv run mypy agent/ api/ src/

# 格式化代码
format:
	uv run black agent/ api/ src/ test/
	uv run isort agent/ api/ src/ test/

# 检查依赖
check-deps:
	uv pip list --outdated

# 运行测试
test:
	uv run pytest test/ -v

# 运行测试并生成覆盖率报告
test-cov:
	uv run pytest test/ --cov=agent --cov=api --cov=src --cov-report=html --cov-report=term

# 运行开发服务器
run:
	uv run python main.py

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
	@echo "项目版本: $(shell uv run python -c 'import tomllib; print(tomllib.load(open("pyproject.toml", "rb"))["project"]["version"])')"
	@echo "Python版本: $(shell uv run python --version)"
	@echo "uv版本: $(shell uv --version)"
