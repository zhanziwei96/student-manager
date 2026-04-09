# ClassHub 文档地图

---

**文档版本**: v1.0  
**最后更新**: 2026-04-05  
**适用版本**: v3.0.0+  
**状态**: ✅ 已同步代码

---

## 文档结构总览

```
student-manager/
├── README.md                          # 项目主文档 - 快速开始入口
├── CLAUDE.md                          # AI助手开发指南
├── CHANGELOG.md                       # 项目更新日志
├── CONTRIBUTING.md                    # 贡献者指南
├── GETTING_STARTED.md                 # 开发者快速开始指南
│
├── docs/                              # 项目文档
│   ├── DOCUMENTATION_MAP.md           # 本文档 - 文档导航
│   ├── ARCHITECTURE_DIAGRAMS.md       # 架构图和ER图
│   ├── API_CHANGELOG.md               # API变更日志
│   ├── API_EXAMPLES.md                # API使用示例
│   ├── DEPRECATIONS.md                # 弃用说明
│   ├── DOCUMENTATION_GUIDE.md         # 文档维护指南
│   ├── FAQ.md                         # 常见问题解答
│   ├── OPTIMIZATION_PLAN.md           # 项目优化方案
│   ├── REQUIREMENTS.md                # 需求规格说明书
│   └── GLOSSARY.md                    # 术语表
│
├── .agents/                           # 开发规范文档
│   ├── CHECKLIST.md                   # 执行前检查清单
│   ├── CONFIG_GUIDE.md                # 配置管理指南
│   ├── DEPLOYMENT.md                  # 快速部署指南
│   ├── ERRORS.md                      # 约束清单和纠错记录
│   └── TEST_GUIDE.md                  # 完整测试指南
│
├── backend/                           # 后端代码
│   └── README.md                      # 后端架构指南
│
├── frontend-v3/                       # 前端代码
│   ├── DESIGN_SYSTEM.md               # 前端设计系统
│   └── docs/
│       └── ARCHITECTURE.md            # 前端架构指南
│
├── tests/                             # 测试代码
│   ├── README.md                      # 后端测试说明
│   └── e2e/
│       └── README.md                  # E2E测试说明
│
└── migrations/                        # 数据库迁移
    └── README.md                      # 数据库迁移指南
```

---

## 按角色导航

### 新开发者

首次接触项目，按以下顺序阅读：

1. **[README.md](../README.md)** - 了解项目概况和快速开始
2. **[GETTING_STARTED.md](./GETTING_STARTED.md)** - 详细的开发环境搭建
3. **[docs/FAQ.md](./FAQ.md)** - 常见问题解答
4. **[.agents/DEPLOYMENT.md](../.agents/DEPLOYMENT.md)** - 部署指南

### 前端开发者

1. **[frontend-v3/DESIGN_SYSTEM.md](../frontend-v3/DESIGN_SYSTEM.md)** - 设计系统规范
2. **[frontend-v3/docs/ARCHITECTURE.md](../frontend-v3/docs/ARCHITECTURE.md)** - 前端架构指南
3. **[CLAUDE.md](../CLAUDE.md)** - 前端开发约束
4. **[.agents/TEST_GUIDE.md](../.agents/TEST_GUIDE.md)** - 前端测试指南

### 后端开发者

1. **[backend/README.md](../backend/README.md)** - 后端架构指南
2. **[CLAUDE.md](../CLAUDE.md)** - 后端开发约束
3. **[.agents/CONFIG_GUIDE.md](../.agents/CONFIG_GUIDE.md)** - 配置管理
4. **[tests/README.md](../tests/README.md)** - 后端测试说明

### 运维/部署人员

1. **[.agents/DEPLOYMENT.md](../.agents/DEPLOYMENT.md)** - 部署指南
2. **[.agents/CONFIG_GUIDE.md](../.agents/CONFIG_GUIDE.md)** - 配置管理
3. **[migrations/README.md](../migrations/README.md)** - 数据库迁移
4. **[docs/FAQ.md](./FAQ.md)** - 运维常见问题

### 项目经理/产品经理

1. **[README.md](../README.md)** - 项目概况
2. **[docs/REQUIREMENTS.md](./REQUIREMENTS.md)** - 需求规格
3. **[docs/ARCHITECTURE_DIAGRAMS.md](./ARCHITECTURE_DIAGRAMS.md)** - 架构图
4. **[docs/OPTIMIZATION_PLAN.md](./OPTIMIZATION_PLAN.md)** - 优化方案

