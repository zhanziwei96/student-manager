# 班级管理系统生产环境部署指南

## 系统要求

- Ubuntu 20.04 LTS 或更高版本
- 至少 1GB RAM
- 至少 10GB 磁盘空间

## 快速部署（一键脚本）

```bash
# 1. 克隆代码
git clone https://github.com/zhanziwei96/student-manager.git
cd student-manager

# 2. 运行部署脚本
sudo bash deploy.sh
```

## 手动部署步骤

### 1. 安装系统依赖

```bash
sudo apt-get update
sudo apt-get install -y python3 python3-pip python3-venv nginx nodejs npm git
```

### 2. 构建前端项目

```bash
cd frontend
npm install
npm run build
```

构建完成后，前端文件位于 `frontend/dist/` 目录。

### 3. 配置后端环境

```bash
cd backend
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
pip install gunicorn
```

### 4. 配置 Nginx

复制配置文件：
```bash
sudo cp nginx.conf /etc/nginx/sites-available/student-manage
```

编辑配置文件，修改路径为你的实际路径：
```bash
sudo nano /etc/nginx/sites-available/student-manage
```

启用站点：
```bash
sudo ln -s /etc/nginx/sites-available/student-manage /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl restart nginx
```

### 5. 启动后端服务

开发模式测试：
```bash
cd backend
source venv/bin/activate
export FLASK_ENV=production
python app.py
```

生产模式（使用 Gunicorn）：
```bash
cd backend
source venv/bin/activate
gunicorn -w 4 -b 127.0.0.1:5000 app:app
```

### 6. 配置系统服务（推荐）

创建服务文件：
```bash
sudo nano /etc/systemd/system/student-manage.service
```

添加以下内容：
```ini
[Unit]
Description=Student Manage Flask App
After=network.target

[Service]
Type=simple
User=www-data
Group=www-data
WorkingDirectory=/opt/student-manage/backend
Environment="PATH=/opt/student-manage/backend/venv/bin"
Environment="FLASK_ENV=production"
ExecStart=/opt/student-manage/backend/venv/bin/gunicorn -w 4 -b 127.0.0.1:5000 app:app
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

启动服务：
```bash
sudo systemctl daemon-reload
sudo systemctl enable student-manage
sudo systemctl start student-manage
```

## 访问系统

- 首页: http://你的服务器IP
- 管理后台: http://你的服务器IP/admin

默认管理员账户：
- 用户名: `admin`
- 密码: `admin123`

## 日常维护

### 查看服务状态
```bash
sudo systemctl status student-manage
sudo systemctl status nginx
```

### 查看日志
```bash
# Flask 应用日志
sudo journalctl -u student-manage -f

# Nginx 访问日志
sudo tail -f /var/log/nginx/student-manage-access.log

# Nginx 错误日志
sudo tail -f /var/log/nginx/student-manage-error.log
```

### 更新代码
```bash
cd /opt/student-manage
git pull

# 重新构建前端
cd frontend
npm install
npm run build

# 重启服务
sudo systemctl restart student-manage
sudo systemctl restart nginx
```

### 修改管理员密码
登录管理后台后，在右上角用户菜单中选择"修改密码"。

## HTTPS 配置（推荐）

使用 Let's Encrypt 免费证书：

```bash
sudo apt-get install certbot python3-certbot-nginx
sudo certbot --nginx -d your-domain.com
```

## 性能优化

### 1. Gunicorn 配置优化

对于更高并发，可以调整 workers 数量：
```bash
# workers = 2 * CPU核心数 + 1
gunicorn -w 8 -b 127.0.0.1:5000 --worker-class gevent app:app
```

### 2. Nginx 缓存配置

已在 nginx.conf 中启用静态资源缓存（30天）。

### 3. 数据库优化

SQLite 适合中小型应用，如需更高性能可迁移到 MySQL/PostgreSQL。

## 故障排查

### 1. 前端显示 404

检查 Nginx 配置中的路径是否正确：
```bash
nginx -t
```

### 2. API 请求失败

检查后端服务是否运行：
```bash
curl http://127.0.0.1:5000/api/stats
```

### 3. 权限问题

确保文件权限正确：
```bash
sudo chown -R www-data:www-data /opt/student-manage
```

## 安全建议

1. **修改默认密码**: 首次登录后立即修改 admin 密码
2. **启用 HTTPS**: 生产环境必须启用 HTTPS
3. **防火墙配置**: 只开放 80/443 端口
4. **定期备份**: 备份 `data/class_system.db` 数据库文件
5. **更新依赖**: 定期更新系统和 Python 依赖

## 技术栈

- **前端**: Vue 3 + Element Plus + Vite
- **后端**: Flask + SQLite
- **服务器**: Nginx + Gunicorn
- **部署**: Systemd + Bash
