import axios from 'axios'
import { useUserStore } from '@/stores/user'

// 是否在登录页面（防止重复跳转）
let isRedirecting = false

const request = axios.create({
  baseURL: '/api',
  timeout: 10000,
  withCredentials: true,
  headers: {
    'Content-Type': 'application/json'
  }
})

// 响应拦截器
request.interceptors.response.use(
  response => {
    return response.data
  },
  error => {
    // 使用 Naive UI 的 message（在组件外部需要使用 window.$message）
    const message = window.$message
    
    if (error.response) {
      const status = error.response.status
      const msg = error.response.data?.detail || error.response.data?.message || '请求失败'
      
      // 获取请求路径
      const requestUrl = error.config?.url || ''
      
      // 登录接口的 401 错误由登录页面自己处理
      if (status === 401 && requestUrl.includes('/login')) {
        return Promise.reject(error)
      }
      
      switch (status) {
        case 401:
          {
            const userStore = useUserStore()
            userStore.clearUser()
            
            if (message) message.warning('登录已过期，请重新登录')
            
            if (!isRedirecting && window.location.pathname !== '/login') {
              isRedirecting = true
              setTimeout(() => {
                window.location.href = '/login'
                isRedirecting = false
              }, 1500)
            }
          }
          break
          
        case 403:
          if (message) message.error('没有权限执行此操作')
          break
          
        case 429:
          if (message) message.warning('请求过于频繁，请稍后再试')
          break
          
        case 500:
        case 502:
        case 503:
          if (message) message.error('服务器繁忙，请稍后重试')
          break
          
        default:
          if (message) message.error(msg)
      }
    } else if (error.request) {
      if (message) message.error('网络连接失败，请检查网络')
    } else {
      if (message) message.error('请求发生错误')
    }
    
    return Promise.reject(error)
  }
)

export default request
