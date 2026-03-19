#!/bin/bash
# 班级管理系统生产环境部署脚本
# 适用于 Ubuntu/Debian 系统

set -e  # 遇到错误立即退出

echo "=========================================="
echo "班级管理系统生产环境部署"
echo "=========================================="

# 配置变量
PROJECT_DIR="/opt/student-manage"
NGINX_CONF="/etc/nginx/sites-available/student-manage"
SERVICE_NAME="student-manage"

# 检查是否以 root 权限运行
if [ "$EUID" -ne 0 ]; then 
    echo "请使用 sudo 运行此脚本"
    exit 1
fi

echo ""
echo "步骤 1/6: 安装系统依赖..."
apt-get update
apt-get install -y python3 python3-pip python3-venv nginx nodejs npm git

echo ""
echo "步骤 2/6: 克隆/更新项目代码..."
if [ -d "$PROJECT_DIR" ]; then
    echo "项目目录已存在，执行更新..."
    cd $PROJECT_DIR
    git pull
else
    echo "克隆项目代码..."
    git clone https://github.com/zhanziwei96/student-manager.git $PROJECT_DIR
    cd $PROJECT_DIR
fi

echo ""
echo "步骤 3/6: 构建前端项目..."
cd $PROJECT_DIR/frontend
npm install
npm run build

echo ""
echo "步骤 4/6: 配置 Python 环境..."
cd $PROJECT_DIR/backend
python3 -m venv venv
source venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
pip install gunicorn  # 生产环境 WSGI 服务器

echo ""
echo "步骤 5/6: 配置 Nginx..."
cp $PROJECT_DIR/nginx.conf $NGINX_CONF

# 修改 nginx 配置中的路径
sed -i "s|/path/to/student-manage|$PROJECT_DIR|g" $NGINX_CONF

# 启用站点
if [ ! -L "/etc/nginx/sites-enabled/student-manage" ]; then
    ln -s $NGINX_CONF /etc/nginx/sites-enabled/
fi

# 检查配置并重启
nginx -t
systemctl restart nginx
systemctl enable nginx

echo ""
echo "步骤 6/6: 创建系统服务..."
cat > /etc/systemd/system/$SERVICE_NAME.service << EOF
[Unit]
Description=Student Manage Flask App
After=network.target

[Service]
Type=simple
User=www-data
Group=www-data
WorkingDirectory=$PROJECT_DIR/backend
Environment="PATH=$PROJECT_DIR/backend/venv/bin"
Environment="FLASK_ENV=production"
ExecStart=$PROJECT_DIR/backend/venv/bin/gunicorn -w 4 -b 127.0.0.1:5000 app:app
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
EOF

# 重载系统服务
systemctl daemon-reload
systemctl enable $SERVICE_NAME
systemctl start $SERVICE_NAME

echo ""
echo "=========================================="
echo "部署完成！"
echo "=========================================="
echo ""
echo "服务状态:"
echo "- Nginx: $(systemctl is-active nginx)"
echo "- $SERVICE_NAME: $(systemctl is-active $SERVICE_NAME)"
echo ""
echo "访问地址:"
echo "- 首页: http://$(hostname -I | awk '{print $1}')"
echo ""
echo "常用命令:"
echo "- 查看服务状态: systemctl status $SERVICE_NAME"
echo "- 重启服务: systemctl restart $SERVICE_NAME"
echo "- 查看日志: journalctl -u $SERVICE_NAME -f"
echo "- 更新代码: cd $PROJECT_DIR && git pull && ./deploy.sh"
echo ""
echo "默认管理员账户:"
echo "- 用户名: admin"
echo "- 密码: admin123"
echo "=========================================="
