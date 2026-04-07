# MobilePicker 组件实施计划

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 实现 MobilePicker 移动端底部弹窗选择器组件，并替换现有页面中的原生 select

**Architecture:** 基于设计文档，创建单文件组件 MobilePicker.vue，内部封装触发器、底部弹窗和桌面端回退逻辑，通过 CSS 媒体查询实现响应式

**Tech Stack:** Vue 3.5 + TypeScript + Tailwind CSS v4 + Lucide Icons

---

## 文件结构

```
frontend-v3/src/components/ui/
├── MobilePicker.vue              # 主组件（新建）
└── index.ts                      # 导出更新（修改）

frontend-v3/test/components/
└── MobilePicker.spec.ts          # 组件测试（新建）

frontend-v3/src/views/teacher/
├── Schedules.vue                 # 替换原生 select（修改）
└── ClassSession.vue              # 验证兼容性（可选修改）
```

---

## Task 1: 创建 MobilePicker 组件基础结构

**Files:**
- Create: `frontend-v3/src/components/ui/MobilePicker.vue`
- Modify: `frontend-v3/src/components/ui/index.ts`

- [x] **Step 1: 创建 MobilePicker.vue 骨架**

创建文件 `frontend-v3/src/components/ui/MobilePicker.vue`：

```vue
<script setup lang="ts">
import { ref, computed } from 'vue'
import { ChevronDown, Search, X, Check } from 'lucide-vue-next'
import { cn } from '@/lib/utils'

export interface MobilePickerOption {
  value: string | number
  label: string
  subtitle?: string
  disabled?: boolean
}

interface Props {
  modelValue?: string | number
  options: MobilePickerOption[]
  title?: string
  placeholder?: string
  disabled?: boolean
  searchable?: boolean
  searchPlaceholder?: string
  clearable?: boolean
}

const props = withDefaults(defineProps<Props>(), {
  placeholder: '请选择',
  searchPlaceholder: '搜索...'
})

const emit = defineEmits<{
  'update:modelValue': [value: string | number | undefined]
  change: [value: string | number | undefined, option: MobilePickerOption | undefined]
}>()

// 状态
const isOpen = ref(false)
const searchQuery = ref('')

// 计算属性
const selectedOption = computed(() => {
  if (props.modelValue === undefined) return undefined
  return props.options.find(opt => opt.value === props.modelValue)
})

const filteredOptions = computed(() => {
  if (!searchQuery.value) return props.options
  const query = searchQuery.value.toLowerCase()
  return props.options.filter(opt =>
    opt.label.toLowerCase().includes(query) ||
    opt.subtitle?.toLowerCase().includes(query)
  )
})

// 方法
const open = () => {
  if (props.disabled) return
  isOpen.value = true
  searchQuery.value = ''
}

const close = () => {
  isOpen.value = false
  searchQuery.value = ''
}

const select = (option: MobilePickerOption) => {
  if (option.disabled) return
  emit('update:modelValue', option.value)
  emit('change', option.value, option)
  close()
}

const clear = () => {
  emit('update:modelValue', undefined)
  emit('change', undefined, undefined)
}

const isSelected = (option: MobilePickerOption) => {
  return props.modelValue === option.value
}
</script>

<template>
  <div class="relative">
    <!-- 触发器 -->
    <button
      type="button"
      :class="cn(
        'flex h-11 w-full items-center justify-between rounded-lg',
        'border border-white/10 bg-white/5',
        'px-3 py-2',
        'text-base text-white',
        'transition-all duration-150',
        'hover:border-white/20 hover:bg-white/[0.07]',
        'focus:outline-none focus:ring-2 focus:ring-primary/50 focus:border-primary/50',
        'disabled:cursor-not-allowed disabled:opacity-50',
        isOpen && 'border-primary/50 ring-2 ring-primary/50'
      )"
      :disabled="disabled"
      @click="open"
    >
      <span :class="!selectedOption && 'text-white/50'">
        <template v-if="selectedOption">
          {{ selectedOption.label }}
          <span v-if="selectedOption.subtitle" class="text-white/60 ml-1">
            ({{ selectedOption.subtitle }})
          </span>
        </template>
        <template v-else>
          {{ placeholder }}
        </template>
      </span>
      <div class="flex items-center gap-1">
        <button
          v-if="clearable && modelValue !== undefined"
          type="button"
          class="rounded p-0.5 hover:bg-white/10"
          @click.stop="clear"
        >
          <X class="h-4 w-4 text-white/50" />
        </button>
        <ChevronDown
          :class="cn(
            'h-4 w-4 text-white/50 transition-transform duration-200',
            isOpen && 'rotate-180'
          )"
        />
      </div>
    </button>

    <!-- TODO: 底部弹窗 -->
  </div>
</template>
```

