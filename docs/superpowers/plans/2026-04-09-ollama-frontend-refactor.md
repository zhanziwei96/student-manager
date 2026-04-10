# Ollama 设计系统前端重构实施计划

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 将 ClassHub 前端从深色主题重构为 Ollama 风格的极简白色主题，完全遵循 DESIGN.md 的设计规范。

**Architecture:** 通过更新 CSS Tokens 和 UI 组件，然后逐个重构页面，确保整体视觉一致性。

**Tech Stack:** Vue 3, Tailwind CSS v4, TypeScript

---

## 文件变更映射

| 文件 | 操作 | 责任 |
|------|------|------|
| `frontend-v3/src/styles/tokens.css` | 修改 | 定义所有新的颜色、字体、圆角 CSS 变量 |
| `frontend-v3/src/styles/components.css` | 修改 | 更新组件基础样式 |
| `frontend-v3/src/components/ui/Button.vue` | 修改 | 重构为 Ollama 风格的二元圆角按钮 |
| `frontend-v3/src/components/ui/Card.vue` | 修改 | 重构为 12px 圆角、无边框阴影卡片 |
| `frontend-v3/src/components/ui/Input.vue` | 修改 | 重构为药丸形输入框 |
| `frontend-v3/src/components/ui/Badge.vue` | 修改 | 重构为药丸形标签 |
| `frontend-v3/src/views/LoginPage.vue` | 修改 | 重构登录页为白色主题 |
| `frontend-v3/src/views/admin/Dashboard.vue` | 修改 | 重构管理员仪表盘 |
| `frontend-v3/src/views/admin/Students.vue` | 修改 | 重构学生管理页 |
| `frontend-v3/src/views/admin/Teachers.vue` | 修改 | 重构教师管理页 |
| `frontend-v3/src/views/teacher/Dashboard.vue` | 修改 | 重构教师仪表盘 |
| `frontend-v3/src/views/student/Dashboard.vue` | 修改 | 重构学生仪表盘 |
| `frontend-v3/src/views/student/Checkin.vue` | 修改 | 重构签到页面 |
| `frontend-v3/index.html` | 修改 | 更新字体加载 |

---

## Task 1: 更新 CSS Tokens 文件

**Files:**
- Modify: `frontend-v3/src/styles/tokens.css`

- [ ] **Step 1: 备份原 tokens.css**

```bash
cp frontend-v3/src/styles/tokens.css frontend-v3/src/styles/tokens.css.backup
```

- [ ] **Step 2: 重写 tokens.css 为 Ollama 设计系统**

