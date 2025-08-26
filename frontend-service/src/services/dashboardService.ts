import type { DashboardStats, Activity, TrendDataPoint } from '@/types/dashboard'

class DashboardService {
  /**
   * 获取仪表盘统计数据
   */
  async getDashboardStats(): Promise<DashboardStats> {
      console.log('使用模拟数据: 仪表盘统计数据')
      return this.getMockDashboardStats()
  }

  /**
   * 获取任务趋势数据
   */
  async getTaskTrends(days: number = 7): Promise<TrendDataPoint[]> {
    console.log('使用模拟数据: 任务趋势数据')
    return this.getMockTaskTrends(days)
  }

  /**
   * 获取最近活动
   */
  async getRecentActivities(limit: number = 10): Promise<Activity[]> {
    console.log('使用模拟数据: 最近活动')
    return this.getMockRecentActivities(limit)
  }

  /**
   * 获取模拟仪表盘统计数据
   */
  private getMockDashboardStats(): DashboardStats {
    return {
      tasks: {
        total: 156,
        running: 8,
        completed: 132,
        failed: 16,
        todayCount: 12
      },
      accounts: {
        total: 42,
        active: 28,
        inactive: 10,
        suspended: 4
      },
      proxies: {
        total: 78,
        active: 65,
        inactive: 13,
        averageSpeed: 256
      },
      results: {
        totalCount: 12560,
        todayCount: 342,
        weekCount: 2189,
        monthCount: 8921
      }
    }
  }

  /**
   * 获取模拟任务趋势数据
   */
  private getMockTaskTrends(days: number = 7): TrendDataPoint[] {
    const trends: TrendDataPoint[] = []
    const now = new Date()
    
    for (let i = days - 1; i >= 0; i--) {
      const date = new Date(now)
      date.setDate(date.getDate() - i)
      
      trends.push({
        date: date.toISOString().split('T')[0],
        value: Math.floor(Math.random() * 50) + 20,
        label: date.toLocaleDateString('zh-CN')
      })
    }
    
    return trends
  }

  /**
   * 获取模拟最近活动
   */
  private getMockRecentActivities(limit: number = 10): Activity[] {
    const activityTypes = [
      'task_created', 'task_completed', 'task_failed', 
      'account_added', 'proxy_added', 'user_login'
    ]
    
    const activityTitles = {
      task_created: '新任务创建',
      task_completed: '任务完成',
      task_failed: '任务失败',
      account_added: '账户添加',
      proxy_added: '代理添加',
      user_login: '用户登录'
    }
    
    const users = ['admin', 'user1', 'user2', 'operator1']
    const activities: Activity[] = []
    const now = new Date()
    
    for (let i = 0; i < limit; i++) {
      const type = activityTypes[Math.floor(Math.random() * activityTypes.length)]
      const user = users[Math.floor(Math.random() * users.length)]
      const timestamp = new Date(now.getTime() - Math.random() * 24 * 60 * 60 * 1000 * 3)
      
      activities.push({
        id: `activity-${i}`,
        type: type as any,
        title: activityTitles[type as keyof typeof activityTitles],
        user,
        timestamp: timestamp.toISOString(),
        metadata: {
          taskId: type.includes('task') ? `task-${Math.floor(Math.random() * 1000)}` : undefined,
          accountId: type.includes('account') ? `account-${Math.floor(Math.random() * 100)}` : undefined,
          proxyId: type.includes('proxy') ? `proxy-${Math.floor(Math.random() * 100)}` : undefined
        }
      })
    }
    
    return activities.sort((a, b) => new Date(b.timestamp).getTime() - new Date(a.timestamp).getTime())
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