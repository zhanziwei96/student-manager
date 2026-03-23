# 📚 ClassHub 班级管理系统

一个现代化的班级管理系统，采用前后端分离架构，支持网页签到、班级管理、分数统计等功能。

## ✨ 功能特性

- **👥 学生管理**：添加、删除、导入学生信息，支持 Excel 批量导入
- **📝 网页签到**：学生输入学号和姓名即可完成签到，支持一机一签限制
- **📊 分数管理**：给学生增减分数，记录变更历史，查看排名
- **📈 数据可视化**：首页统计、排行榜、签到率实时展示
- **🔐 权限管理**：RBAC 角色权限（admin/teacher/student），班级数据隔离
- **🎯 上课模式**：实时显示班级签到状态，老师可代签
- **🔍 学生查询**：学生可查询自己的分数、排名和变更记录
- **💾 数据安全**：SQLite 数据库存储，支持数据备份和恢复
- **⚡ 性能优化**：内存限流 + 数据库索引

## 🏗️ 技术架构

### 前端 (frontend-v3)
- **Vue 3.5** - Composition API + TypeScript
- **Tailwind CSS v4** - 原子化 CSS 框架
- **Vue Router 4** - 路由管理
- **Pinia** - 状态管理
- **TanStack Query** - 服务端状态管理
- **Vite 6** - 构建工具
- **Lucide Vue** - 图标库

### 后端
- **FastAPI** - Python 异步 Web 框架
- **Python 3.11+** - 编程语言
- **SQLite** - 轻量级数据库
- **JWT** - 认证（python-jose）
- **Pydantic** - 数据验证
- **DDD 架构** - 领域驱动设计

### 架构模式
```
API → CRUD → Models ← Core
```

- **API**: 路由定义、请求/响应模型、依赖注入、权限控制
- **CRUD**: 数据库操作层
- **Models**: 数据模型、业务常量
- **Core**: 配置、数据库连接、安全工具、异常处理

## 📖 文档索引

| 文档 | 说明 | 位置 |
|------|------|------|
| [AI助手速查手册](.agents/AGENTS.md) | 常用命令、快速检查清单 | `.agents/AGENTS.md` |
| [快速部署指南](.agents/DEPLOYMENT.md) | 部署步骤、常见问题 | `.agents/DEPLOYMENT.md` |
| [常见错误速查](.agents/ERRORS.md) | 错误记录、避坑指南 | `.agents/ERRORS.md` |
| [配置管理说明](.agents/CONFIG_GUIDE.md) | 环境变量、配置优先级 | `.agents/CONFIG_GUIDE.md` |
| [数据库迁移](.agents/DB_MIGRATION.md) | 旧数据库迁移步骤 | `.agents/DB_MIGRATION.md` |
| [测试指南](.agents/TEST_GUIDE.md) | 测试运行、冒烟测试 | `.agents/TEST_GUIDE.md` |
| [测试说明](tests/README.md) | 详细测试步骤、系统测试 | `tests/README.md` |
| [迁移指南](migrations/README.md) | 完整迁移文档 | `migrations/README.md` |

## 🚀 快速开始

### 环境要求
| 软件 | 版本要求 |
|------|----------|
| Python | 3.11+ |
| Node.js | 20+ |
| pnpm | 8+ |

### 1. 克隆项目

```bash
git clone <repository-url>
cd student-manager
```

### 2. 后端部署

```bash
# 创建 conda 环境
conda create -n student-manage python=3.11 -y
conda activate student-manage

# 安装依赖
cd backend
pip install -r requirements.txt

# 启动后端服务
python main.py
```

后端服务将运行在 http://localhost:8000

### 3. 前端部署

```bash
cd frontend-v3

# 安装依赖
pnpm install

# 启动开发服务器
pnpm dev
```

前端服务将运行在 http://localhost:5173

### 4. 一键启动（推荐）

```bash
# 在项目根目录
make dev

# 停止所有服务
make stop

# 查看日志
make logs
```

## 🗄️ 环境配置

### 配置文件

复制环境变量示例文件：

```bash
cp backend/.env.example backend/.env
```

编辑 `.env` 文件修改配置：

```bash
# 应用配置
ENV=development
DEBUG=true
HOST=0.0.0.0
PORT=8000

# 数据库配置
DB_PATH=./data/student_manage.db
DB_TIMEOUT=30

# 安全配置
SECURITY_SECRET_KEY=your-secret-key-change-in-production  # JWT 密钥
```

### 环境检查

部署完成后，验证服务状态：

```bash
# 检查后端
curl http://localhost:8000/health

# 检查前端
curl http://localhost:5173

# 验证配置
python -c "from app.core.config import get_settings; print(get_settings().app.env)"
```

## 📖 使用指南

### 默认账户
- **管理员**: `admin` / `admin123`
- **教师示例**: `zhanziwei` / `zha123` (账号为姓名拼音首字母，密码为账号+123)
- **学生**: 学号作为账号，默认密码为学号

**首次登录后请立即修改密码**

### 权限说明

| 角色 | 权限范围 |
|------|----------|
| admin | 全校数据管理、用户管理、系统配置 |
| teacher | 绑定班级管理、学生签到管理 |
| student | 仅签到和查询自己信息 |

### 老师操作

1. **登录管理后台**：访问 `/admin`，使用 admin 账户登录
2. **导入学生**：支持 Excel (.xlsx/.xls) 文件，自动识别学号、姓名、班级列
3. **开始上课**：选择班级点击"开始上课"，学生即可签到
4. **分数管理**：点击学生分数进行调整，可填写变更原因
5. **代签功能**：老师可帮未带设备的学生代签到

### 学生操作

1. **签到**：访问首页，输入学号和姓名完成签到
2. **查询信息**：在首页"学生查询"区域输入学号姓名，查看分数和排名
3. **一机一签**：每台设备每天只能签到一次

