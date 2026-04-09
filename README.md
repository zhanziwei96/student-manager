# 📚 ClassHub 班级管理系统

一个现代化的班级管理系统，采用前后端分离架构，支持网页签到、班级管理、分数统计等功能。

---

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

---

## 🏗️ 技术架构

### 前端 (frontend-v3)

**技术栈**:
- **Vue 3.5** - Composition API + `<script setup>` 语法
- **TypeScript 5.0+** - 完整类型支持
- **Tailwind CSS v4** - 原子化 CSS 框架
- **Vue Router 4** - 路由管理
- **Pinia 3** - 状态管理
- **TanStack Query** - 服务端状态管理 + 缓存
- **Vite 6** - 构建工具
- **Lucide Vue** - 图标库
- **Vitest** - 单元测试（130 个测试全部通过）

**前端架构特点**:
- Feature-based 代码组织
- 全局 `useToast` 通知系统
- Teleport 实现 SSR 安全的弹窗/Toast
- 内存泄漏防护（已修复 P0 问题）

### 后端

- **FastAPI** - Python 异步 Web 框架
- **Python 3.11+** - 编程语言
- **SQLite** - 轻量级数据库
- **JWT** - 认证（python-jose）
- **Pydantic** - 数据验证
- **分层架构** - 经典的三层架构（API/CRUD/Models/Core）

### 架构模式
```
API → CRUD → Models ← Core
```

- **API**: 路由定义、请求/响应模型、依赖注入、权限控制
- **CRUD**: 数据库操作层
- **Models**: 数据模型、业务常量
- **Core**: 配置、数据库连接、安全工具、异常处理

---

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

---

## 🧪 测试

### 后端测试

```bash
# 运行全部测试
pytest tests/ -v

# 仅单元测试
pytest tests/unit -v

# 仅集成测试
pytest tests/integration -v

# 生成覆盖率报告
pytest tests/ --cov=backend/app --cov-report=html
```

### 前端测试

```bash
cd frontend-v3

# 运行所有测试（130 个测试）
pnpm test:run

# 交互式测试模式
pnpm test

# 生成覆盖率报告
npx vitest run --coverage
```

**测试统计**:
- 后端: 43 个测试文件，467 个测试用例 ✅
- 前端: 16 个测试文件，130 个测试用例 ✅
- **全部通过**

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

---

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

# 数据库配置（双下划线分隔嵌套属性）
DATABASE__PATH=./data/class_system.db
DATABASE__TIMEOUT=30

# 安全配置（双下划线分隔嵌套属性）
SECURITY__SECRET_KEY=your-secret-key-change-in-production  # JWT 密钥，生产环境必须修改
```

### 环境检查

部署完成后，验证服务状态：

```bash
# 检查后端
curl http://localhost:8000/api/v1/health

# 检查前端
curl http://localhost:5173

# 验证配置
python -c "from backend.app.core.config import get_settings; print(get_settings().app.env)"
```

---

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

---

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
│
├── frontend-v3/              # Vue3 + TypeScript 前端
│   ├── src/
│   │   ├── api/              # API 请求封装
│   │   ├── assets/           # 静态资源
│   │   ├── components/       # 组件 (ui/ + admin/ + teacher/)
│   │   ├── composables/      # 组合式函数
│   │   ├── features/         # Feature-based 功能模块
│   │   ├── layouts/          # 布局组件
│   │   ├── lib/              # 工具函数 (api/date/device/error/utils)
│   │   ├── router/           # 路由配置
│   │   ├── stores/           # Pinia 状态管理
│   │   ├── styles/           # 样式文件 (tokens/components)
│   │   ├── types/            # TypeScript 类型定义
│   │   └── views/            # 页面组件 (admin/teacher/student/)
│   ├── test/                 # Vitest 测试 (130 个测试)
│   ├── package.json
│   └── vitest.config.ts      # Vitest 配置
│
├── frontend/                 # 旧版前端 (不再维护)
├── tests/                    # 后端测试套件 (467 个测试)
│   ├── unit/                 # 单元测试
│   └── integration/          # 集成测试
├── migrations/               # 数据库迁移脚本
├── docker/                   # Docker 配置
├── Makefile                  # 常用命令
└── README.md
```

