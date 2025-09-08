import type { DashboardStats, Activity, TrendDataPoint } from '@/types/dashboard'
import { 
  getAccountsRealtimeAnalytics, 
  getProxiesRealtimeAnalytics, 
  getTasksRealtimeAnalytics, 
  getTasksTrends,
  getRecentActivities
} from '@/api/analytics'
import type { 
  RecentActivity
} from '@/types/analytics'

class DashboardService {
  /**
   * 获取仪表盘统计数据
   */
  async getDashboardStats(): Promise<DashboardStats> {
    try {
      console.log('获取实时分析数据...')
      
      // 并行获取所有实时统计数据
      const [accountsData, proxiesData, tasksData] = await Promise.all([
        getAccountsRealtimeAnalytics(),
        getProxiesRealtimeAnalytics(),
        getTasksRealtimeAnalytics(),
      ])

      // 提取数据或使用默认值
      const accountsStats = accountsData.success ? accountsData.data : { active_accounts: 0, login_success_rate: 0 }
      const proxiesStats = proxiesData.success ? proxiesData.data : { total_proxies: 0, active_proxies: 0, success_rate: 0, avg_speed: 0 }
      const tasksStats = tasksData.success ? tasksData.data : { total_tasks: 0, running_tasks: 0, completed_tasks: 0, failed_tasks: 0 }

      return {
        tasks: {
          total: tasksStats.total_tasks || 0,
          running: tasksStats.running_tasks || 0,
          completed: tasksStats.completed_tasks || 0,
          failed: tasksStats.failed_tasks || 0,
          todayCount: tasksStats.today_tasks || 0
        },
        accounts: {
          total: accountsStats.total_accounts || accountsStats.active_accounts || 0,
          active: accountsStats.active_accounts || 0,
          inactive: (accountsStats.total_accounts || accountsStats.active_accounts || 0) - (accountsStats.active_accounts || 0),
          suspended: 0, // 需要从账户服务获取挂起状态
          loginSuccessRate: accountsStats.login_success_rate || 0
        },
        proxies: {
          total: proxiesStats.total_proxies || 0,
          active: proxiesStats.active_proxies || 0,
          inactive: (proxiesStats.total_proxies || 0) - (proxiesStats.active_proxies || 0),
          averageSpeed: proxiesStats.avg_speed || 0,
          successRate: proxiesStats.success_rate || 0
        }
      }
    } catch (error) {
      console.error('获取仪表盘统计数据失败:', error)
      throw new Error('无法获取仪表盘统计数据，请检查分析服务连接')
    }
  }

  /**
   * 获取任务趋势数据
   */
  async getTaskTrends(days: number = 7): Promise<any> {
    try {
      console.log('获取任务趋势数据...')
      
      // 根据天数确定时间范围
      let timeRange = '24h'
      if (days === 7) timeRange = '7d'
      else if (days === 30) timeRange = '30d'

      const response = await getTasksTrends(timeRange)
      
      if (response.success && response.data) {
        // 返回完整的API响应数据，让前端组件处理图表配置
        return response.data
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
      throw new Error('无法获取任务趋势数据，请检查分析服务连接')
    }
  }

  /**
   * 格式化趋势标签
   */
  private formatTrendLabel(timestamp: string, timeRange: string): string {
    const date = new Date(timestamp)
    
    if (timeRange === '24h' || timeRange === '1h') {
      return date.toLocaleTimeString('zh-CN', { 
        hour: '2-digit', 
        minute: '2-digit' 
      })
    } else {
      return date.toLocaleDateString('zh-CN', { 
        month: 'short', 
        day: 'numeric' 
      })
    }
  }

  /**
   * 获取最近活动
   */
  async getRecentActivities(limit: number = 10): Promise<Activity[]> {
    try {
      console.log('获取最近活动数据...')
      
      const response = await getRecentActivities(limit)
      
      if (response.activities) {
        // 转换分析服务数据为前端需要的格式
        return response.activities.map((activity: RecentActivity) => ({
          id: activity.id,
          type: this.mapActivityType(activity.type),
          title: this.getActivityTitle(activity.type, activity.status),
          status: activity.status,
          description: activity.description,
          user: this.extractUserFromActivity(activity),
          timestamp: activity.timestamp,
          metadata: activity.details
        }))
      }
      
      // 如果API返回空数据，返回空数组
      return []
    } catch (error) {
      console.error('获取最近活动数据失败:', error)
      throw new Error('无法获取最近活动数据，请检查分析服务连接')
    }
  }

  /**
   * 映射活动类型
   */
  private mapActivityType(activityType: string): 'account' | 'proxy' | 'task' | 'system' {
    const typeMap: Record<string, 'account' | 'proxy' | 'task' | 'system'> = {
      'ACCOUNT_LOGIN': 'account',
      'PROXY_USAGE': 'proxy',
      'TASK_EXECUTION': 'task'
    }
    return typeMap[activityType] || 'system'
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
      'COMPLETED': '已完成'
    }
    
    const typeTitle = typeTitles[activityType] || '系统活动'
    const statusTitle = statusTitles[status] || status
    
    return `${typeTitle}--${statusTitle}`
  }

  /**
   * 从活动数据中提取用户信息
   */
  private extractUserFromActivity(activity: RecentActivity): string {
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