# ClassHub 项目 Claude Code 插件使用指南

本文档介绍如何使用 Claude Code 中已安装的插件来高效开发 ClassHub 项目。

---

## 已安装插件清单

| 插件 | 类型 | 用途 |
|------|------|------|
| **superpowers** | 核心技能集 | 开发流程标准化（TDD、调试、计划执行等） |
| **feature-dev** | 功能开发 | 特性化开发向导，架构分析 |
| **code-review** | 代码审查 | PR 审查、代码质量检查 |
| **frontend-design** | 前端设计 | 创建高质量 UI 组件 |
| **code-simplifier** | 代码优化 | 简化重构代码 |
| **github** | GitHub 集成 | PR、Issue、仓库操作 |
| **playwright** | 浏览器测试 | E2E 测试、页面操作 |
| **context7** | 文档查询 | 查询框架/库文档 |

---

## 一、日常开发工作流

### 1.1 开始新功能开发

```bash
# 方式1: 使用 skill 命令启动 brainstorm（推荐）
/skill superpowers:brainstorming

# 方式2: 描述需求让 Claude 自动选择技能
我要开发一个【学生成绩导出】功能，支持导出 Excel 和 PDF 格式
```

**插件会自动执行:**
1. **superpowers:brainstorming** - 分析需求、探索方案
2. **feature-dev** - 分析现有代码架构
3. **superpowers:writing-plans** - 生成实施计划

### 1.2 使用 Worktree 隔离开发

```bash
# 创建独立工作区进行功能开发
/skill superpowers:using-git-worktrees

# 或手动执行
创建一个 worktree 用于开发 score-export 功能
```

### 1.3 执行开发计划

```bash
# 当已有计划文件时，使用执行计划技能
/skill superpowers:executing-plans

# 或在计划中包含独立任务时使用
/skill superpowers:subagent-driven-development
```

---

## 二、按场景的使用指南

### 场景1: 新增后端 API

**流程:**
```
1. brainstorming → 2. writing-plans → 3. TDD → 4. 编码 → 5. code-review
```

**具体操作:**

```bash
# Step 1: 需求分析
/skill superpowers:brainstorming
# 输入: 我要添加一个批量导入学生成绩的 API，支持 Excel 文件上传

# Step 2: 生成计划（brainstorming 会自动调用）
# 计划文件保存在 .claude/plans/batch_import_scores.md

# Step 3: 测试驱动开发
/skill superpowers:test-driven-development
# 先写测试: tests/integration/test_score_import_api.py

# Step 4: 执行计划
/skill superpowers:executing-plans
# 按步骤实现: model → crud → api → tests

# Step 5: 代码简化
/skill code-simplifier
```

**关键检查点 (CLAUDE.md):**
- [ ] Python 环境: `conda run -n student-manage`
- [ ] 修改后检查相关测试
- [ ] API 响应使用 `res.data.xxx` 格式

---

### 场景2: 新增前端页面

**流程:**
```
1. frontend-design → 2. brainstorming → 3. TDD → 4. 编码 → 5. playwright 测试
```

**具体操作:**

```bash
# Step 1: 设计 UI
/skill frontend-design
# 输入: 设计一个学生成绩管理页面，包含表格、搜索、导出按钮

# Step 2: 需求澄清
/skill superpowers:brainstorming
# 确认: 使用 Tailwind v4？响应式布局？暗黑主题？

# Step 3: 测试驱动
/skill superpowers:test-driven-development
# 先写测试: frontend-v3/test/views/ScoreManagement.spec.ts

# Step 4: 开发组件
# Views: frontend-v3/src/views/teacher/ScoreManagement.vue
# Components: frontend-v3/src/components/teacher/ScoreTable.vue
# Composables: frontend-v3/src/composables/useScoreManagement.ts

# Step 5: E2E 测试
/skill playwright
# 创建: tests/e2e/score-management.spec.ts
```

**关键检查点:**
- [ ] API 响应使用 `res.data.xxx`
- [ ] Tailwind v4 `@theme` 保留 `--spacing: 0.25rem`
- [ ] 类型定义在 `frontend-v3/src/types/api.ts`

---

### 场景3: Bug 修复

**流程:**
```
1. systematic-debugging → 2. TDD（复现测试）→ 3. 修复 → 4. verification
```

**具体操作:**

```bash
# Step 1: 系统调试
/skill superpowers:systematic-debugging
# 描述 bug: 学生签到时返回 500 错误，日志显示...

# Step 2: 创建复现测试
/skill superpowers:test-driven-development
# 先写失败测试，确认能复现问题

# Step 3: 修复代码
# 修改相关文件

# Step 4: 验证修复
/skill superpowers:verification-before-completion
# 运行: pytest tests/unit/crud/test_checkin.py -v
```

---

### 场景4: 代码重构

**流程:**
```
1. code-simplifier → 2. TDD（确保行为不变）→ 3. 重构 → 4. verification
```

**具体操作:**

