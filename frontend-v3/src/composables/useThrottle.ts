/**
 * 节流/防抖组合式函数
 * 用于防止按钮重复点击或接口重复请求
 */
import { ref, computed, onScopeDispose, getCurrentScope } from 'vue'

/**
 * 使用节流状态
 * @param cooldownMs 冷却时间（毫秒）
 * @returns 节流控制对象
 */
export function useThrottle(cooldownMs: number = 2000) {
  const isThrottled = ref(false)
  const lastExecuted = ref<number>(0)
  let timeoutId: ReturnType<typeof setTimeout> | null = null

  const canExecute = computed(() => {
    if (!isThrottled.value) return true
    const now = Date.now()
    return now - lastExecuted.value >= cooldownMs
  })

  const clearThrottleTimeout = () => {
    if (timeoutId) {
      clearTimeout(timeoutId)
      timeoutId = null
    }
  }

  const execute = async <T>(fn: () => Promise<T>): Promise<T | undefined> => {
    if (isThrottled.value && !canExecute.value) {
      // 仅在开发环境输出调试信息
      if (import.meta.env.DEV) {
        console.log(`操作过于频繁，请等待 ${cooldownMs}ms`)
      }
      return undefined
    }

    isThrottled.value = true
    lastExecuted.value = Date.now()

    try {
      const result = await fn()
      return result
    } finally {
      // 冷却时间后解除限制
      timeoutId = setTimeout(() => {
        isThrottled.value = false
        timeoutId = null
      }, cooldownMs)
    }
  }

  const reset = () => {
    clearThrottleTimeout()
    isThrottled.value = false
    lastExecuted.value = 0
  }

  // 组件卸载时清理定时器（如果当前在 Vue 作用域内）
  if (getCurrentScope()) {
    onScopeDispose(() => {
      clearThrottleTimeout()
    })
  }

  return {
    isThrottled: computed(() => isThrottled.value),
    canExecute,
    execute,
    reset,
  }
}

/**
 * 使用防抖状态（延迟执行）
 * @param delayMs 延迟时间（毫秒）
 * @returns 防抖控制对象
 */
export function useDebounce(delayMs: number = 300) {
  // 使用 ref 使 timeoutId 成为组件级状态，避免多组件共享
  const timeoutId = ref<ReturnType<typeof setTimeout> | null>(null)

  const execute = <T>(fn: () => Promise<T> | T): Promise<T | undefined> => {
    return new Promise((resolve) => {
      if (timeoutId.value) {
        clearTimeout(timeoutId.value)
      }

      timeoutId.value = setTimeout(async () => {
        try {
          const result = await fn()
          resolve(result)
        } catch (error) {
          resolve(undefined)
        } finally {
          timeoutId.value = null
        }
      }, delayMs)
    })
  }

  const cancel = () => {
    if (timeoutId.value) {
      clearTimeout(timeoutId.value)
      timeoutId.value = null
    }
  }

  // 组件卸载时自动清理（如果当前在 Vue 作用域内）
  if (getCurrentScope()) {
    onScopeDispose(() => {
      cancel()
    })
  }

  return {
    execute,
    cancel,
  }
}
