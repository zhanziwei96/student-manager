# ClassHub 设计体系 (Design System)

---

**文档版本**: v3.0.0  
**最后更新**: 2026-04-10  
**适用版本**: v3.0.0+  
**状态**: 已同步代码 (Ollama 白色主题)

---

## 1. 设计原则

### 1.1 核心设计理念
- **白色优先**: 以纯净白色为基底，营造简洁、明亮、专业的视觉体验
- **极简主义**: 去除冗余装饰（渐变、发光、毛玻璃、复杂阴影），内容即焦点
- **清晰层级**: 通过颜色深浅（黑/灰/浅灰）和微妙边框建立空间层次
- **高可读性**: 深色文字在白色背景上提供最佳阅读体验

### 1.2 设计关键词
`简洁` `专业` `明亮` `现代` `高效`

---

## 2. 色彩系统

### 2.1 主色调 (Primary)
| Token | 值 | 用途 |
|-------|-----|------|
| `--color-primary` | `#000000` | 标题、主按钮文字、链接高亮 |
| `--color-primary-foreground` | `#ffffff` | 深色背景上的文字 |
| `--color-primary-hover` | `#737373` | 主色悬停状态 |
| `--color-primary-muted` | `#e5e5e5` | 图标容器背景、次级按钮背景 |

### 2.2 背景色 (Background)
| Token | 值 | 用途 |
|-------|-----|------|
| `--color-background` | `#ffffff` | 页面主背景、卡片背景 |
| `--color-background-elevated` | `#fafafa` | 抬升表面、悬停背景 |
| `--color-background-card` | `#ffffff` | 卡片内容区 |
| `--color-background-hover` | `#f5f5f5` | 悬停背景、斑马纹 |

### 2.3 文字色 (Foreground)
| Token | 值 | 用途 |
|-------|-----|------|
| `--color-text-primary` | `#000000` / `#262626` | 标题、重要文字 |
| `--color-text-secondary` | `#737373` | 正文、描述、标签 |
| `--color-text-tertiary` | `#a3a3a3` | 辅助信息、时间戳、占位符 |
| `--color-text-muted` | `#737373` | 禁用状态提示 |

### 2.4 边框色 (Border)
| Token | 值 | 用途 |
|-------|-----|------|
| `--color-border` | `#e5e5e5` | 卡片边框、分隔线、输入框边框 |
| `--color-border-hover` | `#d4d4d4` | 悬停边框 |
| `--color-border-focus` | `#3b82f6` | 聚焦状态环 |

### 2.5 状态色 (Status)
状态色保留原有语义，但改为在白色背景上使用低饱和背景：
| Token | 文字色 | 背景色 | 边框色 | 用途 |
|-------|--------|--------|--------|------|
| `success` | `#22c55e` | `#22c55e/15` | `#22c55e/30` | 成功、已签到 |
| `warning` | `#f97316` | `#f97316/15` | `#f97316/30` | 警告、待处理 |
| `error` | `#ef4444` | `#ef4444/15` | `#ef4444/30` | 错误、冲突 |
| `info` | `#3b82f6` | `#3b82f6/15` | `#3b82f6/30` | 信息提示 |

---

## 3. 全局替换规则

所有页面视图重构时遵循以下 Tailwind 类名替换规则：

| 旧值（暗色） | 新值（Ollama 白色） |
|---|---|
| `bg-background` | `bg-white` |
| `bg-background-elevated` | `bg-[#fafafa]` |
| `bg-[#030307]` | `bg-white` |
| `bg-[#0a0a0f]` | `bg-white` |
| `bg-white/[0.02]` | `bg-white` |
| `bg-white/5` | `bg-white` |
| `bg-white/10` | `bg-[#fafafa]` |
| `bg-white/20` | `bg-[#f5f5f5]` |
| `text-white` (非按钮) | `text-black` |
| `text-white/70` | `text-[#737373]` |
| `text-white/50` | `text-[#a3a3a3]` |
| `text-white/40` | `text-[#a3a3a3]` |
| `border-white/10` | `border-[#e5e5e5]` |
| `border-white/20` | `border-[#d4d4d4]` |
| `hover:bg-white/10` | `hover:bg-[#fafafa]` |
| `hover:bg-white/20` | `hover:bg-[#f5f5f5]` |
| `font-bold` | `font-medium` |
| `font-semibold` | `font-medium` |
| `rounded-md` (按钮/输入) | `rounded-full` |
| `rounded-md` (容器) | `rounded-xl` |
| `rounded-lg` (按钮/输入) | `rounded-full` |
| `rounded-lg` (容器) | `rounded-xl` |
| `rounded-2xl` | `rounded-xl` |