---

## 🔒 安全特性

1. **密码加密**: bcrypt 算法（自动处理盐值）
2. **JWT 认证**: Token 存储在 HttpOnly Cookie，24小时有效期
3. **请求限流**: 登录 5次/分钟，签到/分数 10次/分钟
4. **RBAC 权限**: 角色分级，班级数据隔离
5. **审计日志**: 记录所有敏感操作
6. **XSS 防护**: 输入过滤和输出转义
7. **CORS 配置**: 跨域安全策略

---

## 🛠️ API 接口

### 用户认证
- `POST /api/v1/login` - 登录（限流 5/分钟）
- `POST /api/v1/logout` - 登出
- `GET /api/v1/me` - 获取当前用户信息
- `POST /api/v1/change-password` - 修改密码

### 学生管理
- `GET /api/v1/students` - 获取学生列表（支持缓存）
- `POST /api/v1/students` - 添加学生
- `DELETE /api/v1/students/{id}` - 删除学生
- `PUT /api/v1/students/{id}/score` - 更新分数（限流 10/分钟）
- `PUT /api/v1/students/{id}/reset-password` - 重置学生密码
- `POST /api/v1/students/import` - Excel 批量导入

### 签到系统
- `POST /api/v1/checkin` - 学生签到（限流 10/分钟）
- `POST /api/v1/teacher-checkin` - 教师代签
- `GET /api/v1/checkin/records` - 签到记录查询

### 课堂会话
- `GET /api/v1/class-session` - 获取当前课堂状态
- `POST /api/v1/class-session` - 设置/结束课堂
- `GET /api/v1/class-session/students` - 课堂学生签到状态

### 统计数据
- `GET /api/v1/stats` - 首页统计数据
- `GET /api/v1/score/logs` - 分数变更日志
- `POST /api/v1/student/query` - 学生自助查询

### 系统管理
- `GET /api/v1/health` - 健康检查
- `GET /api/v1/audit/logs` - 审计日志（仅管理员）

完整 API 文档访问: http://localhost:8000/docs

---

## 💾 数据备份

### 手动备份

```bash
# 备份数据库
cp backend/app/data/class_system.db backup/class_system_$(date +%Y%m%d).db

# 或使用备份脚本
./backup/backup-data.sh
```

### 自动备份

系统支持自动备份配置，备份文件存储在 `backup/data/` 目录。

---

## 🐳 Docker 部署

```bash
# 构建镜像
docker-compose build

# 启动服务
docker-compose up -d

# 查看日志
docker-compose logs -f
```

---

## 📱 使用场景

- **课堂签到**：实时统计出勤情况
- **活动签到**：快速导入名单，现场签到
- **分数管理**：积分制教学，实时查看排名
- **学生自查**：学生自主查询成绩和记录

---

## 🔧 日常维护

```bash
# 查看后端状态
ps aux | grep "python main.py"

# 查看数据库大小
ls -lh backend/app/data/

# 查看日志
tail -f backend/logs/app.log

# 运行前端测试
cd frontend-v3 && pnpm test:run
```

---

## 📚 文档地图

### 入门指南
| 文档 | 说明 | 位置 |
|------|------|------|
| **项目简介** | 本文档 - 快速开始和功能介绍 | `README.md` |
| [快速开始指南](GETTING_STARTED.md) | 开发者环境搭建详细指南 | `GETTING_STARTED.md` |
| [常见问题 FAQ](docs/FAQ.md) | 25个常见问题解答 | `docs/FAQ.md` |
| [部署指南](.agents/DEPLOYMENT.md) | 环境搭建、服务启停 | `.agents/DEPLOYMENT.md` |
| [术语表](docs/GLOSSARY.md) | 专业术语和缩写解释 | `docs/GLOSSARY.md` |

