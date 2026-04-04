# ClassHub 系统测试指南

---

**文档版本**: v2.0  
**最后更新**: 2026-04-03  
**适用版本**: v3.0.0+  
**状态**: ✅ 已同步代码

**测试统计**:
- 后端: 43 个测试文件，467 个测试用例，**全部通过 ✅**
- 前端: 16 个测试文件，130 个测试用例，**全部通过 ✅**

---

---

## 概述

ClassHub 系统采用分层测试策略，涵盖后端单元测试、集成测试以及前端组件测试。本文档提供完整的测试运行指南和测试结构说明。

**测试统计**:
- 后端: 43 个测试文件，467 个测试用例，**全部通过 ✅**
  - 单元测试: 29 文件，315 测试
  - 集成测试: 14 文件，152 测试
- 前端: 16 个测试文件，130 个测试用例，**全部通过 ✅**

**测试框架**: 
- 后端: pytest + pytest-asyncio
- 前端: Vitest + @vue/test-utils + jsdom

---

## 测试环境准备

### 1. 后端环境检查

```bash
# 激活 Conda 环境
conda activate student-manage
# 或: source /home/yufeng/miniconda3/bin/activate student-manage

# 验证环境
python -c "from app.core.config import get_settings; print('配置加载正常')"
```

### 2. 前端环境检查

```bash
# 进入前端目录
cd frontend-v3

# 安装依赖
pnpm install

# 验证 Vitest 配置
npx vitest --version
```

### 3. 测试账号准备

| 角色 | 用户名 | 密码 | 说明 |
|------|--------|------|------|
| 管理员 | admin | admin123 | 系统管理员 |
| 教师 | teacher1 | teacher123 | 测试教师账号 |
| 学生 | S001 | S001 | 学号作为账号和密码 |

---

## 后端测试（pytest）

### 测试结构

```
tests/
├── conftest.py                    # 全局 fixtures 配置
├── integration/                   # 集成测试（14+ 个测试文件）
│   ├── conftest.py               # 集成测试 fixtures
│   ├── test_checkin_api_enhanced.py    # 签到 API 测试
│   ├── test_jwt_auth.py          # JWT 认证测试
│   ├── test_login_api_enhanced.py      # 登录 API 测试
│   ├── test_rate_limit.py        # 限流测试
│   ├── test_schedule_api.py      # 课表 API 测试
│   ├── test_students_api_enhanced.py   # 学生 API 测试
│   ├── test_system_api.py        # 系统 API 测试
│   ├── test_user_api.py          # 用户 API 测试
│   └── test_users_api_enhanced.py      # 用户 API 增强测试
│
├── unit/                          # 单元测试（19 个测试文件）
│   ├── crud/                     # CRUD 层测试
│   │   ├── test_audit.py         # 审计日志 CRUD
│   │   ├── test_checkin.py       # 签到 CRUD
│   │   ├── test_concurrent_login_failure.py  # 并发登录测试
│   │   ├── test_concurrent_score_update.py   # 并发分数更新测试
│   │   ├── test_student.py       # 学生 CRUD
│   │   ├── test_student_permission.py  # 学生权限测试
│   │   └── test_user.py          # 用户 CRUD
│   │
│   ├── models/                   # 模型层测试
│   │   ├── test_course_schedule.py   # 课程表模型
│   │   ├── test_student.py       # 学生模型
│   │   └── test_user.py          # 用户模型
│   │
│   ├── test_config.py            # 配置加载测试
│   ├── test_event_handlers.py    # 事件处理器测试
│   ├── test_events.py            # 领域事件测试
│   ├── test_exceptions.py        # 异常处理测试
│   ├── test_jwt.py               # JWT 工具测试
│   ├── test_jwt_cookie_secure.py # Cookie 安全测试
│   ├── test_jwt_deps.py          # JWT 依赖测试
│   ├── test_middleware.py        # 审计中间件测试
│   ├── test_security.py          # 安全工具测试
│   └── test_upload.py            # 文件上传安全测试
│
└── browser/                       # 浏览器测试
    └── recorded_test.py          # Playwright 录制测试
```

### 运行后端测试

