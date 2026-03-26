<script setup lang="ts">
import { computed, onUnmounted, watch } from 'vue'
import { cn } from '@/lib/utils'
import { X } from 'lucide-vue-next'

/**
 * Dialog 组件
 * 基于 ClassHub 设计体系 v1.0.0
 * 支持作为 form 使用，解决密码字段警告
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

// Lock body scroll when open
watch(
  () => props.open,
  (isOpen) => {
    if (isOpen) {
      document.body.style.overflow = 'hidden'
    } else {
      document.body.style.overflow = ''
    }
  }
)

// 组件卸载时重置 body overflow
onUnmounted(() => {
  document.body.style.overflow = ''
})

const overlayClasses = computed(() =>
  cn(
    'fixed inset-0 z-50 bg-black/80 backdrop-blur-sm',
    'transition-opacity duration-300 ease-out',
    props.open ? 'opacity-100' : 'opacity-0 pointer-events-none'
  )
)

const contentClasses = computed(() =>
  cn(
    // 定位
    'fixed left-1/2 top-1/2 z-50 -translate-x-1/2 -translate-y-1/2',
    // 尺寸
    'w-full max-w-lg max-h-[85vh] overflow-y-auto',
    // 样式
    'rounded-xl border border-border bg-background-elevated p-6',
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
  <!-- Overlay - 不使用 Teleport 以保留 form 上下文 -->
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
          <slot name="title">{{ title }}</slot>
        </h3>
        <p 
          v-if="description || $slots.description" 
          class="text-sm text-text-secondary"
        >
          <slot name="description">{{ description }}</slot>
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
</template>
