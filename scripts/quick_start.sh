#!/bin/bash

# 小胰宝智能助手平台 - 快速启动脚本
# 用于快速部署和启动认证系统

set -e

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 打印带颜色的消息
print_info() {
    echo -e "${BLUE}ℹ️  $1${NC}"
}

print_success() {
    echo -e "${GREEN}✅ $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

print_error() {
    echo -e "${RED}❌ $1${NC}"
}

print_header() {
    echo -e "${BLUE}"
    echo "=================================================="
    echo "🚀 小胰宝智能助手平台 - 快速启动"
    echo "=================================================="
    echo -e "${NC}"
}

# 检查命令是否存在
check_command() {
    if ! command -v $1 &> /dev/null; then
        print_error "$1 未安装，请先安装 $1"
        return 1
    fi
    return 0
}

# 检查Python版本
check_python_version() {
    print_info "检查Python版本..."
    if ! check_command python; then
        exit 1
    fi
    
    python_version=$(python --version 2>&1 | awk '{print $2}' | cut -d. -f1,2)
    required_version="3.12"
    
    if [ "$(printf '%s\n' "$required_version" "$python_version" | sort -V | head -n1)" != "$required_version" ]; then
        print_error "Python版本过低，需要 $required_version 或更高版本，当前版本: $python_version"
        exit 1
    fi
    
    print_success "Python版本检查通过: $python_version"
}

# 检查uv是否安装
check_uv() {
    print_info "检查uv包管理器..."
    if ! check_command uv; then
        print_warning "uv未安装，正在安装..."
        curl -LsSf https://astral.sh/uv/install.sh | sh
        source ~/.bashrc 2>/dev/null || source ~/.zshrc 2>/dev/null || true
    fi
    
    if check_command uv; then
        print_success "uv已安装: $(uv --version)"
    else
        print_error "uv安装失败"
        exit 1
    fi
}

# 检查MongoDB
check_mongodb() {
    print_info "检查MongoDB..."
    if ! check_command mongod; then
        print_warning "MongoDB未安装"
        echo "请选择安装方式："
        echo "1. 使用包管理器安装 (推荐)"
        echo "2. 使用Docker运行"
        echo "3. 跳过检查"
        read -p "请输入选择 (1-3): " choice
        
        case $choice in
            1)
                if [[ "$OSTYPE" == "darwin"* ]]; then
                    print_info "macOS系统，使用Homebrew安装MongoDB..."
                    brew install mongodb-community
                    brew services start mongodb-community
                elif [[ "$OSTYPE" == "linux-gnu"* ]]; then
                    print_info "Linux系统，使用apt安装MongoDB..."
                    sudo apt update
                    sudo apt install -y mongodb
                    sudo systemctl start mongod
                    sudo systemctl enable mongod
                else
                    print_error "不支持的操作系统，请手动安装MongoDB"
                    exit 1
                fi
                ;;
            2)
                print_info "使用Docker运行MongoDB..."
                if ! check_command docker; then
                    print_error "Docker未安装，请先安装Docker"
                    exit 1
                fi
                docker run -d --name mongodb -p 27017:27017 mongo:latest
                print_success "MongoDB容器已启动"
                ;;
            3)
                print_warning "跳过MongoDB检查，请确保MongoDB服务正在运行"
                ;;
            *)
                print_error "无效选择"
                exit 1
                ;;
        esac
    else
        print_success "MongoDB已安装"
        # 尝试启动MongoDB服务
        if [[ "$OSTYPE" == "darwin"* ]]; then
            brew services start mongodb-community 2>/dev/null || true
        elif [[ "$OSTYPE" == "linux-gnu"* ]]; then
            sudo systemctl start mongod 2>/dev/null || true
        fi
    fi
}

# 设置环境变量
setup_environment() {
    print_info "设置环境变量..."
    
    if [ ! -f .env ]; then
        if [ -f env.example ]; then
            cp env.example .env
            print_success ".env文件已创建"
            print_warning "请编辑.env文件，特别是JWT_SECRET_KEY和数据库配置"
        else
            print_error "env.example文件不存在"
            exit 1
        fi
    else
        print_info ".env文件已存在"
    fi
}

# 安装依赖
install_dependencies() {
    print_info "安装项目依赖..."
    uv sync
    print_success "依赖安装完成"
}

# 创建管理员用户
create_admin() {
    print_info "创建管理员用户..."
    if [ -f scripts/create_admin.py ]; then
        uv run python scripts/create_admin.py
        print_success "管理员用户创建完成"
    else
        print_warning "create_admin.py脚本不存在，跳过管理员用户创建"
    fi
}

# 启动服务
start_service() {
    print_info "启动服务..."
    print_success "服务启动完成！"
    echo ""
    echo "🌐 服务地址: http://localhost:8000"
    echo "📖 API文档: http://localhost:8000/docs"
    echo "🔐 认证API: http://localhost:8000/api/v1/auth/"
    echo "🔍 智能体管理: http://localhost:8000/api/v1/agents/"
    echo "💚 健康检查: http://localhost:8000/health"
    echo ""
    echo "按 Ctrl+C 停止服务"
    echo ""
    
    uv run uvicorn main:app --reload --host 0.0.0.0 --port 8000
}

# 主函数
main() {
    print_header
    
    # 检查系统环境
    check_python_version
    check_uv
    check_mongodb
    
    # 设置项目环境
    setup_environment
    install_dependencies
    
    # 创建管理员用户
    create_admin
    
    # 启动服务
    start_service
}

# 错误处理
trap 'print_error "脚本执行失败，请检查错误信息"; exit 1' ERR

# 运行主函数
main "$@"