```bash
# Step 1: 代码简化分析
/skill code-simplifier
# 输入: 请简化 backend/app/crud/checkin.py 中的重复代码

# Step 2: 确保测试覆盖
pytest tests/unit/crud/test_checkin.py -v --cov=app.crud.checkin

# Step 3: 应用简化建议
# 或使用 subagent 并行处理多个文件

# Step 4: 验证
/skill superpowers:verification-before-completion
```

---

### 场景5: 提交代码审查

**流程:**
```
1. verification → 2. requesting-code-review → 3. (optional) github PR
```

**具体操作:**

```bash
# Step 1: 验证所有检查通过
/skill superpowers:verification-before-completion
# 运行全部测试: pytest tests/ -v && cd frontend-v3 && pnpm test:run

# Step 2: 请求代码审查
/skill superpowers:requesting-code-review
# 输入: 完成学生成绩导入功能，包含后端 API 和前端页面

# Step 3: 创建 GitHub PR（如需要）
/skill github
# 输入: 创建 PR，标题为 "feat: 添加学生成绩批量导入功能"
```

---

## 三、插件详细使用说明

### 3.1 Superpowers 核心技能集

#### Brainstorming（需求分析）
```bash
/skill superpowers:brainstorming
```
**何时使用:** 任何新功能开始前
**输入示例:** "我要添加一个学生请假审批流程，包含提交、审批、通知三个环节"
**输出:** 需求澄清、技术方案、边界条件、实施步骤

#### Writing Plans（写计划）
```bash
/skill superpowers:writing-plans
```
**何时使用:** 需求明确后，编码前
**输入:** 功能描述或 brainstorm 结果
**输出:** `.claude/plans/<feature>.md` 文件

#### Test Driven Development（TDD）
```bash
/skill superpowers:test-driven-development
```
**何时使用:** 编写任何新功能前
**流程:** 先写测试 → 运行失败 → 写实现 → 运行通过 → 重构
**后端测试位置:** `tests/unit/` 或 `tests/integration/`
**前端测试位置:** `frontend-v3/test/`

#### Systematic Debugging（系统调试）
```bash
/skill superpowers:systematic-debugging
```
**何时使用:** 遇到 Bug 时
**输入:** 错误信息、复现步骤、预期行为
**禁止:** 未诊断直接修复

#### Verification Before Completion（完成前验证）
```bash
/skill superpowers:verification-before-completion
```
**何时使用:** 声称完成前、提交前
**检查项:** 测试通过、类型检查、约束遵守

#### Executing Plans（执行计划）
```bash
/skill superpowers:executing-plans
```
**何时使用:** 已有计划文件，需要执行
**自动处理:** 检查点、错误恢复、子 Agent 调度

### 3.2 Feature Dev（功能开发向导）

```bash
/skill feature-dev
```
**功能:**
- 分析现有代码架构
- 理解项目约定和模式
- 提供实现蓝图

**使用场景:**
- 不熟悉的新项目
- 复杂功能需要架构分析
- 需要了解数据流和依赖关系

### 3.3 Code Review（代码审查）

```bash
# 审查当前修改
/skill code-review

# 审查特定 PR
/skill github
# 输入: 审查 PR #123
```

**审查重点:**
- 安全漏洞（SQL 注入、XSS）
- 项目约定遵守
- 测试覆盖
- 代码质量

### 3.4 Frontend Design（前端设计）

```bash
/skill frontend-design
```
**适用:**
- 创建新页面/组件
- 设计 UI 布局
- 实现响应式/暗黑主题

**设计系统遵循:** `frontend-v3/DESIGN_SYSTEM.md`
- 背景色: `#030307`
- 主色: `#6366f1`
- 字体: Inter

### 3.5 Context7（文档查询）

```bash
# 查询 Vue 3 Composition API
使用 context7 查询 Vue 3 defineProps 和 defineEmits 的最新用法

# 查询 FastAPI
使用 context7 查询 FastAPI 依赖注入的最佳实践
```

**支持库:** React, Vue, Next.js, Express, Tailwind 等主流框架

### 3.6 GitHub（GitHub 操作）

```bash
# 查看 PR
/skill github
查看 PR #42

# 创建 Issue
创建 Issue: Bug - 签到 API 返回 500 错误

# 搜索代码
搜索项目中所有使用 verify_password 的地方
```

### 3.7 Playwright（浏览器测试）

```bash
# 创建 E2E 测试
/skill playwright
创建学生签到流程的 E2E 测试

# 截图验证
访问 http://localhost:5173 并截图
```

---

## 四、项目特定约束

### 4.1 后端约束 (FastAPI)

```python
# ✅ 必须使用的新接口
from app.core.security import verify_password, hash_password
is_valid = verify_password("plain", stored_hash)

# ✅ JWT 时区
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo
expire = datetime.now(ZoneInfo("Asia/Shanghai")) + timedelta(hours=24)

# ✅ API 响应常量
from app.models.constants import ApiResponseConst, MessageConst
return {
    ApiResponseConst.SUCCESS: True,
    ApiResponseConst.MESSAGE: MessageConst.USER_CREATED,
    ApiResponseConst.DATA: user.model_dump()
}

# ✅ JWT Claims 访问
user_id = user.get("sub")  # 不是 user["sub"]
```

