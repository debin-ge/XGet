import type { BaseEntity, PaginationParams, PaginatedResponse } from './common'

// 代理类型 - 注意API返回的是大写
export type ProxyType = 'HTTP' | 'HTTPS' | 'SOCKS4' | 'SOCKS5'

// 代理状态
export type ProxyStatus = 'ACTIVE' | 'INACTIVE'

// 代理实体 - 匹配真实API响应格式
export interface Proxy {
  id: string
  type: ProxyType
  ip: string // API中使用ip而不是host
  port: number
  username?: string
  password?: string
  country?: string // 所属国家
  city?: string // 城市信息，API中有这个字段
  isp?: string | null // ISP供应商
  latency?: number // 网络延迟 (ms)
  success_rate?: number // 成功率 (0-1)
  last_check?: string // 最后检查时间
  status: ProxyStatus
  created_at: string // 创建时间
  updated_at: string // 更新时间
}

// 创建代理参数
export interface ProxyCreateParams {
  ip: string
  port: number
  type: ProxyType
  username?: string
  password?: string
  country?: string
  city?: string
  isp?: string
}

// 更新代理参数
export interface ProxyUpdateParams {
  ip?: string
  port?: number
  type?: ProxyType
  username?: string
  password?: string
  status?: ProxyStatus
  country?: string
  city?: string
  isp?: string
}

// 代理质量信息 - 匹配真实API响应格式
export interface ProxyQuality {
  proxy_id: string
  ip: string
  port: number
  proxy_type: ProxyType // 代理类型
  total_usage: number // 总使用次数
  success_count: number // 成功次数
  success_rate: number // 成功率 (0-1)
  quality_score: number // 质量分数 (0-1)
  last_used: string | null // 最近使用时间
  status: ProxyStatus // 代理状态
  country?: string // 国家
  city?: string // 城市
  isp?: string | null // ISP供应商
  latency: number // 延迟(ms)
  created_at: string // 创建时间
  updated_at: string // 更新时间
}

// 代理历史记录
export interface ProxyHistory extends BaseEntity {
  id: string // 历史记录ID
  proxy_id: string // 代理ID
  proxy_ip: string // 代理IP
  account_email?: string // 账户邮箱
  account_id: string // 账户ID
  task_name?: string // 任务名称
  task_id: string // 任务ID
  service_name: string // 服务名称
  success: string // 是否成功
  response_time: number // 响应时长 (ms)
  created_at: string // 创建时间
  updated_at: string // 更新时间
}

// 代理统计
export interface ProxyStats {
  total: number
  active: number
  inactive: number
  byType: Record<ProxyType, number>
  byCountry: Record<string, number>
  byRegion: Record<string, number>
  averageLatency: number
  totalUsageCount: number
}

// 导出代理类型别名
export type { PaginationParams, PaginatedResponse } 

export interface ProxyCheckResponse {
  total: number
  checked: number
  active: number
  inactive: number
  results: ProxyCheckResult[]
}

export interface ProxyCheckResult {
  id: string
  status: string
  latency?: number
  success_rate?: number
  error_msg?: string
}

export interface ProxyQualityListResponse {
  items: ProxyQuality[]
  total: number
  page: number
  size: number
  pages: number
}

export interface ProxyQualityInfo {
  proxy_id: string
  ip: string
  port: number
  proxy_type: ProxyType
  total_usage: number
  success_count: number
  success_rate: number
  quality_score: number
  last_used: string | null
}

export interface ProxyQualityListParams {
  page?: number
  size?: number
  status?: string
  country?: string
  min_quality_score?: string
  sort_by?: string
  sort_order?: string
}

export interface ProxyHistoryListParams {
  page?: number
  size?: number
  status?: string
  country?: string
  min_quality_score?: string
  success?: string
  service_name?: string
  start_date?: string
  end_date?: string
  account_email?: string
  task_name?: string
}

export interface ProxyHistoryListResponse {
  items: ProxyHistory[]
  total: number
  page: number
  size: number
  pages: number
}

export interface ProxyHistoryItem {
  id: string
  proxy_id: string
  proxy_ip: string
  account_email?: string
  account_id: string
  task_name?: string
  task_id: string
  service_name: string
  success: string
  response_time: number
  created_at: string
  updated_at: string
}