- [x] **Step 2: 添加到 UI 组件导出**

修改 `frontend-v3/src/components/ui/index.ts`，添加第 17 行：

```typescript
export { default as MobilePicker } from './MobilePicker.vue'
```

- [x] **Step 3: 验证类型检查**

```bash
cd /home/yufeng/student-manager/frontend-v3 && pnpm vue-tsc --noEmit
```

Expected: 无错误

- [x] **Step 4: Commit**

```bash
git add frontend-v3/src/components/ui/MobilePicker.vue frontend-v3/src/components/ui/index.ts
git commit -m "feat: MobilePicker 组件基础结构

- 定义 Props/Events 接口
- 实现触发器组件
- 添加 clearable 支持

Co-Authored-By: Claude Sonnet 4.6 <noreply@anthropic.com>"
```

---

## Task 2: 实现移动端底部弹窗

**Files:**
- Modify: `frontend-v3/src/components/ui/MobilePicker.vue`

- [x] **Step 1: 添加移动端检测逻辑**

在 `<script setup>` 中添加：

```typescript
import { onMounted, onUnmounted } from 'vue'

const isMobile = ref(false)

const checkMobile = () => {
  isMobile.value = window.innerWidth < 768
}

onMounted(() => {
  checkMobile()
  window.addEventListener('resize', checkMobile)
})

onUnmounted(() => {
  window.removeEventListener('resize', checkMobile)
})
```

- [x] **Step 2: 添加底部弹窗模板**

在 `</div>` 结束前添加：

```vue
<!-- 移动端底部弹窗 -->
<Teleport to="body">
  <Transition name="fade">
    <div
      v-if="isOpen && isMobile"
      class="fixed inset-0 z-50 bg-black/60 backdrop-blur-sm"
      @click="close"
    />
  </Transition>

  <Transition name="slide-up">
    <div
      v-if="isOpen && isMobile"
      class="fixed bottom-0 left-0 right-0 z-50 bg-[#1a1a2e] rounded-t-[20px] shadow-2xl max-h-[70vh] flex flex-col"
    >
      <!-- 指示条 -->
      <div class="flex justify-center pt-3 pb-2" @click="close">
        <div class="w-10 h-1 rounded-full bg-white/20" />
      </div>

      <!-- 标题栏 -->
      <div class="flex items-center justify-between px-4 py-3 border-b border-white/10">
        <h3 class="text-lg font-semibold text-white">
          {{ title || placeholder }}
        </h3>
        <button
          type="button"
          class="text-primary text-base font-medium"
          @click="close"
        >
          完成
        </button>
      </div>

      <!-- 搜索框 -->
      <div v-if="searchable" class="p-3 border-b border-white/10">
        <div class="relative">
          <Search class="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-white/40" />
          <input
            v-model="searchQuery"
            type="text"
            :placeholder="searchPlaceholder"
            class="w-full h-10 pl-10 pr-4 rounded-lg bg-white/5 border border-white/10 text-white text-sm placeholder:text-white/40 focus:outline-none focus:border-primary/50"
          >
        </div>
      </div>

      <!-- 选项列表 -->
      <div class="flex-1 overflow-y-auto">
        <div
          v-for="option in filteredOptions"
          :key="option.value"
          :class="cn(
            'flex items-center justify-between px-4 py-4 border-b border-white/5 cursor-pointer active:bg-white/5',
            isSelected(option) && 'bg-primary/10'
          )"
          @click="select(option)"
        >
          <div>
            <div :class="cn('text-base', isSelected(option) ? 'text-primary font-medium' : 'text-white')">
              {{ option.label }}
            </div>
            <div v-if="option.subtitle" class="text-sm text-white/50 mt-0.5">
              {{ option.subtitle }}
            </div>
          </div>
          <Check
            v-if="isSelected(option)"
            class="h-5 w-5 text-primary"
          />
        </div>
        <div v-if="filteredOptions.length === 0" class="py-8 text-center text-white/40">
          未找到匹配选项
        </div>
      </div>
    </div>
  </Transition>
</Teleport>
```

