# Ollama 设计系统前端重构设计规格

**日期**: 2026-04-10
**分支**: `feature/ollama-design-refactor`
**状态**: 待实施

## 目标

将 ClassHub 前端从暗色主题（#030307 背景、indigo #6366f1 主色、cyan #22d3ee 强调色、阴影/发光/渐变效果）重构为 Ollama 风格的极简白色主题（纯白背景、灰度色板、药丸形交互、二进制圆角、零阴影），同时保留语义状态色以保证管理系统的可用性。

## 决策记录

| 决策项 | 选择 | 理由 |
|--------|------|------|
| 状态色 | 保留语义色（success/warning/error/info） | 管理系统需要颜色区分数据状态 |
| 导航布局 | 保留侧边栏布局 | 适合后台管理，导航空间充足 |
| 重构范围 | 一次性全量重构 40+ 文件 | 用户明确要求 |
| 移动端 | 同步适配 | 避免主题不一致 |
| 整体风格 | Ollama 极简基底 + 状态色（方案B） | 平衡美学与可用性 |

## 1. 色彩体系

### 1.1 灰度色板（页面基底）

| 角色 | CSS 变量 | 色值 | 用途 |
|------|----------|------|------|
| Pure Black | `--color-pure-black` | `#000000` | 标题、主文字 |
| Near Black | `--color-near-black` | `#262626` | 按钮文字（灰按钮上） |
| Mid Gray | `--color-mid-gray` | `#525252` | 强调次要文字 |
| Stone | `--color-stone` | `#737373` | 次要文字、footer 链接 |
| Silver | `--color-silver` | `#a3a3a3` | 三级文字、placeholder |
| Button Text Dark | `--color-button-text-dark` | `#404040` | 白色按钮上的文字 |
| Border Light | `--color-border-light` | `#d4d4d4` | 白色表面按钮边框 |
| Light Gray | `--color-light-gray` | `#e5e5e5` | 按钮背景、通用边框 |
| Snow | `--color-snow` | `#fafafa` | 区域背景、轻微区分表面 |
| Pure White | `--color-pure-white` | `#ffffff` | 页面主背景、卡片背景 |
| Darkest Surface | `--color-darkest-surface` | `#090909` | 极少使用（footer 等） |

### 1.2 语义映射

| 角色 | CSS 变量 | 色值 |
|------|----------|------|
| 页面背景 | `--color-background` | `#ffffff` |
| 提升表面 | `--color-background-elevated` | `#fafafa` |
| 卡片背景 | `--color-background-card` | `#ffffff` |
| 主文字 | `--color-text-primary` | `#000000` |
| 次要文字 | `--color-text-secondary` | `#737373` |
| 三级文字 | `--color-text-tertiary` | `#a3a3a3` |
| Placeholder | `--color-text-placeholder` | `#a3a3a3` |
| 边框 | `--color-border` | `#e5e5e5` |
| 边框 Hover | `--color-border-hover` | `#d4d4d4` |
| 边框 Focus | `--color-border-focus` | `#000000` |
| Focus Ring | `--color-focus-ring` | `#3b82f6` |

### 1.3 语义状态色（仅用于数据/状态指示）

| 角色 | CSS 变量 | 色值 | 用途 |
|------|----------|------|------|
| Success | `--color-success` | `#22c55e` | 签到成功、成绩优秀 |
| Warning | `--color-warning` | `#f59e0b` | 迟到、成绩警告 |
| Error | `--color-error` | `#ef4444` | 缺勤、错误状态 |
| Info | `--color-info` | `#3b82f6` | 提示信息 |

### 1.4 废弃颜色

以下颜色将从 tokens.css 和所有组件中移除：
- `#6366f1` (indigo 主色) 及所有 `rgba(99,102,241,x)` 变体
- `#22d3ee` (cyan 强调色) 及所有 `rgba(34,211,238,x)` 变体
- `#030307` / `#0a0a0f` (暗色背景)
- 所有 `rgba(255,255,255,x)` 透明色
- `#1a1a2e` (暗蓝色面板背景)
- 所有卡片主题色变量 (`--card-indigo-*`, `--card-neutral-*` 等)

## 2. 字体系统

### 2.1 字体栈

| 角色 | CSS 变量 | 字体栈 |
|------|----------|--------|
| Display/标题 | `--font-display` | `ui-rounded, 'Hiragino Sans GB', 'PingFang SC', 'Microsoft YaHei', sans-serif` |
| Body/UI | `--font-body` | `ui-sans-serif, system-ui, -apple-system, 'PingFang SC', 'Microsoft YaHei', sans-serif` |
| Monospace | `--font-mono` | `ui-monospace, 'SFMono-Regular', Menlo, Consolas, 'Liberation Mono', 'Courier New', monospace` |

### 2.2 字重限制

- **400** (regular): 正文、描述文字
- **500** (medium): 标题、导航、强调
- **禁止**: 300 (light)、600 (semibold)、700 (bold)

### 2.3 变更

- 移除 Google Fonts `Inter:wght@300;400;500;600;700` 引用
- 移除 JetBrains Mono 外部字体
- 全部使用系统字体栈，零外部字体依赖
- 全局替换 `font-bold`/`font-semibold` 为 `font-medium`

