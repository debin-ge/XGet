import request from '@/utils/request'
import type { Proxy } from '../types/task'
import type { 
  ProxyCreateParams, 
  ProxyUpdateParams, 
  ProxyCheckResponse, 
  ProxyQualityListResponse, 
  ProxyQualityListParams, 
  ProxyHistoryListParams,
  ProxyHistoryListResponse
} from '../types/proxy'

export interface ProxyListResponse {
  items: Proxy[]
  total: number
  page: number
  size: number
  pages: number
}

export interface ProxyListParams {
  page?: number
  size?: number
  status?: string
  type?: string
  country?: string
  ip?: string
}

// 获取代理列表
export const getProxies = async (params: ProxyListParams = {}): Promise<ProxyListResponse> => {
  const response = await request.get<ProxyListResponse>('/proxies', { params })
  return response.data
}

// 获取可用代理列表（用于选择器）
export const getAvailableProxies = async (): Promise<Proxy[]> => {
  const response = await request.get<ProxyListResponse>('/proxies', {
    params: { status: 'ACTIVE', size: 10 }
  })
  return response.data.items
}

// 获取单个代理详情
export const getProxyById = async (id: string): Promise<Proxy> => {
  const response = await request.get<Proxy>(`/proxies/${id}`)
  return response.data
} 

export const deleteProxy = async (id: string): Promise<boolean> => {
  const response = await request.delete(`/proxies/${id}`)
  return response.status === 200
}

export const createProxy = async (data: ProxyCreateParams): Promise<Proxy> => {
  const response = await request.post('/proxies', data)
  return response.data
}

export const updateProxy = async (id: string, data: ProxyUpdateParams): Promise<Proxy> => {
  const response = await request.put(`/proxies/${id}`, data)
  return response.data
}

export const checkProxy = async (id: string): Promise<ProxyCheckResponse> => {
  const response = await request.post(`/proxies/check`, { proxy_ids: [id] })
  return response.data
}

export const getProxyQuality = async (params: ProxyQualityListParams = {}): Promise<ProxyQualityListResponse> => {
  const response = await request.get<ProxyQualityListResponse>('/proxies/quality-info', { params })
  return response.data
}

export const getProxyHistory = async (params: ProxyHistoryListParams = {}): Promise<ProxyHistoryListResponse> => {
  const response = await request.get<ProxyHistoryListResponse>('/proxies/usage/history', { params })
  return response.data
}