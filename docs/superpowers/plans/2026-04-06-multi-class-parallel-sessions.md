# 多班级并行上课功能实施计划

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 完善多班级并行上课功能的前端交互，包括单课堂状态下的"开始新课堂"入口、移动端下拉选择器、软限制警告、网络错误提示、空班级检查。

**Architecture:** 基于现有 Vue 3 + TanStack Query 架构，扩展 ClassSession.vue 组件，添加智能刷新策略和边界情况处理。保持后端 API 不变。

**Tech Stack:** Vue 3.5, TypeScript, TanStack Query v5, Tailwind CSS v4, Lucide Vue

---

## 文件变更清单

| 文件 | 操作 | 说明 |
|------|------|------|
| `frontend-v3/src/views/teacher/ClassSession.vue` | 修改 | 主界面：添加开始新课堂按钮、表单、移动端适配 |
| `frontend-v3/src/composables/useClassSession.ts` | 修改 | 智能刷新策略 |
| `frontend-v3/src/composables/useNetworkError.ts` | 新建 | 网络错误状态管理 |
| `frontend-v3/src/components/ui/NetworkErrorBanner.vue` | 新建 | 网络错误提示组件 |
| `frontend-v3/src/composables/index.ts` | 修改 | 导出新增 composable |
| `tests/e2e/multi-class-session.spec.ts` | 新建 | E2E测试 |

---

## Task 1: 创建网络错误状态管理 Composable

**Files:**
- Create: `frontend-v3/src/composables/useNetworkError.ts`
- Modify: `frontend-v3/src/composables/index.ts`

**Why:** 集中管理网络错误状态，供多个组件共享错误提示和重试逻辑。

- [x] **Step 1: 创建 useNetworkError.ts**

```typescript
import { ref, readonly } from 'vue'

const networkError = ref<Error | null>(null)
const isOffline = ref(false)

export function useNetworkError() {
  const setError = (error: Error | null) => {
    networkError.value = error
    isOffline.value = error !== null
  }

  const clearError = () => {
    networkError.value = null
    isOffline.value = false
  }

  return {
    networkError: readonly(networkError),
    isOffline: readonly(isOffline),
    setError,
    clearError,
  }
}
```

- [x] **Step 2: 在 index.ts 中导出**

```typescript
// frontend-v3/src/composables/index.ts
export { useNetworkError } from './useNetworkError'
```

- [x] **Step 3: Commit**

```bash
git add frontend-v3/src/composables/useNetworkError.ts frontend-v3/src/composables/index.ts
git commit -m "feat: add useNetworkError composable for centralized error handling"
```

---

## Task 2: 创建网络错误提示组件

**Files:**
- Create: `frontend-v3/src/components/ui/NetworkErrorBanner.vue`
- Modify: `frontend-v3/src/components/ui/index.ts`

**Why:** 统一的网络错误提示 UI，支持重试操作。

- [x] **Step 1: 创建 NetworkErrorBanner.vue**

```vue
<script setup lang="ts">
import { AlertTriangle, RefreshCw, X } from 'lucide-vue-next'
import { Button } from './Button'

interface Props {
  message?: string
}

withDefaults(defineProps<Props>(), {
  message: '网络连接失败，数据同步异常',
})

const emit = defineEmits<{
  retry: []
  dismiss: []
}>()
</script>

<template>
  <div
    class="fixed top-0 left-0 right-0 z-50 bg-red-500/90 backdrop-blur-sm text-white px-4 py-3 shadow-lg"
    role="alert"
  >
    <div class="flex items-center justify-between max-w-7xl mx-auto">
      <div class="flex items-center gap-2">
        <AlertTriangle class="h-5 w-5 flex-shrink-0" />
        <span class="text-sm font-medium">{{ message }}</span>
      </div>
      
      <div class="flex items-center gap-2">
        <Button
          variant="ghost"
          size="sm"
          class="text-white hover:bg-white/20"
          @click="emit('retry')"
        >
          <RefreshCw class="h-4 w-4 mr-1" />
          重试
        </Button>
        <Button
          variant="ghost"
          size="sm"
          class="text-white hover:bg-white/20 p-1"
          @click="emit('dismiss')"
        >
          <X class="h-4 w-4" />
        </Button>
      </div>
    </div>
  </div>
</template>
```

