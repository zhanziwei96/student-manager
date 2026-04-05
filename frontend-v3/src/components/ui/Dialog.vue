<script setup lang="ts">
import { computed, ref, watch } from 'vue'
import { useScrollLock } from '@vueuse/core'
import { cn } from '@/lib/utils'
import { X } from 'lucide-vue-next'

/**
 * Dialog 组件
 * 基于 ClassHub 设计体系 v1.0.0
 * 支持作为 form 使用，解决密码字段警告
 *
 * 使用 useScrollLock 锁定 body 滚动，支持多 Dialog 同时打开
 */

interface Props {
  open?: boolean
  class?: string
  title?: string
  description?: string
  /** 是否作为 form 元素渲染，用于包裹表单内容 */
  asForm?: boolean
  /** form 提交处理函数 */
  onSubmit?: (e: Event) => void
}

const props = withDefaults(defineProps<Props>(), {
  open: false,
  asForm: false,
})

const emit = defineEmits<{
  (e: 'update:open', value: boolean): void
}>()

// 用于 Teleport 的目标元素
const teleportTarget = ref('body')

// 检查是否在客户端环境（SSR 安全）
const isClient = typeof window !== 'undefined'

// 使用 useScrollLock 替代手动操作 body overflow
// 自动处理多 Dialog 同时打开的情况（ref 计数器）
const isLocked = useScrollLock(isClient ? document.body : null)

// 同步 open 状态和滚动锁定
watch(
  () => props.open,
  (isOpen) => {
    isLocked.value = isOpen
  },
  { immediate: true }
)

const overlayClasses = computed(() =>
  cn(
    'fixed inset-0 z-50 bg-black/80 backdrop-blur-sm',
    'flex items-center justify-center',
    'transition-opacity duration-300 ease-out',
    props.open ? 'opacity-100' : 'opacity-0 pointer-events-none'
  )
)

const contentClasses = computed(() =>
  cn(
    // 定位 - 使用 flex 居中，移动端固定边距
    'relative w-full max-w-lg mx-4 sm:mx-0 max-h-[90vh] overflow-y-auto',
    // 样式
    'rounded-xl border border-border bg-background-elevated p-4 sm:p-6',
    // 阴影
    'shadow-2xl',
    // 动画
    'transition-all duration-300 ease-out',
    props.open
      ? 'opacity-100 scale-100'
      : 'opacity-0 scale-95 pointer-events-none',
    props.class
  )
)

const close = () => {
  emit('update:open', false)
}

// 处理 form 提交
const handleSubmit = (e: Event) => {
  e.preventDefault()
  props.onSubmit?.(e)
}
</script>

<template>
  <!-- REVIEW-P1: 使用 Teleport 挂载到 body，避免 z-index 层级问题 -->
  <Teleport
    v-if="isClient"
    :to="teleportTarget"
  >
    <div
      v-if="open"
      :class="overlayClasses"
      @click="close"
    >
      <!-- Content -->
      <component
        :is="asForm ? 'form' : 'div'"
        :class="contentClasses"
        @click.stop
        @submit="asForm ? handleSubmit : undefined"
      >
        <!-- Header -->
        <div
          v-if="title || $slots.title"
          class="flex flex-col space-y-1.5 text-center sm:text-left mb-4"
        >
          <h3 class="text-lg font-semibold text-text-primary">
            <slot name="title">
              {{ title }}
            </slot>
          </h3>
          <p
            v-if="description || $slots.description"
            class="text-sm text-text-secondary break-words"
          >
            <slot name="description">
              {{ description }}
            </slot>
          </p>
        </div>

        <!-- Body -->
        <div class="text-text-secondary">
          <slot />
        </div>

        <!-- Footer -->
        <div 
          v-if="$slots.footer" 
          class="flex flex-col-reverse sm:flex-row sm:justify-end sm:gap-2 mt-6 pt-4 border-t border-border"
        >
          <slot name="footer" />
        </div>

        <!-- Close button -->
        <button
          type="button"
          class="absolute right-4 top-4 p-1 rounded-md text-text-muted hover:text-text-primary hover:bg-white/10 transition-colors focus:outline-none focus:ring-2 focus:ring-primary/50"
          @click="close"
        >
          <X class="h-4 w-4" />
          <span class="sr-only">关闭</span>
        </button>
      </component>
    </div>
  </Teleport>
</template>
