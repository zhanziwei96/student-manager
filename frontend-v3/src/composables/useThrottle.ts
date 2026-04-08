/**
 * 节流/防抖组合式函数
 * 用于防止按钮重复点击或接口重复请求
 */
import { ref, computed } from 'vue'

/**
 * 使用节流状态
 * @param cooldownMs 冷却时间（毫秒）
 * @returns 节流控制对象
 */
export function useThrottle(cooldownMs: number = 2000) {
  const isThrottled = ref(false)
  const lastExecuted = ref<number>(0)

  const canExecute = computed(() => {
    if (!isThrottled.value) return true
    const now = Date.now()
    return now - lastExecuted.value >= cooldownMs
  })

  const execute = async <T>(fn: () => Promise<T>): Promise<T | undefined> => {
    if (isThrottled.value && !canExecute.value) {
      console.log(`操作过于频繁，请等待 ${cooldownMs}ms`)
      return undefined
    }

    isThrottled.value = true
    lastExecuted.value = Date.now()

    try {
      const result = await fn()
      return result
    } finally {
      // 冷却时间后解除限制
      setTimeout(() => {
        isThrottled.value = false
      }, cooldownMs)
    }
  }

  const reset = () => {
    isThrottled.value = false
    lastExecuted.value = 0
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
  let timeoutId: ReturnType<typeof setTimeout> | null = null

  const execute = <T>(fn: () => Promise<T> | T): Promise<T | undefined> => {
    return new Promise((resolve) => {
      if (timeoutId) {
        clearTimeout(timeoutId)
      }

      timeoutId = setTimeout(async () => {
        try {
          const result = await fn()
          resolve(result)
        } catch (error) {
          resolve(undefined)
        }
      }, delayMs)
    })
  }

  const cancel = () => {
    if (timeoutId) {
      clearTimeout(timeoutId)
      timeoutId = null
    }
  }

  return {
    execute,
    cancel,
  }
}