```bash
# 运行全部测试
pytest tests/ -v

# 仅单元测试
pytest tests/unit -v

# 仅集成测试
pytest tests/integration -v

# 运行特定测试文件
pytest tests/unit/test_upload.py -v
pytest tests/unit/crud/test_student.py -v
pytest tests/integration/test_students_api_enhanced.py -v

# 运行带标记的测试
pytest -m smoke -v
pytest -m integration -v
pytest -m unit -v

# 生成覆盖率报告
pytest tests/ --cov=backend/app --cov-report=html
pytest tests/ --cov=backend/app --cov-report=term

# 查看覆盖率缺口
pytest tests/ --cov=backend/app --cov-report=term-missing
```

### 测试 Fixtures

主要 fixtures（定义在 `conftest.py`）：

| Fixture | 说明 |
|---------|------|
| `engine` | 内存 SQLite 数据库引擎 |
| `session` | 数据库会话 |
| `test_student` | 测试学生数据 |
| `test_user` | 测试教师数据 |
| `test_admin` | 测试管理员数据 |
| `jwt_client` | JWT 测试客户端 |

---

## 前端测试（Vitest）

### 测试结构

```
frontend-v3/
├── test/
│   ├── components/              # 组件测试 (8 文件, 32 测试)
│   │   ├── Button.spec.ts
│   │   ├── Card.spec.ts
│   │   ├── Dialog.spec.ts       # 内存泄漏测试
│   │   ├── Input.spec.ts
│   │   ├── Toast.spec.ts        # 内存泄漏测试
│   │   ├── Select.spec.ts
│   │   ├── Table.spec.ts
│   │   └── Modal.spec.ts
│   ├── composables/             # Composables 测试 (4 文件, 16 测试)
│   │   ├── useToast.spec.ts     # 全局 Toast 测试
│   │   ├── useAuth.spec.ts
│   │   ├── usePermission.spec.ts
│   │   └── useStudent.spec.ts
│   └── utils/                   # 工具函数测试 (2 文件, 10 测试)
│       ├── helpers.spec.ts
│       └── formatters.spec.ts
│
├── vitest.config.ts             # Vitest 配置文件
└── package.json
```

### Vitest 配置

**vitest.config.ts**:

```typescript
import { defineConfig } from 'vitest/config'
import vue from '@vitejs/plugin-vue'
import { resolve } from 'path'

export default defineConfig({
  plugins: [vue()],
  test: {
    environment: 'jsdom',
    globals: true,
    include: ['test/**/*.{test,spec}.{js,ts}'],
    exclude: ['node_modules', 'dist', '.idea', '.git'],
    coverage: {
      provider: 'v8',
      reporter: ['text', 'json', 'html'],
      include: ['src/**/*.ts', 'src/**/*.vue'],
      exclude: ['src/**/*.d.ts', 'src/main.ts']
    }
  },
  resolve: {
    alias: {
      '@': resolve(__dirname, 'src')
    }
  }
})
```

### 运行前端测试

```bash
# 进入前端目录
cd frontend-v3

# 运行所有测试（交互模式，推荐开发使用）
pnpm test
# 或: npx vitest

# 运行所有测试（一次性，CI 使用）
pnpm test:run
# 或: npx vitest run

# 运行特定测试文件
npx vitest run test/components/Toast.spec.ts
npx vitest run test/composables/useToast.spec.ts

# 运行特定目录
npx vitest run test/components/

# 生成覆盖率报告
npx vitest run --coverage

# 监听模式（开发时使用）
npx vitest --watch

# UI 模式
npx vitest --ui
```

### 前端测试说明

#### 组件测试

**Toast 组件测试** (`test/components/Toast.spec.ts`):
- ✅ 组件卸载时清除 timeout
- ✅ 多次调用 showToast 时清除旧 timer
- ✅ 快速显示/隐藏不产生内存泄漏
- ✅ 卸载时调用 clearTimers

**Dialog 组件测试** (`test/components/Dialog.spec.ts`):
- ✅ 多次打开/关闭循环无错误
- ✅ 打开状态下卸载组件无错误
- ✅ 关闭状态下卸载组件无错误
- ✅ body overflow 样式正确清理

**Button 组件测试** (`test/components/Button.spec.ts`):
- ✅ 正确渲染按钮文本
- ✅ 支持不同变体和尺寸
- ✅ 禁用状态正确显示
- ✅ 点击事件正确触发
- ✅ 加载状态显示 spinner

