import type { BaseEntity, PaginationParams, PaginatedResponse } from './common'

// 任务类型
export type TaskType = 'USER_TWEETS' | 'SEARCH' | 'TOPIC' | 'FOLLOWERS' | 'FOLLOWING' | 'USER_INFO'

// 任务状态
export type TaskStatus = 'PENDING' | 'RUNNING' | 'COMPLETED' | 'FAILED' | 'STOPPED'


// 任务基础信息
export interface Task {
  id: string
  task_name: string
  task_type: TaskType
  describe?: string
  status: TaskStatus
  parameters: TaskParameters
  account_id: string
  proxy_id?: string
  error_message?: string
  created_at: string
  updated_at: string
}

// 任务参数
export interface TaskParameters {
  // 用户推文
  uid?: string
  limit?: number
  include_replies?: boolean
  include_retweets?: boolean
  
  // 搜索推文
  query?: string
  
  // 话题推文
  topic?: string
  
  // 用户信息
  username?: string
}

// 创建任务参数
export interface TaskCreateParams {
  task_name: string
  task_type: TaskType
  describe?: string
  parameters: TaskParameters
  account_id: string
  proxy_id?: string
}

// 更新任务参数
export interface TaskUpdateParams {
  task_name?: string
  describe?: string
  parameters?: TaskParameters
  account_id?: string
  proxy_id?: string
}

// 任务状态响应
export interface TaskStatusResponse {
  id: string
  task_name: string
  status: TaskStatus
  error_message?: string
  created_at: string
  updated_at?: string
}

// 任务结果
export interface TaskResult {
  _id: string
  task_id: string
  data_type: string
  data: any
  created_at: string
}

// 任务结果列表响应
export interface TaskResultListResponse {
  items: TaskResult[]
  total: number
  page?: number
  size?: number
}

// 任务结果查询参数
export interface TaskResultQuery {
  skip?: number
  limit?: number
  data_type?: string
  start_date?: string
  end_date?: string
}

// 批量创建任务参数
export interface BatchTaskCreateParams {
  tasks: TaskCreateParams[]
}

// 账户信息
export interface Account {
  id: string
  username: string
  email?: string
  login_method: string
  active: boolean
  proxy_id?: string
  last_used?: string
  created_at: string
  updated_at: string
  error_msg: string
  cookies: Record<string, string> | null
  headers: Record<string, string> | null
  user_agent: string
}

// 账户列表响应
export interface AccountListResponse {
  items: Account[]
  total: number
  page: number
  size: number
  pages: number
}

// 代理信息
export interface Proxy {
  id: string
  type: string
  ip: string
  port: number
  username?: string
  password?: string
  country?: string
  city?: string
  status: string
  created_at: string
  updated_at: string
}

// 代理列表响应
export interface ProxyListResponse {
  items: Proxy[]
  total: number
  page: number
  size: number
  pages: number
}

// 任务列表响应
export interface TaskListResponse {
  items: Task[]
  total: number
  page: number
  size: number
  pages: number
}

// 任务统计（前端计算使用）
export interface TaskStats {
  total: number
  pending: number
  running: number
  completed: number
  failed: number
  byType: Record<TaskType, number>
  totalResults: number
}

// 导出任务类型别名
export { PaginationParams, PaginatedResponse } 