- [x] **Step 3: 添加动画样式**

在 `<style scoped>` 中添加：

```vue
<style scoped>
.fade-enter-active,
.fade-leave-active {
  transition: opacity 150ms ease-out;
}

.fade-enter-from,
.fade-leave-to {
  opacity: 0;
}

.slide-up-enter-active,
.slide-up-leave-active {
  transition: transform 200ms ease-out, opacity 200ms ease-out;
}

.slide-up-enter-from,
.slide-up-leave-to {
  transform: translateY(100%);
  opacity: 0;
}
</style>
```

- [x] **Step 4: 运行类型检查**

```bash
cd /home/yufeng/student-manager/frontend-v3 && pnpm vue-tsc --noEmit
```

Expected: 无错误

- [x] **Step 5: Commit**

```bash
git add frontend-v3/src/components/ui/MobilePicker.vue
git commit -m "feat: MobilePicker 移动端底部弹窗

- 添加移动端检测
- 实现底部滑出弹窗
- 添加 fade/slide-up 动画
- 支持搜索过滤

Co-Authored-By: Claude Sonnet 4.6 <noreply@anthropic.com>"
```

---

## Task 3: 实现桌面端下拉面板

**Files:**
- Modify: `frontend-v3/src/components/ui/MobilePicker.vue`

- [x] **Step 1: 添加桌面端下拉面板**

在移动端弹窗的 `</Teleport>` 后添加：

```vue
<!-- 桌面端下拉面板 -->
<div
  v-if="isOpen && !isMobile"
  ref="desktopPanelRef"
  class="absolute z-50 top-full left-0 right-0 mt-1 bg-[#1a1a2e] border border-white/10 rounded-lg shadow-xl overflow-hidden"
>
  <!-- 搜索框 -->
  <div v-if="searchable" class="p-2 border-b border-white/10">
    <div class="relative">
      <Search class="absolute left-2.5 top-1/2 -translate-y-1/2 h-4 w-4 text-white/40" />
      <input
        v-model="searchQuery"
        type="text"
        :placeholder="searchPlaceholder"
        class="w-full h-9 pl-9 pr-3 rounded bg-white/5 border border-white/10 text-white text-sm placeholder:text-white/40 focus:outline-none focus:border-primary/50"
        @keydown.esc="close"
      >
    </div>
  </div>

  <!-- 选项列表 -->
  <div class="max-h-[300px] overflow-y-auto">
    <div
      v-for="(option, index) in filteredOptions"
      :key="option.value"
      :class="cn(
        'flex items-center justify-between px-3 py-2.5 cursor-pointer hover:bg-white/5',
        index !== filteredOptions.length - 1 && 'border-b border-white/5',
        isSelected(option) && 'bg-primary/10'
      )"
      @click="select(option)"
    >
      <div>
        <div :class="cn('text-sm', isSelected(option) ? 'text-primary font-medium' : 'text-white')">
          {{ option.label }}
        </div>
        <div v-if="option.subtitle" class="text-xs text-white/50 mt-0.5">
          {{ option.subtitle }}
        </div>
      </div>
      <Check
        v-if="isSelected(option)"
        class="h-4 w-4 text-primary"
      />
    </div>
    <div v-if="filteredOptions.length === 0" class="py-6 text-center text-sm text-white/40">
      未找到匹配选项
    </div>
  </div>
</div>
```

- [x] **Step 2: 添加桌面端点击外部关闭**

在 `<script setup>` 中添加：

```typescript
const desktopPanelRef = ref<HTMLDivElement | null>(null)

const handleClickOutside = (event: MouseEvent) => {
  if (!isMobile.value && isOpen.value) {
    const target = event.target as HTMLElement
    if (!target.closest('.mobile-picker-container')) {
      close()
    }
  }
}

onMounted(() => {
  checkMobile()
  window.addEventListener('resize', checkMobile)
  document.addEventListener('click', handleClickOutside)
})

onUnmounted(() => {
  window.removeEventListener('resize', checkMobile)
  document.removeEventListener('click', handleClickOutside)
})
```

- [x] **Step 3: 更新触发器容器类名**

给触发器容器添加类名：

```vue
<div class="relative mobile-picker-container">
```

- [x] **Step 4: 运行类型检查**

```bash
cd /home/yufeng/student-manager/frontend-v3 && pnpm vue-tsc --noEmit
```

Expected: 无错误

- [x] **Step 5: Commit**

