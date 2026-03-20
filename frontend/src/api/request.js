import axios from 'axios'
import { ElMessage } from 'element-plus'
import Cookies from 'js-cookie'

// 是否在登录页面（防止重复跳转）
let isRedirecting = false

const request = axios.create({
  baseURL: '/api',
  timeout: 10000,
  withCredentials: true  // 允许携带 cookie
})

// 请求拦截器
request.interceptors.request.use(
  config => {
    // 可以在这里添加 token 等
    return config
  },
  error => {
    return Promise.reject(error)
  }
)

// 响应拦截器
request.interceptors.response.use(
  response => {
    return response.data
  },
  error => {
    // 处理HTTP错误状态码
    if (error.response) {
      const status = error.response.status
      const message = error.response.data?.detail || error.response.data?.message || '请求失败'
      
      switch (status) {
        case 401:
          // 未授权：清除登录状态并跳转到登录页
          Cookies.remove('user_id', { path: '/' })
          Cookies.remove('username', { path: '/' })
          Cookies.remove('name', { path: '/' })
          
          ElMessage.warning('登录已过期，请重新登录')
          
          // 避免重复跳转
          if (!isRedirecting && window.location.pathname !== '/login') {
            isRedirecting = true
            setTimeout(() => {
              window.location.href = '/login'
              isRedirecting = false
            }, 1500)
          }
          break
          
        case 403:
          // 禁止访问
          ElMessage.error('没有权限执行此操作')
          break
          
        case 429:
          // 请求过于频繁
          ElMessage.warning('请求过于频繁，请稍后再试')
          break
          
        case 500:
        case 502:
        case 503:
          // 服务器错误
          ElMessage.error('服务器繁忙，请稍后重试')
          break
          
        default:
          // 其他错误
          ElMessage.error(message)
      }
    } else if (error.request) {
      // 网络错误（无响应）
      ElMessage.error('网络连接失败，请检查网络')
    } else {
      // 其他错误
      ElMessage.error('请求发生错误')
    }
    
    return Promise.reject(error)
  }
)

export default request
