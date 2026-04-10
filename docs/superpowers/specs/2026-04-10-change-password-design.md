# 修改密码功能设计文档

日期: 2026-04-10
状态: 已批准

## 概述

为教师和学生角色添加修改密码功能。管理员已有重置密码能力，教师和学生需要自助修改密码的入口。

**前提条件**：后端 API 和前端 API 函数已完整实现，只需补全前端 UI 层。

## 已有基础设施

| 层级 | 文件 | 状态 |
|------|------|------|
| 后端 API | `POST /change-password` in `backend/app/api/routes/login.py` | 已实现，支持所有角色 |
| CRUD | `update_user_password()` in `backend/app/crud/user.py` | 已实现 |
| 前端 API | `authApi.changePassword()` in `frontend-v3/src/api/auth.ts` | 已实现 |
| 类型 | `ChangePasswordRequest` in `frontend-v3/src/types/api.ts` | 已定义 |

## 设计方案

### 入口：用户头像下拉菜单

**位置**：DashboardLayout 侧边栏用户信息区域。

**交互**：
- 用户头像区域变为可点击，带 hover 效果（`hover:bg-[#fafafa]`）
- 点击展开下拉菜单，包含：
  - "修改密码"（KeyRound 图标）→ 打开修改密码对话框
  - "退出登录"（LogOut 图标）→ 调用 authStore.logout()
- 点击菜单外部自动关闭（通过 `@clickoutside` 或 `v-click-outside`）
- 移除底部原有的独立退出登录按钮，功能合并到下拉菜单

**样式**：Ollama 白色主题
- 下拉菜单：白色背景、12px 圆角（`rounded-xl`）、`border-[#e5e5e5]`
- 菜单项：`text-sm font-medium text-[#737373]`，hover 时 `bg-[#fafafa] text-black`
- 定位：absolute，在用户头像区域下方

### 修改密码对话框

**组件**：`ChangePasswordDialog.vue` 放在 `frontend-v3/src/components/ui/`

**Props**：
- `open: boolean` — 控制对话框显示/隐藏（v-model:open）

**表单字段**：
1. 旧密码（`old_password`）— type=password，placeholder "请输入旧密码"
2. 新密码（`new_password`）— type=password，placeholder "请输入新密码"
3. 确认新密码（`confirm_password`）— type=password，placeholder "请再次输入新密码"

**校验规则**（前端 only）：
- 所有字段必填
- 新密码最少 6 个字符
- 确认密码必须与新密码一致
- 提交前一次性校验所有字段，显示第一个错误

**提交逻辑**：
1. `useMutation` 调用 `authApi.changePassword({ old_password, new_password })`
2. 成功：关闭对话框 + `useToast().success('密码修改成功')` + 重置表单
3. 失败：`useToast().error(getErrorMessage(err))` 显示错误（如"旧密码不正确"）
4. 提交期间禁用按钮，显示 loading 状态

**样式**：
- 使用现有 `ch-dialog-overlay` + `ch-dialog` 样式
- 输入框：`border-[#e5e5e5] rounded-xl`，focus 时 `border-black ring-2 ring-[#3b82f6]/50`
- 标题：`font-medium text-black`，使用 `font-family: ui-rounded`
- 提交按钮：Black Pill CTA（`bg-black text-white rounded-full`），与登录页一致
- 取消按钮：Gray Pill（`bg-[#e5e5e5] text-black rounded-full`）

### 数据流

```
DashboardLayout.vue
  ├── UserDropdown（内联在 DashboardLayout 中）
  │     ├── 点击用户头像区域 → showDropdown = !showDropdown
  │     ├── 点击"修改密码" → showChangePassword = true, showDropdown = false
  │     └── 点击"退出登录" → authStore.logout()
  └── ChangePasswordDialog.vue
        ├── v-model:open="showChangePassword"
        ├── 表单输入 → local reactive state
        ├── 校验 → 前端规则
        ├── 提交 → useMutation → authApi.changePassword
        └── 结果 → useToast 反馈
```

**不新建 composable**：逻辑简单（一个 mutation + 表单校验），直接在 Dialog 组件内处理。

## 涉及文件

| 操作 | 文件 | 说明 |
|------|------|------|
| 修改 | `frontend-v3/src/layouts/DashboardLayout.vue` | 用户头像区域变为可点击下拉菜单，移除底部退出按钮 |
| 新建 | `frontend-v3/src/components/ui/ChangePasswordDialog.vue` | 修改密码对话框组件 |
| 修改 | `frontend-v3/src/components/ui/index.ts` | 导出 ChangePasswordDialog |
| 修改 | `frontend-v3/src/components/ui/MobileDrawer.vue` | 添加"修改密码"菜单项 |

**不需要修改**：后端代码、API 函数、类型定义、路由。

## 移动端适配

- 桌面端（lg+）：下拉菜单在侧边栏用户头像区域下方展开
- 移动端（<lg）：侧边栏不显示，需要在 MobileDrawer 组件中添加同样的"修改密码"入口
  - MobileDrawer 已有用户信息区域，在该区域添加"修改密码"菜单项
  - 点击后打开同一个 ChangePasswordDialog
- ChangePasswordDialog 自身是响应式的（使用 `ch-dialog` 的移动端适配样式）

## 测试要求

- 前端组件测试：ChangePasswordDialog 的表单校验逻辑
- 前端组件测试：下拉菜单的显示/隐藏行为
