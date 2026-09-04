# ClassHub 开发规范

---

**文档版本**: v1.0  
**最后更新**: 2026-04-13  
**适用版本**: v3.0.0+  
**状态**: 已同步代码

---

本文档整合项目所有开发规范，涵盖通用操作禁令、后端/前端开发约束、测试规范、代码风格以及 Git 协作流程。是 `CLAUDE.md`（AI 快速参考）的完整版，供所有开发人员查阅。

**相关文档索引**:
- [CLAUDE.md](../CLAUDE.md) - AI 助手快速参考
- [.agents/ERRORS.md](../.agents/ERRORS.md) - 完整纠错记录
- [.agents/CHECKLIST.md](../.agents/CHECKLIST.md) - 执行前检查清单
- [CONTRIBUTING.md](../CONTRIBUTING.md) - 贡献者指南
- [backend/README.md](../backend/README.md) - 后端架构
- [frontend-v3/docs/ARCHITECTURE.md](../frontend-v3/docs/ARCHITECTURE.md) - 前端架构
- [.agents/TEST_GUIDE.md](../.agents/TEST_GUIDE.md) - 测试完整指南

---

## 目录

1. [通用开发与操作规范](#1-通用开发与操作规范)
2. [后端开发规范](#2-后端开发规范)
3. [前端开发规范](#3-前端开发规范)
4. [测试规范](#4-测试规范)
5. [Git 与协作规范](#5-git-与协作规范)
6. [纠错记录](#6-纠错记录)

---

## 1. 通用开发与操作规范

### 1.1 绝对禁止（Universal Prohibitions）

以下行为**绝对禁止**：

| # | 禁令 | 违反后果 |
|---|------|----------|
| 1 | 不要在未检查服务状态的情况下重启服务 | 重复部署，端口冲突 |
| 2 | 不要快速连续执行停止+启动命令 | 残留进程导致启动失败 |
| 3 | 不要假设数据库/服务路径 | 操作错误的文件 |
| 4 | 不要在未验证的情况下认为操作成功 | 隐藏错误 |
| 5 | **禁止在碰到问题后回退组件版本** | 掩盖问题，重复犯错 |
| 6 | **禁止在非虚拟环境的 python 环境下运行 python 命令** | 模块找不到，环境混乱 |
| 7 | **禁止修改后端代码后不检查/更新对应测试** | 测试失效，覆盖率下降 |
| 8 | **禁止修改 Vue/TS 文件后不创建或修改测试** | 前端类型变更无测试覆盖 |
| 9 | **禁止未经用户明确同意擅自修改功能或简化需求** | 违背用户意图，破坏信任 |
| 10 | **禁止在未阅读完所有相关代码的情况下直接修复整改** | 破坏项目结构一致性 |
| 11 | **禁止测试不通过时删除测试用例** | 应修复问题而非绕过测试 |
| 12 | **禁止在未阅读完调用链的情况下修改公共函数接口** | 修改签名后必须同步所有调用方 |

### 1.2 环境要求

- **Python**: 3.11+，必须使用 Conda 环境 `student-manage`
- **Node.js**: 20+，使用 pnpm 8+
- **数据库**: PostgreSQL 15（开发=本地安装，生产=Docker 容器）

执行 Python 命令前必须确认环境：

```bash
# 方式1：激活环境
conda activate student-manage

# 方式2：前缀方式运行（适用于 shell 脚本）
conda run -n student-manage python <脚本>

# 验证
which python  # 输出必须包含 miniconda
```

### 1.3 服务操作规范

**重启服务前必须检查状态**：

```bash
curl -s --max-time 5 http://localhost:8000/api/v1/health
curl -s --max-time 5 http://localhost:5173 > /dev/null && echo "前端运行中"
```

**后端重启强制流程**（禁止直接 `python main.py`）：

```bash
pkill -f "python main.py" 2>/dev/null || true
sleep 3  # 必须等待
ps aux | grep "python.*main.py" | grep -v grep  # 检查残留，有则 pkill -9
cd /home/yufeng/student-manager/backend
conda run -n student-manage ENV=production python main.py &
sleep 5
curl -s --max-time 5 http://localhost:8000/api/v1/health  # 必须验证
```

**前端重启强制流程**：

```bash
pkill -f "pnpm dev" 2>/dev/null || true
sleep 2
cd /home/yufeng/student-manager/frontend-v3
pnpm dev &
sleep 3
curl -s --max-time 5 http://localhost:5173 > /dev/null && echo "前端运行中"
```

### 1.4 Read 工具预检（AI 助手强制约定）

每次调用 Read 工具前，必须在 commentary 中显式输出参数确认行（如：`Read preflight: limit=200, offset=1. OK.`）：
- `limit` 必须是正整数（> 0），禁止负数或 0
- `offset` >= 1
- 超大文件优先用 Grep 定位，不盲目读全文
- **未输出此行即调用 Read，视为违规**

### 1.5 跨文件修改一致性工作流

当修改涉及多个文件（如新增功能、重构接口、修改 queryKey）时，必须执行：

1. **修改前 - 依赖分析**：用 Grep 搜索所有相关引用
2. **修改中 - 同步检查**：
   - queryKey / invalidateQueries 格式在所有文件保持一致
   - 变量处理（空值、undefined）在所有位置一致
   - 类型转换在比较操作中明确处理
3. **修改后 - 一致性验证**：确保所有引用数量与预期一致
4. **测试验证**：手动测试跨文件交互场景，检查 DevTools Network 确认缓存失效请求

---

## 2. 后端开发规范

### 2.1 架构与分层

后端采用 FastAPI + SQLModel 分层架构：

```
backend/app/
├── api/           # API 层（路由、依赖注入）
│   ├── deps.py    # 依赖注入（get_current_user 等）
│   └── routes/    # 路由处理器
├── core/          # 核心工具
│   ├── config.py  # 配置管理（pydantic-settings）
│   ├── db.py      # 数据库连接
│   ├── security.py # JWT、密码哈希（bcrypt）
│   ├── events.py  # 领域事件发布
│   └── exceptions.py # 异常处理
├── crud/          # 数据库操作层（含乐观锁）
├── events/        # 事件处理器
└── models/        # SQLModel 实体 + Pydantic 模式
```

### 2.2 Python 代码风格

- 遵循 PEP 8
- 使用类型注解
- 最大行长度 100 字符
- 按需导入，禁止 `from datetime import *`

```python
# 正确
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

def update_student_score(
    session: Session,
    student_id: int,
    score_change: float,
    changed_by: int
) -> Student:
    """更新学生分数"""
    pass

# 错误
from datetime import *

def update_student_score(session, student_id, score_change, changed_by):
    pass
```

### 2.3 API 设计规范

#### RESTful 接口

| 方法 | 用途 | 示例 |
|------|------|------|
| GET | 获取资源 | `GET /api/v1/students` |
| POST | 创建资源 | `POST /api/v1/students` |
| PUT | 更新资源 | `PUT /api/v1/students/{id}/score` |
| DELETE | 删除资源 | `DELETE /api/v1/students/{id}` |

#### 统一响应格式

```json
// 成功
{ "success": true, "data": { ... }, "message": "操作成功" }

// 失败
{ "success": false, "message": "错误信息" }
```

错误处理必须使用 HTTPException，禁止返回裸字典：

```python
# 正确
raise HTTPException(status_code=400, detail="参数错误")

# 错误
return {"error": "参数错误"}
```

### 2.4 API 响应常量（强制）

**禁止硬编码响应字段名**，必须使用常量：

```python
from app.models.constants import ApiResponseConst, MessageConst

# 正确
return {
    ApiResponseConst.SUCCESS: True,
    ApiResponseConst.MESSAGE: MessageConst.USER_CREATED,
    ApiResponseConst.DATA: user.model_dump()
}

# 错误
# return {"success": True, "message": "用户创建成功"}
```

### 2.5 JWT 与安全规范

#### JWT Claims

Token 包含字段：

```python
{
    "sub": "1",           # 用户ID（字符串）
    "username": "admin",  # 用户名
    "name": "管理员",      # 显示名称
    "role": "admin",      # 角色
    "is_admin": true,     # 是否管理员
}
```

**禁止假设字段存在**，始终使用 `.get()`：

```python
user_id = user.get("sub")  # 正确
user_id = user["sub"]      # 可能报错
```

#### JWT 时区（强制）

所有 JWT Token 过期时间必须使用 `Asia/Shanghai` 时区：

```python
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

# 正确
now = datetime.now(ZoneInfo("Asia/Shanghai"))
expire = now + timedelta(hours=24)

# 错误
expire = datetime.utcnow() + timedelta(hours=24)
```

#### 密码验证接口（强制）

必须使用新接口（bcrypt 自动处理盐值）：

```python
from app.core.security import verify_password, hash_password

# 正确
is_valid = verify_password("plain_password", stored_hash)
new_hash = hash_password("new_password")

# 错误 - 已弃用
is_valid = verify_password_hash("plain_password", stored_hash, salt)
```

### 2.6 环境变量配置（强制）

使用**双下划线**访问嵌套配置：

```bash
# 正确
DATABASE__PATH=./data/class_system.db
SECURITY__SECRET_KEY=your-secret
SECURITY__MAX_LOGIN_FAILURES=10
JWT__ACCESS_TOKEN_EXPIRE_MINUTES=1440

# 错误 - 单下划线会被忽略
# DATABASE_PATH=xxx
```

环境变量设置时机：必须在导入应用代码**之前**设置：

```bash
# 正确
export ENV=testing
python main.py

# 错误 - Python 内设置不生效
python -c "import os; os.environ['ENV'] = 'testing'; from app.core.config import get_settings"
```

### 2.7 数据库操作约束

#### 路径确认（强制）

执行任何数据库操作前，确认实际路径：

```bash
python -c "from app.core.config import get_settings; print(get_settings().get_database_path())"
```

#### 集成测试隔离（强制）

集成测试使用内存数据库，**禁止**连接到生产数据库。

#### 乐观锁保护

```python
class Student(SQLModel, table=True):
    id: int = Field(primary_key=True)
    score: int = Field(default=0)
    version: int = Field(default=0)
```

并发冲突自动抛出 `ConcurrentUpdateError`。

### 2.8 限流与状态码（强制）

限流触发时必须返回 **429 Too Many Requests**，禁止 503：

```python
# 正确
raise HTTPException(status_code=429, detail="请求过于频繁")

# 错误
raise HTTPException(status_code=503, detail="服务不可用")
```

### 2.9 错误排查顺序

遇到问题时，**按顺序**执行：

1. 查看后端日志输出（不是猜测）
2. 检查进程：`ps aux | grep python`
3. 验证配置：`python -c "from app.core.config import get_settings; print(get_settings().app.env)"`

**禁止**在没有查看日志的情况下尝试修复。

---

## 3. 前端开发规范

### 3.1 架构与目录结构

前端采用 Vue 3.5 + TypeScript，Feature-based 组织：

```
frontend-v3/src/
├── api/           # API 请求层
├── components/    # UI 组件（ui/ + common/）
├── composables/   # 组合式函数（useToast 是全局的）
├── features/      # 特性化模块
├── views/         # 页面级组件
├── router/        # Vue Router
├── stores/        # Pinia
├── styles/        # 样式文件
├── types/         # 类型定义
└── utils/         # 工具函数
```

### 3.2 Vue/TypeScript 代码风格

- 使用 Composition API + `<script setup>`
- 组件名使用 PascalCase
- Props 必须使用类型定义
- 使用 `storeToRefs` 解构 Pinia Store 保持响应性

```vue
<script setup lang="ts">
// 正确
interface Props {
  title: string
  visible: boolean
}

const props = defineProps<Props>()
const emit = defineEmits<{
  close: []
}>()

// 错误
const props = defineProps(['title', 'visible'])
</script>
```

### 3.3 Feature-based 架构规范

按功能域组织代码，每个 feature 包含所需的所有组件、逻辑和类型：

```
features/feature-name/
├── components/          # 该功能专用组件
├── composables/         # 该功能专用 composables
├── types.ts            # 该功能专用类型
├── constants.ts        # 该功能常量
└── index.ts            # 统一导出（门面模式）
```

`index.ts` 示例：

```typescript
export { default as ComponentA } from './components/ComponentA.vue'
export { useFeatureA } from './composables/useFeatureA'
export type { FeatureAData } from './types'
```

### 3.4 Composables 规范

#### 命名规范

| 类型 | 命名格式 | 示例 |
|------|----------|------|
| 列表管理 | `use{Feature}List` | `useStudentList` |
| 表单管理 | `use{Feature}Form` | `useStudentForm` |
| 操作逻辑 | `use{Action}{Feature}` | `useDeleteStudent` |

#### 参数传递

```typescript
// 正确：使用对象参数
export function useFeatureList(options: UseFeatureListOptions) {
  const { initialPage = 1, pageSize = 10 } = options
}

// 调用
const { features } = useFeatureList({ initialPage: 1, pageSize: 20 })
```

#### 错误处理

```typescript
import { useToast } from '@/composables/useToast'

export function useFeatureList() {
  const { showToast } = useToast()
  const { data, error, isLoading, refetch } = useQuery({
    queryKey: ['features'],
    queryFn: fetchFeatures,
    onError: (err: Error) => {
      showToast(err.message || '加载失败', 'error')
    }
  })
  return { data, error, isLoading, refresh: refetch }
}
```

### 3.5 组件设计原则

1. **单一职责**：一个组件只负责一个功能点（列表、表单、弹窗分离）
2. **Props Down, Events Up**：
   - 使用明确类型定义 Props
   - 使用 `emit` 代替回调 Props
3. **Slots 增强灵活性**：页眉/页脚/内容使用具名插槽
4. **Teleport 使用规范**：弹窗、Toast 必须渲染到 body，并处理 SSR 安全

```vue
<template>
  <Teleport to="body">
    <div v-if="visible" class="dialog-overlay">...</div>
  </Teleport>
</template>

<script setup lang="ts">
import { onMounted, ref } from 'vue'
const isMounted = ref(false)
onMounted(() => { isMounted.value = true })
</script>
```

### 3.6 API 响应处理（强制）

后端返回格式：`{success: true, data: {...}, message: "..."}`

**禁止直接访问 `res.xxx`**，必须访问 `res.data`：

```typescript
// 错误
res.user.role

// 正确
res.data.user.role
```

### 3.7 Tailwind CSS v4 约束（强制）

自定义 `@theme` 会**完全覆盖**默认主题，必须保留 `--spacing: 0.25rem` 基础单位：

```css
/* 正确 */
@theme inline {
  --color-primary: #6366f1;
}

/* 或 */
@theme {
  --spacing: 0.25rem;  /* 必须保留 */
  --color-primary: #6366f1;
}
```

### 3.8 TanStack Query 缓存一致性（强制）

- **修改 `useQuery` 的 `queryKey` 后，同步检查所有 `invalidateQueries` 调用**
- 同一数据源的 `queryKey` 必须完全一致
- 变量处理：`['key', var || 'default']` 与 `['key', var]` 是不同的键
- **跨文件修改时**，用 Grep 搜索所有使用该 queryKey 的文件
- **空值处理一致性**：`undefined`、`null`、`''` 在 queryKey 中是不同的值

### 3.9 类型一致性（强制）

- **JWT Token `sub` 是字符串，API 返回的 `id` 通常是数字**
- 比较前统一转换：`Number(userId) === apiId` 或 `String(userId) === apiId`
- 检查 `===`、`!==`、`>`、`<` 等操作数的类型匹配

```typescript
// 错误
"2" !== 2  // true

// 正确
Number("2") !== 2  // false
```

### 3.10 异步刷新与内存优化

#### 异步刷新顺序

mutation 后需要刷新数据时，**先 await refetch，再显示成功提示**：

```typescript
// 错误
mutate(); showSuccess(); refetch()

// 正确
await mutate(); await refetch(); showSuccess()
```

#### 清理副作用

组件卸载时必须清理 timers 和事件监听：

```vue
<script setup lang="ts">
import { onUnmounted, ref } from 'vue'

const timer = ref<NodeJS.Timeout | null>(null)

onUnmounted(() => {
  if (timer.value) clearInterval(timer.value)
})
</script>
```

#### 性能优化

- 大型对象使用 `shallowRef` 替代 `ref`
- 复杂列表使用 `v-memo`
- 路由与重型组件使用懒加载
- 静态内容使用 `v-once`
- 计算结果使用 `computed` 缓存

---

## 4. 测试规范

### 4.1 后端测试

#### 测试结构

```
tests/
├── unit/              # 单元测试
│   ├── test_*.py
│   └── crud/
├── integration/       # API 集成测试
│   └── test_*_api*.py
└── conftest.py       # 全局 fixtures
```

#### 运行命令（必须在项目根目录执行）

```bash
pytest tests/ -v                    # 全部（467个）
pytest tests/unit -v                 # 仅单元
pytest tests/integration -v          # 仅集成
pytest tests/unit/test_<模块>.py -v  # 单个文件
```

#### 修改后端代码后检查清单（强制）

1. 查找相关单元测试：`tests/unit/test_<模块>.py` 或 `tests/unit/<模块>/test_*.py`
2. 查找相关集成测试：`tests/integration/test_<模块>_api*.py`
3. 确认测试覆盖修改的代码
4. 运行相关测试验证
5. **如有失败，必须修复测试后再提交（禁止删除测试用例）**

### 4.2 前端测试

#### 测试结构

```
frontend-v3/test/
├── components/        # 组件测试
├── composables/       # Composables 测试
└── utils/            # 工具函数测试
```

#### 运行命令

```bash
cd frontend-v3
pnpm test:run         # 一次性运行
pnpm test             # 交互模式
npx vitest run --coverage
```

#### 修改 Vue/TS 代码后检查清单（强制）

- [ ] 评估是否需要创建新测试
- [ ] 评估是否需要修改已有测试
- [ ] 运行前端测试：`pnpm test:run`

### 4.3 修改后的测试询问流程（强制）

修改或新增功能后，**必须询问用户**：

> "修改/新增功能已完成，是否需要运行测试？
> - 运行全部测试: `pytest tests/ -v`
> - 仅单元测试: `pytest tests/unit -v`
> - 仅集成测试: `pytest tests/integration -v`
> - 不需要测试"

**禁止**擅自决定不运行测试。

---

## 5. Git 与协作规范

### 5.1 Commit Message 规范

格式：`<type>(<scope>): <subject>`

| 类型 | 说明 |
|------|------|
| `feat` | 新功能 |
| `fix` | 修复 bug |
| `docs` | 文档更新 |
| `style` | 代码格式（不影响功能） |
| `refactor` | 重构 |
| `test` | 测试相关 |
| `chore` | 构建/工具相关 |

示例：

```bash
feat(auth): 添加 JWT Token 刷新机制

- 实现 /api/v1/refresh-token 接口
- 添加 Token 过期自动刷新逻辑
- 更新前端 axios 拦截器

Closes #123
```

### 5.2 分支命名规范

```
feature/<功能描述>      # 新功能
fix/<bug描述>           # Bug修复
docs/<文档描述>         # 文档更新
refactor/<重构描述>     # 代码重构
test/<测试描述>         # 测试相关
chore/<工具描述>        # 构建/工具
```

### 5.3 PR 提交规范

#### PR 标题格式

```
[<type>] <简短描述>
```

示例：

```
[feat] 添加学生 Excel 批量导入功能
[fix] 修复登录限流状态码错误
```

#### PR 描述模板

```markdown
## 变更说明
简要描述本次变更的内容

## 变更类型
- [ ] 新功能
- [ ] Bug修复
- [ ] 文档更新
- [ ] 代码重构
- [ ] 性能优化
- [ ] 测试相关

## 测试情况
- [ ] 本地测试通过
- [ ] 新增测试用例
- [ ] 更新现有测试

## 检查清单
- [ ] 代码遵循项目规范
- [ ] 测试全部通过
- [ ] 文档已更新
- [ ] Commit 信息规范

## 相关 Issue
Fixes #123
Closes #456
```

### 5.4 代码审查流程

审查 Checklist：

- [ ] 代码逻辑正确
- [ ] 测试覆盖充分
- [ ] 文档已更新
- [ ] 无安全漏洞
- [ ] 性能影响评估
- [ ] 向后兼容性

---

## 6. 纠错记录

以下是从过往错误中总结的关键约束，需要时刻警惕：

| 日期 | 错误 | 约束 |
|------|------|------|
| - | 未检查服务状态就重启 | 执行前必须检查 health |
| - | 快速停止+启动导致残留进程 | 必须 sleep 3 秒 |
| - | 未激活 Conda 环境 | 必须检查 `which python` |
| - | Tailwind v4 覆盖默认主题 | 必须保留 `--spacing` |
| - | 访问 `res.user` 而非 `res.data` | 必须使用 `res.data.xxx` |
| 2026-03-23 | 碰到问题回退组件版本 | **禁止回退版本**，先尝试修复或报告 |
| 2026-03-24 | 使用系统自带 python 运行脚本 | **必须激活 Conda 环境** |
| 2026-03-25 | 修改后端代码后未检查测试 | **必须检查并适配测试** |
| 2026-03-26 | 未阅读完相关代码就修复整改 | **必须先了解项目结构** |
| 2026-03-26 | 测试不通过时删除测试 | **禁止删除测试用例** |
| 2026-03-26 | 修改 Vue/TS 文件后未创建或修改测试 | **必须更新前端测试** |
| 2026-03-31 | 未阅读完调用链就修复 API 函数 | **修改公共接口必须同步所有调用方** |
| 2026-04-01 | 未经用户同意擅自简化地图功能 | **禁止擅自修改功能或简化需求** |
| 2026-04-02 | curl 请求长时间无超时导致阻塞 | **curl 必须设置超时时间** |
| 2026-04-06 | JWT `sub`（字符串）与 API `id`（数字）类型不一致导致比较失败 | **比较前统一类型转换** |
| 2026-04-06 | useQuery queryKey 与 invalidateQueries 不一致导致缓存不刷新 | **缓存键一致性** |
| 2026-04-06 | mutation 后未 await refetch 就显示成功提示 | **异步刷新顺序**：先 refetch 再提示 |

---

**参考文档**:
- [CLAUDE.md](../CLAUDE.md) - AI 快速参考
- [.agents/ERRORS.md](../.agents/ERRORS.md) - 完整纠错记录
- [.agents/CHECKLIST.md](../.agents/CHECKLIST.md) - 执行前检查清单
- [CONTRIBUTING.md](../CONTRIBUTING.md) - 贡献者指南
- [.agents/TEST_GUIDE.md](../.agents/TEST_GUIDE.md) - 测试完整指南