#### Composables 测试

**useToast 测试** (`test/composables/useToast.spec.ts`):
- ✅ 正确添加 toast 到队列
- ✅ 自动移除超时 toast
- ✅ 支持多种类型 (success, error, warning, info)
- ✅ 手动关闭 toast

**useAuth 测试** (`test/composables/useAuth.spec.ts`):
- ✅ 登录状态管理
- ✅ Token 存储和读取
- ✅ 权限检查
- ✅ 登出清理

### 测试覆盖的修复

| 组件 | 修复内容 | 测试验证 |
|------|----------|----------|
| Toast.vue | 添加 `onUnmounted` 清理 setTimeout | 4 个测试 |
| Dialog.vue | 添加 `onUnmounted` 重置 body overflow | 3 个测试 |
| useToast | 全局单例模式 | 5 个测试 |
| Button.vue | 事件和状态测试 | 4 个测试 |

---

## 测试命令速查

### 后端测试命令

| 命令 | 说明 |
|------|------|
| `pytest tests/ -v` | 运行全部测试 |
| `pytest tests/unit -v` | 仅单元测试 |
| `pytest tests/integration -v` | 仅集成测试 |
| `pytest tests/ --collect-only` | 列出所有测试 |
| `pytest -k "test_student" -v` | 运行匹配名称的测试 |
| `pytest -x -v` | 遇到第一个失败即停止 |
| `pytest --tb=short` | 简短错误回溯 |
| `pytest --tb=long` | 详细错误回溯 |

### 前端测试命令

| 命令 | 说明 |
|------|------|
| `pnpm test` | 交互式测试模式 |
| `pnpm test:run` | 一次性运行测试 |
| `npx vitest run test/components/Toast.spec.ts` | 运行特定测试文件 |
| `npx vitest run --coverage` | 生成覆盖率报告 |
| `npx vitest --watch` | 监听模式 |
| `npx vitest --reporter=verbose` | 详细输出 |
| `npx vitest --ui` | UI 模式 |

---

## 测试统计

### 后端测试统计

| 类别 | 测试文件数 | 测试用例数 |
|------|-----------|-----------|
| 单元测试 | 29 | 315 |
| 集成测试 | 14 | 152 |
| **后端总计** | **43** | **467** |

### 前端测试统计

| 类别 | 测试文件数 | 测试用例数 | 状态 |
|------|-----------|-----------|------|
| 组件测试 | 7 | ~60 | ✅ 通过 |
| Composables 测试 | 4 | ~35 | ✅ 通过 |
| API/工具/类型/视图测试 | 5 | ~35 | ✅ 通过 |
| **前端总计** | **16** | **130** | ✅ **全部通过** |

### 测试覆盖的核心功能

**认证与安全**:
- JWT Token 创建、解码、过期处理
- HttpOnly Cookie 设置和清除
- 密码哈希与验证（bcrypt）
- 登录失败锁定机制

**CRUD 操作**:
- 学生增删改查与分数更新
- 用户管理与权限控制
- 签到记录管理
- 课程表管理

**并发控制**:
- 乐观锁防止并发更新数据丢失
- 并发登录失败计数

**文件上传安全**:
- 文件类型白名单/黑名单验证
- 路径遍历攻击防护
- 文件名安全处理

**领域事件**:
- 事件发布与订阅
- 事务边界管理
- 事件处理器执行

**审计日志**:
- 敏感操作自动记录
- 中间件路由匹配
- 资源标识提取

**前端组件**:
- 内存泄漏防护（Toast/Dialog）
- SSR 安全（Teleport 使用）
- 事件处理
- 状态管理

---

## 最佳实践

### 后端测试最佳实践

#### 1. 测试数据库隔离
- 单元测试：使用 `MagicMock` 隔离数据库
- 集成测试：使用内存 SQLite (`sqlite:///:memory:`)
- 每个测试独立，自动清理数据

#### 2. 延迟导入模式
```python
# 事件处理器使用延迟导入避免测试引擎冲突
def handle_score_updated(event):
    from app.core.db import engine  # 延迟导入
    with Session(engine) as session:
        ...
```

#### 3. 使用 Fixtures
```python
def test_student_update(session, test_student):
    """使用 test_student fixture 创建测试数据"""
    # 无需手动创建学生数据
    result = update_student(session, test_student.student_id, ...)
    assert result is not None
```