```css
/**
 * ClassHub Ollama 设计系统 - CSS Tokens
 * 版本: 3.0.0 (Tailwind v4)
 * 完全遵循 Ollama 极简白色主题
 */

@theme inline {
  /* ========== 响应式断点 ========== */
  --breakpoint-sm: 640px;
  --breakpoint-md: 768px;
  --breakpoint-lg: 1024px;
  --breakpoint-xl: 1280px;

  /* ========== Ollama 色彩系统（纯灰度） ========== */
  
  /* 核心颜色 */
  --color-pure-black: #000000;
  --color-near-black: #262626;
  --color-mid-gray: #525252;
  --color-stone: #737373;
  --color-silver: #a3a3a3;
  --color-button-text-dark: #404040;
  
  /* 表面颜色 */
  --color-darkest-surface: #090909;
  --color-pure-white: #ffffff;
  --color-snow: #fafafa;
  --color-light-gray: #e5e5e5;
  --color-border-light: #d4d4d4;
  
  /* 语义映射 */
  --color-background: #ffffff;
  --color-background-elevated: #fafafa;
  --color-background-card: #fafafa;
  
  --color-text-primary: #000000;
  --color-text-secondary: #737373;
  --color-text-tertiary: #a3a3a3;
  --color-text-muted: #a3a3a3;
  --color-text-placeholder: #a3a3a3;
  
  /* 按钮颜色 */
  --color-button-primary-bg: #e5e5e5;
  --color-button-primary-text: #262626;
  --color-button-secondary-bg: #ffffff;
  --color-button-secondary-text: #404040;
  --color-button-cta-bg: #000000;
  --color-button-cta-text: #ffffff;
  
  /* 边框 */
  --color-border: #e5e5e5;
  --color-border-hover: #d4d4d4;
  --color-border-focus: #000000;
  
  /* 聚焦环 - 唯一非灰色 */
  --color-focus-ring: #3b82f6;
  
  /* 状态色（调整为灰度系） */
  --color-success: #22c55e;
  --color-warning: #f59e0b;
  --color-error: #ef4444;
  --color-info: #3b82f6;

  /* ========== Ollama 字体系统 ========== */
  --font-display: ui-rounded, 'SF Pro Rounded', -apple-system, 'PingFang SC', 'Microsoft YaHei', sans-serif;
  --font-body: ui-sans-serif, system-ui, -apple-system, 'PingFang SC', 'Microsoft YaHei', sans-serif;
  --font-mono: ui-monospace, 'SFMono-Regular', 'Menlo', 'Monaco', 'Consolas', 'Liberation Mono', 'Courier New', monospace;
  
  /* ========== Ollama 圆角系统（严格二元） ========== */
  --radius-container: 12px;
  --radius-pill: 9999px;
  
  /* ========== Ollama 间距系统 ========== */
  --spacing-unit: 8px;
  --spacing-section-sm: 88px;
  --spacing-section-lg: 112px;
  
  /* 按钮内边距（严格一致） */
  --button-padding-y: 10px;
  --button-padding-x: 24px;
  
  /* 卡片内边距 */
  --card-padding: 24px;
  --card-padding-lg: 32px;
  
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
  --radius-container: 12px;
  --radius-pill: 9999px;
}
```

- [ ] **Step 3: 验证 tokens.css 语法**

```bash
cd frontend-v3 && npx tailwindcss --input src/styles/tokens.css --output /tmp/test.css 2>&1 | head -20
```

Expected: 无错误输出

- [ ] **Step 4: Commit**

```bash
git add frontend-v3/src/styles/tokens.css
git commit -m "feat(styles): 更新 tokens.css 为 Ollama 白色主题"
```

---

## Task 2: 重构 Button 组件

**Files:**
- Modify: `frontend-v3/src/components/ui/Button.vue`

- [ ] **Step 1: 重写 Button.vue**

```vue
<script setup lang="ts">
import { computed } from 'vue'
import { cva, type VariantProps } from 'class-variance-authority'
import { cn } from '@/lib/utils'

/**
 * Button 组件 - Ollama 设计系统 v3.0.0
 * 严格遵循二元圆角系统：所有按钮 pill-shaped (9999px)
 * 严格按钮内边距：10px 24px
 * 零阴影、无动画
 */

const buttonVariants = cva(
  // 基础样式
  'inline-flex items-center justify-center gap-2 whitespace-nowrap ' +
  'font-medium transition-none ' + // 无过渡
  'focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-[#3b82f6]/50 ' +
  'disabled:pointer-events-none disabled:opacity-50 disabled:cursor-not-allowed',
  {
    variants: {
      variant: {
        // Gray Pill (Primary) - Ollama 默认按钮
        default: 
          'bg-[#e5e5e5] text-[#262626] border border-[#e5e5e5] ' +
          'hover:bg-[#d4d4d4]', // 仅背景色变化，无动画
        
        // White Pill (Secondary)
        outline: 
          'bg-white text-[#404040] border border-[#d4d4d4] ' +
          'hover:bg-[#fafafa]',
        
        // Black Pill (CTA)
        cta: 
          'bg-black text-white border border-black ' +
          'hover:bg-[#262626]',
        
        // Ghost
        ghost: 
          'bg-transparent text-[#737373] border-transparent ' +
          'hover:text-black hover:bg-[#fafafa]',
        
        // Destructive (灰度处理)
        destructive: 
          'bg-[#ef4444] text-white border-[#ef4444] ' +
          'hover:bg-[#dc2626]',
        
        // Link
        link: 'text-black underline-offset-4 hover:underline bg-transparent border-transparent',
      },
      size: {
        // 严格 padding 10px 24px
        default: 'h-10 px-6 text-sm', // 约 10px 24px
        sm: 'h-8 px-4 text-xs',
        lg: 'h-12 px-8 text-base',
        icon: 'h-10 w-10 p-0',
      },
    },
    defaultVariants: {
      variant: 'default',
      size: 'default',
    },
  }
)

// 强制所有圆角为 pill
const baseClasses = 'rounded-full' // 9999px

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
}))

const classes = computed(() => 
  cn(buttonVariants({ variant: props.variant, size: props.size }), baseClasses, props.class)
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

- [ ] **Step 2: 验证 Button 组件**

```bash
cd frontend-v3 && npx vue-tsc --noEmit src/components/ui/Button.vue 2>&1 | head -20
```

Expected: 无类型错误

- [ ] **Step 3: Commit**

```bash
git add frontend-v3/src/components/ui/Button.vue
git commit -m "feat(ui): 重构 Button 组件为 Ollama 风格"
```

---

## Task 3: 重构 Card 组件

**Files:**
- Modify: `frontend-v3/src/components/ui/Card.vue`

- [ ] **Step 1: 重写 Card.vue**

```vue
<script setup lang="ts">
import { computed } from 'vue'
import { cn } from '@/lib/utils'