### Excel 导入格式

支持列名自动识别，顺序不固定：

| 学号 | 姓名 | 班级 |
|------|------|------|
| 2024001 | 张三 | 软件1班 |
| 2024002 | 李四 | 软件1班 |

支持的关键词：学号/学生号/id/编号/studentid、姓名/名字/name、班级/class/classname

## 🔧 目录结构

```
student-manager/
├── backend/                  # FastAPI 后端
│   ├── app/
│   │   ├── api/              # API 层 (路由、依赖注入)
│   │   ├── core/             # 核心层 (配置、数据库、安全)
│   │   ├── crud/             # 数据操作层
│   │   └── models/           # 数据模型
│   ├── data/                 # SQLite 数据库
│   ├── main.py               # 后端入口
│   └── requirements.txt      # Python 依赖
├── frontend-v3/              # Vue3 + TypeScript 前端
│   ├── src/
│   │   ├── api/              # API 请求
│   │   ├── components/ui/    # UI 组件库
│   │   ├── composables/      # 组合式函数
│   │   ├── views/            # 页面组件
│   │   ├── stores/           # Pinia 状态管理
│   │   ├── router/           # 路由配置
│   │   └── styles/           # 样式文件
│   ├── package.json
│   └── vite.config.ts
├── frontend/                 # 旧版前端 (不再维护)
├── tests/                    # 测试套件
│   ├── unit/                 # 单元测试
│   └── integration/          # 集成测试
├── migrations/               # 数据库迁移脚本
├── docker/                   # Docker 配置
├── Makefile                  # 常用命令
└── README.md
```

## 🔒 安全特性

1. **密码加密**: bcrypt 算法（自动处理盐值）
2. **JWT 认证**: Token 存储在 HttpOnly Cookie，24小时有效期
3. **请求限流**: 登录 5次/分钟，签到/分数 10次/分钟
4. **RBAC 权限**: 角色分级，班级数据隔离
5. **审计日志**: 记录所有敏感操作
6. **XSS 防护**: 输入过滤和输出转义
7. **CORS 配置**: 跨域安全策略

## 🛠️ API 接口

### 用户认证
- `POST /api/login` - 登录（限流 5/分钟）
- `POST /api/logout` - 登出
- `GET /api/me` - 获取当前用户信息
- `POST /api/change-password` - 修改密码

### 学生管理
- `GET /api/students` - 获取学生列表（支持缓存）
- `POST /api/students` - 添加学生
- `DELETE /api/students/{id}` - 删除学生
- `PUT /api/students/{id}/score` - 更新分数（限流 10/分钟）
- `PUT /api/students/{id}/reset-password` - 重置学生密码
- `POST /api/students/import` - Excel 批量导入

### 签到系统
- `POST /api/checkin` - 学生签到（限流 10/分钟）
- `POST /api/teacher-checkin` - 教师代签
- `GET /api/checkin/records` - 签到记录查询

### 课堂会话
- `GET /api/class-session` - 获取当前课堂状态
- `POST /api/class-session` - 设置/结束课堂
- `GET /api/class-session/students` - 课堂学生签到状态

### 统计数据
- `GET /api/stats` - 首页统计数据
- `GET /api/score/logs` - 分数变更日志
- `POST /api/student/query` - 学生自助查询

### 系统管理
- `GET /health` - 健康检查
- `GET /api/audit/logs` - 审计日志（仅管理员）

完整 API 文档访问: http://localhost:8000/docs

## 🧪 测试

### 运行冒烟测试

```bash
# 安装测试依赖
pip install -r tests/requirements-test.txt

# 运行所有冒烟测试
python -m pytest tests/smoke/ -v

# 只运行后端测试
python -m pytest tests/smoke/ -v -m backend

# 只运行前端测试
python -m pytest tests/smoke/ -v -m frontend
```

### 测试数据管理

```bash
# 初始化测试数据
python tests/test_data_manager.py setup

# 清理测试数据
python tests/test_data_manager.py cleanup

# 重置测试数据
python tests/test_data_manager.py reset
```

## 💾 数据备份

### 手动备份

```bash
# 备份数据库
cp data/student_manage.db backups/student_manage_$(date +%Y%m%d).db

# 或使用备份脚本
./backup/backup-data.sh
```

### 自动备份

系统支持自动备份配置，备份文件存储在 `backup/data/` 目录。

## 🐳 Docker 部署

```bash
# 构建镜像
docker-compose build

# 启动服务
docker-compose up -d

# 查看日志
docker-compose logs -f
```

## 📱 使用场景

- **课堂签到**：实时统计出勤情况
- **活动签到**：快速导入名单，现场签到
- **分数管理**：积分制教学，实时查看排名
- **学生自查**：学生自主查询成绩和记录

## 🔧 日常维护

```bash
# 查看后端状态
ps aux | grep "python main.py"

# 查看数据库大小
ls -lh data/

# 查看日志
tail -f backend/logs/app.log
```

## 📚 相关文档

| 文档 | 说明 |
|------|------|
| [AGENTS.md](./AGENTS.md) | AI 助手操作指南 |
| [DEPLOYMENT.md](./DEPLOYMENT.md) | 详细部署指南 |
| [TEST_PLAN.md](./TEST_PLAN.md) | 测试方案 |
| [SECURITY_SOLUTION.md](./SECURITY_SOLUTION.md) | 安全解决方案 |
| [OPTIMIZATION_STATUS.md](./OPTIMIZATION_STATUS.md) | 优化进度追踪 |

## 📄 许可

MIT License

---

**版本**: v3.0  
**最后更新**: 2026-03-23 (Frontend-v3 更新 - Tailwind v4 + TypeScript)
