# ClassHub Ollama 设计系统重构方案

> 将 ClassHub 从深色科技风（#030307/#6366f1）重构为 Ollama 风格的极简白色主题

---

## 1. 设计目标

完全遵循 Ollama 设计哲学：
- **纯粹极简**: 纯白色背景，零装饰
- **二元系统**: 仅 12px（容器）和 9999px（交互）两种圆角
- **零阴影**: 层次通过背景和边框区分
- **即时交互**: 无动画、无过渡

---

## 2. 色彩系统（灰度唯一）

| 变量名 | 色值 | 用途 |
|--------|------|------|
| `--color-pure-black` | `#000000` | 主标题、主链接 |
| `--color-near-black` | `#262626` | 浅底按钮文字 |
| `--color-mid-gray` | `#525252` | 强调次要文字 |
| `--color-stone` | `#737373` | 次要正文、页脚链接 |
| `--color-silver` | `#a3a3a3` | 第三级文字、占位符 |
| `--color-button-text-dark` | `#404040` | 白底按钮文字 |
| `--color-darkest-surface` | `#090909` | 最深表面（页脚） |
| `--color-pure-white` | `#ffffff` | 页面背景、次按钮 |
| `--color-snow` | `#fafafa` | 卡片背景、区块背景 |
| `--color-light-gray` | `#e5e5e5` | 主按钮背景、边框 |
| `--color-border-light` | `#d4d4d4` | 白底按钮边框 |
| `--color-ring-blue` | `#3b82f6` | 聚焦环（唯一非灰色，50%透明度） |

**约束**: 零渐变色、零彩色、边框不超过 1px

---

## 3. 字体系统

### 字体族

```css
/* Display 字体 - 标题 */
--font-display: ui-rounded, 'SF Pro Rounded', -apple-system, 'PingFang SC', 'Microsoft YaHei', sans-serif;

/* Body 字体 - 正文 */
--font-body: ui-sans-serif, system-ui, -apple-system, 'PingFang SC', 'Microsoft YaHei', sans-serif;

/* Monospace 字体 - 代码 */
--font-mono: ui-monospace, 'SFMono-Regular', 'Menlo', 'Monaco', 'Consolas', 'Liberation Mono', 'Courier New', monospace;
```

### 字体层级

| 层级 | 字体 | 大小 | 字重 | 行高 | 字间距 |
|------|------|------|------|------|--------|
| Display/Hero | Display | 48px | 500 | 1.00 | normal |
| Section Heading | Display | 36px | 500 | 1.11 | normal |
| Sub-heading | Display/Body | 30px | 400-500 | 1.20 | normal |
| Card Title | Body | 24px | 400 | 1.33 | normal |
| Body Large | Body | 18px | 400-500 | 1.56 | normal |
| Body/Link | Body | 16px | 400-500 | 1.50 | normal |
| Caption | Body | 14px | 400 | 1.43 | normal |
| Small | Body | 12px | 400 | 1.33 | normal |
| Code Body | Mono | 16px | 400 | 1.50 | normal |
| Code Caption | Mono | 14px | 400 | 1.43 | normal |
| Code Small | Mono | 12px | 400-700 | 1.63 | normal |

**约束**: 仅使用 400 和 500 字重，不使用 bold (700)

---

## 4. 圆角系统（严格二元）

| 类型 | 值 | 用途 |
|------|-----|------|
| 容器圆角 | `12px` | 卡片、代码块、面板（唯一非 pill） |
| 交互圆角 | `9999px` | 按钮、输入框、标签、标签页、徽章 |

**约束**: 不使用 4px、6px、8px 或其他中间值

---

## 5. 组件规范

### 按钮（所有按钮 padding: 10px 24px，radius: 9999px）

**Gray Pill (Primary)**
- 背景: `#e5e5e5`
- 文字: `#262626`
- 边框: `1px solid #e5e5e5`
- 圆角: `9999px`

**White Pill (Secondary)**
- 背景: `#ffffff`
- 文字: `#404040`
- 边框: `1px solid #d4d4d4`
- 圆角: `9999px`

**Black Pill (CTA)**
- 背景: `#000000`
- 文字: `#ffffff`
- 圆角: `9999px`

### 卡片
- 背景: `#ffffff` 或 `#fafafa`
- 边框: `1px solid #e5e5e5`
- 圆角: `12px`
- 内边距: 24px-32px
- 阴影: **无**

### 输入框
- 背景: `#ffffff`
- 边框: `1px solid #e5e5e5`
- 圆角: `9999px`（pill-shaped）
- 聚焦环: `#3b82f6` 50%
- 占位符: `#a3a3a3`

### Tab Pills
- 形状: 药丸形 (`9999px`)
- 激活: Light Gray (`#e5e5e5`) 背景
- 未激活: 透明背景

### Model Tags
- 形状: 小药丸形 (`9999px`)
- 背景: Light Gray (`#e5e5e5`)
- 文字: 深色

