# ClassHub 班级管理系统

一个现代化的班级管理系统，采用前后端分离架构，支持网页签到、班级管理、分数统计等功能。

---

## 功能特性

- **学生管理**：添加、删除、导入学生信息，支持 Excel 批量导入
- **网页签到**：学生输入学号和姓名即可完成签到，支持一机一签限制
- **分数管理**：给学生增减分数，记录变更历史，查看排名
- **数据可视化**：首页统计、排行榜、签到率实时展示
- **权限管理**：RBAC 角色权限（admin/teacher/student），班级数据隔离
- **上课模式**：实时显示班级签到状态，老师可代签
- **学生查询**：学生可查询自己的分数、排名和变更记录

---

## 技术栈

| 前端 | 后端 |
|------|------|
| Vue 3.5 + TypeScript 5 | FastAPI + Python 3.11+ |
| Tailwind CSS v4 | SQLite |
| Pinia 3 | JWT (python-jose) |
| TanStack Query | Pydantic |
| Vite 6 | SQLModel |

---

## 快速开始

```bash
# 1. 克隆项目
git clone <repository-url>
cd student-manager

# 2. 启动后端（终端 1）
cd backend
conda create -n student-manage python=3.11 -y
conda activate student-manage
pip install -r requirements.txt
cp .env.example .env
python main.py

# 3. 启动前端（终端 2）
cd frontend-v3
pnpm install
pnpm dev
```

- 后端：`http://localhost:8000`
- 前端：`http://localhost:5173`

详细的部署说明、故障排查和开发流程，请参阅 [GETTING_STARTED.md](./GETTING_STARTED.md)。

---

## 默认账户

| 角色 | 用户名 | 密码 |
|------|--------|------|
| 管理员 | `admin` | `admin123` |
| 教师（示例） | `zhanziwei` | `zha123` |
| 学生 | 学号 | 学号 |

**首次登录后请立即修改密码。**

---

## 项目结构

```
student-manager/
├── backend/        # FastAPI 后端
├── frontend-v3/    # Vue 3 + TypeScript 前端
├── tests/          # 后端测试套件（467 个测试）
├── migrations/     # 数据库迁移脚本
└── docs/           # 项目文档
```

---

## 文档地图

| 文档 | 说明 |
|------|------|
| [GETTING_STARTED.md](./GETTING_STARTED.md) | 开发者快速开始指南（环境搭建、故障排查） |
| [docs/FAQ.md](./docs/FAQ.md) | 常见问题解答（25 个问题） |
| [docs/GLOSSARY.md](./docs/GLOSSARY.md) | 专业术语和缩写解释 |
| [docs/DOCUMENTATION_MAP.md](./docs/DOCUMENTATION_MAP.md) | 完整文档导航地图 |
| [CLAUDE.md](./CLAUDE.md) | AI 助手开发规范与约束 |
| [.agents/DEPLOYMENT.md](./.agents/DEPLOYMENT.md) | 部署与运维指南 |
| [backend/README.md](./backend/README.md) | 后端架构指南 |
| [frontend-v3/docs/ARCHITECTURE.md](./frontend-v3/docs/ARCHITECTURE.md) | 前端架构指南 |

---

**文档版本**: v3.1  
**最后更新**: 2026-04-13  
**适用版本**: v3.0.0+  
**状态**: 已同步代码
