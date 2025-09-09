import type { DashboardStats, Activity } from '@/types/dashboard'
import request from '@/utils/request'

class DashboardService {
  /**
   * 获取仪表盘统计数据
   * 直接从各服务获取实时数据
   */
  async getDashboardStats(): Promise<DashboardStats> {
    try {
      console.log('从各服务获取实时分析数据...')
      
      // 并行从各服务获取实时统计数据
      const [accountsData, proxiesData, tasksData] = await Promise.all([
        this.getAccountsRealtimeData(),
        this.getProxiesRealtimeData(),
        this.getTasksRealtimeData(),
      ])

      return {
        tasks: {
          total: tasksData.total_tasks || 0,
          running: tasksData.running_tasks || 0,
          completed: tasksData.completed_tasks || 0,
          failed: tasksData.failed_tasks || 0,
          todayCount: tasksData.today_tasks || 0
        },
        accounts: {
          total: accountsData.total_accounts || accountsData.active_accounts || 0,
          active: accountsData.active_accounts || 0,
          inactive: (accountsData.total_accounts || accountsData.active_accounts || 0) - (accountsData.active_accounts || 0),
          suspended: accountsData.suspended_accounts || 0,
          loginSuccessRate: accountsData.login_success_rate || 0
        },
        proxies: {
          total: proxiesData.total_proxies || 0,
          active: proxiesData.active_proxies || 0,
          inactive: (proxiesData.total_proxies || 0) - (proxiesData.active_proxies || 0),
          averageSpeed: proxiesData.avg_speed || proxiesData.averageSpeed || 0,
          successRate: proxiesData.success_rate || 0
        }
      }
    } catch (error) {
      console.error('获取仪表盘统计数据失败:', error)
      throw new Error('无法获取仪表盘统计数据，请检查服务连接')
    }
  }

  /**
   * 从账户服务获取实时数据
   */
  private async getAccountsRealtimeData(): Promise<any> {
    try {
      const response = await request.get('/accounts/analytics/realtime')
      return response.data?.data || response.data || {}
    } catch (error) {
      console.warn('获取账户实时数据失败，使用默认值:', error)
      return { active_accounts: 0, login_success_rate: 0 }
    }
  }

  /**
   * 从代理服务获取实时数据
   */
  private async getProxiesRealtimeData(): Promise<any> {
    try {
      const response = await request.get('/proxies/analytics/realtime')
      return response.data?.data || response.data || {}
    } catch (error) {
      console.warn('获取代理实时数据失败，使用默认值:', error)
      return { total_proxies: 0, active_proxies: 0, success_rate: 0, avg_speed: 0 }
    }
  }

  /**
   * 从采集服务获取实时数据
   */
  private async getTasksRealtimeData(): Promise<any> {
    try {
      const response = await request.get('/tasks/analytics/realtime')
      return response.data?.data || response.data || {}
    } catch (error) {
      console.warn('获取任务实时数据失败，使用默认值:', error)
      return { total_tasks: 0, running_tasks: 0, completed_tasks: 0, failed_tasks: 0 }
    }
  }

  /**
   * 获取任务趋势数据
   * 直接从采集服务获取
   */
  async getTaskTrends(days: number = 7): Promise<any> {
    try {
      console.log('从采集服务获取任务趋势数据...')
      
      // 根据天数确定时间范围
      let timeRange = '24h'
      if (days === 7) timeRange = '7d'
      else if (days === 30) timeRange = '30d'

      const response = await request.get('/tasks/analytics/trends', {
        params: { time_range: timeRange }
      })
      
      const data = response.data?.data || response.data || {}
      
      if (data && data.time_labels && data.series_data) {
        return data
      }
      
      // 如果API返回空数据，返回默认结构
      return {
        time_labels: [],
        series_data: {
          completed_tasks: [],
          failed_tasks: [],
          pending_tasks: [],
          running_tasks: [],
          total_tasks: [],
          success_rate: []
        }
      }
    } catch (error) {
      console.error('获取任务趋势数据失败:', error)
      throw new Error('无法获取任务趋势数据，请检查采集服务连接')
    }
  }

  /**
   * 获取最近活动
   * 从各服务获取活动数据并整合排序
   */
  async getRecentActivities(limit: number = 10): Promise<Activity[]> {
    try {
      console.log('从各服务获取最近活动数据...')
      
      // 并行从各服务获取活动数据
      const [accountActivities, proxyActivities, taskActivities] = await Promise.all([
        this.getAccountActivities(limit),
        this.getProxyActivities(limit),
        this.getTaskActivities(limit),
      ])

      // 合并所有活动数据
      const allActivities = [
        ...accountActivities,
        ...proxyActivities,
        ...taskActivities
      ]

      // 按时间戳降序排序
      allActivities.sort((a, b) => 
        new Date(b.timestamp).getTime() - new Date(a.timestamp).getTime()
      )

      // 返回前N个活动
      return allActivities.slice(0, limit)
    } catch (error) {
      console.error('获取最近活动数据失败:', error)
      throw new Error('无法获取最近活动数据，请检查服务连接')
    }
  }