## 3. 圆角系统

### 3.1 严格二元

| 值 | 用途 | Tailwind 类 |
|----|------|------------|
| `12px` | 非交互容器：卡片、对话框、代码块 | `rounded-xl` |
| `9999px` | 交互元素：按钮、输入框、标签、tab | `rounded-full` |

### 3.2 废弃

- `rounded-sm` (6px) → `rounded-xl` 或 `rounded-full`
- `rounded-md` (8px) → `rounded-full`（交互元素）或 `rounded-xl`（容器）
- `rounded-lg` (8px in Tailwind) → `rounded-xl`（容器）或 `rounded-full`（交互）
- `rounded-2xl` (24px) → `rounded-xl`
- `rounded-[20px]` → `rounded-xl`

## 4. 阴影系统

**零阴影**。所有阴影相关定义和使用全部移除：

- tokens.css 中的 `--shadow-sm/md/lg`、`--shadow-glow-primary/accent`
- index.css 中的 `.glow-primary`、`.glow-accent` 工具类
- 所有组件中的 `shadow-*` Tailwind 类
- `backdrop-filter: blur()` 玻璃效果

深度通过背景色差（`#fff` vs `#fafafa`）和 `1px solid #e5e5e5` 边框传达。

## 5. 核心组件规范

### 5.1 按钮 (Button)

| 变体 | 背景 | 文字 | 边框 | 用途 |
|------|------|------|------|------|
| default (Gray Pill) | `#e5e5e5` | `#262626` | `1px solid #e5e5e5` | 主要操作 |
| outline (White Pill) | `#ffffff` | `#404040` | `1px solid #d4d4d4` | 次要操作 |
| cta (Black Pill) | `#000000` | `#ffffff` | `1px solid #000` | 强调操作 |
| ghost | transparent | `#737373` | none | 轻量操作 |
| destructive | `#ef4444` | `#ffffff` | `1px solid #ef4444` | 危险操作 |
| link | transparent | `#000000` | none | 链接式 |

统一规范：
- 圆角：`rounded-full` (9999px)
- Padding：`10px 24px`（h-10 px-6）
- 零阴影、零过渡动画
- Focus：`ring-2 ring-[#3b82f6]/50`
- Hover：仅背景色变化，无 scale/glow
- 禁用：`opacity-50 pointer-events-none`

### 5.2 卡片 (Card)

| 变体 | 背景 | 边框 |
|------|------|------|
| default | `#ffffff` | `1px solid #e5e5e5` |
| snow | `#fafafa` | `1px solid #e5e5e5` |

统一规范：
- 圆角：`rounded-xl` (12px)
- 零阴影
- Padding：`p-6` (24px)

### 5.3 输入框 (Input / Select / SearchableSelect)

- 背景：`#ffffff`
- 边框：`1px solid #e5e5e5`
- 圆角：`rounded-full` (9999px)
- Placeholder：`#a3a3a3`
- Focus：`border-black` + `ring-2 ring-[#3b82f6]/50`
- 移除暗色背景 `#1a1a2e`

### 5.4 对话框 (Dialog)

- 背景：`#ffffff`
- 边框：`1px solid #e5e5e5`
- 圆角：`rounded-xl` (12px)
- 遮罩：`rgba(0,0,0,0.3)`
- 零阴影

### 5.5 Toast

- 背景：`#ffffff`
- 边框：`1px solid #e5e5e5`
- 圆角：`rounded-xl` (12px)
- 零阴影

### 5.6 标签 (Badge)

- 圆角：`rounded-full` (9999px)
- 默认：`bg-[#e5e5e5] text-[#262626]`
- 状态变体保留对应状态色

### 5.7 StatCard (统计卡片)

- 白色卡片 + 灰度图标区
- 零阴影、零发光
- 数值：`text-black`，状态相关用状态色
- 圆角：`rounded-xl` (12px)

## 6. 布局规范

### 6.1 DashboardLayout（主布局）

| 区域 | 重构后 |
|------|--------|
| 侧边栏 | `#ffffff` + `border-r border-[#e5e5e5]` |
| 侧边栏文字 | `#737373`，激活项 `#000` |
| 导航项 | `rounded-full` + hover `bg-[#fafafa]` |
| 激活导航项 | `bg-[#e5e5e5]` + `text-[#000]` |
| 顶部栏 | `#ffffff` + `border-b border-[#e5e5e5]` |
| 内容区背景 | `#fafafa` |

### 6.2 移动端组件

| 组件 | 重构后 |
|------|--------|
| BottomNav | `#ffffff` + `border-t border-[#e5e5e5]` |
| MobileDrawer | `#ffffff` + 右边框 |
| MobilePicker | `#ffffff` + `rounded-t-xl` |

## 7. 页面规范

### 7.1 登录页 (LoginPage)

- 纯白 `#ffffff` 全屏背景
- 居中卡片：`rounded-xl`、`border-[#e5e5e5]`、零阴影
- 角色选择：三个药丸形按钮，激活 = `#e5e5e5` 背景
- 输入框：`rounded-full`、`border-[#e5e5e5]`
- 登录按钮：Black Pill CTA