- [x] **Step 2: 在 ui/index.ts 中导出**

```typescript
// Add to existing exports
export { default as NetworkErrorBanner } from './NetworkErrorBanner.vue'
```

- [x] **Step 3: Commit**

```bash
git add frontend-v3/src/components/ui/NetworkErrorBanner.vue frontend-v3/src/components/ui/index.ts
git commit -m "feat: add NetworkErrorBanner component for network error display"
```

---

## Task 3: 修改 useClassSession 添加智能刷新

**Files:**
- Modify: `frontend-v3/src/composables/useClassSession.ts`

**Why:** 当前班级5秒刷新，无课堂时30秒刷新，节省资源。

- [x] **Step 1: 修改 useClassSessions 函数**

```typescript
export function useClassSessions() {
  const { data, isPending, error, refetch } = useQuery({
    queryKey: ['classSessions'],
    queryFn: async () => {
      const sessions = await classSessionApi.getCurrent()
      if (sessions && sessions.length > 0) {
        safeLocalStorage.setItem('activeClassSessions', JSON.stringify(sessions))
        return sessions
      }
      safeLocalStorage.removeItem('activeClassSessions')
      return []
    },
    // 智能刷新策略
    refetchInterval: (data) => {
      // 有活跃课堂时5秒刷新，否则30秒
      return data && data.length > 0 ? 5000 : 30000
    },
    staleTime: 3000,
    refetchOnWindowFocus: true,
    retry: 0, // 不重试，立即显示错误
  })

  return { data, isPending, error, refetch }
}
```

- [x] **Step 2: Commit**

```bash
git add frontend-v3/src/composables/useClassSession.ts
git commit -m "feat: add smart refresh strategy to useClassSessions (5s active/30s idle)"
```

---

## Task 4: 重构 ClassSession.vue - 添加状态定义和计算属性

**Files:**
- Modify: `frontend-v3/src/views/teacher/ClassSession.vue`

**Why:** 添加开始新课堂表单状态、软限制检查、空班级检查所需的状态和计算属性。

- [x] **Step 1: 在状态定义区域添加新状态**

```typescript
// ===== 状态定义 =====
const className = ref('')
const courseName = ref('')
const studentCode = ref('')
const searchQuery = ref('')

// 新增状态
const showStartForm = ref(false)      // 显示开始新课堂表单
const softLimitWarning = ref(false)   // 显示软限制警告

// 常量定义
const SOFT_LIMIT = 5  // 软限制：5个班级
```

- [x] **Step 2: 在计算属性区域添加新属性**

```typescript
// ===== 计算属性 =====
const isSessionActive = computed(() => activeSessions.value?.length > 0)
const hasMultipleSessions = computed(() => (activeSessions.value?.length || 0) > 1)

// 新增计算属性
const sessionCount = computed(() => activeSessions.value?.length || 0)
const nearSoftLimit = computed(() => sessionCount.value >= 3)
const atSoftLimit = computed(() => sessionCount.value >= SOFT_LIMIT)

// 当前选中班级（桌面端标签页，移动端下拉）
const currentActiveClass = computed(() => selectedSession.value?.class_name || '')
```

- [x] **Step 3: Commit**

```bash
git add frontend-v3/src/views/teacher/ClassSession.vue
git commit -m "feat: add new state and computed properties for multi-session management"
```

---

## Task 5: 重构 ClassSession.vue - 修改事件处理函数

**Files:**
- Modify: `frontend-v3/src/views/teacher/ClassSession.vue`

**Why:** 添加空班级检查、软限制警告、表单关闭逻辑。

