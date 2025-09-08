import request from '@/utils/request'
import type { AnalyticsResponse, RecentActivitiesResponse } from '@/types/analytics'

// 获取账户实时统计数据
export const getAccountsRealtimeAnalytics = async (): Promise<AnalyticsResponse> => {
  const response = await request.get('/analytics/accounts/realtime')
  return response.data
}

// 获取账户历史统计数据
export const getAccountsHistoryAnalytics = async (timeRange: string = '24h'): Promise<AnalyticsResponse> => {
  const response = await request.get('/analytics/accounts/history', { 
    params: { time_range: timeRange } 
  })
  return response.data
}

// 获取代理实时统计数据
export const getProxiesRealtimeAnalytics = async (): Promise<AnalyticsResponse> => {
  const response = await request.get('/analytics/proxies/realtime')
  return response.data
}

// 获取代理历史统计数据
export const getProxiesHistoryAnalytics = async (timeRange: string = '24h'): Promise<AnalyticsResponse> => {
  const response = await request.get('/analytics/proxies/history', { 
    params: { time_range: timeRange } 
  })
  return response.data
}

// 获取任务实时统计数据
export const getTasksRealtimeAnalytics = async (): Promise<AnalyticsResponse> => {
  const response = await request.get('/analytics/tasks/realtime')
  return response.data
}

// 获取任务历史统计数据
export const getTasksHistoryAnalytics = async (timeRange: string = '24h'): Promise<AnalyticsResponse> => {
  const response = await request.get('/analytics/tasks/history', { 
    params: { time_range: timeRange } 
  })
  return response.data
}

// 获取代理质量统计
export const getProxyQualityStats = async (proxyId?: string): Promise<AnalyticsResponse> => {
  const response = await request.get('/analytics/proxies/quality', { 
    params: { proxy_id: proxyId } 
  })
  return response.data
}

// 获取任务效率统计
export const getTaskEfficiencyStats = async (taskId?: string): Promise<AnalyticsResponse> => {
  const response = await request.get('/analytics/tasks/efficiency', { 
    params: { task_id: taskId } 
  })
  return response.data
}

// 获取数据质量洞察
export const getDataQualityInsights = async (collectionName?: string): Promise<AnalyticsResponse> => {
  const response = await request.get('/analytics/results/quality', { 
    params: { collection_name: collectionName } 
  })
  return response.data
}

// 获取账户使用统计
export const getAccountUsageStats = async (accountId?: string): Promise<AnalyticsResponse> => {
  const response = await request.get('/analytics/accounts/usage', { 
    params: { account_id: accountId } 
  })
  return response.data
}

// 获取任务历史统计数据（新端点）
export const getTasksTrends = async (timeRange: string = '7d'): Promise<any> => {
  const response = await request.get('/analytics/tasks/trends', { 
    params: { 
      time_range: timeRange,
    } 
  })
  return response.data
}

// 获取最近活动（新端点）
export const getRecentActivities = async (limit: number = 10): Promise<RecentActivitiesResponse> => {
  const response = await request.get('/analytics/activities/recent', { 
    params: { limit } 
  })
  return response.data
}