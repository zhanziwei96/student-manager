# 前端页面全面视觉优化实施计划

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 将CSS变量方案推广到所有13个前端页面，统一视觉体验，确保移动端和桌面端一致

**Architecture:** 基于已完成的 `student/Dashboard.vue` 优化经验，使用CSS变量(`--card-{color}-*`)替代Tailwind动态类，每个卡片使用一致的颜色系统（blue/green/purple/orange）

**Tech Stack:** Vue 3.5 + TypeScript + Tailwind CSS v4 + CSS Variables

---

## 文件清单

### 需要修改的13个文件

| 批次 | 文件路径 | 复杂度 | 预估时间 |
|------|----------|--------|----------|
| 1 | `frontend-v3/src/views/teacher/Dashboard.vue` | 低 | 20分钟 |
| 1 | `frontend-v3/src/views/admin/Dashboard.vue` | 低 | 20分钟 |
| 2 | `frontend-v3/src/views/student/Checkin.vue` | 中 | 30分钟 |
| 2 | `frontend-v3/src/views/student/Leaderboard.vue` | 中 | 25分钟 |
| 3 | `frontend-v3/src/views/teacher/Students.vue` | 中 | 25分钟 |
| 3 | `frontend-v3/src/views/teacher/ClassSession.vue` | 高 | 35分钟 |
| 3 | `frontend-v3/src/views/teacher/Schedules.vue` | 中 | 25分钟 |
| 4 | `frontend-v3/src/views/admin/Classes.vue` | 中 | 25分钟 |
| 4 | `frontend-v3/src/views/admin/Teachers.vue` | 中 | 25分钟 |
| 4 | `frontend-v3/src/views/admin/Students.vue` | 中 | 25分钟 |
| 4 | `frontend-v3/src/views/admin/Checkins.vue` | 中 | 25分钟 |
| 5 | `frontend-v3/src/views/LandingPage.vue` | 高 | 35分钟 |
| 5 | `frontend-v3/src/views/NotFound.vue` | 低 | 15分钟 |

---

## CSS变量参考

位于 `frontend-v3/src/styles/tokens.css`:

```css
/* 蓝色主题 - 班级/信息 */
--card-blue-bg: rgba(59, 130, 246, 0.15);
--card-blue-border: rgba(59, 130, 246, 0.4);
--card-blue-icon-bg: rgba(96, 165, 250, 0.3);
--card-blue-icon-text: #93c5fd;
--card-blue-shadow: rgba(23, 37, 84, 0.3);
--card-blue-glow: rgba(59, 130, 246, 0.1);

/* 绿色主题 - 状态/成功 */
--card-green-bg: rgba(34, 197, 94, 0.15);
--card-green-border: rgba(34, 197, 94, 0.4);
--card-green-icon-bg: rgba(74, 222, 128, 0.3);
--card-green-icon-text: #86efac;
--card-green-shadow: rgba(5, 46, 22, 0.3);
--card-green-glow: rgba(34, 197, 94, 0.1);

/* 紫色主题 - 身份/学号 */
--card-purple-bg: rgba(168, 85, 247, 0.15);
--card-purple-border: rgba(168, 85, 247, 0.4);
--card-purple-icon-bg: rgba(192, 132, 252, 0.3);
--card-purple-icon-text: #d8b4fe;
--card-purple-shadow: rgba(59, 7, 100, 0.3);
--card-purple-glow: rgba(168, 85, 247, 0.1);
```

---

## 辅助函数模板

每个文件需要添加以下辅助函数：

```typescript
type CardColor = 'blue' | 'green' | 'purple' | 'orange'

const getCardStyle = (color: CardColor) => {
  const varPrefix = `--card-${color}`
  return {
    backgroundColor: `var(${varPrefix}-bg)`,
    borderColor: `var(${varPrefix}-border)`,
    '--tw-shadow-color': `var(${varPrefix}-shadow)`,
  } as Record<string, string>
}

const getCardIconStyle = (color: CardColor) => {
  const varPrefix = `--card-${color}`
  return {
    backgroundColor: `var(${varPrefix}-icon-bg)`,
    color: `var(${varPrefix}-icon-text)`,
  }
}

const getCardGlowStyle = (color: CardColor) => {
  const varPrefix = `--card-${color}`
  return {
    backgroundColor: `var(${varPrefix}-glow)`,
  }
}
```

---

## Task 1: Teacher Dashboard 视觉优化

**Files:**
- Modify: `frontend-v3/src/views/teacher/Dashboard.vue`

**目标**: 将统计卡片改为CSS变量方案

- [ ] **Step 1: 添加类型定义和辅助函数**

在 `<script setup>` 中添加：

```typescript
type CardColor = 'blue' | 'green' | 'purple'

const getCardStyle = (color: CardColor) => {
  const varPrefix = `--card-${color}`
  return {
    backgroundColor: `var(${varPrefix}-bg)`,
    borderColor: `var(${varPrefix}-border)`,
    '--tw-shadow-color': `var(${varPrefix}-shadow)`,
  } as Record<string, string>
}

const getCardIconStyle = (color: CardColor) => {
  const varPrefix = `--card-${color}`
  return {
    backgroundColor: `var(${varPrefix}-icon-bg)`,
    color: `var(${varPrefix}-icon-text)`,
  }
}

const getCardGlowStyle = (color: CardColor) => {
  const varPrefix = `--card-${color}`
  return {
    backgroundColor: `var(${varPrefix}-glow)`,
  }
}
```

