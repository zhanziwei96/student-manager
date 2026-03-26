import { ref } from 'vue'

type ToastVariant = 'default' | 'success' | 'error' | 'warning' | 'info'

interface ToastOptions {
  message: string
  variant?: ToastVariant
  duration?: number
}

const show = ref(false)
const message = ref('')
const variant = ref<ToastVariant>('default')
const duration = ref(3000)

/**
 * Toast notification composable
 * Provides a global toast notification system
 */
export function useToast() {
  const showToast = (options: ToastOptions | string, variantOrDuration?: ToastVariant | number, dur?: number) => {
    if (typeof options === 'string') {
      // 便捷调用: showToast('message', 'variant', duration)
      message.value = options
      variant.value = (variantOrDuration as ToastVariant) || 'default'
      duration.value = dur || 3000
    } else {
      // 标准调用: showToast({ message: '...', variant: '...' })
      message.value = options.message
      variant.value = options.variant || 'default'
      duration.value = options.duration || 3000
    }
    show.value = true
  }

  const hideToast = () => {
    show.value = false
  }

  return {
    // 状态（用于绑定到 Toast 组件）
    show,
    message,
    variant,
    duration,
    // 操作方法
    showToast,
    hideToast,
    // 便捷方法
    success: (msg: string, dur?: number) => showToast({ message: msg, variant: 'success', duration: dur }),
    error: (msg: string, dur?: number) => showToast({ message: msg, variant: 'error', duration: dur }),
    warning: (msg: string, dur?: number) => showToast({ message: msg, variant: 'warning', duration: dur }),
    info: (msg: string, dur?: number) => showToast({ message: msg, variant: 'info', duration: dur }),
  }
}
