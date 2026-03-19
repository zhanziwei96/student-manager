#!/bin/bash
# 生成随机的 SECRET_KEY

echo "=========================================="
echo "  生成 Flask SECRET_KEY"
echo "=========================================="
echo ""

# 使用 openssl 生成随机密钥
SECRET_KEY=$(openssl rand -hex 32)

echo "生成的密钥:"
echo "$SECRET_KEY"
echo ""
echo "=========================================="
echo "使用方式:"
echo "=========================================="
echo ""
echo "1. 临时设置（当前终端有效）:"
echo "   export SECRET_KEY=$SECRET_KEY"
echo ""
echo "2. 永久设置（添加到 ~/.bashrc）:"
echo "   echo 'export SECRET_KEY=$SECRET_KEY' >> ~/.bashrc"
echo "   source ~/.bashrc"
echo ""
echo "3. 启动脚本中使用（推荐用于生产环境）:"
echo "   在 start_dev.sh 或 deploy.sh 中添加:"
echo "   export SECRET_KEY=$SECRET_KEY"
echo ""
echo "=========================================="
