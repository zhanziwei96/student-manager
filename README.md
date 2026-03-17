# 📚 班级管理系统

一个现代化的班级管理系统，采用前后端分离架构，支持网页签到、班级管理、分数统计等功能。

## ✨ 功能特性

- **👥 学生管理**：添加、删除、导入学生信息，支持 Excel 批量导入
- **📝 网页签到**：学生输入学号和姓名即可完成签到，支持一机一签限制
- **📊 分数管理**：给学生增减分数，记录变更历史，查看排名
- **📈 数据可视化**：首页统计、排行榜、签到率实时展示
- **🔐 权限管理**：管理后台需要老师登录，支持修改密码
- **🎯 上课模式**：实时显示班级签到状态，老师可代签
- **🔍 学生查询**：学生可查询自己的分数、排名和变更记录
- **💾 数据安全**：SQLite 数据库存储，支持测试/生产环境分离

## 🏗️ 技术架构

### 前端
- **Vue 3** - Composition API
- **Element Plus** - UI 组件库
- **Vue Router** - 路由管理
- **Axios** - HTTP 请求
- **Vite** - 构建工具

### 后端
- **Flask** - Python Web 框架
- **SQLite** - 轻量级数据库
- **Gunicorn** - WSGI 服务器
- **Nginx** - 反向代理 + 静态资源服务

## 🚀 快速开始

### 开发环境

```bash
# 1. 安装后端依赖
pip install -r requirements.txt

# 2. 安装前端依赖
cd frontend
npm install

# 3. 启动开发服务器
# 方式一：使用 tmux（推荐）
./start_dev_tmux.sh

# 方式二：前台运行
./start_dev.sh

# 方式三：后台运行
./start_dev_simple.sh
```

访问 http://localhost:3000

### 生产部署

```bash
# 1. 构建前端
cd frontend
npm install
npm run build

# 2. 配置 nginx
sudo cp nginx-main-3000.conf /etc/nginx/sites-available/student-manage
# 修改配置文件中的路径，然后启用
sudo ln -s /etc/nginx/sites-available/student-manage /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl restart nginx

# 3. 启动后端
source ~/.nvm/nvm.sh  # 如果使用 nvm
pip install -r requirements.txt
gunicorn -w 4 -b 127.0.0.1:5000 app:app --daemon --pid /tmp/gunicorn.pid
```

## 🗄️ 测试环境与生产环境

系统支持两个独立的数据库环境：

| 环境 | 数据库文件 | 启动方式 |
|------|-----------|---------|
| 生产环境 | `backend/data/class_system.db` | 默认 |
| 测试环境 | `backend/data/test_class_system.db` | `export FLASK_ENV=testing` |

在管理后台右上角会显示当前环境标识。

## 📖 使用指南

### 默认账户
- 用户名：`admin`
- 密码：`admin123`
- **首次登录后请立即修改密码**

### 老师操作

1. **登录管理后台**：访问 `/admin`，使用 admin 账户登录
2. **导入学生**：支持 Excel (.xlsx/.xls) 文件，自动识别学号、姓名、班级列
3. **开始上课**：选择班级点击"开始上课"，学生即可签到
4. **分数管理**：点击学生分数进行调整，可填写变更原因
5. **代签功能**：老师可帮未带设备的学生代签到

### 学生操作

1. **签到**：访问首页或 `/checkin`，输入学号和姓名
2. **查询信息**：在首页"学生查询"区域输入学号姓名，查看分数和排名
3. **一机一签**：每台设备每天只能签到一次，刷新页面无法重复签到

### Excel 导入格式

支持列名自动识别，顺序不固定：

| 学号 | 姓名 | 班级 |
|------|------|------|
| 2024001 | 张三 | 一班 |
| 2024002 | 李四 | 一班 |

支持的关键词：学号/学生号/id/编号/studentid、姓名/名字/name、班级/class/classname

## 🔧 目录结构

```
student-manage/
├── app.py                 # Flask 后端入口
├── data_manager.py        # 数据管理模块
├── requirements.txt       # Python 依赖
├── nginx-main-3000.conf   # nginx 配置
├── README.md             # 本文件
├── Makefile              # 常用命令
├── backup-data.sh        # 备份脚本
├── start_dev*.sh         # 开发启动脚本
├── stop_dev.sh           # 停止脚本
├── backend/              # 备用后端目录
│   └── data/            # 数据库文件
├── frontend/             # Vue 3 前端
│   ├── dist/            # 构建产物
│   ├── src/
│   │   ├── api/         # API 请求
│   │   ├── views/       # 页面组件
│   │   │   ├── Home.vue      # 首页（统计+查询）
│   │   │   ├── Login.vue     # 登录页
│   │   │   ├── Admin.vue     # 管理后台
│   │   │   ├── Checkin.vue   # 签到页面
│   │   │   └── PublicHome.vue # 公共首页
│   │   └── router/      # 路由配置
│   └── package.json
├── backups/              # 数据备份目录
└── uploads/              # 文件上传目录
```

## 🔒 安全特性

1. **密码加密**：PBKDF2 算法 + 随机盐值
2. **Session 管理**：1 小时有效期，安全 Cookie
3. **一机一签**：localStorage + 后端双重验证
4. **姓名验证**：签到时验证学号姓名匹配
5. **环境隔离**：测试/生产数据库分离

## 🛠️ API 接口

### 用户相关
- `POST /api/login` - 登录
- `POST /api/logout` - 登出
- `GET /api/me` - 获取用户信息
- `POST /api/change-password` - 修改密码

### 学生管理
- `GET /api/students` - 获取所有学生
- `POST /api/students` - 添加学生
- `DELETE /api/students/:id` - 删除学生
- `POST /api/students/:id/score` - 更新分数
- `POST /api/students/import` - 批量导入

### 签到相关
- `POST /api/checkin` - 学生签到
- `POST /api/teacher-checkin` - 老师代签
- `GET /api/checkin/records` - 签到记录

### 上课状态
- `GET /api/class-session` - 获取状态
- `POST /api/class-session` - 设置班级
- `GET /api/class-session/students` - 学生列表

### 统计查询
- `GET /api/stats` - 首页统计数据
- `GET /api/score/logs` - 分数变更日志
- `POST /api/student/query` - 学生自助查询

## 💾 数据备份

数据库文件位于 `backend/data/class_system.db`，直接复制即可备份：

```bash
# 手动备份
cp backend/data/class_system.db backups/class_system_$(date +%Y%m%d).db

# 使用备份脚本
./backup-data.sh
```

## 📱 使用场景

- **课堂签到**：实时统计出勤情况
- **活动签到**：快速导入名单，现场签到
- **分数管理**：积分制教学，实时查看排名
- **学生自查**：学生自主查询成绩和记录

## 🔧 日常维护

```bash
# 查看后端状态
ps aux | grep gunicorn

# 查看 nginx 状态
sudo systemctl status nginx

# 重启后端
kill $(cat /tmp/gunicorn.pid)
gunicorn -w 4 -b 127.0.0.1:5000 app:app --daemon --pid /tmp/gunicorn.pid

# 更新部署（修改代码后）
cd frontend && npm run build
cd .. && sudo nginx -s reload
```

## 📄 许可

MIT License
