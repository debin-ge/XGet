import axios from 'axios'
import type { AxiosInstance, AxiosRequestConfig, AxiosResponse } from 'axios'
import { ElMessage } from 'element-plus'

// 创建axios实例
const request: AxiosInstance = axios.create({
  baseURL: import.meta.env.VITE_API_BASE_URL,
  timeout: 10000,
  headers: {
    'Content-Type': 'application/json',
  },
})

// 请求拦截器
request.interceptors.request.use(
  async (config) => {
    // 检查token是否即将过期，如果是则自动刷新
    const token = localStorage.getItem('access_token')
    const expiresAt = localStorage.getItem('token_expires_at')
    
    if (token && expiresAt) {
      const now = new Date().getTime()
      // 解析格式为 "%Y-%m-%d %H:%M:%S" 的时间字符串
      const expiresTime = new Date(expiresAt.replace(' ', 'T') + 'Z').getTime()
      const threeMinutes = 3 * 60 * 1000
      
      // 如果token即将过期，尝试刷新
      if (expiresTime - now <= threeMinutes) {
        try {
          const authService = (await import('@/services/authService')).authService
          const refreshed = await authService.refreshToken()
          if (refreshed) {
            console.log('Token自动刷新成功')
          }
        } catch (error) {
          console.error('Token自动刷新失败:', error)
          // 刷新失败不影响原始请求
        }
      }
    }
    
    // 自动添加token
    if (token && config.headers) {
      config.headers.Authorization = `Bearer ${token}`
    }
    return config
  },
  (error) => {
    return Promise.reject(error)
  }
)

// 响应拦截器
request.interceptors.response.use(
  (response: AxiosResponse) => {
    return response.data
  },
  async (error) => {
    // 统一错误处理
    if (error.response) {
      const { status, data } = error.response
      
      switch (status) {
        case 401:
          // 未授权，清除本地token并跳转到登录页
          localStorage.removeItem('access_token')
          localStorage.removeItem('refresh_token')
          localStorage.removeItem('user_info')
          // 显示错误消息
          ElMessage.error('登录状态已过期，请重新登录')
          // 直接跳转到登录页面
          window.location.href = '/login'
          break
        case 403:
          ElMessage.error('权限不足')
          break
        case 404:
          ElMessage.error('请求的资源不存在')
          break
        case 500:
          ElMessage.error('服务器内部错误')
          break
        default:
          ElMessage.error(data?.message || '请求失败')
      }
    } else {
      ElMessage.error('网络错误，请检查网络连接')
    }
    
    return Promise.reject(error)
  }
)

export default request 