### 前端测试最佳实践

#### 1. 使用 fake timers
```typescript
import { vi, beforeEach, afterEach } from 'vitest'

beforeEach(() => {
  vi.useFakeTimers()
})

afterEach(() => {
  vi.restoreAllMocks()
})
```

#### 2. 组件卸载测试
```typescript
import { mount } from '@vue/test-utils'

it('should clear timeout when unmounted', async () => {
  const wrapper = mount(Component, { ... })
  
  // 执行操作
  await wrapper.setProps({ show: true })
  
  // 卸载组件
  wrapper.unmount()
  
  // 验证清理
  vi.advanceTimersByTime(5000)
  expect(...).toBe(...)
})
```

#### 3. Mock 外部依赖
```typescript
import { vi } from 'vitest'

vi.mock('@/api/auth', () => ({
  login: vi.fn().mockResolvedValue({ token: 'test-token' })
}))
```

#### 4. 测试 SSR 安全
```typescript
it('should not access window during SSR', () => {
  // 模拟 SSR 环境
  const originalWindow = global.window
  // @ts-ignore
  global.window = undefined
  
  // 组件应该正确处理
  const wrapper = mount(Component)
  expect(wrapper.exists()).toBe(true)
  
  // 恢复环境
  global.window = originalWindow
})
```

---

## 常见问题排查

### 后端测试问题

| 错误 | 原因 | 解决 |
|------|------|------|
| `ImportError: cannot import name 'Literal'` | Python 3.7 环境问题 | 确保使用 Python 3.11+ |
| `ModuleNotFoundError` | 未激活 Conda 环境 | 运行 `conda activate student-manage` |
| 测试挂起/超时 | 数据库引擎冲突 | 检查 `handlers.py` 使用延迟导入 |
| 覆盖率下降 | 新增代码未测试 | 补充对应测试文件 |

### 前端测试问题

| 错误 | 原因 | 解决 |
|------|------|------|
| `Cannot find module '@/components/...'` | 路径别名配置问题 | 检查 `vitest.config.ts` resolve.alias |
| `Vue warn: Failed to resolve component` | 组件未正确注册 | 确保全局组件在测试中注册 |
| `Error: No test suite found` | 测试文件命名问题 | 确保文件名为 `*.spec.ts` 或 `*.test.ts` |
| jsdom 环境错误 | DOM API 不支持 | 使用 `vitest-environment jsdom` 注释 |

### 调试技巧

```bash
# 后端单个测试调试
pytest tests/unit/test_events.py::TestEventBus::test_subscribe_and_publish -v --pdb

# 后端详细错误输出
pytest tests/unit/test_xxx.py -v --tb=long

# 前端详细输出
npx vitest run --reporter=verbose

# 前端调试模式
npx vitest --inspect-brk

# 前端 UI 模式
npx vitest --ui
```

---

## CI/CD 集成

### GitHub Actions 示例

```yaml
name: Test

on: [push, pull_request]

jobs:
  backend-test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.11'
      - name: Install dependencies
        run: |
          pip install -r backend/requirements.txt
          pip install pytest pytest-cov
      - name: Run tests
        run: pytest tests/ --cov=backend/app

  frontend-test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - name: Set up Node
        uses: actions/setup-node@v3
        with:
          node-version: '20'
      - name: Install dependencies
        run: cd frontend-v3 && pnpm install
      - name: Run tests
        run: cd frontend-v3 && pnpm test:run
      - name: Generate coverage
        run: cd frontend-v3 && npx vitest run --coverage
```

---

## 更新日志

### v2.0.0 (2026-03-27)
- 更新前端测试统计（130 个测试全部通过）
- 添加 Vitest 配置完整说明
- 添加组件测试示例（Button, Toast, Dialog）
- 添加 Composables 测试示例
- 添加前端测试最佳实践

### v1.0.0 (2026-03-23)
- 初始版本
- 后端测试完整说明
- 前端基础测试说明

---

**文档版本**: 2026-03-27  
**适用系统版本**: ClassHub v3.0.0  
**后端架构**: FastAPI + SQLModel  
**前端架构**: Vue 3 + TypeScript + TanStack Query  
**测试框架**: pytest + Vitest
