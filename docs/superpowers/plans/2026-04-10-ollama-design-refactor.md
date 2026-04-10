# Ollama 设计系统前端重构实施计划

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 将 ClassHub 前端从暗色主题全面重构为 Ollama 风格极简白色主题

**Architecture:** 分层重构——先改 CSS Token 基础层，再改 UI 组件，再改布局，最后逐个改页面视图。每层改完 commit 一次。

**Tech Stack:** Vue 3, Tailwind CSS v4, TypeScript

**设计规格:** `docs/superpowers/specs/2026-04-10-ollama-design-refactor.md`

---

## 全局颜色映射规则

所有页面视图重构时遵循以下 Tailwind 类名替换规则：

| 旧值（暗色） | 新值（Ollama 白色） |
|---|---|
| `bg-background` | `bg-white` |
| `bg-background-elevated` | `bg-[#fafafa]` |
| `bg-[#030307]` | `bg-white` |
| `bg-[#0a0a0f]` | `bg-white` |
| `bg-[#1a1a2e]` | `bg-white` |
| `bg-white/[0.02]` | `bg-white` |
| `bg-white/[0.05]` | `bg-white` |
| `bg-white/5` | `bg-white` |
| `bg-white/10` | `bg-[#fafafa]` |
| `bg-white/20` | `bg-[#f5f5f5]` |
| `text-white` (非按钮) | `text-black` |
| `text-white/70` | `text-[#737373]` |
| `text-white/50` | `text-[#a3a3a3]` |
| `text-white/40` | `text-[#a3a3a3]` |
| `text-text-secondary` | `text-[#737373]` (token 会自动更新) |
| `border-white/10` | `border-[#e5e5e5]` |
| `border-white/15` | `border-[#e5e5e5]` |
| `border-white/20` | `border-[#d4d4d4]` |
| `border-border` | `border-[#e5e5e5]` (token 会自动更新) |
| `text-primary` (原 indigo) | `text-black` (token 会自动更新为 #000) |
| `bg-primary/10` 或 `bg-primary/20` | `bg-[#e5e5e5]` |
| `shadow-sm/md/lg/xl/2xl` | 删除 |
| `shadow-inner` | 删除 |
| `shadow-glow-primary` | 删除 |
| `shadow-glow-accent` | 删除 |
| `backdrop-blur-sm` 或 `backdrop-blur-lg` | 删除 |
| `bg-gradient-to-*` 及 `from-*` `via-*` `to-*` | 删除整行 |
| `font-bold` | `font-medium` |
| `font-semibold` | `font-medium` |
| `rounded-md` (按钮/输入) | `rounded-full` |
| `rounded-md` (容器) | `rounded-xl` |
| `rounded-lg` (按钮/输入) | `rounded-full` |
| `rounded-lg` (容器) | `rounded-xl` |
| `rounded-2xl` | `rounded-xl` |
| `rounded-[20px]` | `rounded-xl` |
| `hover:bg-white/10` | `hover:bg-[#fafafa]` |
| `hover:bg-white/20` | `hover:bg-[#f5f5f5]` |
| `hover:shadow-glow-primary` | 删除 |
| `hover:scale-[1.02]` | 删除 |
| `active:scale-[0.98]` | 删除 |
| `transition-all duration-150` | 删除或改为 `transition-colors` |
| `ring-primary/50` | `ring-[#3b82f6]/50` |
| `bg-black/80` (遮罩) | `bg-black/30` |

**保留不动的：**
- 状态色类名：`text-success`、`bg-success/10`、`border-success/30` 等保留
- `rounded-full` (已经是药丸形) 保留
- `rounded-xl` (12px 容器) 保留
- 所有功能性逻辑代码不动
- 所有 TypeScript 接口/类型不动

---

## Task 1: tokens.css

**Files:**
- Modify: `frontend-v3/src/styles/tokens.css`

- [x] **Step 1: 替换 tokens.css 全部内容**

```css
/**
 * ClassHub Ollama 设计系统 - CSS Tokens
 * 版本: 3.0.0 (Tailwind v4)
 */

@theme inline {
  /* ========== 响应式断点 ========== */
  --breakpoint-sm: 640px;
  --breakpoint-md: 768px;
  --breakpoint-lg: 1024px;
  --breakpoint-xl: 1280px;

  /* ========== 触摸目标标准 ========== */
  --touch-target-min: 2.75rem;
  --touch-target-comfort: 3rem;

  /* ========== Ollama 色彩系统 ========== */

  /* 背景色 */
  --color-background: #ffffff;
  --color-background-elevated: #fafafa;
  --color-background-card: #ffffff;
  --color-background-hover: #fafafa;
  --color-background-active: #f5f5f5;

  /* 文字色 */
  --color-text-primary: #000000;
  --color-text-secondary: #737373;
  --color-text-tertiary: #a3a3a3;
  --color-text-muted: #a3a3a3;
  --color-text-placeholder: #a3a3a3;

  /* 主色（灰度系） */
  --color-primary: #000000;
  --color-primary-foreground: #ffffff;
  --color-primary-hover: #262626;
  --color-primary-muted: #e5e5e5;

  /* 边框 */
  --color-border: #e5e5e5;
  --color-border-hover: #d4d4d4;
  --color-border-focus: #000000;
  --color-divider: #f5f5f5;

  /* 状态色 */
  --color-success: #22c55e;
  --color-success-muted: rgba(34, 197, 94, 0.15);
  --color-warning: #f59e0b;
  --color-warning-muted: rgba(245, 158, 11, 0.15);
  --color-error: #ef4444;
  --color-error-muted: rgba(239, 68, 68, 0.15);
  --color-info: #3b82f6;
  --color-info-muted: rgba(59, 130, 246, 0.15);

  /* ========== 字体系统 ========== */
  --font-sans: ui-sans-serif, system-ui, -apple-system, 'PingFang SC', 'Microsoft YaHei', sans-serif;
  --font-mono: ui-monospace, 'SFMono-Regular', Menlo, Consolas, 'Liberation Mono', monospace;

  /* ========== 圆角系统（严格二元） ========== */
  --radius-container: 0.75rem;
  --radius-full: 9999px;

  /* ========== 过渡时间 ========== */
  --duration-instant: 100ms;
  --duration-fast: 150ms;
  --duration-normal: 200ms;
  --duration-slow: 300ms;
  --duration-slower: 500ms;

  /* ========== Z-Index 层级 ========== */
  --z-base: 0;
  --z-dropdown: 10;
  --z-sticky: 20;
  --z-fixed: 30;
  --z-modal-backdrop: 40;
  --z-modal: 50;
  --z-popover: 60;
  --z-tooltip: 70;
  --z-toast: 80;
}

/* ========== CSS 变量导出 ========== */
:root {
  --color-background: #ffffff;
  --color-text-primary: #000000;
  --color-text-secondary: #737373;
  --color-border: #e5e5e5;
}
```

- [x] **Step 2: Commit**

```bash
git add frontend-v3/src/styles/tokens.css
git commit -m "refactor(styles): 重写 tokens.css 为 Ollama 白色主题"
```

---

## Task 2: index.html

**Files:**
- Modify: `frontend-v3/index.html`

- [x] **Step 1: 替换 index.html 全部内容**

```html
<!DOCTYPE html>
<html lang="zh-CN">
  <head>
    <meta charset="UTF-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no, viewport-fit=cover" />
    <title>ClassHub</title>
    <style>
      html { background-color: #ffffff; }
      body {
        margin: 0;
        padding: 0;
        padding-top: env(safe-area-inset-top);
        padding-bottom: env(safe-area-inset-bottom);
        -webkit-font-smoothing: antialiased;
        -moz-osx-font-smoothing: grayscale;
      }
      /* 防止 iOS 输入框缩放 */
      @supports (-webkit-touch-callout: none) {
        input, select, textarea {
          font-size: 16px !important;
        }
      }
    </style>
    <script type="text/javascript">
      window._AMapSecurityConfig = { securityJsCode: 'd97e2a73a5e840b30a063cf4b5a0797c' }
    </script>
    <script type="text/javascript" src="https://webapi.amap.com/maps?v=2.0&key=8d3e99a8b3b40c1b3c60b4e3b3e7c9c0"></script>
  </head>
  <body>
    <div id="app"></div>
    <script type="module" src="/src/main.ts"></script>
  </body>
</html>
```

关键变更：
- 移除 `<html class="dark">` 中的 `dark`
- `lang="en"` → `lang="zh-CN"`
- 删除 Google Fonts Inter 引用
- 背景色 `#030307` → `#ffffff`
- body 颜色删除（跟随 token）
- 保留 AMap 脚本

- [x] **Step 2: Commit**

```bash
git add frontend-v3/index.html
git commit -m "refactor(html): 移除暗色主题和外部字体引用"
```

---

## Task 3: index.css

**Files:**
- Modify: `frontend-v3/src/index.css`

- [x] **Step 1: 替换 index.css 全部内容**

```css
@import "tailwindcss";
@import "./styles/tokens.css";
@import "./styles/components.css";

@theme inline {
  --color-background: #ffffff;
  --color-background-elevated: #fafafa;
  --color-primary: #000000;
  --color-primary-hover: #262626;
  --color-success: #22c55e;
  --color-warning: #f59e0b;
  --color-error: #ef4444;
  --font-sans: ui-sans-serif, system-ui, -apple-system, 'PingFang SC', 'Microsoft YaHei', sans-serif;
  --font-mono: ui-monospace, 'SFMono-Regular', Menlo, Consolas, 'Liberation Mono', monospace;
}

@layer base {
  *, *::before, *::after {
    box-sizing: border-box;
  }

  html {
    scroll-behavior: smooth;
  }

  body {
    font-family: var(--font-sans);
    background-color: #ffffff;
    color: #000000;
    -webkit-font-smoothing: antialiased;
    -moz-osx-font-smoothing: grayscale;
  }
}

/* 自定义滚动条 */
::-webkit-scrollbar {
  width: 6px;
  height: 6px;
}

::-webkit-scrollbar-track {
  background: transparent;
}

::-webkit-scrollbar-thumb {
  background: #d4d4d4;
  border-radius: 9999px;
}

::-webkit-scrollbar-thumb:hover {
  background: #a3a3a3;
}

/* 选中文字 */
::selection {
  background-color: rgba(0, 0, 0, 0.08);
  color: #000000;
}
```

关键变更：
- 删除 `.text-gradient`、`.glass`、`.glow-primary`、`.glow-accent`、`.glow-bg` 工具类
- 删除 `@layer utilities` 中的所有彩色 safelist 类
- 删除所有动画关键帧 (`fade-in`, `slide-in-up`, `spin`, `pulse-glow`)
- 滚动条颜色改为灰色系
- 选中色改为浅灰

- [x] **Step 2: Commit**

```bash
git add frontend-v3/src/index.css
git commit -m "refactor(styles): 清理 index.css，移除渐变/发光/动画"
```

---

## Task 4: components.css

**Files:**
- Modify: `frontend-v3/src/styles/components.css`

- [x] **Step 1: 替换 components.css 全部内容**

```css
/**
 * ClassHub Ollama Design System v3.0.0
 * 组件基础样式 - 白色主题
 */

/* ========== Buttons ========== */
.ch-button {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  gap: 0.5rem;
  white-space: nowrap;
  font-weight: 500;
  font-size: 0.875rem;
  line-height: 1.25rem;
  padding: 0.625rem 1.5rem;
  border-radius: 9999px;
  border: 1px solid #e5e5e5;
  background-color: #e5e5e5;
  color: #262626;
  cursor: pointer;
  outline: none;
}

.ch-button:focus-visible {
  box-shadow: 0 0 0 2px rgba(59, 130, 246, 0.5);
}

.ch-button:hover {
  background-color: #d4d4d4;
}

.ch-button:disabled {
  opacity: 0.5;
  cursor: not-allowed;
  pointer-events: none;
}

.ch-button--outline {
  background-color: #ffffff;
  border-color: #d4d4d4;
  color: #404040;
}

.ch-button--outline:hover {
  background-color: #fafafa;
}

.ch-button--ghost {
  background-color: transparent;
  border-color: transparent;
  color: #737373;
}

.ch-button--ghost:hover {
  color: #000000;
  background-color: #fafafa;
}

.ch-button--destructive {
  background-color: #ef4444;
  border-color: #ef4444;
  color: #ffffff;
}

.ch-button--destructive:hover {
  background-color: #dc2626;
}

.ch-button--sm {
  height: 2rem;
  padding: 0.375rem 1rem;
  font-size: 0.75rem;
}

.ch-button--lg {
  height: 2.75rem;
  padding: 0.625rem 2rem;
  font-size: 1rem;
}

/* ========== Cards ========== */
.ch-card {
  background-color: #ffffff;
  border: 1px solid #e5e5e5;
  border-radius: 0.75rem;
  padding: 1.5rem;
}

.ch-card--elevated {
  background-color: #fafafa;
}

.ch-card--active {
  background-color: #fafafa;
  border-color: #d4d4d4;
}

/* ========== Inputs ========== */
.ch-input {
  display: flex;
  width: 100%;
  height: 2.25rem;
  border-radius: 9999px;
  border: 1px solid #e5e5e5;
  background-color: #ffffff;
  padding: 0.5rem 0.75rem;
  font-size: 0.875rem;
  color: #000000;
  outline: none;
}

.ch-input::placeholder {
  color: #a3a3a3;
}

.ch-input:hover {
  border-color: #d4d4d4;
}

.ch-input:focus {
  border-color: #000000;
  box-shadow: 0 0 0 2px rgba(59, 130, 246, 0.5);
}

.ch-input:disabled {
  opacity: 0.5;
  cursor: not-allowed;
  background-color: #fafafa;
}

/* ========== Badges ========== */
.ch-badge {
  display: inline-flex;
  align-items: center;
  border-radius: 9999px;
  padding: 0.125rem 0.625rem;
  font-size: 0.75rem;
  font-weight: 500;
  white-space: nowrap;
}

.ch-badge--default {
  background-color: #e5e5e5;
  color: #262626;
}

.ch-badge--success {
  background-color: rgba(34, 197, 94, 0.15);
  color: #16a34a;
}

.ch-badge--warning {
  background-color: rgba(245, 158, 11, 0.15);
  color: #d97706;
}

.ch-badge--error {
  background-color: rgba(239, 68, 68, 0.15);
  color: #dc2626;
}

.ch-badge--info {
  background-color: rgba(59, 130, 246, 0.15);
  color: #2563eb;
}

.ch-badge--outline {
  border: 1px solid #e5e5e5;
  color: #737373;
  background-color: transparent;
}

/* ========== Nav Items ========== */
.ch-nav-item {
  display: flex;
  align-items: center;
  gap: 0.75rem;
  padding: 0.5rem 0.75rem;
  border-radius: 9999px;
  font-size: 0.875rem;
  color: #737373;
  cursor: pointer;
  text-decoration: none;
}

.ch-nav-item:hover {
  background-color: #fafafa;
  color: #000000;
}

.ch-nav-item--active {
  background-color: #e5e5e5;
  color: #000000;
}

/* ========== Tables ========== */
.ch-table {
  width: 100%;
  border-collapse: collapse;
}

.ch-table th {
  text-align: left;
  padding: 0.75rem 1rem;
  font-size: 0.75rem;
  font-weight: 500;
  color: #737373;
  text-transform: uppercase;
  letter-spacing: 0.05em;
  border-bottom: 1px solid #e5e5e5;
}

.ch-table td {
  padding: 0.75rem 1rem;
  font-size: 0.875rem;
  color: #000000;
  border-bottom: 1px solid #f5f5f5;
}

.ch-table tr:hover td {
  background-color: #fafafa;
}

/* ========== Dialogs ========== */
.ch-dialog-overlay {
  position: fixed;
  inset: 0;
  z-index: 50;
  background-color: rgba(0, 0, 0, 0.3);
  display: flex;
  align-items: center;
  justify-content: center;
}

.ch-dialog {
  position: relative;
  width: calc(100vw - 2rem);
  min-width: 28rem;
  max-width: 32rem;
  max-height: 90vh;
  overflow-y: auto;
  border-radius: 0.75rem;
  border: 1px solid #e5e5e5;
  background-color: #ffffff;
  padding: 1.5rem;
}

@media (min-width: 768px) {
  .ch-dialog {
    width: 32rem;
  }
}

/* ========== Toasts ========== */
.ch-toast {
  pointer-events: auto;
  display: flex;
  width: 100%;
  max-width: 24rem;
  align-items: center;
  gap: 0.75rem;
  border-radius: 0.75rem;
  border: 1px solid #e5e5e5;
  background-color: #ffffff;
  padding: 1rem;
  font-size: 0.875rem;
  color: #000000;
}

@media (min-width: 768px) {
  .ch-toast {
    min-width: 20rem;
  }
}

.ch-toast--success {
  background-color: rgba(34, 197, 94, 0.1);
  border-color: rgba(34, 197, 94, 0.3);
  color: #16a34a;
}

.ch-toast--error {
  background-color: rgba(239, 68, 68, 0.1);
  border-color: rgba(239, 68, 68, 0.3);
  color: #dc2626;
}

.ch-toast--warning {
  background-color: rgba(245, 158, 11, 0.1);
  border-color: rgba(245, 158, 11, 0.3);
  color: #d97706;
}

.ch-toast--info {
  background-color: rgba(59, 130, 246, 0.1);
  border-color: rgba(59, 130, 246, 0.3);
  color: #2563eb;
}
```

关键变更：
- 所有 `.ch-*` 组件从暗色改为白色
- 按钮全部 `border-radius: 9999px` (药丸形)
- 卡片 `border-radius: 0.75rem` (12px)
- 输入框 `border-radius: 9999px`
- 移除所有 `box-shadow`（除了 focus ring）
- 移除所有 `backdrop-filter`
- 移除动画关键帧

- [x] **Step 2: Commit**

```bash
git add frontend-v3/src/styles/components.css
git commit -m "refactor(styles): 重写 components.css 为 Ollama 白色主题"
```

---

## Task 5: Button.vue

**Files:**
- Modify: `frontend-v3/src/components/ui/Button.vue`

- [x] **Step 1: 替换 Button.vue 全部内容**

```vue
<script setup lang="ts">
import { computed } from 'vue'
import { cva, type VariantProps } from 'class-variance-authority'
import { cn } from '@/lib/utils'

const buttonVariants = cva(
  'inline-flex items-center justify-center gap-2 whitespace-nowrap font-medium ' +
  'focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-[#3b82f6]/50 ' +
  'disabled:pointer-events-none disabled:opacity-50 disabled:cursor-not-allowed',
  {
    variants: {
      variant: {
        default: 'bg-[#e5e5e5] text-[#262626] border border-[#e5e5e5] hover:bg-[#d4d4d4]',
        outline: 'bg-white text-[#404040] border border-[#d4d4d4] hover:bg-[#fafafa]',
        cta: 'bg-black text-white border border-black hover:bg-[#262626]',
        ghost: 'bg-transparent text-[#737373] hover:text-black hover:bg-[#fafafa]',
        destructive: 'bg-[#ef4444] text-white border border-[#ef4444] hover:bg-[#dc2626]',
        link: 'text-black underline-offset-4 hover:underline bg-transparent',
      },
      size: {
        default: 'h-10 px-6 text-sm rounded-full',
        sm: 'h-8 px-4 text-xs rounded-full',
        lg: 'h-12 px-8 text-base rounded-full',
        icon: 'h-10 w-10 p-0 rounded-full',
      },
    },
    defaultVariants: {
      variant: 'default',
      size: 'default',
    },
  }
)

type ButtonVariants = VariantProps<typeof buttonVariants>

interface Props {
  variant?: ButtonVariants['variant']
  size?: ButtonVariants['size']
  class?: string
  disabled?: boolean
  type?: 'button' | 'submit' | 'reset'
  loading?: boolean
}

const props = withDefaults(defineProps<Props>(), {
  variant: 'default',
  size: 'default',
  type: 'button',
  loading: false,
})

const classes = computed(() =>
  cn(buttonVariants({ variant: props.variant, size: props.size }), props.class)
)
</script>

<template>
  <button
    :class="classes"
    :disabled="disabled || loading"
    :type="type"
  >
    <slot />
  </button>
</template>
```

关键变更：
- 6 个变体：default(灰药丸)、outline(白药丸)、cta(黑药丸)、ghost、destructive、link
- 所有 size 都是 `rounded-full`
- 移除 `transition-all duration-150`、`active:scale-[0.98]`、`shadow-md`、`hover:shadow-glow-primary`
- 移除 `ring-offset-background`
- focus ring 改为 `ring-[#3b82f6]/50`

- [x] **Step 2: Commit**

```bash
git add frontend-v3/src/components/ui/Button.vue
git commit -m "refactor(ui): 重写 Button 组件为 Ollama 药丸形按钮"
```

---

## Task 6: Card.vue

**Files:**
- Modify: `frontend-v3/src/components/ui/Card.vue`

- [x] **Step 1: 替换 Card.vue 全部内容**

```vue
<script setup lang="ts">
import { computed } from 'vue'
import { cn } from '@/lib/utils'

interface Props {
  class?: string
  variant?: 'default' | 'snow' | 'active'
}

const props = withDefaults(defineProps<Props>(), {
  variant: 'default',
})

const variantClasses = {
  default: 'bg-white border-[#e5e5e5]',
  snow: 'bg-[#fafafa] border-[#e5e5e5]',
  active: 'bg-[#fafafa] border-[#d4d4d4]',
}

const classes = computed(() =>
  cn(
    'rounded-xl border p-4 md:p-6 text-black',
    variantClasses[props.variant],
    props.class
  )
)
</script>

<template>
  <div :class="classes">
    <slot />
  </div>
</template>
```

- [x] **Step 2: Commit**

```bash
git add frontend-v3/src/components/ui/Card.vue
git commit -m "refactor(ui): 重写 Card 组件为 Ollama 风格"
```

---

## Task 7: Input.vue

**Files:**
- Modify: `frontend-v3/src/components/ui/Input.vue`

- [x] **Step 1: 替换 Input.vue 中基础样式类**

将 Input.vue 的 `<input>` 基础类从：

```
flex h-9 w-full rounded-md px-3 py-2 border border-border bg-transparent text-sm text-text-primary placeholder:text-text-placeholder file:border-0 file:bg-transparent file:text-sm file:font-medium file:text-text-primary transition-all duration-150 ease-out hover:border-border-hover focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-primary/50 focus-visible:border-primary disabled:cursor-not-allowed disabled:opacity-50 disabled:bg-white/[0.02]
```

改为：

```
flex h-9 w-full rounded-full px-4 py-2 border border-[#e5e5e5] bg-white text-sm text-black placeholder:text-[#a3a3a3] file:border-0 file:bg-transparent file:text-sm file:font-medium focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-[#3b82f6]/50 focus-visible:border-black disabled:cursor-not-allowed disabled:opacity-50 disabled:bg-[#fafafa]
```

- [x] **Step 2: Commit**

```bash
git add frontend-v3/src/components/ui/Input.vue
git commit -m "refactor(ui): Input 改为药丸形白色风格"
```

---

## Task 8: Select.vue

**Files:**
- Modify: `frontend-v3/src/components/ui/Select.vue`

- [x] **Step 1: 替换 Select.vue 中基础样式类**

将 `<select>` 的基础类从：

```
flex h-9 w-full items-center justify-between rounded-md px-3 py-2 pr-10 border border-border bg-transparent text-sm text-text-primary placeholder:text-text-placeholder transition-all duration-150 ease-out hover:border-border-hover focus:outline-none focus:ring-2 focus:ring-primary/50 focus:border-primary disabled:cursor-not-allowed disabled:opacity-50 disabled:bg-white/[0.02] appearance-none cursor-pointer
```

改为：

```
flex h-9 w-full items-center justify-between rounded-full px-4 py-2 pr-10 border border-[#e5e5e5] bg-white text-sm text-black placeholder:text-[#a3a3a3] focus:outline-none focus:ring-2 focus:ring-[#3b82f6]/50 focus:border-black disabled:cursor-not-allowed disabled:opacity-50 disabled:bg-[#fafafa] appearance-none cursor-pointer
```

将 options 的 `bg-background-elevated text-text-primary` 改为 `bg-white text-black`。

- [x] **Step 2: Commit**

```bash
git add frontend-v3/src/components/ui/Select.vue
git commit -m "refactor(ui): Select 改为药丸形白色风格"
```

---

## Task 9: Dialog.vue

**Files:**
- Modify: `frontend-v3/src/components/ui/Dialog.vue`

- [x] **Step 1: 修改 Dialog.vue 样式**

Overlay 类从：
`fixed inset-0 z-50 bg-black/80 backdrop-blur-sm`

改为：
`fixed inset-0 z-50 bg-black/30`

Content 类从：
`relative w-full max-w-lg mx-4 sm:mx-0 max-h-[90vh] overflow-y-auto rounded-xl border border-border bg-background-elevated p-4 sm:p-6 shadow-2xl`

改为：
`relative w-full max-w-lg mx-4 sm:mx-0 max-h-[90vh] overflow-y-auto rounded-xl border border-[#e5e5e5] bg-white p-4 sm:p-6`

Header title 从 `text-lg font-semibold text-text-primary` 改为 `text-lg font-medium text-black`。

Description 从 `text-sm text-text-secondary` 改为 `text-sm text-[#737373]`。

Close 按钮 focus ring 从 `focus-visible:ring-primary/50` 改为 `focus-visible:ring-[#3b82f6]/50`，颜色从 `text-text-tertiary hover:text-text-primary` 改为 `text-[#a3a3a3] hover:text-black`。

- [x] **Step 2: Commit**

```bash
git add frontend-v3/src/components/ui/Dialog.vue
git commit -m "refactor(ui): Dialog 改为白色主题，移除阴影和模糊"
```

---

## Task 10: Toast.vue

**Files:**
- Modify: `frontend-v3/src/components/ui/Toast.vue`

- [x] **Step 1: 修改 Toast.vue 样式**

基础类从 `rounded-lg ... shadow-2xl` 改为 `rounded-xl ... shadow-none`（移除 shadow-2xl）。

Container 类保持 `rounded-xl`。

variant 类映射：
- `default`: 从 `bg-background-elevated border-border text-text-primary` 改为 `bg-white border-[#e5e5e5] text-black`
- `success`: `bg-success/10 border-success/30 text-success` → 保持（token 自动更新）
- `error`: 同上保持
- `warning`: 同上保持
- `info`: 同上保持

Close 按钮颜色从 `text-text-tertiary hover:text-text-primary` 改为 `text-[#a3a3a3] hover:text-black`。

- [x] **Step 2: Commit**

```bash
git add frontend-v3/src/components/ui/Toast.vue
git commit -m "refactor(ui): Toast 改为白色主题"
```

---

## Task 11: Badge.vue

**Files:**
- Modify: `frontend-v3/src/components/ui/Badge.vue`

- [x] **Step 1: 替换 Badge.vue variant 定义**

将 cva variants 从暗色改为白色：

```typescript
const badgeVariants = cva(
  'inline-flex items-center rounded-full px-2.5 py-0.5 text-xs font-medium whitespace-nowrap',
  {
    variants: {
      variant: {
        default: 'bg-[#e5e5e5] text-[#262626]',
        success: 'bg-success/15 text-success',
        warning: 'bg-warning/15 text-warning',
        error: 'bg-error/15 text-error',
        info: 'bg-info/15 text-info',
        outline: 'border border-[#e5e5e5] text-[#737373] bg-transparent',
        secondary: 'bg-[#fafafa] text-[#737373]',
      },
    },
    defaultVariants: {
      variant: 'default',
    },
  }
)
```

- [x] **Step 2: Commit**

```bash
git add frontend-v3/src/components/ui/Badge.vue
git commit -m "refactor(ui): Badge 改为白色灰度风格"
```

---

## Task 12: StatCard.vue

**Files:**
- Modify: `frontend-v3/src/components/ui/StatCard.vue`

- [x] **Step 1: 大幅简化 StatCard**

移除所有 CSS 变量主题系统（`--card-indigo-*` 等）、移除 glow 装饰、移除 hover scale。

将 Card 包裹类从：
`group relative overflow-hidden p-6 shadow-lg transition-all duration-300 hover:scale-[1.02]`

改为：
`relative overflow-hidden p-6`

图标容器从 `h-10 w-10 rounded-xl shadow-inner bg-[var(--card-{color}-icon-bg)]` 改为：
- indigo → `h-10 w-10 rounded-xl bg-[#e5e5e5] text-[#262626]`
- neutral → `h-10 w-10 rounded-xl bg-[#fafafa] text-[#737373]`
- success → `h-10 w-10 rounded-xl bg-success/15 text-success`
- warning → `h-10 w-10 rounded-xl bg-warning/15 text-warning`
- error → `h-10 w-10 rounded-xl bg-error/15 text-error`

数值从 `text-3xl font-bold` 改为 `text-3xl font-medium text-black`。

标题从使用 text-text-secondary 改为 `text-[#737373]`。

移除底部的 glow 装饰 div（`absolute -right-4 -bottom-4 h-16 w-16 rounded-full blur-2xl`）。

- [x] **Step 2: Commit**

```bash
git add frontend-v3/src/components/ui/StatCard.vue
git commit -m "refactor(ui): StatCard 简化为白色风格，移除发光效果"
```

---

## Task 13: Checkbox.vue

**Files:**
- Modify: `frontend-v3/src/components/ui/Checkbox.vue`

- [x] **Step 1: 修改颜色**

选中态从 `bg-primary border-primary` 改为 `bg-black border-black`。
未选中态从 `bg-transparent border-border hover:border-border-hover` 改为 `bg-white border-[#e5e5e5] hover:border-[#d4d4d4]`。
Check 图标颜色保持 `text-white`（黑底白勾）。

- [x] **Step 2: Commit**

```bash
git add frontend-v3/src/components/ui/Checkbox.vue
git commit -m "refactor(ui): Checkbox 改为黑白色"
```

---

## Task 14: SearchableSelect.vue

**Files:**
- Modify: `frontend-v3/src/components/ui/SearchableSelect.vue`

- [x] **Step 1: 修改样式**

Trigger 按钮从 `h-10 rounded-lg border-white/10 bg-white/5` 改为 `h-10 rounded-full border-[#e5e5e5] bg-white`。

Dropdown 面板从 `bg-[#1a1a2e] border-white/10 rounded-lg shadow-xl` 改为 `bg-white border-[#e5e5e5] rounded-xl`。

搜索输入框从暗色改为白色：`bg-[#fafafa] border-[#e5e5e5] rounded-full`。

Option 选中态从 `bg-primary/20 text-primary` 改为 `bg-[#e5e5e5] text-black`。
Option hover 从 `hover:bg-white/10` 改为 `hover:bg-[#fafafa]`。
Option 文字从 `text-white/70` 改为 `text-[#737373]`。

- [x] **Step 2: Commit**

```bash
git add frontend-v3/src/components/ui/SearchableSelect.vue
git commit -m "refactor(ui): SearchableSelect 改为白色主题"
```

---

## Task 15: MobilePicker.vue

**Files:**
- Modify: `frontend-v3/src/components/ui/MobilePicker.vue`

- [x] **Step 1: 修改样式**

移动端底部面板从 `bg-[#1a1a2e] rounded-t-[20px]` 改为 `bg-white rounded-t-xl`。

Drag handle 从 `bg-white/20` 改为 `bg-[#d4d4d4]`。

桌面端 dropdown 从 `bg-[#1a1a2e] border-white/10 rounded-lg shadow-xl` 改为 `bg-white border-[#e5e5e5] rounded-xl`。

标题从 `text-white font-semibold` 改为 `text-black font-medium`。

Option 选中态从 `bg-primary/10` 改为 `bg-[#e5e5e5]`。
Option 文字从 `text-white/70` 改为 `text-[#737373]`。

Trigger 按钮从暗色改为白色：`border-[#e5e5e5] bg-white text-black`。

搜索输入框：`bg-[#fafafa] border-[#e5e5e5] rounded-full text-black placeholder:text-[#a3a3a3]`。

- [x] **Step 2: Commit**

```bash
git add frontend-v3/src/components/ui/MobilePicker.vue
git commit -m "refactor(ui): MobilePicker 改为白色主题"
```

---

## Task 16: NetworkErrorBanner.vue

**Files:**
- Modify: `frontend-v3/src/components/ui/NetworkErrorBanner.vue`

- [x] **Step 1: 修改样式**

从 `bg-red-500/90 backdrop-blur-sm text-white shadow-lg` 改为 `bg-[#ef4444] text-white`。移除 `backdrop-blur-sm` 和 `shadow-lg`。

- [x] **Step 2: Commit**

```bash
git add frontend-v3/src/components/ui/NetworkErrorBanner.vue
git commit -m "refactor(ui): NetworkErrorBanner 移除模糊和阴影"
```

---

## Task 17: DashboardLayout.vue

**Files:**
- Modify: `frontend-v3/src/layouts/DashboardLayout.vue`

- [x] **Step 1: 修改桌面端侧边栏**

背景从 `bg-[#0a0a0f] border-r border-white/10` 改为 `bg-white border-r border-[#e5e5e5]`。

Logo 文字从 `text-white font-bold` 改为 `text-black font-medium`。

用户信息面板从 `bg-primary/20` 改为 `bg-[#fafafa]`，头像从 `text-primary` 改为 `text-black`，名字从 `text-white font-medium` 改为 `text-black font-medium`，角色从 `text-white/50` 改为 `text-[#a3a3a3]`。

导航项：
- 默认态从 `text-white/70 hover:bg-white/10` 改为 `text-[#737373] hover:bg-[#fafafa]`
- 激活态从 `bg-primary/10 text-primary` 改为 `bg-[#e5e5e5] text-black`
- 圆角从 `rounded-lg` 改为 `rounded-full`

登出按钮从 `text-white/50 hover:text-white` 改为 `text-[#a3a3a3] hover:text-black`。

- [x] **Step 2: 修改移动端头部**

从 `bg-[#0a0a0f] border-b border-white/10` 改为 `bg-white border-b border-[#e5e5e5]`。

Logo 从 `text-white font-bold` 改为 `text-black font-medium`。

汉堡按钮从 `text-white` 改为 `text-black`。

- [x] **Step 3: 修改内容区**

内容区不需要显式背景色（继承 body 白色）。

- [x] **Step 4: Commit**

```bash
git add frontend-v3/src/layouts/DashboardLayout.vue
git commit -m "refactor(layout): DashboardLayout 改为白色主题"
```

---

## Task 18: MobileDrawer.vue

**Files:**
- Modify: `frontend-v3/src/components/ui/MobileDrawer.vue`

- [x] **Step 1: 修改样式**

Overlay 从 `bg-black/80 backdrop-blur-sm` 改为 `bg-black/30`。

Drawer 从 `bg-[#0a0a0f] border-r border-white/10` 改为 `bg-white border-r border-[#e5e5e5]`。

Header Logo 从 `text-white font-bold` 改为 `text-black font-medium`。关闭按钮从 `text-white/50 hover:text-white` 改为 `text-[#a3a3a3] hover:text-black`。

用户信息：头像从 `bg-primary/20` 改为 `bg-[#fafafa]`，名字从 `text-white` 改为 `text-black`，角色从 `text-white/50` 改为 `text-[#a3a3a3]`。

导航项同 DashboardLayout 的改法：默认 `text-[#737373] hover:bg-[#fafafa]`，激活 `bg-[#e5e5e5] text-black`。

- [x] **Step 2: Commit**

```bash
git add frontend-v3/src/components/ui/MobileDrawer.vue
git commit -m "refactor(ui): MobileDrawer 改为白色主题"
```

---

## Task 19: BottomNav.vue

**Files:**
- Modify: `frontend-v3/src/components/ui/BottomNav.vue`

- [x] **Step 1: 修改样式**

从 `bg-[#0a0a0f] border-t border-white/10` 改为 `bg-white border-t border-[#e5e5e5]`。

导航项：默认从 `text-white/50` 改为 `text-[#a3a3a3]`，激活从 `text-primary` 改为 `text-black`。

- [x] **Step 2: Commit**

```bash
git add frontend-v3/src/components/ui/BottomNav.vue
git commit -m "refactor(ui): BottomNav 改为白色主题"
```

---

## Task 20: LoginPage.vue

**Files:**
- Modify: `frontend-v3/src/views/LoginPage.vue`

- [x] **Step 1: 全面重构为白色主题**

背景从 `bg-[#030307]` 改为 `bg-white`。

移除所有装饰性渐变背景 div。

卡片容器：`bg-white border border-[#e5e5e5] rounded-xl shadow-none`。

Logo 图标容器从暗色改为 `bg-[#fafafa] border border-[#e5e5e5] rounded-xl`，图标 `text-black`。

标题从 `text-white font-bold` 改为 `text-2xl font-medium text-black`。

副标题从 `text-white/70` 改为 `text-sm text-[#737373]`。

角色选择按钮改为药丸形：`rounded-full border-[#e5e5e5]`，激活态 `bg-[#e5e5e5] text-[#262626]`，非激活 `bg-white text-[#737373]`。

输入框改为药丸形：`rounded-full border-[#e5e5e5] pl-11`，focus `border-black ring-[#3b82f6]/50`。

登录按钮使用 `variant="cta"`（黑药丸）。

Label 从暗色改为 `text-black`。

- [x] **Step 2: Commit**

```bash
git add frontend-v3/src/views/LoginPage.vue
git commit -m "refactor(views): LoginPage 改为 Ollama 白色主题"
```

---

## Task 21: NotFound.vue

**Files:**
- Modify: `frontend-v3/src/views/NotFound.vue`

- [x] **Step 1: 全面简化**

背景从所有渐变改为 `bg-white`。

移除所有装饰性渐变 div（`bg-gradient-to-br from-orange-500/15` 等）。

标题从 `font-bold text-transparent bg-clip-text bg-gradient-to-r` 改为 `font-medium text-black`。

描述文字改为 `text-[#737373]`。

按钮改为使用 Button 组件的 `cta` variant。

- [x] **Step 2: Commit**

```bash
git add frontend-v3/src/views/NotFound.vue
git commit -m "refactor(views): NotFound 改为纯白风格"
```

---

## Task 22: LandingPage.vue

**Files:**
- Modify: `frontend-v3/src/views/LandingPage.vue`

- [x] **Step 1: 全面简化**

背景从 `bg-[#030307]` 加各种渐变改为 `bg-white`。

移除所有装饰性渐变 div。

标题从渐变文字改为 `text-black font-medium`。

副标题从 `text-white/70` 改为 `text-[#737373]`。

CTA 按钮使用 `variant="cta"`。

特性卡片使用白色 Card 组件。

- [x] **Step 2: Commit**

```bash
git add frontend-v3/src/views/LandingPage.vue
git commit -m "refactor(views): LandingPage 改为纯白风格"
```

---

## Task 23-27: Admin 页面

**Files:**
- Modify: `frontend-v3/src/views/admin/Dashboard.vue`
- Modify: `frontend-v3/src/views/admin/Students.vue`
- Modify: `frontend-v3/src/views/admin/Teachers.vue`
- Modify: `frontend-v3/src/views/admin/Classes.vue`

对每个 admin 页面应用全局颜色映射规则。每个页面 commit 一次。

**Dashboard.vue 具体变更：**
- 页面标题 `font-bold` → `font-medium`
- StatCard 的 color prop 保持不变（StatCard 内部已改为白色）
- 卡片容器移除 `shadow-lg`、`shadow-inner`
- 表格遵循 `ch-table` 样式
- 所有 `text-white` → `text-black`
- 所有 `text-white/70` → `text-[#737373]`
- 所有 `bg-white/[0.02]` → `bg-white`
- 所有 `border-white/10` → `border-[#e5e5e5]`
- 所有 `rounded-xl` 保留（已是 12px 容器标准）

```bash
git add frontend-v3/src/views/admin/Dashboard.vue
git commit -m "refactor(views): admin/Dashboard 改为白色主题"
```

**Students.vue、Teachers.vue、Classes.vue** 同理，应用全局映射规则。

---

## Task 28-33: Teacher 页面

**Files:**
- Modify: `frontend-v3/src/views/teacher/Dashboard.vue`
- Modify: `frontend-v3/src/views/teacher/Students.vue`
- Modify: `frontend-v3/src/views/teacher/Checkin.vue`
- Modify: `frontend-v3/src/views/teacher/CourseSession.vue`
- Modify: `frontend-v3/src/views/teacher/Schedules.vue`
- Modify: `frontend-v3/src/views/teacher/SessionsHistory.vue`

每个页面应用全局颜色映射规则。每个页面 commit 一次。

**额外注意：**
- Schedules.vue 中有大量 `bg-indigo-500/20 text-indigo-300 border-indigo-500/30` 等硬编码 indigo 色 → 全部改为灰度（`bg-[#e5e5e5] text-[#262626] border-[#e5e5e5]`）
- Schedules.vue 中的自定义发光阴影 `shadow-[0_0_8px_rgba(239,68,68,0.5)]` → 删除
- Checkin.vue 中的签到状态色保留（绿/黄/红）
- CourseSession.vue 中的 `rounded-2xl` → `rounded-xl`

---

## Task 34-36: Student 页面

**Files:**
- Modify: `frontend-v3/src/views/student/Dashboard.vue`
- Modify: `frontend-v3/src/views/student/Checkin.vue`
- Modify: `frontend-v3/src/views/student/Leaderboard.vue`

每个页面应用全局颜色映射规则。每个页面 commit 一次。

**额外注意：**
- student/Dashboard.vue 中有大量渐变背景装饰（`bg-gradient-to-br from-primary/25 via-primary/15 to-accent-cyan/20`）→ 全部删除
- Leaderboard.vue 中的奖牌色（金银铜）可保留为状态色语义
- student/Dashboard.vue 的 `rounded-2xl` → `rounded-xl`

---

## Task 37-41: 特性组件

**Files:**
- Modify: `frontend-v3/src/components/teacher/StudentCheckinGrid.vue`
- Modify: `frontend-v3/src/components/teacher/CheckinStats.vue`
- Modify: `frontend-v3/src/components/teacher/ScheduleAdjustmentDialog.vue`
- Modify: `frontend-v3/src/components/admin/ManageSchedulesDialog.vue`
- Modify: `frontend-v3/src/components/admin/ManageClassesDialog.vue`

**额外注意：**
- StudentCheckinGrid.vue：移除 `bg-gradient-to-r from-white/[0.03]` 等渐变
- CheckinStats.vue：`bg-gradient-to-br from-blue-500/10` 改为 `bg-[#fafafa]`，`bg-gradient-to-br from-purple-500/10` 改为 `bg-[#fafafa]`
- ManageSchedulesDialog.vue：移除 `bg-[#030307]` 暗色背景
- ManageClassesDialog.vue：同理

---

## Task 42-44: Students 特性组件

**Files:**
- Modify: `frontend-v3/src/features/students/components/StudentCard.vue`
- Modify: `frontend-v3/src/features/students/components/StudentFilters.vue`
- Modify: `frontend-v3/src/features/students/components/QuickScoreButton.vue`

**额外注意：**
- QuickScoreButton.vue：移除自定义发光 `shadow-[0_0_12px_rgba(115,191,105,0.25)]`
- StudentCard.vue：移除 shadow、暗色背景

---

## Task 45: DESIGN_SYSTEM.md

**Files:**
- Modify: `frontend-v3/DESIGN_SYSTEM.md`

- [x] **Step 1: 重写设计系统文档**

将文档完全重写为 Ollama 设计系统文档，反映新的色彩、字体、圆角、阴影规范。使用设计规格 `docs/superpowers/specs/2026-04-10-ollama-design-refactor.md` 作为内容源。

- [x] **Step 2: Commit**

```bash
git add frontend-v3/DESIGN_SYSTEM.md
git commit -m "docs: 重写设计系统文档为 Ollama 风格"
```

---

## Task 46: 验证

- [x] **Step 1: 运行类型检查**

```bash
cd frontend-v3 && npx vue-tsc --noEmit 2>&1 | tail -30
```

Expected: 无类型错误

- [x] **Step 2: 运行前端测试**

```bash
cd frontend-v3 && pnpm test:run 2>&1 | tail -30
```

Expected: 全部通过（130 个测试）

- [x] **Step 3: 启动开发服务器，手动验证视觉效果**

```bash
cd frontend-v3 && pnpm dev
```

检查清单：
- [x] 页面背景纯白
- [x] 文字为黑色
- [x] 按钮为药丸形
- [x] 卡片 12px 圆角、零阴影
- [x] 边框 1px solid #e5e5e5
- [x] 无渐变
- [x] 字重只有 400/500
- [x] 状态色正常显示
- [x] 移动端同步白色主题
