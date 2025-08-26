import * as proxyApi from '@/api/proxies'
import type { Proxy, ProxyCreateParams, ProxyUpdateParams, PaginationParams, PaginatedResponse } from '@/types/proxy'
import { ElMessage, ElMessageBox } from 'element-plus'

class ProxyService {
  /**
   * 获取代理列表
   */
  async getProxies(params?: PaginationParams): Promise<Proxy[]> {
    try {
      // 转换PaginationParams为API需要的格式
      const apiParams: any = {}
      
      if (params?.page && params?.pageSize) {
        apiParams.page = params.page
        apiParams.size = params.pageSize
      }
      
      if (params?.search) {
        apiParams.search = params.search
      }
      
      // 注意：这里可能需要根据实际API调整状态参数
      const result = await proxyApi.getProxies(apiParams)
      return result.items as unknown as Proxy[]
    } catch (error) {
      ElMessage.error('获取代理列表失败')
      throw error
    }
  }

  /**
   * 创建代理
   */
  async createProxy(data: ProxyCreateParams): Promise<Proxy> {
    try {
      const proxy = await proxyApi.createProxy(data)
      ElMessage.success('代理创建成功')
      return proxy as unknown as Proxy
    } catch (error) {
      ElMessage.error('代理创建失败')
      throw error
    }
  }

  /**
   * 更新代理
   */
  async updateProxy(id: string, data: ProxyUpdateParams): Promise<Proxy> {
    try {
      const proxy = await proxyApi.updateProxy(id, data)
      ElMessage.success('代理更新成功')
      return proxy as unknown as Proxy
    } catch (error) {
      ElMessage.error('代理更新失败')
      throw error
    }
  }

  /**
   * 删除代理
   */
  async deleteProxy(id: string, ip: string): Promise<boolean> {
    try {
      await ElMessageBox.confirm(
        `确定要删除代理 "${ip}" 吗？此操作不可撤销。`,
        '删除确认',
        {
          confirmButtonText: '确定删除',
          cancelButtonText: '取消',
          type: 'warning',
          confirmButtonClass: 'el-button--danger'
        }
      )

      await proxyApi.deleteProxy(id)
      ElMessage.success('代理删除成功')
      return true
    } catch (error) {
      if (error !== 'cancel') {
        ElMessage.error('代理删除失败')
      }
      return false
    }
  }

  /**
   * 检测代理连接
   */
  async checkProxy(id: string): Promise<boolean> {
    try {
      ElMessage.info('正在检测代理连接...')
      const result = await proxyApi.checkProxy(id)
      
      if (result.active > 0) {
        const latencyText = result.results[0].latency ? ` (延迟: ${result.results[0].latency}ms)` : ''
        ElMessage.success(`代理 "${id}" 连接测试成功${latencyText}`)
        return true
      } else {
        ElMessage.warning(`代理 "${id}" 连接测试失败: ${result.results[0].error_msg || '未知错误'}`)
        return false
      }
    } catch (error) {
      ElMessage.error(`代理 "${id}" 连接测试失败`)
      return false
    }
  }

  /**
   * 健康检查
   */
  async healthCheckProxy(id: string, ip: string): Promise<boolean> {
    try {
      // TODO: 实现健康检查API
      // const result = await proxyApi.healthCheckProxy(id)
      ElMessage.info(`代理 "${ip}" 健康检查功能暂未实现`)
      return false
    } catch (error) {
      ElMessage.error(`代理 "${ip}" 健康检查失败`)
      return false
    }
  }

  /**
   * 格式化代理状态
   */
  formatProxyStatus(status: string): { text: string; type: string } {
    const statusMap = {
      active: { text: '活跃', type: 'success' },
      inactive: { text: '未激活', type: 'info' },
      error: { text: '错误', type: 'danger' },
      testing: { text: '测试中', type: 'warning' }
    }
    return statusMap[status as keyof typeof statusMap] || { text: status, type: 'info' }
  }

  /**
   * 格式化代理类型
   */
  formatProxyType(type: string): string {
    const typeMap = {
      http: 'HTTP',
      https: 'HTTPS',
      socks4: 'SOCKS4',
      socks5: 'SOCKS5'
    }
    return typeMap[type as keyof typeof typeMap] || type
  }

  /**
   * 格式化代理地址
   */
  formatProxyAddress(proxy: Proxy): string {
    return `${proxy.ip}:${proxy.port}`
  }

  /**
   * 验证代理表单数据
   */
  validateProxyForm(data: ProxyCreateParams | ProxyUpdateParams): string[] {
    const errors: string[] = []

    if ('ip' in data && !data.ip?.trim()) {
      errors.push('IP地址不能为空')
    }

    if ('port' in data && (!data.port || data.port < 1 || data.port > 65535)) {
      errors.push('端口号必须在1-65535之间')
    }

    if ('type' in data && !data.type) {
      errors.push('请选择代理类型')
    }

    // 验证IP地址格式
    if ('ip' in data && data.ip) {
      const ipRegex = /^(?:(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.){3}(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)$/
      const domainRegex = /^[a-zA-Z0-9][a-zA-Z0-9-]{0,61}[a-zA-Z0-9](?:\.[a-zA-Z0-9][a-zA-Z0-9-]{0,61}[a-zA-Z0-9])*$/
      
      if (!ipRegex.test(data.ip) && !domainRegex.test(data.ip)) {
        errors.push('请输入有效的IP地址或域名')
      }
    }

    return errors
  }
}

// 导出单例实例
export const proxyService = new ProxyService()
export default proxyService 