- [x] **Step 1: 修改 handleStartSession 函数**

```typescript
const handleStartSession = async () => {
  if (!className.value) {
    showErrorToast('请选择班级')
    return
  }

  // 空班级检查
  const students = classStudents.value
  if (students && students.length === 0) {
    showErrorToast('该班级暂无学生，无法开启课堂')
    return
  }

  // 软限制检查
  if (atSoftLimit.value) {
    softLimitWarning.value = true
    return
  }

  try {
    await startSession({
      className: className.value,
      courseName: courseName.value || undefined
    })
    showSuccessToast('课堂已开始！')
    activeTab.value = className.value
    className.value = ''
    courseName.value = ''
    showStartForm.value = false
    softLimitWarning.value = false
  } catch (err: unknown) {
    showErrorToast(getErrorMessage(err) || '开始课堂失败')
  }
}
```

- [x] **Step 2: 添加软限制继续函数**

```typescript
const handleContinueDespiteLimit = async () => {
  softLimitWarning.value = false
  
  try {
    await startSession({
      className: className.value,
      courseName: courseName.value || undefined
    })
    showSuccessToast('课堂已开始！')
    activeTab.value = className.value
    className.value = ''
    courseName.value = ''
    showStartForm.value = false
  } catch (err: unknown) {
    showErrorToast(getErrorMessage(err) || '开始课堂失败')
  }
}

const handleCancelStart = () => {
  softLimitWarning.value = false
  showStartForm.value = false
  className.value = ''
  courseName.value = ''
}
```

- [x] **Step 3: Commit**

```bash
git add frontend-v3/src/views/teacher/ClassSession.vue
git commit -m "feat: update event handlers with empty class check and soft limit warning"
```

---

## Task 6: 重构 ClassSession.vue - 修改状态卡片区域

**Files:**
- Modify: `frontend-v3/src/views/teacher/ClassSession.vue`

**Why:** 在单课堂状态下显示"开始新课堂"按钮。

- [x] **Step 1: 找到 Session status Card 区域（约第230行），替换按钮部分**

```vue
        <div class="flex-shrink-0 flex gap-2">
          <template v-if="!isSessionActive">
            <Button
              :loading="isStartingSession"
              class="w-full sm:w-auto min-h-[44px]"
              @click="showStartForm = true"
            >
              <Play class="mr-2 h-4 w-4" />
              开始课堂
            </Button>
          </template>
          <template v-else>
            <Button
              variant="outline"
              :loading="isStartingSession"
              class="w-full sm:w-auto min-h-[44px] border-white/20 text-white hover:bg-white/10"
              @click="showStartForm = true"
            >
              <Plus class="mr-2 h-4 w-4" />
              开始新课堂
            </Button>
            <Button
              v-if="!hasMultipleSessions"
              variant="destructive"
              :loading="isEndingSession"
              class="w-full sm:w-auto min-h-[44px]"
              @click="handleEndSession()"
            >
              <Square class="mr-2 h-4 w-4" />
              结束课堂
            </Button>
          </template>
        </div>
```

- [x] **Step 2: Commit**

```bash
git add frontend-v3/src/views/teacher/ClassSession.vue
git commit -m "feat: add 'Start New Session' button in single session state"
```

---

## Task 7: 重构 ClassSession.vue - 添加开始新课堂表单

**Files:**
- Modify: `frontend-v3/src/views/teacher/ClassSession.vue`

**Why:** 展开/收起形式的开始课堂表单，支持软限制警告。

- [x] **Step 1: 在开始课堂表单区域（原 Card v-if="!isSessionActive"）之后，添加新的表单 Card**

