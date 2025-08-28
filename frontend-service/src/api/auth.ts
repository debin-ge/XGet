import request from '@/utils/request'
import type { LoginParams, LoginResponse, RegisterParams } from '@/types/auth'

// 用户登录
export const login = async (data: LoginParams): Promise<LoginResponse> => {
  const response = await request.post<LoginResponse>('/users/login', data)
  return response.data
}

// 用户注册
export const register = async (data: RegisterParams): Promise<void> => {
  const response = await request.post('/users/register', data)
  return response.data
}

// 刷新token
export const refreshToken = async (): Promise<LoginResponse> => {
  const response = await request.post<LoginResponse>('/auth/refresh')
  return response.data
}

// 用户登出
export const logout = async (): Promise<void> => {
  const response = await request.post('/auth/logout')
  return response.data
}

// 获取当前用户信息
export const getCurrentUser = async () => {
  const response = await request.get('/users/me')
  return response.data
} 