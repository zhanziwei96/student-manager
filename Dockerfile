# ClassHub Dockerfile - 生产环境
# 使用 Alpine 基础镜像 + 腾讯云镜像源

FROM python:3.11-alpine

WORKDIR /app

# 使用 Alpine 腾讯云镜像源
RUN sed -i 's/dl-cdn.alpinelinux.org/mirrors.cloud.tencent.com/g' /etc/apk/repositories

# 安装系统依赖（编译 Python 包所需）
RUN apk add --no-cache gcc musl-dev libffi-dev

# 使用腾讯云 PyPI 镜像
RUN pip config set global.index-url https://mirrors.cloud.tencent.com/pypi/simple

# 安装 Python 依赖
COPY backend/requirements.txt /tmp/requirements.txt
RUN pip install --no-cache-dir -r /tmp/requirements.txt

# 复制后端代码
COPY backend/ /app/

# 复制前端构建产物
COPY frontend-v3/dist /var/www/html

# 创建必要的目录
RUN mkdir -p /app/data /app/logs /var/www/html

# 环境变量
ENV PYTHONUNBUFFERED=1
ENV DATABASE_PATH=/app/data/class_system.db

# 暴露端口
EXPOSE 8000

# 健康检查（使用 Python 内置方式）
HEALTHCHECK --interval=30s --timeout=10s --start-period=10s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8000/health')" || exit 1

# 启动命令 - Gunicorn + Uvicorn worker，4 workers 匹配 4 核 CPU
CMD ["gunicorn", "main:app", "-k", "uvicorn.workers.UvicornWorker", "--bind", "0.0.0.0:8000", "--workers", "4", "--preload", "--access-logfile", "-", "--error-logfile", "-"]