### 7.2 各角色仪表盘（Admin/Teacher/Student）

- 页面背景：`#fafafa`
- 卡片：`bg-white border border-[#e5e5e5] rounded-xl`
- 标题：`text-black font-medium`（weight 500）
- 次要文字：`text-[#737373]`
- 移除所有 `shadow-*` 和 `bg-gradient-*`

### 7.3 签到页面 (Checkin)

- 状态用语义色标识（出勤=绿、迟到=黄、缺勤=红）
- 卡片遵循白色主题规范
- 移除渐变装饰

### 7.4 NotFound / LandingPage

- 移除所有彩色渐变
- 改为纯白+黑色排版

## 8. index.css 清理

- 移除 `.gradient-text` 渐变文字效果
- 移除 `.glow-primary`、`.glow-accent` 发光类
- 移除 safelist 中的彩色类（`from-primary/25`、`via-purple-500` 等）
- 移除 `backdrop-filter: blur()` 玻璃效果
- 保留必要的 `@theme inline` 定义

## 9. 影响文件清单

### 基础层（优先修改）
1. `frontend-v3/src/styles/tokens.css` — 色彩、字体、圆角、阴影 token
2. `frontend-v3/src/styles/components.css` — `.ch-*` 组件基础样式
3. `frontend-v3/src/index.css` — 主题配置、工具类、safelist
4. `frontend-v3/index.html` — 移除外部字体引用、修改关键 CSS

### UI 组件层
5. `frontend-v3/src/components/ui/Button.vue`
6. `frontend-v3/src/components/ui/Card.vue`
7. `frontend-v3/src/components/ui/Input.vue`
8. `frontend-v3/src/components/ui/Select.vue`
9. `frontend-v3/src/components/ui/Dialog.vue`
10. `frontend-v3/src/components/ui/Toast.vue`
11. `frontend-v3/src/components/ui/Badge.vue`
12. `frontend-v3/src/components/ui/StatCard.vue`
13. `frontend-v3/src/components/ui/Checkbox.vue`
14. `frontend-v3/src/components/ui/SearchableSelect.vue`
15. `frontend-v3/src/components/ui/MobilePicker.vue`
16. `frontend-v3/src/components/ui/MobileDrawer.vue`
17. `frontend-v3/src/components/ui/BottomNav.vue`
18. `frontend-v3/src/components/ui/NetworkErrorBanner.vue`

### 布局
19. `frontend-v3/src/layouts/DashboardLayout.vue`

### 页面视图
20. `frontend-v3/src/views/LoginPage.vue`
21. `frontend-v3/src/views/LandingPage.vue`
22. `frontend-v3/src/views/NotFound.vue`
23. `frontend-v3/src/views/admin/Dashboard.vue`
24. `frontend-v3/src/views/admin/Students.vue`
25. `frontend-v3/src/views/admin/Teachers.vue`
26. `frontend-v3/src/views/admin/Classes.vue`
27. `frontend-v3/src/views/teacher/Dashboard.vue`
28. `frontend-v3/src/views/teacher/Students.vue`
29. `frontend-v3/src/views/teacher/Checkin.vue`
30. `frontend-v3/src/views/teacher/CourseSession.vue`
31. `frontend-v3/src/views/teacher/Schedules.vue`
32. `frontend-v3/src/views/teacher/SessionsHistory.vue`
33. `frontend-v3/src/views/student/Dashboard.vue`
34. `frontend-v3/src/views/student/Checkin.vue`
35. `frontend-v3/src/views/student/Leaderboard.vue`

### 特性组件
36. `frontend-v3/src/components/teacher/StudentCheckinGrid.vue`
37. `frontend-v3/src/components/teacher/CheckinStats.vue`
38. `frontend-v3/src/components/teacher/ScheduleAdjustmentDialog.vue`
39. `frontend-v3/src/components/teacher/ManageSchedulesDialog.vue`（如存在）
40. `frontend-v3/src/components/admin/ManageSchedulesDialog.vue`
41. `frontend-v3/src/components/admin/ManageClassesDialog.vue`
42. `frontend-v3/src/features/students/components/StudentCard.vue`
43. `frontend-v3/src/features/students/components/StudentFilters.vue`
44. `frontend-v3/src/features/students/components/QuickScoreButton.vue`

### 文档
45. `frontend-v3/DESIGN_SYSTEM.md` — 重写为新设计系统文档

## 10. 验证清单

重构完成后验证：
- [ ] 页面背景为纯白色 (#ffffff)
- [ ] 主要文字为纯黑色 (#000000)
- [ ] 按钮使用药丸形状 (rounded-full)
- [ ] 卡片使用 rounded-xl (12px)
- [ ] 无阴影效果
- [ ] 边框为 1px solid #e5e5e5
- [ ] 字重只有 400 或 500
- [ ] 无渐变背景
- [ ] 无 hover scale/glow 动画
- [ ] 状态色仅用于数据/状态指示
- [ ] 移动端同步白色主题
- [ ] 无外部字体依赖
- [ ] 所有测试通过