**需删除的效果：**
- `shadow-sm/md/lg/xl/2xl` -> 删除
- `shadow-inner` -> 删除
- `shadow-glow-primary/glow-accent` -> 删除
- `backdrop-blur-sm/backdrop-blur-lg` -> 删除
- `bg-gradient-to-*` 及 `from-*` `via-*` `to-*` -> 删除（时间线等可替换为纯色）
- `hover:scale-[1.02]` / `group-hover:scale-110` -> 删除
- `active:scale-[0.98]` -> 删除
- `transition-all duration-150` -> 删除或改为 `transition-colors`

**保留不动的：**
- 状态色类名：`text-success`、`bg-success/10` 等保留
- `rounded-full` (已经是药丸形) 保留
- `rounded-xl` (12px 容器圆角) 保留
- 所有功能性逻辑代码和 TypeScript 类型不动

---

## 4. 排版系统

### 4.1 字体
- **主字体**: system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif
- **字重规范**: 统一使用 `font-medium`（500），避免 `font-bold`（700）和 `font-semibold`（600）
- **行高**: 正文 `leading-relaxed` (1.625)，标题 `leading-tight` (1.25)

### 4.2 字号层级
| 层级 | Tailwind | 用途 |
|------|----------|------|
| 页面标题 | `text-2xl font-medium` | 页面级 H1 |
| 区块标题 | `text-lg font-medium` | 卡片标题、分组标题 |
| 正文 | `text-sm` | 列表、描述 |
| 辅助文字 | `text-xs` | 标签、时间戳、Badge |

---

## 5. 组件规范

### 5.1 Button
- **形状**: 所有按钮统一使用 `rounded-full`（药丸形）
- **主按钮**: `bg-black text-white hover:bg-[#262626]`
- **次级按钮**: `bg-[#e5e5e5] text-black hover:bg-[#d4d4d4]`
- **幽灵按钮**: `bg-transparent border border-[#e5e5e5] text-black hover:bg-[#fafafa]`
- **危险按钮**: `bg-red-500 text-white hover:bg-red-600`

### 5.2 Card
- **背景**: `bg-white`
- **边框**: `border border-[#e5e5e5]`
- **圆角**: `rounded-xl`
- **无阴影**: 不使用任何 shadow 类

### 5.3 Input / Select
- **形状**: 按钮和输入框使用 `rounded-full`，容器使用 `rounded-xl`
- **边框**: `border border-[#e5e5e5]`
- **聚焦**: `focus:border-[#3b82f6] focus:ring-[#3b82f6]/50`
- **背景**: `bg-white`

### 5.4 Badge
- **形状**: `rounded-full px-2.5 py-0.5 text-xs font-medium`
- **default**: `bg-[#e5e5e5] text-[#262626]`
- **secondary**: `bg-[#fafafa] text-[#737373]`
- **outline**: `border border-[#e5e5e5] text-[#737373] bg-transparent`
- **success/error/warning/info**: 对应状态色低饱和背景

### 5.5 图标容器
- **背景**: `bg-primary/10`（即 `#e5e5e5`）
- **图标色**: `text-primary`（即 `text-black`）
- **圆角**: `rounded-full` 或 `rounded-xl`
- **尺寸**: 默认 `h-10 w-10`

---

## 6. 布局规范

### 6.1 页面边距
- 桌面端: `px-6 py-5`
- 移动端: `px-4 py-4`

### 6.2 间距
- 区块间距: `space-y-5`
- 卡片内间距: `p-4` 到 `p-6`
- 元素间隙: `gap-3` 或 `gap-4`

### 6.3 侧边栏
- **桌面**: `w-64 bg-white border-r border-[#e5e5e5]`
- **移动端**: 抽屉式导航，白色背景

---

## 7. 反模式清单

以下效果在 Ollama 白色主题中被明确移除，禁止在新代码中使用：

- `blur-2xl` 发光装饰背景
- `shadow-glow-*` 任何发光阴影
- `backdrop-blur` 毛玻璃效果
- `bg-gradient-to-*` 渐变色背景
- `group-hover:scale-110` 缩放动画
- `text-white` 在普通文字上（按钮除外）
- `border-white/10` 任何基于白色透明的边框
- 通过 `getCardStyle()` 等运行时 JS 函数注入样式

---

## 8. 文件索引

| 文件 | 说明 |
|------|------|
| `src/styles/tokens.css` | CSS 设计 Token（颜色、圆角、间距） |
| `src/styles/index.css` | 全局基础样式、Tailwind v4 主题导入 |
| `src/styles/components.css` | 组件级基础样式覆盖 |
| `src/components/ui/*.vue` | 核心 UI 组件（Button、Card、Input、Badge 等） |

---

## 相关文档

| 文档 | 说明 |
|------|------|
| [前端架构](./docs/ARCHITECTURE.md) | 前端代码架构（Feature-based、状态管理、测试） |
| [架构图](../docs/ARCHITECTURE_DIAGRAMS.md) | 系统架构图与前端状态管理图 |
| [CLAUDE.md](../CLAUDE.md) | 前端开发约束与规范 |

---

**注：所有前端开发必须遵循此设计体系，确保视觉一致性。**