/**
 * Card 组件 - Ollama 设计系统 v3.0.0
 * 圆角: 12px (唯一非 pill 圆角)
 * 阴影: 零
 * 边框: 1px solid #e5e5e5
 */

interface Props {
  class?: string
  variant?: 'default' | 'snow' | 'bordered'
}

const props = withDefaults(defineProps<Props>(), {
  variant: 'default',
})

const variantClasses = {
  // 默认: 白色背景
  default: 'bg-white border-[#e5e5e5]',
  
  // Snow: 浅灰背景
  snow: 'bg-[#fafafa] border-[#e5e5e5]',
  
  // Bordered: 白色背景 + 边框
  bordered: 'bg-white border-[#e5e5e5]',
}

const classes = computed(() =>
  cn(
    // 严格 12px 圆角（唯一非 pill）
    'rounded-xl border p-6',
    // 零阴影
    'shadow-none',
    // 变体样式
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

- [ ] **Step 2: Commit**

```bash
git add frontend-v3/src/components/ui/Card.vue
git commit -m "feat(ui): 重构 Card 组件为 Ollama 风格 (12px圆角, 零阴影)"
```

---

## Task 4: 重构登录页

**Files:**
- Modify: `frontend-v3/src/views/LoginPage.vue`

- [ ] **Step 1: 重写 LoginPage.vue**

```vue
<script setup lang="ts">
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '@/stores'
import { useToast } from '@/composables'
import { getErrorMessage } from '@/lib/error'
import type { UserRole } from '@/types'
import { Button, Card, Input, Label, ToastContainer } from '@/components/ui'
import { GraduationCap, Lock, User } from 'lucide-vue-next'

const authStore = useAuthStore()
const router = useRouter()
const { success, error: showError } = useToast()

const form = ref({
  username: '',
  password: '',
  role: 'admin' as 'admin' | 'teacher' | 'student',
})

const errors = ref({
  username: '',
  password: '',
})

const roles = [
  { value: 'admin', label: '管理员' },
  { value: 'teacher', label: '教师' },
  { value: 'student', label: '学生' },
]

const validateForm = () => {
  errors.value = { username: '', password: '' }
  let isValid = true

  if (!form.value.username.trim()) {
    errors.value.username = '请输入用户名'
    showError('请输入用户名')
    isValid = false
  } else if (!form.value.password.trim()) {
    errors.value.password = '请输入密码'
    showError('请输入密码')
    isValid = false
  }

  return isValid
}

const handleSubmit = async () => {
  if (!validateForm()) {
    return
  }

  try {
    const userInfo = await authStore.login(form.value)
    success('登录成功！')

    const userRole = userInfo?.role
    const redirectMap: Record<string, string> = {
      admin: '/admin',
      teacher: '/teacher',
      student: '/student',
    }
    if (userRole && redirectMap[userRole]) {
      router.push(redirectMap[userRole])
    } else {
      throw new Error('无法获取用户角色信息')
    }
  } catch (err: unknown) {
    showError(getErrorMessage(err) || '登录失败')
  }
}
</script>

<template>
  <!-- 纯白色背景 -->
  <div class="relative flex min-h-screen items-start sm:items-center justify-center overflow-hidden bg-white p-4 pt-16 sm:pt-4">
    <!-- 登录表单 -->
    <Card class="relative w-full max-w-md border-[#e5e5e5] p-6 sm:p-8 shadow-none">
      <div class="flex flex-col items-center space-y-2 text-center">
        <!-- Logo 图标 -->
        <div class="flex h-12 w-12 items-center justify-center rounded-xl bg-[#fafafa] border border-[#e5e5e5]">
          <GraduationCap class="h-7 w-7 text-black" />
        </div>
        <!-- Display 标题 - SF Pro Rounded 风格 -->
        <h1 class="text-2xl font-medium text-black" style="font-family: ui-rounded, system-ui, sans-serif;">
          欢迎使用智慧课堂
        </h1>
        <p class="text-sm text-[#737373]">
          登录您的账号
        </p>
      </div>

      <form
        class="mt-8 space-y-6"
        autocomplete="off"
        @submit.prevent="handleSubmit"
      >
        <!-- Role selection - 药丸形按钮 -->
        <div class="space-y-2">
          <Label for="role" class="text-black">角色</Label>
          <div class="grid grid-cols-3 gap-2">
            <button
              v-for="role in roles"
              :key="role.value"
              type="button"
              :class="[
                'px-4 py-2 text-sm font-medium transition-none',
                'rounded-full border', // 药丸形
                form.role === role.value
                  ? 'bg-[#e5e5e5] border-[#e5e5e5] text-[#262626]'
                  : 'bg-white border-[#e5e5e5] text-[#737373] hover:bg-[#fafafa]',
              ]"
              @click="form.role = role.value as UserRole"
            >
              {{ role.label }}
            </button>
          </div>
        </div>

        <!-- Username - 药丸形输入框 -->
        <div class="space-y-2 mt-6">
          <Label for="username" class="text-black">用户名</Label>
          <div class="relative">
            <div class="absolute inset-y-0 left-0 flex items-center pl-4 pointer-events-none">
              <User class="h-4 w-4 text-[#a3a3a3]" />
            </div>
            <Input
              id="username"
              v-model="form.username"
              type="text"
              autocomplete="username"
              placeholder="请输入用户名"
              :class="[
                'pl-11 h-10 rounded-full border-[#e5e5e5]', // 药丸形
                'focus:border-black focus:ring-2 focus:ring-[#3b82f6]/50',
                errors.username && 'border-red-500'
              ]"
              @input="errors.username = ''"
            />
          </div>
        </div>

        <!-- Password - 药丸形输入框 -->
        <div class="space-y-2 mt-6">
          <Label for="password" class="text-black">密码</Label>
          <div class="relative">
            <div class="absolute inset-y-0 left-0 flex items-center pl-4 pointer-events-none">
              <Lock class="h-4 w-4 text-[#a3a3a3]" />
            </div>
            <Input
              id="password"
              v-model="form.password"
              type="password"
              autocomplete="current-password"
              placeholder="请输入密码"
              :class="[
                'pl-11 h-10 rounded-full border-[#e5e5e5]', // 药丸形
                'focus:border-black focus:ring-2 focus:ring-[#3b82f6]/50',
                errors.password && 'border-red-500'
              ]"
              @input="errors.password = ''"
            />
          </div>
        </div>

        <!-- Submit button - Black Pill CTA -->
        <Button
          type="submit"
          variant="cta"
          class="w-full mt-8"
          :loading="authStore.isLoggingIn"
        >
          登录
        </Button>
      </form>
    </Card>

    <!-- Toast 通知容器 -->
    <ToastContainer />
  </div>
</template>
```

- [ ] **Step 2: 验证登录页**

```bash
cd frontend-v3 && npx vue-tsc --noEmit src/views/LoginPage.vue 2>&1 | head -20
```

Expected: 无类型错误

- [ ] **Step 3: Commit**

```bash
git add frontend-v3/src/views/LoginPage.vue
git commit -m "feat(views): 重构登录页为 Ollama 白色主题"
```

---

## Task 5: 重构管理员仪表盘

**Files:**
- Modify: `frontend-v3/src/views/admin/Dashboard.vue`

- [ ] **Step 1: 读取当前 Dashboard.vue 内容**

```bash
cat frontend-v3/src/views/admin/Dashboard.vue
```

- [ ] **Step 2: 重构为白色主题**

主要变更：
- `bg-background` → `bg-white`
- `text-white` → `text-black`
- `text-white/70` → `text-[#737373]`
- `border-white/10` → `border-[#e5e5e5]`
- `rounded-xl` → `rounded-xl` (保持 12px)
- `shadow-*` → **移除所有阴影**
- 按钮使用新的 variant

- [ ] **Step 3: Commit**

```bash
git add frontend-v3/src/views/admin/Dashboard.vue
git commit -m "feat(views): 重构管理员仪表盘为 Ollama 白色主题"
```

---

## Task 6: 重构教师管理页

**Files:**
- Modify: `frontend-v3/src/views/admin/Teachers.vue`

- [ ] **Step 1: 读取当前 Teachers.vue 内容**

- [ ] **Step 2: 应用相同的颜色映射变更**

- [ ] **Step 3: Commit**

```bash
git add frontend-v3/src/views/admin/Teachers.vue
git commit -m "feat(views): 重构教师管理页为 Ollama 白色主题"
```

---

## Task 7: 重构学生管理页

**Files:**
- Modify: `frontend-v3/src/views/admin/Students.vue`

- [ ] **Step 1: 应用相同的颜色映射变更**

- [ ] **Step 2: Commit**

```bash
git add frontend-v3/src/views/admin/Students.vue
git commit -m "feat(views): 重构学生管理页为 Ollama 白色主题"
```

---

## Task 8: 重构教师仪表盘

**Files:**
- Modify: `frontend-v3/src/views/teacher/Dashboard.vue`

- [ ] **Step 1: 应用相同的颜色映射变更**

- [ ] **Step 2: Commit**

```bash
git add frontend-v3/src/views/teacher/Dashboard.vue
git commit -m "feat(views): 重构教师仪表盘为 Ollama 白色主题"
```

---

## Task 9: 重构学生仪表盘

**Files:**
- Modify: `frontend-v3/src/views/student/Dashboard.vue`

- [ ] **Step 1: 应用相同的颜色映射变更**

- [ ] **Step 2: Commit**

```bash
git add frontend-v3/src/views/student/Dashboard.vue
git commit -m "feat(views): 重构学生仪表盘为 Ollama 白色主题"
```

---

## Task 10: 重构签到页面

**Files:**
- Modify: `frontend-v3/src/views/student/Checkin.vue`

- [ ] **Step 1: 应用相同的颜色映射变更**

- [ ] **Step 2: Commit**

```bash
git add frontend-v3/src/views/student/Checkin.vue
git commit -m "feat(views): 重构签到页面为 Ollama 白色主题"
```

---

## Task 11: 运行测试验证

**Files:**
- Test: `frontend-v3/`

- [ ] **Step 1: 运行类型检查**

```bash
cd frontend-v3 && npx vue-tsc --noEmit 2>&1 | tail -30
```

Expected: 无类型错误

- [ ] **Step 2: 启动开发服务器验证**

```bash
cd frontend-v3 && timeout 30s pnpm dev 2>&1 &
sleep 5
echo "Server started"
```

- [ ] **Step 3: Commit**

```bash
git commit --allow-empty -m "test: 验证 Ollama 主题重构"
```

---

## 验证清单

所有任务完成后，验证以下 Ollama 设计约束：

- [ ] 页面背景为纯白色 (#ffffff)
- [ ] 主要文字为纯黑色 (#000000)
- [ ] 按钮使用药丸形状 (9999px)
- [ ] 卡片使用 12px 圆角
- [ ] 无阴影效果
- [ ] 边框为 1px solid #e5e5e5
- [ ] 字重只有 400 或 500
- [ ] 无渐变背景
- [ ] 无 hover 动画
- [ ] 按钮 padding 为 10px 24px

---

*计划版本: 1.0.0*
*创建日期: 2026-04-09*
