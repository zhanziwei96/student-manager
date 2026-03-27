# ClassHub 设计体系 (Design System)

> 版本: 1.1.0  
> 更新日期: 2026-03-27  
> 适用范围: frontend-v3 全站

---

## 1. 设计原则

### 1.1 核心设计理念
- **暗色优先**: 深色系为主，减少视觉疲劳，营造专业感
- **玻璃拟态**: 使用 backdrop-blur 和半透明背景创造层次感
- **简洁现代**: 去除冗余装饰，强调内容本身
- **高对比度**: 确保文字在深色背景上的可读性

### 1.2 设计关键词
`科技` `专业` `清晰` `现代` `沉浸`

---

## 2. 色彩系统

### 2.1 主色调 (Primary)
| Token | 值 | 用途 |
|-------|-----|------|
| `--color-primary` | `#6366f1` | 主按钮、链接、高亮 |
| `--color-primary-foreground` | `#ffffff` | 主色上的文字 |
| `--color-primary-hover` | `#818cf8` | 主色悬停状态 |
| `--color-primary-muted` | `rgba(99, 102, 241, 0.2)` | 背景装饰、图标容器 |

### 2.2 强调色 (Accent)
| Token | 值 | 用途 |
|-------|-----|------|
| `--color-accent` | `#22d3ee` | 渐变、特殊高亮、成功状态 |
| `--color-accent-cyan` | `#22d3ee` | 渐变终点、装饰性元素 |
| `--color-accent-foreground` | `#ffffff` | 强调色上的文字 |

### 2.3 背景色 (Background)
| Token | 值 | 用途 |
|-------|-----|------|
| `--color-background` | `#030307` | 页面主背景 |
| `--color-background-elevated` | `#0a0a0f` | 侧边栏、卡片默认背景 |
| `--color-background-card` | `rgba(255, 255, 255, 0.02)` | 卡片内容区 |
| `--color-background-hover` | `rgba(255, 255, 255, 0.04)` | 悬停背景 |

### 2.4 文字色 (Foreground)
| Token | 值 | 用途 |
|-------|-----|------|
| `--color-text-primary` | `#ffffff` | 标题、重要文字 |
| `--color-text-secondary` | `rgba(255, 255, 255, 0.7)` | 正文、描述 |
| `--color-text-tertiary` | `rgba(255, 255, 255, 0.4)` | 辅助信息、时间戳 |
| `--color-text-muted` | `rgba(255, 255, 255, 0.5)` | 占位符、禁用状态 |

### 2.5 状态色 (Status)
| 状态 | 颜色 | Token |
|------|------|-------|
| 成功 (Success) | `#22c55e` | `--color-success` |
| 警告 (Warning) | `#f59e0b` | `--color-warning` |
| 错误 (Error) | `#ef4444` | `--color-error` |
| 信息 (Info) | `#3b82f6` | `--color-info` |

### 2.6 边框与分割线
| Token | 值 | 用途 |
|-------|-----|------|
| `--color-border` | `rgba(255, 255, 255, 0.1)` | 卡片边框、分割线 |
| `--color-border-hover` | `rgba(255, 255, 255, 0.2)` | 悬停时边框 |
| `--color-divider` | `rgba(255, 255, 255, 0.05)` | 内部分割线 |

---

## 3. 字体系统

### 3.1 字体族
```css
--font-sans: 'Inter', system-ui, -apple-system, 'PingFang SC', 'Microsoft YaHei', sans-serif;
--font-mono: 'JetBrains Mono', 'Fira Code', monospace;
```

### 3.2 字号规范
| 级别 | 大小 | 字重 | 行高 | 用途 |
|------|------|------|------|------|
| H1 | 2rem (32px) | 700 | 1.2 | 页面大标题 |
| H2 | 1.5rem (24px) | 600 | 1.3 | 区块标题 |
| H3 | 1.25rem (20px) | 600 | 1.4 | 卡片标题 |
| H4 | 1.125rem (18px) | 500 | 1.4 | 小标题 |
| Body | 1rem (16px) | 400 | 1.5 | 正文 |
| Small | 0.875rem (14px) | 400 | 1.5 | 辅助文字 |
| XSmall | 0.75rem (12px) | 400 | 1.5 | 标签、时间 |

### 3.3 字重规范
| 字重 | 值 | 用途 |
|------|-----|------|
| Regular | 400 | 正文 |
| Medium | 500 | 按钮、导航 |
| Semibold | 600 | 标题 |
| Bold | 700 | 大标题、强调 |

---

## 4. 间距系统

