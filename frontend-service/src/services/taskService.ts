import * as taskApi from '@/api/tasks'
import type { Task, TaskCreateParams, TaskUpdateParams, PaginationParams, PaginatedResponse } from '@/types/task'
import { ElMessage, ElMessageBox } from 'element-plus'

class TaskService {
  /**
   * 获取任务列表
   */
  async getTasks(params: PaginationParams): Promise<PaginatedResponse<Task>> {
    try {
      return await taskApi.getTasks(params)
    } catch (error) {
      ElMessage.error('获取任务列表失败')
      throw error
    }
  }

  /**
   * 创建任务
   */
  async createTask(data: TaskCreateParams): Promise<Task> {
    try {
      const task = await taskApi.createTask(data)
      ElMessage.success('任务创建成功')
      return task
    } catch (error) {
      ElMessage.error('任务创建失败')
      throw error
    }
  }

  /**
   * 更新任务
   */
  async updateTask(id: string, data: TaskUpdateParams): Promise<Task> {
    try {
      const task = await taskApi.updateTask(id, data)
      ElMessage.success('任务更新成功')
      return task
    } catch (error) {
      ElMessage.error('任务更新失败')
      throw error
    }
  }

  /**
   * 删除任务
   */
  async deleteTask(id: string, name: string): Promise<boolean> {
    try {
      await ElMessageBox.confirm(
        `确定要删除任务 "${name}" 吗？此操作不可撤销。`,
        '删除确认',
        {
          confirmButtonText: '确定删除',
          cancelButtonText: '取消',
          type: 'warning',
          confirmButtonClass: 'el-button--danger'
        }
      )

      await taskApi.deleteTask(id)
      ElMessage.success('任务删除成功')
      return true
    } catch (error) {
      if (error !== 'cancel') {
        ElMessage.error('任务删除失败')
      }
      return false
    }
  }

  /**
   * 启动任务
   */
  async startTask(id: string, name: string): Promise<boolean> {
    try {
      await taskApi.startTask(id)
      ElMessage.success(`任务 "${name}" 启动成功`)
      return true
    } catch (error) {
      ElMessage.error(`任务 "${name}" 启动失败`)
      return false
    }
  }

  /**
   * 停止任务
   */
  async stopTask(id: string, name: string): Promise<boolean> {
    try {
      await ElMessageBox.confirm(
        `确定要停止任务 "${name}" 吗？`,
        '停止确认',
        {
          confirmButtonText: '确定停止',
          cancelButtonText: '取消',
          type: 'warning'
        }
      )

      await taskApi.stopTask(id)
      ElMessage.success(`任务 "${name}" 已停止`)
      return true
    } catch (error) {
      if (error !== 'cancel') {
        ElMessage.error(`任务 "${name}" 停止失败`)
      }
      return false
    }
  }

  /**
   * 重启任务
   */
  async restartTask(id: string, name: string): Promise<boolean> {
    try {
      await taskApi.restartTask(id)
      ElMessage.success(`任务 "${name}" 重启成功`)
      return true
    } catch (error) {
      ElMessage.error(`任务 "${name}" 重启失败`)
      return false
    }
  }

  /**
   * 获取任务详情
   */
  async getTaskById(id: string): Promise<Task> {
    try {
      return await taskApi.getTaskById(id)
    } catch (error) {
      ElMessage.error('获取任务详情失败')
      throw error
    }
  }

  /**
   * 获取任务日志
   */
  async getTaskLogs(id: string): Promise<string[]> {
    try {
      const result = await taskApi.getTaskLogs(id)
      return result.logs
    } catch (error) {
      ElMessage.error('获取任务日志失败')
      throw error
    }
  }

  /**
   * 获取任务结果
   */
  async getTaskResults(id: string, params: PaginationParams): Promise<PaginatedResponse<any>> {
    try {
      return await taskApi.getTaskResults(id, params)
    } catch (error) {
      ElMessage.error('获取任务结果失败')
      throw error
    }
  }

  /**
   * 导出任务结果
   */
  async exportTaskResults(id: string, format: 'csv' | 'json' | 'xlsx', taskName: string): Promise<void> {
    try {
      ElMessage.info('正在导出数据...')
      const blob = await taskApi.exportTaskResults(id, format)
      
      // 创建下载链接
      const url = window.URL.createObjectURL(blob)
      const link = document.createElement('a')
      link.href = url
      link.download = `${taskName}_results.${format}`
      link.click()
      
      // 清理URL对象
      window.URL.revokeObjectURL(url)
      
      ElMessage.success('数据导出成功')
    } catch (error) {
      ElMessage.error('数据导出失败')
      throw error
    }
  }

  /**
   * 格式化任务状态
   */
  formatTaskStatus(status: string): { text: string; type: string } {
    const statusMap = {
      pending: { text: '等待中', type: 'info' },
      running: { text: '运行中', type: 'primary' },
      completed: { text: '已完成', type: 'success' },
      failed: { text: '失败', type: 'danger' },
      cancelled: { text: '已取消', type: 'warning' },
      paused: { text: '已暂停', type: 'warning' }
    }
    return statusMap[status as keyof typeof statusMap] || { text: status, type: 'info' }
  }

  /**
   * 格式化任务类型
   */
  formatTaskType(type: string): string {
    const typeMap = {
      scrape_user: '用户抓取',
      scrape_tweets: '推文抓取',
      scrape_followers: '粉丝抓取',
      scrape_following: '关注抓取',
      scrape_search: '搜索抓取'
    }
    return typeMap[type as keyof typeof typeMap] || type
  }

  /**
   * 格式化任务优先级
   */
  formatTaskPriority(priority: string): { text: string; type: string } {
    const priorityMap = {
      low: { text: '低', type: 'info' },
      normal: { text: '普通', type: 'primary' },
      high: { text: '高', type: 'warning' },
      urgent: { text: '紧急', type: 'danger' }
    }
    return priorityMap[priority as keyof typeof priorityMap] || { text: priority, type: 'info' }
  }

  /**
   * 格式化持续时间
   */
  formatDuration(seconds: number): string {
    if (seconds < 60) {
      return `${seconds}秒`
    } else if (seconds < 3600) {
      return `${Math.floor(seconds / 60)}分${seconds % 60}秒`
    } else {
      const hours = Math.floor(seconds / 3600)
      const minutes = Math.floor((seconds % 3600) / 60)
      return `${hours}小时${minutes}分`
    }
  }

  /**
   * 验证任务表单数据
   */
  validateTaskForm(data: TaskCreateParams): string[] {
    const errors: string[] = []

    if (!data.name?.trim()) {
      errors.push('任务名称不能为空')
    }

    if (!data.type) {
      errors.push('请选择任务类型')
    }

    if (!data.config.target?.trim()) {
      errors.push('目标参数不能为空')
    }

    if (data.config.max_results && data.config.max_results <= 0) {
      errors.push('最大结果数必须大于0')
    }

    return errors
  }
}

// 导出单例实例
export const taskService = new TaskService()
export default taskService 