### 贡献者

1. **[CONTRIBUTING.md](../CONTRIBUTING.md)** - 贡献者指南
2. **[CLAUDE.md](../CLAUDE.md)** - 开发规范
3. **[.agents/CHECKLIST.md](../.agents/CHECKLIST.md)** - 执行前检查清单
4. **[docs/DOCUMENTATION_GUIDE.md](./DOCUMENTATION_GUIDE.md)** - 文档维护规范

---

## 按主题导航

### 入门与快速开始

| 文档 | 说明 | 必读指数 |
|------|------|----------|
| [README.md](../README.md) | 项目主文档，快速开始 | ⭐⭐⭐⭐⭐ |
| [GETTING_STARTED.md](./GETTING_STARTED.md) | 开发者快速开始指南 | ⭐⭐⭐⭐⭐ |
| [.agents/DEPLOYMENT.md](../.agents/DEPLOYMENT.md) | 部署指南 | ⭐⭐⭐⭐ |
| [docs/FAQ.md](./FAQ.md) | 常见问题解答 | ⭐⭐⭐⭐ |

### 架构设计

| 文档 | 说明 | 必读指数 |
|------|------|----------|
| [docs/ARCHITECTURE_DIAGRAMS.md](./ARCHITECTURE_DIAGRAMS.md) | 系统架构图、ER图 | ⭐⭐⭐⭐⭐ |
| [backend/README.md](../backend/README.md) | 后端架构指南 | ⭐⭐⭐⭐⭐ |
| [frontend-v3/docs/ARCHITECTURE.md](../frontend-v3/docs/ARCHITECTURE.md) | 前端架构指南 | ⭐⭐⭐⭐⭐ |
| [frontend-v3/DESIGN_SYSTEM.md](../frontend-v3/DESIGN_SYSTEM.md) | 前端设计系统 | ⭐⭐⭐⭐ |

### 开发规范

| 文档 | 说明 | 必读指数 |
|------|------|----------|
| [CLAUDE.md](../CLAUDE.md) | AI助手开发指南、关键约束 | ⭐⭐⭐⭐⭐ |
| [.agents/ERRORS.md](../.agents/ERRORS.md) | 约束清单和纠错记录 | ⭐⭐⭐⭐⭐ |
| [.agents/CHECKLIST.md](../.agents/CHECKLIST.md) | 执行前检查清单 | ⭐⭐⭐⭐⭐ |
| [.agents/CONFIG_GUIDE.md](../.agents/CONFIG_GUIDE.md) | 配置管理指南 | ⭐⭐⭐⭐ |

### API与接口

| 文档 | 说明 | 必读指数 |
|------|------|----------|
| [docs/API_CHANGELOG.md](./API_CHANGELOG.md) | API变更日志 | ⭐⭐⭐⭐ |
| [docs/API_EXAMPLES.md](./API_EXAMPLES.md) | API使用示例 | ⭐⭐⭐⭐ |
| [docs/DEPRECATIONS.md](./DEPRECATIONS.md) | 弃用说明 | ⭐⭐⭐ |
| [backend/README.md](../backend/README.md) | API设计规范 | ⭐⭐⭐⭐ |

### 测试

| 文档 | 说明 | 必读指数 |
|------|------|----------|
| [.agents/TEST_GUIDE.md](../.agents/TEST_GUIDE.md) | 完整测试指南 | ⭐⭐⭐⭐ |
| [tests/README.md](../tests/README.md) | 后端测试说明 | ⭐⭐⭐⭐ |
| [frontend-v3/test/README.md](../frontend-v3/test/README.md) | 前端测试说明 | ⭐⭐⭐ |

### 运维与部署

| 文档 | 说明 | 必读指数 |
|------|------|----------|
| [.agents/DEPLOYMENT.md](../.agents/DEPLOYMENT.md) | 快速部署指南 | ⭐⭐⭐⭐⭐ |
| [.agents/CONFIG_GUIDE.md](../.agents/CONFIG_GUIDE.md) | 配置管理 | ⭐⭐⭐⭐ |
| [migrations/README.md](../migrations/README.md) | 数据库迁移指南 | ⭐⭐⭐⭐ |

### 项目规划