### 4.1 基础单位
基础单位: `4px` (0.25rem)

| Token | 值 | 用途 |
|-------|-----|------|
| `--space-1` | 0.25rem (4px) | 图标内边距 |
| `--space-2` | 0.5rem (8px) | 小间距 |
| `--space-3` | 0.75rem (12px) | 按钮内边距 |
| `--space-4` | 1rem (16px) | 标准间距 |
| `--space-5` | 1.25rem (20px) | 卡片内边距 |
| `--space-6` | 1.5rem (24px) | 区块间距 |
| `--space-8` | 2rem (32px) | 大区块间距 |
| `--space-10` | 2.5rem (40px) | 页面内边距 |
| `--space-12` | 3rem (48px) | 大标题间距 |

### 4.2 组件间距
| 组件 | 内边距 | 说明 |
|------|--------|------|
| Card | 1.5rem (24px) | 标准卡片 |
| Button (sm) | 0.5rem 0.75rem | 小按钮 |
| Button (default) | 0.5rem 1rem | 默认按钮 |
| Button (lg) | 0.75rem 1.5rem | 大按钮 |
| Input | 0.5rem 0.75rem | 输入框 |
| NavItem | 0.5rem 0.75rem | 导航项 |

---

## 5. 圆角系统

| Token | 值 | 用途 |
|-------|-----|------|
| `--radius-sm` | 0.375rem (6px) | 小元素、标签 |
| `--radius-md` | 0.5rem (8px) | 按钮、输入框 |
| `--radius-lg` | 0.75rem (12px) | 卡片、容器 |
| `--radius-xl` | 1rem (16px) | 大卡片、模态框 |
| `--radius-2xl` | 1.5rem (24px) | 特色卡片 |
| `--radius-full` | 9999px | 圆形元素、头像 |

---

## 6. 阴影系统

| Token | 值 | 用途 |
|-------|-----|------|
| `--shadow-sm` | `0 1px 2px rgba(0,0,0,0.3)` | 轻微阴影 |
| `--shadow-md` | `0 4px 6px rgba(0,0,0,0.4)` | 卡片阴影 |
| `--shadow-lg` | `0 10px 15px rgba(0,0,0,0.5)` | 模态框、下拉菜单 |
| `--shadow-glow-primary` | `0 0 20px rgba(99, 102, 241, 0.4)` | 主色发光效果 |
| `--shadow-glow-accent` | `0 0 20px rgba(34, 211, 238, 0.4)` | 强调色发光效果 |

---

## 7. 组件规范

### 7.1 按钮 (Button)

#### 变体 (Variants)
| 变体 | 背景 | 文字 | 边框 | 悬停背景 |
|------|------|------|------|----------|
| Default | `--color-primary` | white | none | `--color-primary-hover` |
| Outline | transparent | `--color-text-secondary` | `--color-border` | `rgba(255,255,255,0.1)` |
| Ghost | transparent | `--color-text-secondary` | none | `rgba(255,255,255,0.1)` |
| Destructive | `--color-error` | white | none | 深红色 |

#### 尺寸 (Sizes)
| 尺寸 | 高度 | 内边距 | 字号 |
|------|------|--------|------|
| sm | 2rem (32px) | 0 0.75rem | 0.75rem |
| default | 2.25rem (36px) | 0 1rem | 0.875rem |
| lg | 2.5rem (40px) | 0 1.5rem | 1rem |

### 7.2 卡片 (Card)

#### 基础样式
```css
background: rgba(255, 255, 255, 0.02);
border: 1px solid rgba(255, 255, 255, 0.1);
border-radius: 0.75rem;
padding: 1.5rem;
```

#### 变体
| 变体 | 背景 | 边框 | 用途 |
|------|------|------|------|
| Default | `rgba(255,255,255,0.02)` | `rgba(255,255,255,0.1)` | 标准卡片 |
| Elevated | `#0a0a0f` | `rgba(255,255,255,0.1)` | 侧边栏、导航 |
| Glass | `rgba(255,255,255,0.05)` + blur | `rgba(255,255,255,0.1)` | 浮层、模态框 |
| Active | `rgba(99,102,241,0.1)` | `--color-primary` | 选中状态 |

### 7.3 输入框 (Input)

#### 基础样式
```css
background: transparent;
border: 1px solid rgba(255, 255, 255, 0.1);
border-radius: 0.5rem;
padding: 0.5rem 0.75rem;
color: white;
```

#### 状态
| 状态 | 边框 | 背景 |
|------|------|------|
| Default | `rgba(255,255,255,0.1)` | transparent |
| Focus | `--color-primary` | transparent |
| Disabled | `rgba(255,255,255,0.05)` | `rgba(255,255,255,0.02)` |

