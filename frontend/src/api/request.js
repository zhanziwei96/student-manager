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
      // 清除登录状态，指定path确保完全清除
      Cookies.remove('user_id', { path: '/' })
      Cookies.remove('username', { path: '/' })
      Cookies.remove('name', { path: '/' })
    }
    return Promise.reject(error)
  }
)

export default request