### 4.2 前端约束 (Vue 3)

```typescript
// ✅ API 响应处理
res.data.role  // 不是 res.role

// ✅ Tailwind v4 主题
@theme inline {
  --color-primary: #6366f1;
}
// 或保留 spacing
@theme {
  --spacing: 0.25rem;
  --color-primary: #6366f1;
}
```

### 4.3 测试约束

```bash
# ✅ 正确 - 项目根目录运行
pytest tests/ -v

# ❌ 错误 - 不要 cd 到 tests 目录
cd tests && pytest  # 错误！

# ✅ 前端测试
pnpm test:run  # 不是 pnpm test (交互式)
```

---

## 五、完整开发示例

### 示例: 开发【学生请假】功能

```bash
# ========== Phase 1: 启动 ==========
# 1. 进入 Plan Mode 进行需求分析
/skill superpowers:brainstorming
# 输入: 我要开发一个学生请假功能，包含：
# - 学生提交请假申请（开始时间、结束时间、原因）
# - 教师审批（批准/拒绝）
# - 通知学生审批结果

# ========== Phase 2: 计划 ==========
# 2. 生成计划（brainstorming 会自动调用 writing-plans）
# 输出: .claude/plans/leave_request_feature.md

# 3. 创建 worktree（可选但推荐）
/skill superpowers:using-git-worktrees
# 命名: leave-request-feature

# ========== Phase 3: 开发 ==========
# 4. 测试驱动开发 - 后端
/skill superpowers:test-driven-development
# 先写: tests/unit/crud/test_leave_request.py
# 再写: tests/integration/test_leave_request_api.py

# 5. 执行计划
/skill superpowers:executing-plans
# 按步骤: model → crud → api → schema

# 6. 前端设计
/skill frontend-design
# 设计: 请假申请表单、审批页面、状态显示

# 7. 前端 TDD
/skill superpowers:test-driven-development
# 先写: frontend-v3/test/views/LeaveRequest.spec.ts

# 8. 前端开发
# - views/teacher/LeaveApproval.vue
# - views/student/LeaveRequest.vue
# - composables/useLeaveRequest.ts

# ========== Phase 4: 验证 ==========
# 9. 代码简化
/skill code-simplifier
# 优化重复代码

# 10. 完成前验证
/skill superpowers:verification-before-completion
# 运行:
# - pytest tests/unit/crud/test_leave_request.py -v
# - pytest tests/integration/test_leave_request_api.py -v
# - cd frontend-v3 && pnpm test:run
# - make status (检查服务健康)

# ========== Phase 5: 提交 ==========
# 11. 请求代码审查
/skill superpowers:requesting-code-review
# 输入: 完成学生请假功能，包含前后端完整实现

# 12. 创建 GitHub PR
/skill github
# 输入: 创建 PR，base: main，head: leave-request-feature

# 13. 退出 worktree
/skill superpowers:finishing-a-development-branch
# 选择: merge, PR, 或 cleanup
```

---

## 六、快速参考卡片

### 常用命令速查

| 场景 | 命令 |
|------|------|
| 新功能开始 | `/skill superpowers:brainstorming` |
| 写计划 | `/skill superpowers:writing-plans` |
| 执行计划 | `/skill superpowers:executing-plans` |
| 创建 Worktree | `/skill superpowers:using-git-worktrees` |
| 开始 TDD | `/skill superpowers:test-driven-development` |
| 调试 Bug | `/skill superpowers:systematic-debugging` |
| 完成验证 | `/skill superpowers:verification-before-completion` |
| 代码审查 | `/skill superpowers:requesting-code-review` |
| 设计 UI | `/skill frontend-design` |
| 创建 GitHub PR | `/skill github` |
| 查询文档 | `使用 context7 查询 <框架> 的 <功能>` |

### 文件位置速查

| 类型 | 路径 |
|------|------|
| 后端模型 | `backend/app/models/` |
| 后端 CRUD | `backend/app/crud/` |
| 后端 API | `backend/app/api/routes/` |
| 前端页面 | `frontend-v3/src/views/` |
| 前端组件 | `frontend-v3/src/components/` |
| 前端组合式函数 | `frontend-v3/src/composables/` |
| 后端测试 | `tests/unit/` 和 `tests/integration/` |
| 前端测试 | `frontend-v3/test/` |
| E2E 测试 | `tests/e2e/` |
| 计划文件 | `.claude/plans/` |

---

## 七、故障排除

### 插件未生效
- 检查 `~/.claude/settings.json` 中 `enabledPlugins`
- 重启 Claude Code

### MCP 工具错误
- 检查服务状态: `make status`
- 查看日志: `make logs`

### 测试失败
- 后端: 确认 conda 环境 `conda run -n student-manage`
- 前端: 确认 Node 版本 20+

---

*最后更新: 2026-04-04*
