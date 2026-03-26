# ClassHub 项目助手指令

> **⚠️ 执行前强制阅读**: 
> 1. **先阅读** [ERRORS.md](./.agents/ERRORS.md) - 执行约束清单
> 2. **然后检查**服务状态，避免重复部署

---

## 通用禁令（绝对禁止）

| # | 禁令 | 违反后果 |
|---|------|----------|
| 1 | ❌ 不要在未检查服务状态的情况下重启服务 | 重复部署，端口冲突 |
| 2 | ❌ 不要快速连续执行停止+启动命令 | 残留进程导致启动失败 |
| 3 | ❌ 不要假设数据库/服务路径 | 操作错误的文件 |
| 4 | ❌ 不要在未验证的情况下认为操作成功 | 隐藏错误 |
| 6 | ❌ **禁止在碰到问题后回退组件版本** | 掩盖问题，重复犯错 |
| 7 | ❌ **禁止在非虚拟环境的 python 环境下运行 python 命令** | 模块找不到，环境混乱 |
| 8 | ❌ **禁止修改后端代码后不检查/更新对应测试** | 测试失效，覆盖率下降 |

---

## 执行前强制检查清单

```bash
# 1. 环境检查 (必须)
which python  # 确认是 miniconda 路径

# 2. 服务状态检查 (必须)
curl -s http://localhost:8000/api/health  # 后端是否已运行？
curl -s http://localhost:5173 > /dev/null && echo "前端运行中"  # 前端是否已运行？

# 3. 数据库路径确认 (涉及 DB 操作时必须)
python -c "from app.core.config import get_settings; print(get_settings().get_database_path())"
```

**决策逻辑**: 服务已运行 → 不需要重启；服务未运行 → 按重启流程执行

---

## 服务重启强制流程

**禁止**直接执行 `python main.py` 或 `pnpm dev`。

```bash
# 后端重启
pkill -f "python main.py" 2>/dev/null || true
sleep 3  # 必须等待！
ps aux | grep "python.*main.py" | grep -v grep  # 检查残留
cd /home/yufeng/student-manager/backend
conda run -n student-manage ENV=production python main.py &
sleep 5
curl -s http://localhost:8000/api/health  # 必须验证！

# 前端重启
pkill -f "pnpm dev" 2>/dev/null || true
sleep 2
cd /home/yufeng/student-manager/frontend-v3
pnpm dev &
sleep 3
curl -s http://localhost:5173 > /dev/null && echo "前端运行中"  # 必须验证！
```

---

## 关键路径

| 项目 | 路径 |
|------|------|
| 后端代码 | `/home/yufeng/student-manager/backend/` |
| 前端代码 | `/home/yufeng/student-manager/frontend-v3/` |
| 旧版前端 | `/home/yufeng/student-manager/frontend/` (不再维护) |
| 数据库 | `/home/yufeng/student-manager/backend/data/class_system.db` |
| 测试代码 | `/home/yufeng/student-manager/tests/` |

---

## 技术架构

### 后端（FastAPI + SQLModel）
```
backend/
├── app/
│   ├── api/           # API路由
│   ├── core/          # 核心组件（config.py, db.py, security.py）
│   ├── crud/          # 数据库操作
│   └── models/        # 数据模型
└── main.py
```
- JWT + HttpOnly Cookie 认证
- 响应格式：`{success: true, data: {...}, message: "..."}`

### 前端（Vue3 + Tailwind CSS v4）
- **Tailwind CSS v4** - 自定义 `@theme` 必须保留 `--spacing: 0.25rem`
- 深色主题: 背景 `#030307`，主色 `#6366f1`
- API 响应访问: 必须用 `res.data.xxx`，禁止 `res.xxx`

---

## 环境要求

| 依赖 | 版本 | 检查命令 |
|------|------|----------|
| Python | 3.11+ | `python --version` |
| Conda | 最新 | `conda --version` |
| Node.js | 20+ | `node --version` |
| pnpm | 8+ | `pnpm --version` |

**必须激活虚拟环境**: `conda activate student-manage`

---

## 工作流程规范

### 修改后端代码后（强制）

**必须**询问用户是否需要运行测试：

> "修改/新增功能已完成，是否需要运行测试？
> - 运行全部测试: `pytest tests/ -v`
> - 仅单元测试: `pytest tests/unit -v`
> - 仅集成测试: `pytest tests/integration -v`
> - 不需要测试"

**禁止**擅自决定不运行测试。

### 测试执行（强制）

```bash
# 正确 - 在项目根目录运行
pytest tests/ -v

# 修改后检查清单
# 1. 查找相关测试文件
ls tests/unit/test_<模块>.py
ls tests/integration/test_<模块>_api*.py
# 2. 运行相关测试验证
pytest tests/unit/test_<修改模块>.py -v
```

---

## 详细文档

| 文档 | 内容 |
|------|------|
| [.agents/ERRORS.md](./.agents/ERRORS.md) | 完整执行约束清单、纠错记录 |
| [.agents/AGENTS.md](./.agents/AGENTS.md) | 完整速查手册、架构说明 |
| [.agents/DEPLOYMENT.md](./.agents/DEPLOYMENT.md) | 完整部署指南 |
| [.agents/CONFIG_GUIDE.md](./.agents/CONFIG_GUIDE.md) | 配置管理说明 |

---

**最后更新**: 2026-03-25
**架构版本**: FastAPI + SQLModel