```vue
    <!-- 开始新课堂表单 (在有一个或多个课堂进行时显示) -->
    <Card
      v-if="isSessionActive && showStartForm"
      class="p-4 md:p-6 mb-5 border-primary/30 bg-primary/5"
    >
      <div class="flex items-center justify-between mb-4">
        <div>
          <h3 class="font-medium text-white text-base md:text-lg">
            开始新课堂
          </h3>
          <p class="text-sm text-white/60">
            {{ hasMultipleSessions ? '同时管理另一个班级' : '添加第二个班级课堂' }}
          </p>
        </div>
        <Button
          variant="ghost"
          size="sm"
          class="text-white/60 hover:text-white"
          @click="showStartForm = false"
        >
          <X class="h-4 w-4" />
        </Button>
      </div>

      <!-- 软限制警告 -->
      <div
        v-if="nearSoftLimit"
        class="mb-4 p-3 bg-yellow-500/10 border border-yellow-500/30 rounded-lg"
      >
        <p class="text-sm text-yellow-400 flex items-center gap-2">
          <AlertTriangle class="h-4 w-4 flex-shrink-0" />
          您已开启{{ sessionCount }}个课堂，建议先结束部分课堂
        </p>
      </div>

      <!-- 强制软限制提示 -->
      <div
        v-if="softLimitWarning"
        class="mb-4 p-3 bg-red-500/10 border border-red-500/30 rounded-lg"
      >
        <p class="text-sm text-red-400 mb-2">
          您已达到软限制（{{ SOFT_LIMIT }}个课堂），继续开启可能影响性能。
        </p>
        <div class="flex gap-2">
          <Button
            size="sm"
            variant="outline"
            class="border-red-500/30 text-red-400 hover:bg-red-500/10"
            @click="handleContinueDespiteLimit"
          >
            仍要继续
          </Button>
          <Button
            size="sm"
            variant="ghost"
            class="text-white/60"
            @click="softLimitWarning = false"
          >
            取消
          </Button>
        </div>
      </div>

      <div class="flex flex-col sm:flex-row gap-3 sm:gap-4 mb-4">
        <Select
          v-model="courseName"
          class="w-full"
          placeholder="请选择课程（可选）"
          :options="courseOptions"
        />
        <Select
          v-model="className"
          class="w-full"
          placeholder="请选择班级"
          :options="availableClassOptions"
        />
      </div>
      <div class="flex gap-2">
        <Button
          :loading="isStartingSession"
          :disabled="!className || softLimitWarning"
          class="flex-1 min-h-[44px]"
          @click="handleStartSession"
        >
          <Play class="mr-2 h-4 w-4" />
          开始上课
        </Button>
        <Button
          variant="outline"
          class="min-h-[44px] border-white/20 text-white hover:bg-white/10"
          @click="handleCancelStart"
        >
          取消
        </Button>
      </div>
    </Card>
```

- [x] **Step 2: Commit**

```bash
git add frontend-v3/src/views/teacher/ClassSession.vue
git commit -m "feat: add expandable start session form with soft limit warning"
```

---

## Task 8: 重构 ClassSession.vue - 修复按钮嵌套问题

**Files:**
- Modify: `frontend-v3/src/views/teacher/ClassSession.vue`

**Why:** 解决 `<button>` 不能嵌套在 `<button>` 中的 HTML 规范问题。

- [x] **Step 1: 找到多课堂标签区域（约第350行），修改标签按钮结构**

原代码（有问题）：
```vue
<button class="...">  // 外层按钮
  <span>{{ session.class_name }}</span>
  <button @click.stop="...">  // 内层按钮 - 非法！
    <X />
  </button>
</button>
```

修改为：
```vue
<div class="...">  // 外层改为 div
  <button class="flex-1 text-left" @click="handleTabChange(...)">
    <span>{{ session.class_name }}</span>
  </button>
  <button class="close-btn" @click="handleEndSession(...)">
    <X />
  </button>
</div>
```

具体修改：