### 开发规范
| 文档 | 说明 | 位置 |
|------|------|------|
| [CLAUDE.md](CLAUDE.md) | AI助手开发指南、关键约束 | `CLAUDE.md` |
| [贡献者指南](CONTRIBUTING.md) | 如何参与项目贡献 | `CONTRIBUTING.md` |
| [执行前检查清单](.agents/CHECKLIST.md) | 强制检查清单 | `.agents/CHECKLIST.md` |
| [约束清单](.agents/ERRORS.md) | 完整约束和纠错记录 | `.agents/ERRORS.md` |
| [配置管理](.agents/CONFIG_GUIDE.md) | 环境变量、多环境配置 | `.agents/CONFIG_GUIDE.md` |

### 架构设计
| 文档 | 说明 | 位置 |
|------|------|------|
| [后端架构](backend/README.md) | FastAPI + SQLModel架构 | `backend/README.md` |
| [前端架构](frontend-v3/docs/ARCHITECTURE.md) | Feature-based架构 | `frontend-v3/docs/ARCHITECTURE.md` |
| [设计体系](frontend-v3/DESIGN_SYSTEM.md) | 前端设计系统规范 | `frontend-v3/DESIGN_SYSTEM.md` |
| [优化方案](docs/OPTIMIZATION_PLAN.md) | 架构评分、优化路线图 | `docs/OPTIMIZATION_PLAN.md` |
| [架构图](docs/ARCHITECTURE_DIAGRAMS.md) | 系统架构图、ER图 | `docs/ARCHITECTURE_DIAGRAMS.md` |

### API 文档
| 文档 | 说明 | 位置 |
|------|------|------|
| [API使用示例](docs/API_EXAMPLES.md) | 详细的API调用示例 | `docs/API_EXAMPLES.md` |
| [API变更日志](docs/API_CHANGELOG.md) | 接口变更历史 | `docs/API_CHANGELOG.md` |
| [弃用说明](docs/DEPRECATIONS.md) | API迁移指南 | `docs/DEPRECATIONS.md` |
| Swagger UI | 在线API文档 | http://localhost:8000/docs |

### 测试文档
| 文档 | 说明 | 位置 |
|------|------|------|
| [测试指南](.agents/TEST_GUIDE.md) | 完整测试指南 | `.agents/TEST_GUIDE.md` |
| [后端测试](tests/README.md) | pytest测试说明 | `tests/README.md` |
| [E2E测试](tests/e2e/README.md) | Playwright测试 | `tests/e2e/README.md` |

### 运维与部署
| 文档 | 说明 | 位置 |
|------|------|------|
| [部署指南](.agents/DEPLOYMENT.md) | 快速部署指南 | `.agents/DEPLOYMENT.md` |
| [配置管理](.agents/CONFIG_GUIDE.md) | 环境变量配置 | `.agents/CONFIG_GUIDE.md` |
| [数据库迁移](migrations/README.md) | 迁移脚本说明 | `migrations/README.md` |

### 项目规划
| 文档 | 说明 | 位置 |
|------|------|------|
| [需求规格](docs/REQUIREMENTS.md) | 功能需求、规划 | `docs/REQUIREMENTS.md` |
| [更新日志](CHANGELOG.md) | 项目版本变更记录 | `CHANGELOG.md` |
| [优化方案](docs/OPTIMIZATION_PLAN.md) | 架构优化路线图 | `docs/OPTIMIZATION_PLAN.md` |

### 文档维护
| 文档 | 说明 | 位置 |
|------|------|------|
| [文档地图](docs/DOCUMENTATION_MAP.md) | 完整文档导航 | `docs/DOCUMENTATION_MAP.md` |
| [文档维护指南](docs/DOCUMENTATION_GUIDE.md) | 文档编写规范 | `docs/DOCUMENTATION_GUIDE.md` |

---

## 📄 许可

MIT License

---

**文档版本**: v3.0  
**最后更新**: 2026-04-03  
**适用版本**: v3.0.0+  
**状态**: ✅ 已同步代码