- [ ] **Step 2: 修改统计卡片样式**

找到统计卡片 `<Card>` 组件（约第132行），修改：

```vue
<Card
  v-for="card in statCards"
  :key="card.title"
  class="group relative overflow-hidden p-4 shadow-lg transition-all duration-300 hover:scale-[1.02] cursor-pointer"
  :style="getCardStyle(card.color)"
  @click="router.push(card.link)"
>
```

- [ ] **Step 3: 修改图标容器样式**

找到图标容器 `div`（约第148行），改为：

```vue
<div
  class="flex h-10 w-10 items-center justify-center rounded-xl shadow-inner transition-transform group-hover:scale-110"
  :style="getCardIconStyle(card.color)"
>
```

- [ ] **Step 4: 修改背景装饰元素**

找到背景装饰 `div`（约第170行），改为：

```vue
<div
  class="absolute -right-4 -bottom-4 h-16 w-16 rounded-full blur-2xl transition-colors opacity-30"
  :style="getCardGlowStyle(card.color)"
/>
```

- [ ] **Step 5: 删除旧的辅助函数（如果存在）**

删除旧的 `getCardTextMutedColor` 函数（如果不使用）。

- [ ] **Step 6: 运行类型检查**

```bash
cd frontend-v3 && pnpm vue-tsc --noEmit
```

- [ ] **Step 7: Commit**

```bash
git add frontend-v3/src/views/teacher/Dashboard.vue
git commit -m "optimize: Teacher Dashboard 使用CSS变量方案"
```

---

## Task 2: Admin Dashboard 视觉优化

**Files:**
- Modify: `frontend-v3/src/views/admin/Dashboard.vue`

**目标**: 应用与 Teacher Dashboard 相同的CSS变量方案

- [ ] **Step 1: 阅读当前 Admin Dashboard 文件**

```bash
cat frontend-v3/src/views/admin/Dashboard.vue
```

- [ ] **Step 2: 添加辅助函数**

复制 Task 1 中的辅助函数到 `<script setup>`。

- [ ] **Step 3: 修改统计卡片**

参考 Task 1 的模式，修改所有统计卡片的样式绑定。

- [ ] **Step 4: 运行类型检查**

```bash
cd frontend-v3 && pnpm vue-tsc --noEmit
```

- [ ] **Step 5: Commit**

```bash
git add frontend-v3/src/views/admin/Dashboard.vue
git commit -m "optimize: Admin Dashboard 使用CSS变量方案"
```

---

## Task 3: Student Checkin 视觉优化

**Files:**
- Modify: `frontend-v3/src/views/student/Checkin.vue`

**目标**: 
- 学生信息卡片使用 purple 主题
- 签到状态卡片使用 green 主题
- 签到按钮区域使用渐变背景
- 签到说明卡片使用 blue 主题

- [ ] **Step 1: 阅读当前文件**

- [ ] **Step 2: 添加辅助函数**

- [ ] **Step 3: 修改学生信息卡片为 purple 主题**

- [ ] **Step 4: 修改签到状态卡片为 green 主题**

- [ ] **Step 5: 修改签到说明卡片为 blue 主题**

- [ ] **Step 6: 运行类型检查并 Commit**

---

## Task 4: Student Leaderboard 视觉优化

**Files:**
- Modify: `frontend-v3/src/views/student/Leaderboard.vue`

**目标**:
- "我的排名"卡片使用渐变背景
- 前三名使用特殊主题色（金牌/银牌/铜牌）
- 当前用户高亮使用 primary 主题

- [ ] **Step 1: 阅读当前文件**

- [ ] **Step 2: 添加辅助函数**

- [ ] **Step 3: 修改"我的排名"卡片样式**

- [ ] **Step 4: 修改前三名排名样式**

- [ ] **Step 5: 运行类型检查并 Commit**

---

## Task 5-13: 其他页面优化

（按照相同模式继续，每个页面一个Task）

---

## 最终验证

- [ ] **运行所有类型检查**

```bash
cd frontend-v3 && pnpm vue-tsc --noEmit
```

- [ ] **运行前端测试**

```bash
pnpm test:run
```

- [ ] **手动验证清单**

打开浏览器验证以下页面：
- [ ] teacher/Dashboard - 移动端 375px
- [ ] teacher/Dashboard - 桌面端 1440px
- [ ] admin/Dashboard - 移动端
- [ ] admin/Dashboard - 桌面端
- [ ] student/Checkin - 两种尺寸
- [ ] student/Leaderboard - 两种尺寸
- [ ] （其他页面...）

- [ ] **提交最终 commit**

```bash
git add .
git commit -m "optimize: 完成所有前端页面视觉优化"
```

---

## 分批执行建议

由于任务量大，建议分批执行：

**第一批**: Task 1-2 (Dashboard页面) - 约40分钟
**第二批**: Task 3-4 (Student模块) - 约55分钟
**第三批**: Task 5-7 (Teacher模块) - 约85分钟
**第四批**: Task 8-11 (Admin模块) - 约100分钟
**第五批**: Task 12-13 (公共页面) - 约50分钟

**总计**: 约5.5小时