### 7.4 徽章 (Badge)

#### 变体
| 变体 | 背景 | 文字 | 用途 |
|------|------|------|------|
| Default | `rgba(255,255,255,0.1)` | `--color-text-secondary` | 默认标签 |
| Success | `rgba(34,197,94,0.2)` | `#22c55e` | 成功状态 |
| Warning | `rgba(245,158,11,0.2)` | `#f59e0b` | 警告状态 |
| Error | `rgba(239,68,68,0.2)` | `#ef4444` | 错误状态 |
| Primary | `rgba(99,102,241,0.2)` | `--color-primary` | 主色标签 |

### 7.5 导航 (Navigation)

#### 侧边栏导航项
```css
/* 默认 */
color: rgba(255, 255, 255, 0.7);
background: transparent;
padding: 0.5rem 0.75rem;
border-radius: 0.5rem;

/* 悬停 */
background: rgba(255, 255, 255, 0.1);
color: white;

/* 激活 */
background: rgba(99, 102, 241, 0.1);
color: #6366f1;
```

---

## 8. 布局规范

### 8.1 页面结构
```
Page
├── Sidebar (fixed, 16rem width)
└── Main (margin-left: 16rem)
    ├── Header (optional)
    └── Content (padding: 2rem, max-width: 80rem)
```

### 8.2 响应式断点
| 断点 | 宽度 | 说明 |
|------|------|------|
| sm | 640px | 小屏手机 |
| md | 768px | 平板 |
| lg | 1024px | 小桌面 |
| xl | 1280px | 标准桌面 |
| 2xl | 1400px | 大桌面 |

### 8.3 容器宽度
- 最大宽度: `80rem` (1280px)
- 内容区最大宽度: `64rem` (1024px)
- 窄内容区: `48rem` (768px)

---

## 9. 动效规范

### 9.1 过渡时间
| 用途 | 时长 | 缓动函数 |
|------|------|----------|
| 微交互（hover） | 150ms | ease-out |
| 按钮点击 | 100ms | ease-in-out |
| 卡片悬停 | 200ms | ease-out |
| 模态框出现 | 300ms | cubic-bezier(0.4, 0, 0.2, 1) |
| 页面切换 | 300ms | ease-in-out |

### 9.2 预设动画
| 动画 | 描述 | 用途 |
|------|------|------|
| fade-in | 淡入 | 内容加载 |
| slide-in-right | 从右滑入 | 侧边栏 |
| slide-in-up | 从下向上滑入 | 模态框 |
| pulse-glow | 发光脉冲 | 装饰性背景 |
| spin | 旋转 | 加载图标 |

---

## 10. 图标规范

### 10.1 图标库
使用 `lucide-vue-next`，统一风格为线性图标。

### 10.2 图标尺寸
| 尺寸 | 用途 |
|------|------|
| 12px (h-3 w-3) | 小按钮内 |
| 16px (h-4 w-4) | 标准按钮、输入框 |
| 20px (h-5 w-5) | 导航项 |
| 24px (h-6 w-6) | 功能图标、标题旁 |
| 32px (h-8 w-8) | Logo、大图标 |

### 10.3 图标颜色
- 默认: `rgba(255, 255, 255, 0.7)`
- 悬停: `white`
- 主色: `--color-primary`
- 成功: `--color-success`

---

## 11. 特殊效果

### 11.1 玻璃拟态 (Glassmorphism)
```css
.glass {
  background: rgba(255, 255, 255, 0.05);
  backdrop-filter: blur(10px);
  border: 1px solid rgba(255, 255, 255, 0.1);
}
```

### 11.2 渐变文字
```css
.gradient-text {
  background: linear-gradient(135deg, #6366f1 0%, #22d3ee 100%);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
}
```

### 11.3 背景光晕
```css
.glow-background {
  position: absolute;
  width: 600px;
  height: 600px;
  border-radius: 50%;
  background: rgba(99, 102, 241, 0.1);
  filter: blur(120px);
}
```

---

## 12. Teleport 使用规范

### 12.1 使用场景
Teleport 用于将组件渲染到 DOM 的其他位置，避免 z-index 和定位问题。

### 12.2 规范要求

#### 模态框和浮层必须使用 Teleport
```vue
<template>
  <Teleport to="body">
    <div v-if="visible" class="modal-overlay">
      <div class="modal-content">
        <!-- 模态框内容 -->
      </div>
    </div>
  </Teleport>
</template>
```