  /**
   * 从账户服务获取活动数据
   */
  private async getAccountActivities(limit: number): Promise<Activity[]> {
    try {
      const response = await request.get('/accounts/analytics/activities/recent', {
        params: { limit }
      })
      
      const activities = response.data?.data || response.data || []
      return activities.map((activity: any) => ({
        id: activity.id || `account-${Date.now()}-${Math.random()}`,
        type: 'account' as const,
        title: this.getActivityTitle(activity.type || 'ACCOUNT_LOGIN', activity.status || 'UNKNOWN'),
        status: activity.status || 'UNKNOWN',
        description: activity.description || `账户活动: ${activity.task_name || activity.account_id || '未知账户'}`,
        user: this.extractUserFromActivity(activity),
        timestamp: activity.timestamp || activity.started_at || new Date().toISOString(),
        metadata: activity.details || activity
      }))
    } catch (error) {
      console.warn('获取账户活动数据失败:', error)
      return []
    }
  }

  /**
   * 从代理服务获取活动数据
   */
  private async getProxyActivities(limit: number): Promise<Activity[]> {
    try {
      const response = await request.get('/proxies/analytics/activities/recent', {
        params: { limit }
      })
      
      const activities = response.data?.data || response.data || []
      return activities.map((activity: any) => ({
        id: activity.id || `proxy-${Date.now()}-${Math.random()}`,
        type: 'proxy' as const,
        title: this.getActivityTitle(activity.type || 'PROXY_USAGE', activity.status || 'UNKNOWN'),
        status: activity.status || 'UNKNOWN',
        description: activity.description || `代理活动: ${activity.proxy_id || activity.proxy_name || '未知代理'}`,
        user: this.extractUserFromActivity(activity),
        timestamp: activity.timestamp || activity.created_at || new Date().toISOString(),
        metadata: activity.details || activity
      }))
    } catch (error) {
      console.warn('获取代理活动数据失败:', error)
      return []
    }
  }

  /**
   * 从采集服务获取活动数据
   */
  private async getTaskActivities(limit: number): Promise<Activity[]> {
    try {
      const response = await request.get('/tasks/analytics/activities/recent', {
        params: { limit }
      })
      
      const activities = response.data?.data || response.data || []
      return activities.map((activity: any) => ({
        id: activity.id || `task-${Date.now()}-${Math.random()}`,
        type: 'task' as const,
        title: this.getActivityTitle(activity.type || 'TASK_EXECUTION', activity.status || 'UNKNOWN'),
        status: activity.status || 'UNKNOWN',
        description: activity.description || `任务活动: ${activity.task_name || activity.task_id || '未知任务'}`,
        user: this.extractUserFromActivity(activity),
        timestamp: activity.timestamp || activity.started_at || new Date().toISOString(),
        metadata: activity.details || activity
      }))
    } catch (error) {
      console.warn('获取任务活动数据失败:', error)
      return []
    }
  }

  /**
   * 获取活动标题
   */
  private getActivityTitle(activityType: string, status: string): string {
    const typeTitles: Record<string, string> = {
      'ACCOUNT_LOGIN': '账户登录',
      'PROXY_USAGE': '代理使用',
      'TASK_EXECUTION': '任务执行'
    }
    
    const statusTitles: Record<string, string> = {
      'SUCCESS': '成功',
      'FAILED': '失败',
      'RUNNING': '进行中',
      'COMPLETED': '已完成',
      'UNKNOWN': '未知'
    }
    
    const typeTitle = typeTitles[activityType] || '系统活动'
    const statusTitle = statusTitles[status] || status
    
    return `${typeTitle}-${statusTitle}`
  }

  /**
   * 从活动数据中提取用户信息
   */
  private extractUserFromActivity(activity: any): string {
    // 尝试从details中提取用户信息
    if (activity.details && activity.details.username) {
      return activity.details.username
    }
    if (activity.details && activity.details.user_id) {
      return `用户 ${activity.details.user_id}`
    }
    if (activity.details && activity.details.account_id) {
      return `账户 ${activity.details.account_id}`
    }
    if (activity.account_id) {
      return `账户 ${activity.account_id}`
    }
    if (activity.proxy_id) {
      return `代理 ${activity.proxy_id}`
    }
    if (activity.task_id) {
      return `任务 ${activity.task_id}`
    }
    
    // 根据活动类型返回默认用户
    switch (activity.type) {
      case 'ACCOUNT_LOGIN':
        return '系统账户'
      case 'PROXY_USAGE':
        return '代理服务'
      case 'TASK_EXECUTION':
        return '任务执行器'
      default:
        return '系统用户'
    }
  }

  /**
   * 格式化活动时间
   */
  formatActivityTime(timestamp: string): string {
    const now = new Date()
    const time = new Date(timestamp)
    const diffMs = now.getTime() - time.getTime()
    const diffMins = Math.floor(diffMs / (1000 * 60))
    const diffHours = Math.floor(diffMins / 60)
    const diffDays = Math.floor(diffHours / 24)

    if (diffMins < 1) {
      return '刚刚'
    } else if (diffMins < 60) {
      return `${diffMins}分钟前`
    } else if (diffHours < 24) {
      return `${diffHours}小时前`
    } else if (diffDays < 30) {
      return `${diffDays}天前`
    } else {
      return time.toLocaleDateString('zh-CN')
    }
  }
}

// 导出单例实例
export const dashboardService = new DashboardService()
export default dashboardService