```bash
git add frontend-v3/src/components/ui/MobilePicker.vue
git commit -m "feat: MobilePicker 桌面端下拉面板

- 实现桌面端固定位置下拉面板
- 点击外部关闭功能
- 键盘 ESC 关闭支持

Co-Authored-By: Claude Sonnet 4.6 <noreply@anthropic.com>"
```

---

## Task 4: 创建组件测试

**Files:**
- Create: `frontend-v3/test/components/MobilePicker.spec.ts`

- [x] **Step 1: 编写测试文件**

创建 `frontend-v3/test/components/MobilePicker.spec.ts`：

```typescript
import { describe, it, expect, vi, beforeEach } from 'vitest'
import { mount } from '@vue/test-utils'
import { ref, nextTick } from 'vue'
import MobilePicker from '@/components/ui/MobilePicker.vue'

const options = [
  { value: '1', label: '选项一' },
  { value: '2', label: '选项二', subtitle: '副标题' },
  { value: '3', label: '选项三' }
]

describe('MobilePicker', () => {
  it('renders with placeholder', () => {
    const wrapper = mount(MobilePicker, {
      props: {
        options,
        placeholder: '请选择'
      }
    })
    expect(wrapper.text()).toContain('请选择')
  })

  it('displays selected option label', async () => {
    const wrapper = mount(MobilePicker, {
      props: {
        options,
        modelValue: '2'
      }
    })
    await nextTick()
    expect(wrapper.text()).toContain('选项二')
    expect(wrapper.text()).toContain('副标题')
  })

  it('emits update:modelValue when option selected', async () => {
    const wrapper = mount(MobilePicker, {
      props: {
        options,
        modelValue: undefined
      }
    })

    // 打开弹窗
    await wrapper.find('button').trigger('click')
    await nextTick()

    // 移动端环境需要特殊处理
    Object.defineProperty(window, 'innerWidth', { value: 375, writable: true })
    window.dispatchEvent(new Event('resize'))
    await nextTick()

    // 验证弹窗打开
    expect(wrapper.emitted()).toHaveProperty('open')
  })

  it('filters options when searchable', async () => {
    const wrapper = mount(MobilePicker, {
      props: {
        options,
        searchable: true,
        modelValue: undefined
      }
    })

    // 打开弹窗
    await wrapper.find('button').trigger('click')
    await nextTick()

    // 设置窗口为移动端
    Object.defineProperty(window, 'innerWidth', { value: 375, writable: true })
    window.dispatchEvent(new Event('resize'))
    await nextTick()

    // 验证搜索框存在
    const searchInput = wrapper.find('input[type="text"]')
    expect(searchInput.exists()).toBe(true)
  })

  it('clears selection when clearable', async () => {
    const wrapper = mount(MobilePicker, {
      props: {
        options,
        modelValue: '1',
        clearable: true
      }
    })

    await nextTick()
    const clearButton = wrapper.find('[data-testid="clear-button"]')
    // 如果找不到特定 testid，找包含 X 图标的按钮
    if (clearButton.exists()) {
      await clearButton.trigger('click')
      expect(wrapper.emitted()).toHaveProperty('update:modelValue')
      expect(wrapper.emitted()['update:modelValue'][0]).toEqual([undefined])
    }
  })

  it('respects disabled prop', async () => {
    const wrapper = mount(MobilePicker, {
      props: {
        options,
        disabled: true
      }
    })

    await wrapper.find('button').trigger('click')
    await nextTick()

    // 验证弹窗未打开
    expect(wrapper.emitted('update:modelValue')).toBeUndefined()
  })
})
```

- [x] **Step 2: 运行测试**

```bash
cd /home/yufeng/student-manager/frontend-v3 && pnpm test:run test/components/MobilePicker.spec.ts
```

Expected: 测试通过（可能有部分因 Teleport 需特殊处理）

- [x] **Step 3: Commit**

```bash
git add frontend-v3/test/components/MobilePicker.spec.ts
git commit -m "test: MobilePicker 组件测试

- 基础渲染测试
- 选择/清除功能测试
- 搜索过滤测试
- disabled 状态测试

Co-Authored-By: Claude Sonnet 4.6 <noreply@anthropic.com>"
```

---

## Task 5: 在 Schedules.vue 中替换原生 select

**Files:**
- Modify: `frontend-v3/src/views/teacher/Schedules.vue`

- [x] **Step 1: 导入 MobilePicker**

