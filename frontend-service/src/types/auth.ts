import type { BaseEntity } from './common'

// 用户偏好设置
export interface UserPreferences {
  theme: 'light' | 'dark'
  notifications: {
    email: boolean
    push: boolean
    sms: boolean
  }
  privacy: {
    profile_visible: boolean
    activity_visible: boolean
  }
  display: {
    items_per_page: number
    sort_order: 'asc' | 'desc'
  }
}

// 用户信息
export interface User {
  id: string
  username: string
  email: string
  first_name: string
  last_name: string
  phone?: string
  avatar_url?: string
  timezone: string
  language: string
  is_active: boolean
  is_verified: boolean
  is_superuser: boolean
  last_login?: string
  failed_login_attempts: number
  locked_until?: string
  preferences: UserPreferences
  created_at: string
  updated_at: string
}

// 用户角色（从is_superuser判断）
export type UserRole = 'admin' | 'user'

// 登录参数
export interface LoginParams {
  username: string
  password: string
  remember?: boolean
}

// 注册参数
export interface RegisterParams {
  username: string
  email: string
  password: string
  confirmPassword: string
  first_name?: string
  last_name?: string
}

// 登录响应
export interface LoginResponse {
  access_token: string
  refresh_token: string
  token_type: string
  expires_at: string
  user: User
}

// 修改密码参数
export interface ChangePasswordParams {
  oldPassword: string
  newPassword: string
  confirmPassword: string
} 