| 文档 | 说明 | 必读指数 |
|------|------|----------|
| [docs/REQUIREMENTS.md](./REQUIREMENTS.md) | 需求规格说明书 | ⭐⭐⭐⭐ |
| [docs/OPTIMIZATION_PLAN.md](./OPTIMIZATION_PLAN.md) | 项目优化方案 | ⭐⭐⭐ |
| [CHANGELOG.md](../CHANGELOG.md) | 项目更新日志 | ⭐⭐⭐ |

---

## 文档状态

### 已完善文档 ✅

| 文档 | 最后更新 | 状态 |
|------|----------|------|
| README.md | 2026-04-03 | ✅ 已同步代码 |
| CLAUDE.md | 2026-04-03 | ✅ 已同步代码 |
| backend/README.md | 2026-04-03 | ✅ 已同步代码 |
| frontend-v3/DESIGN_SYSTEM.md | 2026-04-03 | ✅ 已同步代码 |
| frontend-v3/docs/ARCHITECTURE.md | 2026-04-03 | ✅ 已同步代码 |
| docs/FAQ.md | 2026-04-03 | ✅ 已同步代码 |
| docs/API_CHANGELOG.md | 2026-04-03 | ✅ 已同步代码 |
| docs/ARCHITECTURE_DIAGRAMS.md | 2026-04-03 | ✅ 已同步代码 |
| docs/DEPRECATIONS.md | 2026-04-03 | ✅ 已同步代码 |
| docs/DOCUMENTATION_GUIDE.md | 2026-04-03 | ✅ 已同步代码 |
| docs/OPTIMIZATION_PLAN.md | 2026-04-03 | ✅ 已同步代码 |
| docs/REQUIREMENTS.md | 2026-04-03 | ✅ 已同步代码 |
| .agents/CHECKLIST.md | 2026-04-03 | ✅ 已同步代码 |
| .agents/CONFIG_GUIDE.md | 2026-04-03 | ✅ 已同步代码 |
| .agents/DEPLOYMENT.md | 2026-04-03 | ✅ 已同步代码 |
| .agents/ERRORS.md | 2026-04-03 | ✅ 已同步代码 |
| .agents/TEST_GUIDE.md | 2026-04-03 | ✅ 已同步代码 |
| tests/README.md | 2026-04-03 | ✅ 已同步代码 |
| migrations/README.md | 2026-04-04 | ✅ 已同步代码 |

### 本次新增/完善文档 🆕

| 文档 | 说明 | 状态 |
|------|------|------|
| docs/DOCUMENTATION_MAP.md | 本文档 - 文档导航地图 | 🆕 新增 |
| GETTING_STARTED.md | 开发者快速开始指南 | 🆕 新增 |
| CONTRIBUTING.md | 贡献者指南 | 🆕 新增 |
| CHANGELOG.md | 项目更新日志 | 🆕 新增 |
| docs/API_EXAMPLES.md | API使用示例集合 | 🆕 新增 |
| docs/GLOSSARY.md | 术语表 | 🆕 新增 |

---

## 快速链接

### 常用命令

```bash
# 检查服务状态
make status

# 启动后端
cd backend && conda run -n student-manage ENV=production python main.py

# 启动前端
cd frontend-v3 && pnpm dev

# 运行测试
pytest tests/ -v                    # 后端测试
pnpm test:run                        # 前端测试
```

### 关键配置

| 配置项 | 文件路径 | 说明 |
|--------|----------|------|
| 环境变量 | `backend/.env` | 应用配置 |
| 后端依赖 | `backend/requirements.txt` | Python依赖 |
| 前端依赖 | `frontend-v3/package.json` | Node依赖 |
| 数据库 | `backend/app/data/class_system.db` | SQLite数据库 |

### 服务地址

| 服务 | 地址 | 说明 |
|------|------|------|
| 后端API | http://localhost:8000 | FastAPI服务 |
| 前端 | http://localhost:5173 | Vue3应用 |
| API文档 | http://localhost:8000/docs | Swagger UI |
| 健康检查 | http://localhost:8000/api/v1/health | 服务状态 |

---

## 文档维护

### 更新流程

1. 修改文档时更新版本标记头（版本号、最后更新时间）
2. 同步更新本文档中的文档状态
3. 检查相关文档间的交叉引用
4. 确保测试统计数据一致（467后端/130前端）

### 文档规范

详见 [docs/DOCUMENTATION_GUIDE.md](./DOCUMENTATION_GUIDE.md)

---

**最后检查**: 2026-04-05  
**下次检查建议**: 每月一次或发布新版本时