```vue
    <!-- Multi-session tabs (Desktop) -->
    <div
      v-if="hasMultipleSessions"
      class="mb-5"
    >
      <div class="flex flex-wrap gap-2">
        <div
          v-for="session in activeSessions"
          :key="session.class_name"
          class="flex items-center px-4 py-2 rounded-lg border transition-all duration-200"
          :class="activeTab === session.class_name || (!activeTab && session === activeSessions?.[0])
            ? 'bg-primary/20 border-primary text-white'
            : 'bg-white/5 border-white/10 text-white/70'"
        >
          <button
            class="flex items-center gap-2 flex-1"
            @click="handleTabChange(session.class_name)"
          >
            <Users class="h-4 w-4" />
            <span>{{ session.class_name }}</span>
            <Badge
              variant="secondary"
              class="text-xs"
            >
              {{ session.course_name || '未命名课程' }}
            </Badge>
          </button>
          <button
            class="ml-2 p-1 rounded hover:bg-white/20 text-white/50 hover:text-white transition-colors"
            title="结束此课堂"
            @click="handleEndSession(session.class_name)"
          >
            <X class="h-3 w-3" />
          </button>
        </div>
      </div>
    </div>
```

- [x] **Step 2: Commit**

```bash
git add frontend-v3/src/views/teacher/ClassSession.vue
git commit -m "fix: resolve button nesting violation in multi-session tabs"
```

---

## Task 9: 添加移动端下拉选择器（响应式适配）

**Files:**
- Modify: `frontend-v3/src/views/teacher/ClassSession.vue`

**Why:** 移动端使用下拉选择器替代标签页，节省空间。

- [x] **Step 1: 在多课堂标签区域添加响应式逻辑**

```vue
    <!-- Multi-session selector (Responsive) -->
    <div
      v-if="hasMultipleSessions"
      class="mb-5"
    >
      <!-- Desktop: Tabs -->
      <div class="hidden md:flex flex-wrap gap-2">
        <!-- 桌面端标签页（Task 8已修改） -->
        ...
      </div>

      <!-- Mobile: Dropdown -->
      <div class="md:hidden">
        <label class="block text-sm text-white/60 mb-2">当前课堂</label>
        <Select
          :model-value="activeTab || activeSessions?.[0]?.class_name"
          class="w-full"
          placeholder="选择课堂"
          :options="activeSessions?.map(s => ({
            value: s.class_name,
            label: `${s.class_name} ${s.course_name ? '(' + s.course_name + ')' : ''}`
          })) || []"
          @update:model-value="handleTabChange"
        />
      </div>
    </div>
```

- [x] **Step 2: Commit**

```bash
git add frontend-v3/src/views/teacher/ClassSession.vue
git commit -m "feat: add mobile dropdown selector for multi-session switching"
```

---

## Task 10: 集成网络错误提示

**Files:**
- Modify: `frontend-v3/src/views/teacher/ClassSession.vue`

**Why:** 在页面顶部显示网络错误提示，支持重试。

- [x] **Step 1: 在模板顶部添加 NetworkErrorBanner**

```vue
<template>
  <div>
    <!-- Network Error Banner -->
    <NetworkErrorBanner
      v-if="networkError"
      :message="networkError.message"
      @retry="handleRetry"
      @dismiss="clearError"
    />

    <!-- Header -->
    ...
</template>
```

- [x] **Step 2: 在 script setup 中添加相关引入和处理函数**

```typescript
import { NetworkErrorBanner } from '@/components/ui'
import { useNetworkError } from '@/composables'

const { networkError, setError, clearError } = useNetworkError()

// 重试所有查询
const handleRetry = () => {
  clearError()
  refetchSessions()
  refetchCheckins()
}

// 监听网络错误
watch(() => error.value, (err) => {
  if (err) {
    setError(err as Error)
  }
})
```

- [x] **Step 3: Commit**

```bash
git add frontend-v3/src/views/teacher/ClassSession.vue
git commit -m "feat: integrate network error banner with retry functionality"
```

---

## Task 11: 添加确认弹窗到结束课堂操作

**Files:**
- Modify: `frontend-v3/src/views/teacher/ClassSession.vue`

