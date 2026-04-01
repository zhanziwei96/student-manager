<script setup lang="ts">
import { computed, onMounted, onUnmounted, ref } from 'vue'
import { cn } from '@/lib/utils'
import { X, CheckCircle, AlertCircle, Info } from 'lucide-vue-next'

/**
 * Toast 组件 - 队列模式中的单个 Toast
 * 基于 ClassHub 设计体系 v1.0.0
 */

type ToastVariant = 'default' | 'success' | 'error' | 'warning' | 'info'

interface Props {
  show?: boolean
  message: string
  variant?: ToastVariant
  duration?: number
}

const props = withDefaults(defineProps<Props>(), {
  show: false,
  variant: 'default',
  duration: 3000,
})

const emit = defineEmits<{
  (e: 'update:show', value: boolean): void
  (e: 'close'): void
}>()

const isVisible = ref(false)
const timeoutId = ref<ReturnType<typeof setTimeout> | null>(null)
const closeTimeoutId = ref<ReturnType<typeof setTimeout> | null>(null)

// 变体样式映射
const variantClasses: Record<ToastVariant, string> = {
  default: 'bg-background-elevated border-border text-text-primary',
  success: 'bg-success/10 border-success/30 text-success',
  error: 'bg-error/10 border-error/30 text-error',
  warning: 'bg-warning/10 border-warning/30 text-warning',
  info: 'bg-info/10 border-info/30 text-info',
}

// 图标映射
const iconMap: Record<ToastVariant, typeof CheckCircle> = {
  default: Info,
  success: CheckCircle,
  error: AlertCircle,
  warning: AlertCircle,
  info: Info,
}

const classes = computed(() =>
  cn(
    'pointer-events-auto flex w-full max-w-sm items-center gap-3 rounded-lg border p-4 shadow-2xl',
    'transition-all duration-300 ease-out',
    variantClasses[props.variant],
    isVisible.value
      ? 'opacity-100 translate-y-0'
      : 'opacity-0 translate-y-2'
  )
)

const icon = computed(() => iconMap[props.variant])

const clearTimers = () => {
  if (timeoutId.value) {
    clearTimeout(timeoutId.value)
    timeoutId.value = null
  }
  if (closeTimeoutId.value) {
    clearTimeout(closeTimeoutId.value)
    closeTimeoutId.value = null
  }
}

const showToast = () => {
  clearTimers()
  isVisible.value = true
  timeoutId.value = setTimeout(() => {
    close()
  }, props.duration)
}

const close = () => {
  clearTimers()
  isVisible.value = false
  closeTimeoutId.value = setTimeout(() => {
    emit('close')
    emit('update:show', false)
  }, 300)
}

// 组件挂载时显示
onMounted(() => {
  if (props.show) {
    showToast()
  }
})

// 组件卸载时清理 timer
onUnmounted(() => {
  clearTimers()
})

defineExpose({ show: showToast, close })
</script>

<template>
  <div :class="classes">
    <component
      :is="icon"
      class="h-5 w-5 shrink-0"
    />
    <span class="flex-1 text-sm font-medium">{{ message }}</span>
    <button
      type="button"
      class="shrink-0 p-1 rounded-md text-text-muted hover:text-text-primary hover:bg-white/10 transition-colors focus:outline-none focus:ring-2 focus:ring-primary/50"
      @click="close"
    >
      <X class="h-4 w-4" />
    </button>
  </div>
</template>
