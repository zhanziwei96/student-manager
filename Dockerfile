# ClassHub Dockerfile - 生产环境
# 支持 Nginx + FastAPI + SQLite

FROM python:3.11-slim

WORKDIR /app

# 安装系统依赖
RUN apt-get update && apt-get install -y --no-install-recommends \
    nginx \
    sqlite3 \
    curl \
    && rm -rf /var/lib/apt/lists/*

# 安装 Python 依赖
COPY backend/requirements.txt /tmp/requirements.txt
RUN pip install --no-cache-dir -r /tmp/requirements.txt

# 复制后端代码
COPY backend/ /app/backend/

# 复制前端构建产物（需要提前构建好）
COPY frontend-v3/dist /var/www/html

# 创建必要的目录（用于挂载卷）
RUN mkdir -p /app/backend/data /app/uploads /app/backups /app/backend/logs /var/log/nginx

# Nginx 配置
COPY docker/nginx.conf /etc/nginx/nginx.conf

# 启动脚本
COPY docker/start.sh /app/start.sh
RUN chmod +x /app/start.sh

# 备份脚本
COPY docker/backup.sh /app/backup.sh
RUN chmod +x /app/backup.sh

# 环境变量
ENV PYTHONUNBUFFERED=1
ENV DATABASE_PATH=/app/backend/data/student_manage.db
ENV BACKUP_DIR=/app/backups

# 暴露端口
EXPOSE 80

# 健康检查
HEALTHCHECK --interval=30s --timeout=10s --start-period=10s --retries=3 \
    CMD curl -f http://localhost/health || exit 1

# 启动
CMD ["/app/start.sh"]
