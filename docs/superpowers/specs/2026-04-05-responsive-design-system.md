# ClassHub 响应式设计系统改造方案

**版本**: 1.0.0  
**日期**: 2026-04-05  
**状态**: 待实施

---

## 1. 背景与目标

### 1.1 现状问题

ClassHub 前端目前**完全没有移动端适配**:
- `tokens.css` 和 `components.css` 使用大量固定像素值
- 无响应式断点支持
- `DashboardLayout.vue` 使用固定 256px 侧边栏，在小屏幕上无法使用
- 表格组件无移动端适配
- 触摸目标小于 44px 标准

### 1.2 目标

**完全替换固定像素值为响应式方案**，使系统在手机浏览器上正常使用，同时保持桌面端体验不变。

---

## 2. 设计方案

### 2.1 响应式断点

| 断点 | 宽度 | 设备类型 |
|------|------|----------|
| `default` | < 640px | 手机竖屏 |
| `sm` | ≥ 640px | 手机横屏/大手机 |
| `md` | ≥ 768px | 平板竖屏 |
| `lg` | ≥ 1024px | 平板横屏/小桌面 |
| `xl` | ≥ 1280px | 标准桌面 |

### 2.2 核心策略

**CSS 变量 + Tailwind 响应式前缀** 组合方式:
- 基础样式为移动端优先
- 使用 `@media (min-width: ...)` 覆盖桌面端样式
- 保持与现有 Tailwind 约定一致

---

## 3. 详细设计

### 3.1 tokens.css 改造

新增响应式变量:

```css
@theme inline {
  /* 响应式断点 */
  --breakpoint-sm: 640px;
  --breakpoint-md: 768px;
  --breakpoint-lg: 1024px;
  --breakpoint-xl: 1280px;

  /* 触摸目标标准 */
  --touch-target-min: 2.75rem;      /* 44px */
  --touch-target-comfort: 3rem;     /* 48px */

  /* 间距系统（保持现有，组件中使用响应式覆盖）*/
  --space-1: 0.25rem;
  --space-2: 0.5rem;
  --space-3: 0.75rem;
  --space-4: 1rem;
  --space-5: 1.25rem;
  --space-6: 1.5rem;
  --space-8: 2rem;
  --space-10: 2.5rem;
  --space-12: 3rem;
  --space-16: 4rem;
}
```

### 3.2 components.css 改造

#### 按钮组件 (ch-button)

**移动端优先**（默认样式）:
- 最小高度: 48px (`--touch-target-comfort`)
- 内边距: `0 1.25rem`
- 字体大小: `1rem`（防止 iOS 缩放）

**桌面端覆盖**（@media md）:
- 高度: 36px
- 内边距: `0 1rem`
- 字体大小: `0.875rem`

```css
.ch-button {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  gap: 0.5rem;
  border-radius: var(--radius-md);
  font-weight: 500;
  transition: all var(--duration-fast) ease-out;
  cursor: pointer;
  border: none;
  outline: none;
  /* 移动端优先 */
  min-height: var(--touch-target-comfort);
  padding: 0 1.25rem;
  font-size: 1rem;
}

@media (min-width: 768px) {
  .ch-button {
    min-height: 2.25rem;
    padding: 0 1rem;
    font-size: 0.875rem;
  }
}
```

#### 输入框组件 (ch-input)

**关键**: 移动端字体必须 16px 防止 iOS 自动缩放

```css
.ch-input {
  width: 100%;
  background-color: transparent;
  border: 1px solid var(--color-border);
  border-radius: var(--radius-md);
  color: var(--color-text-primary);
  transition: all var(--duration-fast) ease-out;
  /* 移动端优先 */
  padding: 0.625rem 0.875rem;
  font-size: 1rem;              /* 防止 iOS 缩放 */
  min-height: var(--touch-target-min);
}

@media (min-width: 768px) {
  .ch-input {
    padding: 0.5rem 0.75rem;
    font-size: 0.875rem;
    min-height: auto;
  }
}
```

#### 对话框组件 (ch-dialog)

**移动端**:
- 宽度: `calc(100vw - 2rem)`（全屏减边距）
- 最大高度: `90vh`
- 内边距: `1rem`
- 圆角: 保持 `var(--radius-xl)`

**桌面端**（@media sm）:
- 最小宽度: `24rem`
- 最大宽度: `32rem`
- 内边距: `1.5rem`

