# ClassHub 系统测试指南

---

**文档版本**: v2.1
**最后更新**: 2026-04-13
**适用版本**: v3.0.0+
**状态**: ✅ 已同步代码

---

## 测试统计

| 层级 | 测试文件数 | 测试用例数 | 说明 |
|------|-----------|-----------|------|
| 后端单元测试 | 29 | 315 | 快速、独立运行 |
| 后端集成测试 | 14 | 152 | API 集成测试 |
| **后端总计** | **43** | **467** | **全部通过 ✅** |
| 前端测试 | 16 | 130 | Vitest 组件 + Composables |
| **前端总计** | **16** | **130** | **全部通过 ✅** |

---

## 概述

ClassHub 采用分层测试策略，测试文档按职责分散在不同位置：

- **后端 pytest 测试**：详见 [`tests/README.md`](../tests/README.md)
- **前端 Vitest 测试**：详见 [`frontend-v3/test/README.md`](../frontend-v3/test/README.md)
- **E2E Playwright 测试**：详见 [`tests/e2e/README.md`](../tests/e2e/README.md)

本文档提供测试总览、快速命令速查和跨层测试策略说明。具体操作命令和示例请参考各专项文档。

---

## 测试环境准备

### 后端环境检查

```bash
# 激活 Conda 环境
conda activate student-manage

# 验证环境
python -c "from app.core.config import get_settings; print('配置加载正常')"
```

### 前端环境检查

```bash
cd frontend-v3
pnpm install
npx vitest --version
```

### 测试账号（E2E 使用）

| 角色 | 用户名 | 密码 | 说明 |
|------|--------|------|------|
| 管理员 | admin | admin123 | 系统管理员 |
| 教师 | teacher1 | teacher123 | 测试教师账号 |
| 学生 | S001 | S001 | 学号作为账号和密码 |

---

## 快速命令速查

### 后端测试命令

```bash
# 运行全部测试
pytest tests/ -v

# 仅单元测试
pytest tests/unit -v

# 仅集成测试
pytest tests/integration -v

# 运行特定测试文件
pytest tests/unit/test_upload.py -v
pytest tests/integration/test_students_api_enhanced.py -v

# 生成覆盖率报告
pytest tests/ --cov=app --cov-report=html
pytest tests/ --cov=app --cov-report=term-missing
```

### 前端测试命令

```bash
cd frontend-v3

# 交互式测试模式（开发推荐）
pnpm test

# 一次性运行（CI 使用）
pnpm test:run

# 运行特定测试文件
npx vitest run test/components/Toast.spec.ts

# 生成覆盖率报告
npx vitest run --coverage
```

### E2E 测试命令

```bash
cd tests/e2e
npm install
npx playwright install chromium

# 运行所有 E2E 测试
npx playwright test

# 运行特定文件
npx playwright test login.spec.ts
```

---

## 测试结构总览

### 后端测试结构

```
tests/
├── conftest.py                    # 全局 fixtures 配置
├── integration/                   # 集成测试（14 文件，152 测试）
│   ├── conftest.py
│   ├── test_active_class_sessions.py
│   ├── test_checkin_api_enhanced.py
│   ├── test_dashboard_data_masking.py
│   ├── test_schedule_api.py
│   ├── test_token_refresh.py
│   └── ...
├── unit/                          # 单元测试（29 文件，315 测试）
│   ├── crud/                     # CRUD 层测试（11 文件）
│   ├── models/                   # 模型层测试（3 文件）
│   ├── test_jwt.py
│   ├── test_security.py
│   ├── test_upload.py
│   └── ...
└── e2e/                           # E2E 测试（Playwright）
    └── README.md
```

### 前端测试结构

```
frontend-v3/test/
├── components/              # 组件测试 (8 文件, ~32 测试)
├── composables/             # Composables 测试 (4 文件, ~16 测试)
├── utils/                   # 工具函数测试 (2 文件, ~10 测试)
└── setup.ts                 # 测试初始化配置
```

---

## 跨层测试最佳实践

### 后端测试最佳实践

1. **测试数据库隔离**：使用内存 SQLite，每个测试独立运行
2. **延迟导入模式**：事件处理器中延迟导入 engine，避免测试引擎冲突
3. **使用 Fixtures**：复用 `session`、`test_student`、`test_user` 等 fixtures

### 前端测试最佳实践

1. **使用 fake timers**：涉及 setTimeout 的组件（如 Toast）测试前启用 `vi.useFakeTimers()`
2. **组件卸载测试**：验证 `onUnmounted` 清理逻辑，防止内存泄漏
3. **Mock 外部依赖**：API 调用使用 `vi.mock` 隔离

### CI/CD 集成

```yaml
name: Tests
on: [push, pull_request]

jobs:
  backend-test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: '3.11'
      - name: Install dependencies
        run: |
          pip install -r backend/requirements.txt
          pip install pytest pytest-asyncio httpx pytest-cov
      - run: pytest tests/ -v

  frontend-test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-node@v4
        with:
          node-version: '20'
      - run: cd frontend-v3 && pnpm install
      - run: cd frontend-v3 && pnpm test:run

  e2e-test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-node@v4
        with:
          node-version: '20'
      - run: cd tests/e2e && npm ci && npx playwright install --with-deps chromium
      - run: cd tests/e2e && npx playwright test
```

---

## 常见问题排查

### 后端测试问题

| 错误 | 原因 | 解决 |
|------|------|------|
| `ImportError: cannot import name 'Literal'` | Python 3.7 环境问题 | 确保使用 Python 3.11+ |
| `ModuleNotFoundError` | 未激活 Conda 环境 | 运行 `conda activate student-manage` |
| 测试挂起/超时 | 数据库引擎冲突 | 检查 `handlers.py` 使用延迟导入 |

### 前端测试问题

| 错误 | 原因 | 解决 |
|------|------|------|
| `Cannot find module '@/components/...'` | 路径别名配置问题 | 检查 `vitest.config.ts` resolve.alias |
| `Error: No test suite found` | 测试文件命名问题 | 确保文件名为 `*.spec.ts` 或 `*.test.ts` |

---

## 相关文档

- [后端测试说明](../tests/README.md) — pytest 详细用法、Fixtures、模块级命令
- [前端测试说明](../frontend-v3/test/README.md) — Vitest 配置、组件测试示例、覆盖率
- [E2E 测试说明](../tests/e2e/README.md) — Playwright 环境搭建、测试账号、Page Object 模式

---

**文档版本**: v2.1
**最后更新**: 2026-04-13
**适用系统版本**: ClassHub v3.0.0+
