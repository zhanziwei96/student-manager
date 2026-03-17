# 班级管理系统 Dockerfile - 完整版
# 包含 Nginx + Flask + SSL 证书

FROM python:3.11-slim

WORKDIR /app

# 安装 Nginx 和必要工具
RUN apt-get update && apt-get install -y --no-install-recommends \
    nginx \
    openssl \
    curl \
    sqlite3 \
    && rm -rf /var/lib/apt/lists/*

# 安装 Python 依赖
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt gunicorn

# 复制后端代码
COPY backend/app.py backend/data_manager.py backend/config.py ./

# 复制前端构建产物
COPY frontend/dist /var/www/html

# 创建必要的目录
RUN mkdir -p backend/data uploads backups /etc/nginx/ssl /var/log/nginx

# 生成自签名 SSL 证书
RUN openssl req -x509 -nodes -days 365 -newkey rsa:2048 \
    -keyout /etc/nginx/ssl/server.key \
    -out /etc/nginx/ssl/server.crt \
    -subj "/C=CN/ST=Beijing/L=Beijing/O=StudentManage/CN=localhost"

# Nginx 配置
COPY nginx-docker.conf /etc/nginx/nginx.conf

# 启动脚本
COPY start-docker.sh /app/start.sh
RUN chmod +x /app/start.sh

# 备份脚本
COPY backup-data.sh /app/backup-data.sh
COPY docker/backup-cron.sh /app/docker/backup-cron.sh
RUN chmod +x /app/backup-data.sh /app/docker/backup-cron.sh

# 环境变量
ENV FLASK_ENV=production
ENV PYTHONUNBUFFERED=1
ENV SECRET_KEY=student-manage-fixed-secret-key-2024

# 暴露端口
EXPOSE 80 443

# 健康检查
HEALTHCHECK --interval=30s --timeout=10s --start-period=10s --retries=3 \
    CMD curl -f http://localhost/health || exit 1

# 启动
CMD ["/app/start.sh"]