```css
.ch-dialog {
  position: fixed;
  left: 50%;
  top: 50%;
  transform: translate(-50%, -50%);
  background-color: var(--color-background-elevated);
  border: 1px solid var(--color-border);
  border-radius: var(--radius-xl);
  z-index: var(--z-modal);
  box-shadow: var(--shadow-lg);
  /* 移动端优先 */
  padding: var(--space-4);
  width: calc(100vw - 2rem);
  max-width: 100%;
  max-height: 90vh;
  overflow-y: auto;
}

@media (min-width: 640px) {
  .ch-dialog {
    padding: var(--space-6);
    width: auto;
    min-width: 24rem;
    max-width: 90vw;
  }
}

@media (min-width: 768px) {
  .ch-dialog {
    min-width: 28rem;
    max-width: 32rem;
  }
}
```

#### 卡片组件 (ch-card)

```css
.ch-card {
  background-color: var(--color-background-card);
  border: 1px solid var(--color-border);
  border-radius: var(--radius-lg);
  transition: all var(--duration-normal) ease-out;
  /* 移动端优先 */
  padding: var(--space-4);
}

@media (min-width: 768px) {
  .ch-card {
    padding: var(--space-6);
  }
}
```

#### Toast 组件 (ch-toast)

**移动端**: 底部全宽，左右边距  
**桌面端**: 右下角固定宽度

```css
.ch-toast {
  position: fixed;
  padding: var(--space-4);
  border-radius: var(--radius-lg);
  border: 1px solid var(--color-border);
  z-index: var(--z-toast);
  animation: slide-in-up var(--duration-slow) ease-out;
  /* 移动端优先 */
  bottom: var(--space-4);
  left: var(--space-4);
  right: var(--space-4);
}

@media (min-width: 640px) {
  .ch-toast {
    left: auto;
    right: var(--space-6);
    bottom: var(--space-6);
    min-width: 20rem;
    max-width: 24rem;
  }
}
```

### 3.3 DashboardLayout.vue 改造

**布局结构完全重写**:

```vue
<template>
  <div class="min-h-screen bg-background">
    <!-- 移动端：顶部导航栏 -->
    <header class="lg:hidden fixed top-0 left-0 right-0 h-14 z-50
                   bg-[#0a0a0f] border-b border-white/10
                   flex items-center justify-between px-4">
      <div class="flex items-center gap-2">
        <GraduationCap class="h-6 w-6 text-primary" />
        <span class="text-lg font-bold text-white">智慧课堂</span>
      </div>
      <button @click="showMobileMenu = true" class="p-2 -mr-2 touch-target">
        <Menu class="h-6 w-6 text-white" />
      </button>
    </header>

    <!-- 桌面端：固定侧边栏 -->
    <aside class="hidden lg:fixed lg:left-0 lg:top-0 lg:z-40
                  lg:h-screen lg:w-64 lg:block
                  border-r border-white/10 bg-[#0a0a0f]">
      <!-- 现有侧边栏内容保持不变 -->
    </aside>

    <!-- 移动端：抽屉菜单 -->
    <MobileDrawer v-model:open="showMobileMenu" class="lg:hidden">
      <!-- 导航内容 -->
    </MobileDrawer>

    <!-- 移动端：底部导航栏（学生/教师） -->
    <BottomNav v-if="!isAdmin" class="lg:hidden" />

    <!-- 主内容区：响应式边距 -->
    <main class="min-h-screen p-4 pt-16 pb-20
                  lg:ml-64 lg:p-8 lg:pt-8 lg:pb-8">
      <div class="mx-auto max-w-7xl">
        <RouterView />
      </div>
    </main>
  </div>
</template>
```

**关键变化**:
- `< 1024px`: 隐藏侧边栏，显示顶部导航栏
- `≥ 1024px`: 显示固定侧边栏，隐藏移动端导航
- 主内容区内边距响应式：`p-4` (移动端) → `lg:p-8` (桌面端)
- 移动端顶部预留 `pt-16` (64px) 给顶部栏
- 移动端底部预留 `pb-20` (80px) 给底部导航

### 3.4 关键页面改造

#### 排行榜页面 (student/Leaderboard.vue)

**双视图方案**：小屏幕卡片，大屏幕表格