**Why:** 所有结束课堂操作都需要确认，显示签到统计。

- [x] **Step 1: 添加确认状态和处理函数**

```typescript
// 确认弹窗状态
const showEndConfirm = ref(false)
const endConfirmClassName = ref('')
const endConfirmStats = computed(() => {
  return {
    checkedIn: checkinStats.value.checkedIn,
    notCheckedIn: checkinStats.value.notCheckedIn,
  }
})

const handleEndSession = async (sessionClassName?: string) => {
  endConfirmClassName.value = sessionClassName || selectedSession.value?.class_name || ''
  showEndConfirm.value = true
}

const confirmEndSession = async () => {
  showEndConfirm.value = false
  try {
    await endSession({ className: endConfirmClassName.value })
    showSuccessToast(endConfirmClassName.value ? `${endConfirmClassName.value} 课堂已结束！` : '课堂已结束！')
    if (endConfirmClassName.value === activeTab.value) {
      activeTab.value = ''
    }
  } catch (err: unknown) {
    showErrorToast(getErrorMessage(err) || '结束课堂失败')
  }
}
```

- [x] **Step 2: 在模板底部添加确认弹窗 Dialog**

```vue
    <!-- End Session Confirmation Dialog -->
    <Dialog
      :open="showEndConfirm"
      @update:open="showEndConfirm = $event"
    >
      <DialogContent class="sm:max-w-md">
        <DialogHeader>
          <DialogTitle>确认结束课堂</DialogTitle>
          <DialogDescription>
            确定要结束【{{ endConfirmClassName }}】的课堂吗？
          </DialogDescription>
        </DialogHeader>

        <div class="py-4">
          <div class="flex justify-center gap-8 text-center">
            <div>
              <p class="text-2xl font-bold text-green-400">{{ endConfirmStats.checkedIn }}</p>
              <p class="text-sm text-white/60">已签到</p>
            </div>
            <div>
              <p class="text-2xl font-bold text-red-400">{{ endConfirmStats.notCheckedIn }}</p>
              <p class="text-sm text-white/60">未签到</p>
            </div>
          </div>
        </div>

        <DialogFooter class="flex gap-2">
          <Button
            variant="outline"
            @click="showEndConfirm = false"
          >
            取消
          </Button>
          <Button
            variant="destructive"
            @click="confirmEndSession"
          >
            确认结束
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
```

- [x] **Step 3: Commit**

```bash
git add frontend-v3/src/views/teacher/ClassSession.vue
git commit -m "feat: add confirmation dialog for ending sessions with stats display"
```

---

## Task 12: 运行类型检查

**Files:**
- All modified files

**Why:** 确保 TypeScript 类型正确。

- [x] **Step 1: 运行 vue-tsc**

```bash
cd frontend-v3
pnpm vue-tsc --noEmit
```

- [x] **Step 2: 修复任何类型错误**

如果有错误，修复后继续。

- [x] **Step 3: Commit（如有修复）**

```bash
git add .
git commit -m "fix: resolve TypeScript type errors"
```

---

## Task 13: 创建 E2E 测试

**Files:**
- Create: `tests/e2e/multi-class-session.spec.ts`

**Why:** 验证完整的多班级流程。

- [x] **Step 1: 创建测试文件**

