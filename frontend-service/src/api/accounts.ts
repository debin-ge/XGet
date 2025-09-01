import request from '@/utils/request'
import type { Account, AccountCreateParams, AccountUpdateParams, AccountLoginResponse, AccountLoginParams } from '../types/account'

export interface AccountListResponse {
  items: Account[]
  total: number
  page: number
  size: number
  pages: number
}

export interface AccountListParams {
  page?: number
  size?: number
  active?: boolean
  login_method?: string
}

// 获取账户列表
export const getAccounts = async (params: AccountListParams = {}): Promise<AccountListResponse> => {
  const response = await request.get<AccountListResponse>('/accounts/', { params })
  return response.data
}

// 获取活跃账户列表（用于选择器）
export const getActiveAccounts = async (): Promise<Account[]> => {
  const response = await request.get<AccountListResponse>('/accounts/', {
    params: { active: true, size: 10 }
  })
  return response.data.items as Account[]
}

// 获取单个账户详情
export const getAccountById = async (id: string): Promise<Account> => {
  const response = await request.get<Account>(`/accounts/${id}/`)
  return response.data
} 


export const deleteAccount = async (id: string): Promise<boolean> => {
  const response = await request.delete(`/accounts/${id}/`)
  return response.status === 200
}

export const loginAccount = async (data: AccountLoginParams): Promise<AccountLoginResponse> => {
  const response = await request.post<AccountLoginResponse>('/accounts/login/', data)
  return response.data
}

export const createAccount = async (data: AccountCreateParams): Promise<Account> => {
  const response = await request.post('/accounts/', data)
  return response.data
}

export const updateAccount = async (id: string, data: AccountUpdateParams): Promise<Account> => {
  const response = await request.put(`/accounts/${id}/`, data)
  return response.data
}