```vue
<template>
  <div class="space-y-6">
    <!-- 小屏幕 (< 1024px): 卡片列表 -->
    <div class="lg:hidden space-y-3">
      <div v-for="student in students" :key="student.student_id"
           class="bg-white/[0.02] rounded-lg p-4 border border-white/10">
        <div class="flex items-center justify-between">
          <div class="flex items-center gap-3">
            <RankBadge :rank="student.rank" />
            <div>
              <p class="font-medium text-white">{{ student.name }}</p>
              <p v-if="activeTab === 'school'" class="text-xs text-white/60">
                {{ student.class_name }}
              </p>
            </div>
          </div>
          <span class="text-lg font-bold text-primary">{{ student.score }}</span>
        </div>
      </div>
    </div>

    <!-- 大屏幕 (≥ 1024px): 表格 -->
    <div class="hidden lg:block">
      <Card class="overflow-hidden">
        <table class="w-full">
          <!-- 现有表格内容 -->
        </table>
      </Card>
    </div>
  </div>
</template>
```

#### 学生列表页面

类似改造：小屏幕卡片展示学生信息，大屏幕表格。

---

## 4. 实施范围

### 4.1 需修改的文件清单

| 优先级 | 文件路径 | 改动类型 | 说明 |
|--------|----------|----------|------|
| P0 | `src/styles/tokens.css` | 新增 | 添加响应式变量 |
| P0 | `src/styles/components.css` | 重写 | 所有组件添加 @media 查询 |
| P0 | `src/layouts/DashboardLayout.vue` | 重写 | 响应式布局结构 |
| P0 | `src/components/ui/Dialog.vue` | 修改 | 响应式宽度 |
| P0 | `src/components/ui/Card.vue` | 修改 | 响应式内边距 |
| P1 | `src/views/student/Leaderboard.vue` | 重写 | 表格/卡片双视图 |
| P1 | `src/views/student/Checkin.vue` | 修改 | 触摸优化 |
| P1 | `src/views/teacher/ClassSession.vue` | 修改 | 表单响应式 |
| P1 | `src/views/admin/Students.vue` | 修改 | 表格响应式 |
| P1 | `src/views/teacher/Students.vue` | 修改 | 卡片网格响应式 |
| P2 | `src/components/ui/Button.vue` | 修改 | 移除固定尺寸 |
| P2 | `src/components/ui/Input.vue` | 修改 | 响应式高度 |

### 4.2 需新增的文件

| 文件路径 | 说明 |
|----------|------|
| `src/components/ui/MobileDrawer.vue` | 移动端抽屉菜单 |
| `src/components/ui/BottomNav.vue` | 移动端底部导航 |

---

## 5. 验证标准

### 5.1 设备测试矩阵

| 设备 | 分辨率 | 必测页面 |
|------|--------|----------|
| iPhone SE | 375×667 | 签到、排行榜、个人中心 |
| iPhone 14 | 390×844 | 签到、排行榜、课表 |
| iPad Mini | 768×1024 | 所有页面 |
| Desktop | 1920×1080 | 所有页面（回归测试） |

### 5.2 功能检查清单

- [ ] 所有可点击元素尺寸 ≥ 44×44px
- [ ] 输入框字体大小 = 16px（防止 iOS 缩放）
- [ ] 侧边栏在 < 1024px 自动折叠为抽屉
- [ ] 表格在 < 1024px 自动切换为卡片
- [ ] Toast 在移动端全宽显示，桌面端固定宽度
- [ ] 对话框在移动端全屏减边距，桌面端居中固定宽度
- [ ] 底部导航栏在移动端可见，桌面端隐藏

### 5.3 回归测试

- [ ] 桌面端 (≥ 1280px) 外观与改造前完全一致
- [ ] 所有现有测试通过
- [ ] 构建无警告/错误

---

## 6. 风险评估

| 风险 | 影响 | 缓解措施 |
|------|------|----------|
| 样式冲突 | 高 | 使用 Tailwind 前缀隔离，逐步验证 |
| 桌面端回归 | 中 | 改造前后截图对比，lg: 前缀确保桌面端不变 |
| 性能影响 | 低 | @media 查询开销极小，可忽略 |

---

## 7. 附录

### 7.1 命名约定

- 移动端优先：默认样式为移动端
- 桌面端覆盖：使用 `@media (min-width: 768px)` 等
- Tailwind 类：继续使用 `lg:hidden` 等响应式前缀

### 7.2 参考标准

- [WCAG 2.1 - Target Size](https://www.w3.org/WAI/WCAG21/Understanding/target-size.html): 44×44px 最小触摸目标
- [Apple Human Interface Guidelines](https://developer.apple.com/design/human-interface-guidelines/ios/visual-design/adaptivity-and-layout/): iOS 设计规范
- [Material Design Breakpoints](https://material.io/design/layout/responsive-layout-grid.html#breakpoints): 响应式断点

---

**文档版本**: 1.0.0  
**最后更新**: 2026-04-05
