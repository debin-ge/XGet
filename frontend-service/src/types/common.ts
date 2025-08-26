// 通用响应类型
export interface ApiResponse<T = any> {
  code: number
  message: string
  data: T
}

// 分页参数
export interface PaginationParams {
  page?: number
  pageSize?: number
  search?: string
  sortBy?: string
  sortOrder?: 'asc' | 'desc'
}

// 分页响应
export interface PaginatedResponse<T> {
  items: T[]
  total: number
  page: number
  pageSize: number
  totalPages: number
}

// 选项类型
export interface Option {
  label: string
  value: string | number
  disabled?: boolean
}

// 状态类型
export type Status = 'active' | 'inactive' | 'pending' | 'error' | 'success'

// 基础实体接口
export interface BaseEntity {
  id: string
  createdAt: string
  updatedAt: string
} 