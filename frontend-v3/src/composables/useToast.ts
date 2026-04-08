import { ref, computed } from 'vue'

export type ToastVariant = 'default' | 'success' | 'error' | 'warning' | 'info'

export interface ToastItem {
  id: string
  message: string
  variant: ToastVariant
  duration: number
}

interface ToastOptions {
  message: string
  variant?: ToastVariant
  duration?: number
}

// 全局 toast 队列（单例模式）
const toasts = ref<ToastItem[]>([])

// 最大 Toast 数量限制，防止极端情况下累积过多
const MAX_TOASTS = 10

let idCounter = 0

function generateId(): string {
  return `toast-${Date.now()}-${++idCounter}`
}

/**
 * Toast notification composable - 队列模式
 * 支持多条消息同时显示，先进先出
 */
export function useToast() {
  const showToast = (options: ToastOptions | string, variantOrDuration?: ToastVariant | number, dur?: number) => {
    let toastData: ToastOptions

    if (typeof options === 'string') {
      // 便捷调用: showToast('message', 'variant', duration)
      toastData = {
        message: options,
        variant: (variantOrDuration as ToastVariant) || 'default',
        duration: dur || 1500,
      }
    } else {
      // 标准调用: showToast({ message: '...', variant: '...' })
      toastData = {
        message: options.message,
        variant: options.variant || 'default',
        duration: options.duration || 1500,
      }
    }

    const newToast: ToastItem = {
      id: generateId(),
      message: toastData.message,
      variant: toastData.variant!,
      duration: toastData.duration!,
    }

    // 如果达到上限，移除最早的 toast
    if (toasts.value.length >= MAX_TOASTS) {
      toasts.value.shift()
    }

    toasts.value.push(newToast)
  }

  const hideToast = (id: string) => {
    const index = toasts.value.findIndex(t => t.id === id)
    if (index > -1) {
      toasts.value.splice(index, 1)
    }
  }

  const clearAll = () => {
    toasts.value = []
  }

  return {
    // 状态
    toasts: computed(() => toasts.value),
    // 操作方法
    showToast,
    hideToast,
    clearAll,
    // 便捷方法
    success: (msg: string, dur?: number) => showToast({ message: msg, variant: 'success', duration: dur || 1500 }),
    error: (msg: string, dur?: number) => showToast({ message: msg, variant: 'error', duration: dur }),
    warning: (msg: string, dur?: number) => showToast({ message: msg, variant: 'warning', duration: dur }),
    info: (msg: string, dur?: number) => showToast({ message: msg, variant: 'info', duration: dur }),
  }
}

// 导出全局 toasts 引用，用于 ToastContainer 直接绑定
export { toasts }