```typescript
import { test, expect } from '@playwright/test'

test.describe('多班级并行上课功能', () => {
  test.beforeEach(async ({ page }) => {
    // 登录教师账号
    await page.goto('http://localhost:5174/login')
    await page.fill('[name="username"]', 'teacher1')
    await page.fill('[name="password"]', 'teacher123')
    await page.click('button[type="submit"]')
    await page.waitForURL('**/dashboard')
    
    // 进入课堂签到页面
    await page.click('text=课堂签到')
    await page.waitForURL('**/class-session')
  })

  test('单课堂状态下显示开始新课堂按钮', async ({ page }) => {
    // 开始第一个课堂
    await page.click('text=开始课堂')
    await page.selectOption('select', '一班')
    await page.click('button:has-text("开始上课")')
    
    // 验证显示"开始新课堂"按钮
    await expect(page.locator('button:has-text("开始新课堂")')).toBeVisible()
  })

  test('开始第二个课堂并切换', async ({ page }) => {
    // 已有第一个课堂，点击开始新课堂
    await page.click('text=开始新课堂')
    
    // 选择第二个班级
    await page.selectOption('select', '二班')
    await page.click('button:has-text("开始上课")')
    
    // 验证显示两个标签页/下拉选项
    await expect(page.locator('text=课堂进行中 (2个班级)')).toBeVisible()
    
    // 切换到第一个班级
    await page.click('text=一班')
    
    // 验证显示一班学生
    await expect(page.locator('text=班级学生列表')).toBeVisible()
  })

  test('结束单个课堂后显示剩余课堂', async ({ page }) => {
    // 有两个课堂时
    await page.click('text=一班')  // 切换到一班
    await page.click('button[title="结束此课堂"]')  // 点击结束按钮
    
    // 确认弹窗
    await page.click('button:has-text("确认结束")')
    
    // 验证只剩一个课堂
    await expect(page.locator('text=课堂进行中 (1个班级)')).toBeVisible()
  })

  test('移动端下拉选择器', async ({ page }) => {
    // 设置移动端视口
    await page.setViewportSize({ width: 375, height: 667 })
    
    // 验证显示下拉选择器而非标签页
    await expect(page.locator('label:has-text("当前课堂")')).toBeVisible()
  })
})
```

- [x] **Step 2: Commit**

```bash
git add tests/e2e/multi-class-session.spec.ts
git commit -m "test: add E2E tests for multi-class session feature"
```

---

## Task 14: 最终验证

**Files:**
- All

**Why:** 确保所有功能正常工作。

- [x] **Step 1: 检查服务状态**

```bash
cd /home/yufeng/student-manager
curl -s http://localhost:8000/api/v1/health
curl -s http://localhost:5174 | head -1
```

- [x] **Step 2: 运行后端测试**

```bash
conda run -n student-manage pytest tests/integration/test_checkin_api_enhanced.py -v
```

- [x] **Step 3: 运行前端类型检查**

```bash
cd frontend-v3
pnpm vue-tsc --noEmit
```

- [x] **Step 4: Commit（最终提交）**

```bash
git add .
git commit -m "feat: complete multi-class parallel session feature with all interactions"
```

---

## Summary

| Task | 文件 | 时间估算 |
|------|------|----------|
| 1 | useNetworkError.ts | 10分钟 |
| 2 | NetworkErrorBanner.vue | 15分钟 |
| 3 | useClassSession.ts | 10分钟 |
| 4 | ClassSession.vue - 状态 | 10分钟 |
| 5 | ClassSession.vue - 事件处理 | 15分钟 |
| 6 | ClassSession.vue - 状态卡片 | 10分钟 |
| 7 | ClassSession.vue - 表单 | 20分钟 |
| 8 | ClassSession.vue - 按钮修复 | 15分钟 |
| 9 | ClassSession.vue - 移动端 | 15分钟 |
| 10 | ClassSession.vue - 网络错误 | 15分钟 |
| 11 | ClassSession.vue - 确认弹窗 | 20分钟 |
| 12 | 类型检查 | 10分钟 |
| 13 | E2E测试 | 20分钟 |
| 14 | 最终验证 | 10分钟 |
| **总计** | | **~3小时** |

---

**Plan complete and saved to `docs/superpowers/plans/2026-04-06-multi-class-parallel-sessions.md`.**

**Execution options:**

1. **Subagent-Driven (recommended)** - Dispatch a fresh subagent per task, review between tasks
2. **Inline Execution** - Execute tasks in this session using executing-plans

Which approach would you like to use?
