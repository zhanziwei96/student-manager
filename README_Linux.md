# 班级管理系统 - Linux 启动说明

## 启动方式（三选一）

### 方式一：Tmux 启动（推荐）

需要安装 tmux：
```bash
# Ubuntu/Debian
sudo apt-get install tmux

# CentOS/RHEL
sudo yum install tmux
```

启动：
```bash
./start_dev_tmux.sh
```

**优点：**
- 一个终端窗口同时显示前后端
- 支持多窗口切换查看日志
- 分离后会话后台运行
- 快捷键操作方便

**常用快捷键：**
- `Ctrl+b, 0` - 后端窗口
- `Ctrl+b, 1` - 前端窗口  
- `Ctrl+b, 2` - 日志窗口
- `Ctrl+b, d` - 分离会话（后台运行）
- `Ctrl+b, %` - 垂直分屏

**重新附加：**
```bash
tmux attach -t student-manage
```

**停止服务：**
```bash
tmux kill-session -t student-manage
```

---

### 方式二：前台启动（开发调试）

```bash
./start_dev.sh
```

**特点：**
- 前后端在同一个终端运行
- 输出直接显示在控制台
- 按 `Ctrl+C` 停止所有服务
- 自动检查并安装依赖

---

### 方式三：后台启动（生产测试）

```bash
# 启动
./start_dev_simple.sh

# 停止
./stop_dev.sh
```

**特点：**
- 后台运行，不占用终端
- 日志输出到文件
- 使用 PID 文件管理进程

**查看日志：**
```bash
# 后端日志
tail -f backend.log

# 前端日志
tail -f frontend.log
```

---

## 首次运行准备

### 1. 安装 Python 依赖
```bash
cd backend
pip3 install -r requirements.txt
cd ..
```

### 2. 安装 Node 依赖
```bash
cd frontend
npm install
cd ..
```

### 3. 设置脚本权限
```bash
chmod +x *.sh
```

---

## 访问地址

| 服务 | 地址 |
|:---|:---|
| 前端页面 | http://localhost:3000 |
| 后端 API | http://localhost:5000 |
| 管理后台 | http://localhost:3000/admin |
| 签到页面 | http://localhost:3000/checkin |

**默认账号：** admin / admin123

---

## 常见问题

### 1. 端口被占用

修改端口：
```bash
# 前端端口 - 修改 frontend/vite.config.js
server: {
  port: 3001,  # 修改这里
}

# 后端端口 - 修改 backend/app.py
app.run(port=5001)  # 修改这里
```

### 2. 权限不足
```bash
chmod +x *.sh
```

### 3. Python 命令不存在
```bash
# 创建软链接
sudo ln -s /usr/bin/python3 /usr/bin/python

# 或使用 python3 直接运行
python3 backend/app.py
```

### 4. npm 命令不存在
```bash
# 安装 Node.js
sudo apt-get install nodejs npm

# 或使用 nvm 安装
```

---

## 目录结构

```
student-manage/
├── backend/              # Flask 后端
├── frontend/             # Vue 3 前端
├── start_dev.sh          # 前台启动脚本
├── start_dev_simple.sh   # 后台启动脚本
├── start_dev_tmux.sh     # Tmux 启动脚本（推荐）
├── stop_dev.sh           # 停止脚本
└── README_Linux.md       # 本说明文件
```
