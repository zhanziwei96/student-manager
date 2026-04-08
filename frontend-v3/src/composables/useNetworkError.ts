import { ref, readonly } from 'vue'

// 改为工厂函数，每个组件拥有独立的网络错误状态
// 避免不同页面/组件共享同一错误状态导致互相干扰
export function useNetworkError() {
  const networkError = ref<Error | null>(null)
  const isOffline = ref(false)

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
