import request from './index'
import type { LoginParams, LoginResponse, RegisterParams } from '@/types/auth'

// 用户登录
export const login = (data: LoginParams): Promise<LoginResponse> => {
  return request.post('/users/login', data)
}

// 用户注册
export const register = (data: RegisterParams): Promise<void> => {
  return request.post('/users/register', data)
}

// 刷新token
export const refreshToken = (): Promise<LoginResponse> => {
  return request.post('/auth/refresh')
}

// 用户登出
export const logout = (): Promise<void> => {
  return request.post('/auth/logout')
}

// 获取当前用户信息
export const getCurrentUser = () => {
  return request.get('/users/me')
} 