import request from '@/utils/request'
import type { DashboardStats, SystemStatus } from '@/types/dashboard'

// 获取仪表盘统计数据
export const getDashboardStats = async (): Promise<DashboardStats> => {
  const response = await request.get('/dashboard/stats')
  return response.data
}

// 获取系统状态
export const getSystemStatus = async (): Promise<SystemStatus> => {
  const response = await request.get('/dashboard/system-status')
  return response.data
}

// 获取任务趋势数据
export const getTaskTrends = async (days: number = 7): Promise<any[]> => {
  const response = await request.get('/dashboard/task-trends', { params: { days } })
  return response.data
}

// 获取服务健康状态
export const getServiceHealth = async (): Promise<Record<string, boolean>> => {
  const response = await request.get('/dashboard/service-health')
  return response.data
}

// 获取最近活动
export const getRecentActivities = async (limit: number = 10): Promise<any[]> => {
  const response = await request.get('/dashboard/activities', { params: { limit } })
  return response.data
} 