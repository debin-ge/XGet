// 仪表盘统计数据
export interface DashboardStats {
  tasks: {
    total: number
    running: number
    completed: number
    failed: number
    todayCount: number
  }
  accounts: {
    total: number
    active: number
    inactive: number
    suspended: number
    loginSuccessRate: number
  }
  proxies: {
    total: number
    active: number
    inactive: number
    averageSpeed: number
    successRate: number
  }
}

// 系统状态
export interface SystemStatus {
  cpu: {
    usage: number // 0-100
    cores: number
  }
  memory: {
    used: number // bytes
    total: number // bytes
    usage: number // 0-100
  }
  disk: {
    used: number // bytes
    total: number // bytes
    usage: number // 0-100
  }
  services: ServiceStatus[]
  uptime: number // seconds
}

// 服务状态
export interface ServiceStatus {
  name: string
  status: 'healthy' | 'unhealthy' | 'unknown'
  uptime: number
  lastCheck: string
  response_time?: number
  error_message?: string
}

// 趋势数据点
export interface TrendDataPoint {
  date: string
  value: number
  label?: string
}

// 活动记录
export interface Activity {
  id: string
  type: 'account' | 'proxy' | 'task' | 'system'
  title: string
  status: string
  description?: string
  user: string
  timestamp: string
  metadata?: Record<string, any>
}

// 图表数据
export interface ChartData {
  labels: string[]
  datasets: ChartDataset[]
}

export interface ChartDataset {
  label: string
  data: number[]
  backgroundColor?: string | string[]
  borderColor?: string | string[]
  borderWidth?: number
} 