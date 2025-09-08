// 分析服务响应格式
export interface AnalyticsResponse {
  success: boolean
  message: string
  data?: any
}

// 账户实时统计数据
export interface AccountRealtimeStats {
  active_accounts: number
  login_success_rate: number
  avg_response_time: number
  last_updated: string
  error?: string
}

// 账户历史统计数据
export interface AccountHistoryStats {
  time_range: string
  trends: AccountTrendData[]
  health_metrics: AccountHealthMetrics
  error?: string
}

export interface AccountTrendData {
  timestamp: string
  total_logins: number
  successful_logins: number
  success_rate: number
  avg_response_time: number
}

export interface AccountHealthMetrics {
  total_accounts: number
  active_accounts: number
  error_accounts: number
  health_score: number
}

// 代理实时统计数据
export interface ProxyRealtimeStats {
  total_proxies: number
  active_proxies: number
  success_rate: number
  avg_speed: number
  last_updated: string
  error?: string
}

// 代理历史统计数据
export interface ProxyHistoryStats {
  time_range: string
  trends: ProxyTrendData[]
  quality_metrics: ProxyQualityMetrics
  error?: string
}

export interface ProxyTrendData {
  timestamp: string
  total_requests: number
  successful_requests: number
  success_rate: number
  avg_speed: number
}

export interface ProxyQualityMetrics {
  total_proxies: number
  high_quality: number
  medium_quality: number
  low_quality: number
  avg_quality_score: number
}

// 任务实时统计数据
export interface TaskRealtimeStats {
  total_tasks: number
  running_tasks: number
  completed_tasks: number
  failed_tasks: number
  success_rate: number
  last_updated: string
  error?: string
}

// 任务历史统计数据
export interface TaskHistoryStats {
  time_range: string
  trends: TaskTrendData[]
  efficiency_metrics: TaskEfficiencyMetrics
  error?: string
}

export interface TaskTrendData {
  timestamp: string
  total_tasks: number
  completed_tasks: number
  failed_tasks: number
  success_rate: number
  avg_execution_time: number
}

export interface TaskEfficiencyMetrics {
  total_tasks: number
  avg_success_rate: number
  avg_execution_time: number
  resource_utilization: number
}

// 结果实时统计数据
export interface ResultRealtimeStats {
  total_results: number
  today_results: number
  week_results: number
  month_results: number
  last_updated: string
  error?: string
}

// 结果历史统计数据
export interface ResultHistoryStats {
  time_range: string
  trends: ResultTrendData[]
  quality_metrics: DataQualityMetrics
  error?: string
}

export interface ResultTrendData {
  timestamp: string
  total_results: number
  valid_results: number
  invalid_results: number
  quality_score: number
}

export interface DataQualityMetrics {
  total_results: number
  valid_results: number
  completeness_score: number
  accuracy_score: number
  consistency_score: number
}

// 代理质量统计
export interface ProxyQualityStats {
  proxy_id?: string
  success_rate: number
  avg_speed: number
  reliability_score: number
  usage_count: number
  last_used: string
  error?: string
}

// 任务效率统计
export interface TaskEfficiencyStats {
  task_id?: string
  success_rate: number
  avg_execution_time: number
  resource_usage: number
  completion_rate: number
  error?: string
}

// 数据质量洞察
export interface DataQualityInsights {
  collection_name?: string
  total_documents: number
  valid_documents: number
  completeness: number
  accuracy: number
  timeliness: number
  error?: string
}

// 账户使用统计
export interface AccountUsageStats {
  account_id?: string
  total_logins: number
  successful_logins: number
  avg_response_time: number
  last_login: string
  error?: string
}

// 活动类型枚举
export enum ActivityType {
  ACCOUNT_LOGIN = "ACCOUNT_LOGIN",
  PROXY_USAGE = "PROXY_USAGE",
  TASK_EXECUTION = "TASK_EXECUTION"
}

// 最近活动
export interface RecentActivity {
  id: string
  type: ActivityType
  timestamp: string
  description: string
  status: string
  details: Record<string, any>
  service: string
}

// 最近活动响应
export interface RecentActivitiesResponse {
  activities: RecentActivity[]
  total_count: number
}

// 任务历史统计数据响应格式
export interface TaskHistoryResponse {
  time_range: string
  trends: TaskTrendDataPoint[]
  total_count: number
  success_rate: number
  avg_execution_time: number
}

export interface TaskTrendDataPoint {
  timestamp: string
  total_tasks: number
  completed_tasks: number
  failed_tasks: number
  success_rate: number
  avg_execution_time: number
}