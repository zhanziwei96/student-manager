import axios from 'axios'
import { ElMessage } from 'element-plus'
import Cookies from 'js-cookie'

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
    if (error.response?.status === 401) {
      // 清除登录状态，但不自动跳转
      // 让各个页面自己处理未登录的情况
      Cookies.remove('user_id')
      Cookies.remove('username')
      Cookies.remove('name')
    }
    return Promise.reject(error)
  }
)

export default request
