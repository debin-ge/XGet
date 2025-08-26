export interface Account {
  id: string
  username: string
  email: string
  login_method: 'GOOGLE' | 'TWITTER'
  active: boolean
  proxy_id: string
  last_used: string
  created_at: string
  updated_at: string
  error_msg: string
  cookies: Record<string, string> | null
  headers: Record<string, string> | null
  user_agent: string
  // 前端状态字段
  loginLoading?: boolean
  testLoading?: boolean
}

export interface AccountListParams {
  page?: number
  size?: number
  active?: boolean
  login_method?: string
  search?: string
}

export interface AccountListResponse {
  items: Account[]
  total: number
  page: number
  size: number
  pages: number
}

// 额外的前端表单类型
export interface AccountCreateParams {
  username: string
  password?: string
  email: string
  email_password?: string
  login_method: AccountPlatform
  proxy_id?: string
  notes?: string
}

export interface AccountUpdateParams {
  id?: string
  username?: string
  password?: string
  email?: string
  email_password?: string
  login_method?: AccountPlatform
  proxy_id?: string
  notes?: string
}

export type AccountPlatform = 'GOOGLE' | 'TWITTER' 

export interface AccountLoginResponse {
  id: string
  username: string
  active: boolean
  login_successful: boolean
  cookies_obtained: boolean
  last_used: string
  message: string
}

export interface AccountLoginParams {
  account_id: string
  proxy_id?: string
  async_login?: boolean
}