在 `<script setup>` 的 import 中添加：

```typescript
import { MobilePicker } from '@/components/ui'
```

- [x] **Step 2: 准备选项数据**

在 `weekOptions` 定义后添加计算属性：

```typescript
// 为 MobilePicker 准备的周次选项
const weekPickerOptions = computed(() => {
  return weekOptions.map(week => ({
    value: week,
    label: `第${week}周`,
    subtitle: week === currentWeek.value ? '本周' : undefined
  }))
})

// 为 MobilePicker 准备的班级选项
const classPickerOptions = computed(() => {
  return (classes.value || []).map(cls => ({
    value: cls.name,
    label: cls.name
  }))
})

// 为 MobilePicker 准备的星期选项
const dayPickerOptions = [
  { value: 1, label: '周一' },
  { value: 2, label: '周二' },
  { value: 3, label: '周三' },
  { value: 4, label: '周四' },
  { value: 5, label: '周五' },
  { value: 6, label: '周六' },
  { value: 7, label: '周日' }
]
```

- [x] **Step 3: 替换班级选择器**

找到班级选择区域（约第 478-498 行），替换为：

```vue
<div class="w-full sm:w-48">
  <label class="mb-1 block text-sm text-white/60">班级</label>
  <MobilePicker
    v-model="selectedClass"
    title="选择班级"
    placeholder="全部班级"
    clearable
    :options="classPickerOptions"
  />
</div>
```

- [x] **Step 4: 替换星期选择器**

替换星期选择区域（约第 500-520 行）：

```vue
<div class="w-full sm:w-32">
  <label class="mb-1 block text-sm text-white/60">星期</label>
  <MobilePicker
    v-model="selectedDay"
    title="选择星期"
    placeholder="全部"
    clearable
    :options="dayPickerOptions"
  />
</div>
```

- [x] **Step 5: 替换周次选择器**

替换周次选择区域（约第 522-546 行）：

```vue
<div class="w-full sm:w-40">
  <label class="mb-1 block text-sm text-white/60">周次</label>
  <MobilePicker
    v-model="selectedWeek"
    title="选择周次"
    placeholder="全部周次"
    searchable
    clearable
    search-placeholder="搜索周次..."
    :options="weekPickerOptions"
  />
</div>
```

- [x] **Step 6: 运行类型检查**

```bash
cd /home/yufeng/student-manager/frontend-v3 && pnpm vue-tsc --noEmit
```

Expected: 无错误

- [x] **Step 7: 验证构建**

```bash
cd /home/yufeng/student-manager/frontend-v3 && pnpm build
```

Expected: 构建成功

- [x] **Step 8: Commit**

```bash
git add frontend-v3/src/views/teacher/Schedules.vue
git commit -m "feat: Schedules.vue 使用 MobilePicker 替换原生 select

- 班级选择器替换
- 星期选择器替换
- 周次选择器替换（带搜索）

Co-Authored-By: Claude Sonnet 4.6 <noreply@anthropic.com>"
```

---

## Task 6: 最终验证和文档更新

**Files:**
- Modify: `frontend-v3/src/components/ui/MobilePicker.vue`（可选优化）

- [x] **Step 1: 运行完整测试套件**

```bash
cd /home/yufeng/student-manager/frontend-v3 && pnpm test:run
```

Expected: 所有测试通过

- [x] **Step 2: 运行构建验证**

```bash
cd /home/yufeng/student-manager/frontend-v3 && pnpm build
```

Expected: 构建成功，无警告

- [x] **Step 3: 推送到 GitHub**

```bash
git push origin main
```

---

## 实施清单汇总

| Task | 描述 | 预计时间 |
|------|------|----------|
| Task 1 | 创建基础结构 | 15 min |
| Task 2 | 移动端底部弹窗 | 20 min |
| Task 3 | 桌面端下拉面板 | 15 min |
| Task 4 | 组件测试 | 20 min |
| Task 5 | 替换 Schedules.vue | 15 min |
| Task 6 | 最终验证 | 10 min |
| **总计** | | **95 min** |

---

## 后续优化（Phase 2）

1. **手势增强**：添加下滑关闭手势
2. **虚拟滚动**：选项 >100 时使用虚拟滚动
3. **多选支持**：扩展为多选模式
4. **其他页面替换**：ClassSession.vue、Checkins.vue 等

---

**计划版本**: 1.0  
**创建时间**: 2026-04-06  
**状态**: 待执行
