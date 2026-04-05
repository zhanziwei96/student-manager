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
