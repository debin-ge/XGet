import request from '@/utils/request'
import type { DashboardStats, SystemStatus } from '@/types/dashboard'

// 获取仪表盘统计数据 - 现在直接通过dashboardService从各服务获取
export const getDashboardStats = async (): Promise<DashboardStats> => {
  // 这个函数现在由dashboardService内部实现，直接调用各服务的analytics接口
  throw new Error('请使用dashboardService.getDashboardStats()代替')
}

// 获取系统状态
export const getSystemStatus = async (): Promise<SystemStatus> => {
  const response = await request.get('/dashboard/system-status/')
  return response.data
}

// 获取任务趋势数据 - 现在直接通过dashboardService从采集服务获取
export const getTaskTrends = async (days: number = 7): Promise<any[]> => {
  // 这个函数现在由dashboardService内部实现，直接调用采集服务的analytics接口
  throw new Error('请使用dashboardService.getTaskTrends()代替')
}

// 获取服务健康状态
export const getServiceHealth = async (): Promise<Record<string, boolean>> => {
  const response = await request.get('/dashboard/service-health/')
  return response.data
}

// 获取最近活动 - 现在直接通过dashboardService从各服务获取并整合
export const getRecentActivities = async (limit: number = 10): Promise<any[]> => {
  // 这个函数现在由dashboardService内部实现，直接调用各服务的analytics接口并整合
  throw new Error('请使用dashboardService.getRecentActivities()代替')
} 