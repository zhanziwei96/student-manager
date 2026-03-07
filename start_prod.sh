#!/bin/bash
# 启动生产环境
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"
export FLASK_ENV="production"

echo "========================================"
echo -e "    \033[32m班级管理系统 - 生产环境\033[0m"
echo "========================================"
echo ""

# 检查 Python
if command -v python3 &> /dev/null; then
    PYTHON_CMD="python3"
elif command -v python &> /dev/null; then
    PYTHON_CMD="python"
else
    echo "错误: 找不到 Python"
    exit 1
fi

# 安装依赖
$PYTHON_CMD -m pip install -q flask openpyxl 2>/dev/null || true

# 启动
$PYTHON_CMD app.py