#### SSR 安全封装
```vue
<script setup lang="ts">
import { ref, onMounted } from 'vue'

const isMounted = ref(false)

onMounted(() => {
  isMounted.value = true
})
</script>

<template>
  <Teleport to="body" v-if="isMounted">
    <!-- 只在客户端渲染的内容 -->
  </Teleport>
</template>
```

### 12.3 目标位置
| 目标 | 用途 |
|------|------|
| `to="body"` | 全局模态框、Toast、Dialog |
| `to="#modal-container"` | 特定容器内的模态框 |

---

## 13. SSR 安全检查说明

### 13.1 问题背景
服务端渲染（SSR）时，`window`、`document` 等浏览器对象不存在，直接访问会导致错误。

### 13.2 安全模式

#### 使用环境检测
```typescript
// ✅ 正确：检测环境后再访问浏览器对象
const isClient = typeof window !== 'undefined'

if (isClient) {
  // 安全访问 window/document
  localStorage.setItem('key', value)
}
```

#### 使用 onMounted 钩子
```vue
<script setup lang="ts">
import { onMounted, ref } from 'vue'

const clientData = ref('')

onMounted(() => {
  // onMounted 只在客户端执行
  clientData.value = localStorage.getItem('data') || ''
})
</script>
```

### 13.3 常见场景

| 场景 | 解决方案 |
|------|----------|
| localStorage/sessionStorage | 在 onMounted 中访问 |
| window/document | 使用 typeof 检测或 onMounted |
| 浏览器 API (Notification) | 在 onMounted 中初始化 |
| 第三方库（依赖 window）| 动态导入或客户端标记 |

---

## 14. 全局 Toast 系统

### 14.1 系统概述
使用全局 `useToast` composable 提供统一的 Toast 通知体验。

### 14.2 使用方式

#### 在组件中使用
```vue
<script setup lang="ts">
import { useToast } from '@/composables/useToast'

const { showToast } = useToast()

const handleAction = () => {
  showToast('操作成功', 'success')
}
</script>
```

#### 在 composable 中使用
```typescript
import { useToast } from '@/composables/useToast'

export function useStudentActions() {
  const { showToast } = useToast()
  
  const deleteStudent = async (id: string) => {
    try {
      await api.deleteStudent(id)
      showToast('学生已删除', 'success')
    } catch (error) {
      showToast('删除失败', 'error')
    }
  }
  
  return { deleteStudent }
}
```

### 14.3 Toast 类型
| 类型 | 用途 | 颜色 |
|------|------|------|
| success | 操作成功 | 绿色 `#22c55e` |
| error | 操作失败 | 红色 `#ef4444` |
| warning | 警告提示 | 黄色 `#f59e0b` |
| info | 普通信息 | 蓝色 `#3b82f6` |

### 14.4 位置配置
```typescript
// Toast 默认位置
position: 'top-right' | 'top-center' | 'top-left' | 
          'bottom-right' | 'bottom-center' | 'bottom-left'
```

---

## 15. 命名规范

### 15.1 CSS 类名
使用 Tailwind CSS 命名约定，自定义类名前加前缀避免冲突：
- 组件类: `ch-` (ClassHub)
- 工具类: 直接使用 Tailwind

### 15.2 CSS 变量
```
--color-{property}
--space-{scale}
--radius-{scale}
--shadow-{scale}
--font-{property}
```

---

## 16. 文件组织

```
frontend-v3/
├── src/
│   ├── styles/
│   │   ├── index.css          # 主样式入口
│   │   ├── tokens.css         # CSS 变量定义
│   │   ├── components.css     # 组件样式
│   │   └── utilities.css      # 工具类
│   ├── components/ui/         # UI 组件
│   │   ├── Button.vue
│   │   ├── Card.vue
│   │   ├── Input.vue
│   │   ├── Dialog.vue         # 使用 Teleport
│   │   ├── Toast.vue          # 全局 Toast
│   │   └── ...
│   └── composables/           # Composables
│       ├── useToast.ts        # 全局 Toast
│       └── ...
└── DESIGN_SYSTEM.md           # 本文档
```

---

## 17. 更新日志

### v1.1.0 (2026-03-27)
- 添加 Teleport 使用规范
- 添加 SSR 安全检查说明
- 添加全局 Toast 系统说明
- 更新文件组织结构

### v1.0.0 (2026-03-23)
- 初始版本
- 定义完整的色彩、字体、间距系统
- 规范常用组件样式
- 建立布局与响应式标准

---

**注：所有前端开发必须遵循此设计体系，确保视觉一致性。**