### Terminal Command Block
- 字体: ui-monospace 16px
- 容器: 12px 圆角
- 边框: `1px solid #e5e5e5`
- 复制按钮集成

---

## 6. 布局系统

| 属性 | 值 |
|------|-----|
| 基础间距单位 | 8px |
| 按钮内边距 | 10px 24px（严格一致） |
| 卡片内边距 | 24px-32px |
| 区块垂直间距 | 88px-112px |
| 最大容器宽度 | 1024px-1280px，居中 |

---

## 7. 交互约束

- **零阴影**: 所有元素不使用阴影
- **无 hover 动画**: 无过渡效果
- **即时响应**: 交互感觉即时和直接
- **无渐变色**: 绝对不使用渐变
- **纯灰度**: 除 Ring Blue 聚焦环外不使用彩色
- **边框限制**: 不超过 1px

---

## 8. 需要重构的页面

### 所有页面（完整列表）

| 页面 | 路径 |
|------|------|
| 登录页 | `frontend-v3/src/views/LoginPage.vue` |
| 落地页 | `frontend-v3/src/views/LandingPage.vue` |
| 404页 | `frontend-v3/src/views/NotFound.vue` |
| 管理员-仪表盘 | `frontend-v3/src/views/admin/Dashboard.vue` |
| 管理员-学生管理 | `frontend-v3/src/views/admin/Students.vue` |
| 管理员-教师管理 | `frontend-v3/src/views/admin/Teachers.vue` |
| 管理员-班级管理 | `frontend-v3/src/views/admin/Classes.vue` |
| 管理员-签到记录 | `frontend-v3/src/views/admin/Checkins.vue` |
| 教师-仪表盘 | `frontend-v3/src/views/teacher/Dashboard.vue` |
| 教师-学生管理 | `frontend-v3/src/views/teacher/Students.vue` |
| 教师-课程表 | `frontend-v3/src/views/teacher/Schedules.vue` |
| 教师-课堂会话 | `frontend-v3/src/views/teacher/CourseSession.vue` |
| 教师-历史记录 | `frontend-v3/src/views/teacher/SessionsHistory.vue` |
| 学生-仪表盘 | `frontend-v3/src/views/student/Dashboard.vue` |
| 学生-签到 | `frontend-v3/src/views/student/Checkin.vue` |
| 学生-排行榜 | `frontend-v3/src/views/student/Leaderboard.vue` |

### 需要更新的组件

| 组件 | 路径 |
|------|------|
| Button | `frontend-v3/src/components/ui/Button.vue` |
| Card | `frontend-v3/src/components/ui/Card.vue` |
| Input | `frontend-v3/src/components/ui/Input.vue` |
| Badge | `frontend-v3/src/components/ui/Badge.vue` |
| Select | `frontend-v3/src/components/ui/Select.vue` |
| Dialog | `frontend-v3/src/components/ui/Dialog.vue` |
| StatCard | `frontend-v3/src/components/ui/StatCard.vue` |
| BottomNav | `frontend-v3/src/components/ui/BottomNav.vue` |

### 需要更新的样式文件

| 文件 | 路径 |
|------|------|
| Tokens | `frontend-v3/src/styles/tokens.css` |
| Components | `frontend-v3/src/styles/components.css` |

---

## 9. 变更清单

### CSS 变量变更

| 旧变量 | 旧值 | 新变量 | 新值 |
|--------|------|--------|------|
| `--color-background` | `#030307` | `--color-background` | `#ffffff` |
| `--color-primary` | `#6366f1` | `--color-primary` | `#e5e5e5` |
| `--color-text-primary` | `#ffffff` | `--color-text-primary` | `#000000` |
| `--color-text-secondary` | `rgba(255,255,255,0.7)` | `--color-text-secondary` | `#737373` |
| `--radius-md` | `0.5rem` | `--radius-container` | `12px` |
| `--radius-full` | `9999px` | `--radius-pill` | `9999px` |

### 类名映射（Tailwind）

| 旧类名 | 新类名 |
|--------|--------|
| `bg-[#030307]` | `bg-white` |
| `bg-primary` | `bg-[#e5e5e5]` |
| `text-white` | `text-black` |
| `text-white/70` | `text-[#737373]` |
| `rounded-md` | `rounded-xl` (12px) |
| `rounded-lg` | `rounded-xl` (12px) |
| `rounded-full` | `rounded-full` (9999px) |
| `shadow-md` | **移除** |
| `border-white/10` | `border-[#e5e5e5]` |

---

## 10. 设计约束检查清单

实施时必须验证:

- [ ] 所有颜色都是灰度（除 Ring Blue 聚焦环）
- [ ] 不使用任何渐变
- [ ] 不使用任何阴影
- [ ] 圆角只有 12px 或 9999px
- [ ] 字重只有 400 或 500
- [ ] 按钮 padding 严格 10px 24px
- [ ] 无边框超过 1px
- [ ] 无 hover 动画或过渡
- [ ] 区块间距 88px-112px

---

*设计文档版本: 1.0.0*
*创建日期: 2026-04-09*
