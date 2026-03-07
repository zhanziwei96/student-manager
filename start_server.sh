#!/bin/bash

# 班级管理系统启动脚本 (Linux/Mac)
# 用法: ./start_server.sh [production|test|testing]

# 获取脚本所在目录
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

# 显示帮助信息
show_help() {
    echo "========================================"
    echo "    班级管理系统 - Linux 启动脚本"
    echo "========================================"
    echo ""
    echo "用法:"
    echo "  ./start_server.sh           # 启动生产环境 (默认)"
    echo "  ./start_server.sh test      # 启动测试环境"
    echo "  ./start_server.sh production # 启动生产环境"
    echo "  ./start_server.sh help      # 显示帮助"
    echo ""
}

# 判断环境
ENV="${1:-production}"

case "$ENV" in
    test|testing)
        export FLASK_ENV="testing"
        echo "========================================"
        echo -e "    \033[33m班级管理系统 - 测试环境\033[0m"
        echo "========================================"
        ;;
    production|prod)
        export FLASK_ENV="production"
        echo "========================================"
        echo -e "    \033[32m班级管理系统 - 生产环境\033[0m"
        echo "========================================"
        ;;
    help|--help|-h)
        show_help
        exit 0
        ;;
    *)
        echo "未知环境: $ENV"
        echo "使用 'help' 查看用法"
        exit 1
        ;;
esac

echo ""

# 检查 Python
if command -v python3 &> /dev/null; then
    PYTHON_CMD="python3"
elif command -v python &> /dev/null; then
    PYTHON_CMD="python"
else
    echo "错误: 找不到 Python，请确保已安装 Python 3"
    exit 1
fi

echo "使用 Python: $PYTHON_CMD"

# 检查 pip
if ! $PYTHON_CMD -m pip --version &> /dev/null; then
    echo "错误: pip 未安装"
    exit 1
fi

# 安装依赖
echo "检查依赖..."
$PYTHON_CMD -m pip install -q flask openpyxl 2>/dev/null || {
    echo "正在安装依赖..."
    $PYTHON_CMD -m pip install flask openpyxl
}

# 启动服务
echo "启动服务..."
echo ""
$PYTHON_CMD app.py
