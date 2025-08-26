import request from './index'
import type { DashboardStats, SystemStatus } from '@/types/dashboard'

// 获取仪表盘统计数据
export const getDashboardStats = (): Promise<DashboardStats> => {
  return request.get('/dashboard/stats')
}

// 获取系统状态
export const getSystemStatus = (): Promise<SystemStatus> => {
  return request.get('/dashboard/system-status')
}

// 获取任务趋势数据
export const getTaskTrends = (days: number = 7): Promise<any[]> => {
  return request.get('/dashboard/task-trends', { params: { days } })
}

// 获取服务健康状态
export const getServiceHealth = (): Promise<Record<string, boolean>> => {
  return request.get('/dashboard/service-health')
}

// 获取最近活动
export const getRecentActivities = (limit: number = 10): Promise<any[]> => {
  return request.get('/dashboard/activities', { params: { limit } })
} 