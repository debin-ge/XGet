import * as accountApi from '@/api/accounts'
import type { Account, AccountListParams, AccountCreateParams, AccountUpdateParams, AccountPlatform } from '@/types/account'
import { ElMessage, ElMessageBox } from 'element-plus'

interface PaginationParams {
  page?: number
  pageSize?: number
  search?: string
}

class AccountService {
  async getAccounts(params?: PaginationParams): Promise<Account[]> {
    try {
      const apiParams: AccountListParams = {
        page: params?.page || 1,
        size: params?.pageSize || 20,
        search: params?.search || undefined
      }
      
      const data = await accountApi.getAccounts(apiParams)
      return data.items
    } catch (error) {
      console.error('获取账户列表失败:', error)
      ElMessage.error('获取账户列表失败')
      throw error
    }
  }

  async createAccount(data: AccountCreateParams): Promise<Account> {
    try {
      // 转换前端表单数据到后端API格式
      const apiData: AccountCreateParams = {
        username: data.username,
        email: data.email,
        login_method: data.login_method,
        proxy_id: data.proxy_id
      }
      const account = await accountApi.createAccount(apiData)
      ElMessage.success('账户创建成功')
      return account
    } catch (error) {
      console.error('创建账户失败:', error)
      ElMessage.error('创建账户失败')
      throw error
    }
  }

  async updateAccount(id: string, data: AccountUpdateParams): Promise<Account> {
    try {
      // 转换前端表单数据到后端API格式
      const apiData: AccountUpdateParams = {
        username: data.username,
        password: data.password,
        email: data.email,
        email_password: data.email_password,
        login_method: data.login_method,
        proxy_id: data.proxy_id
      }
      const account = await accountApi.updateAccount(id, apiData)

      return account
    } catch (error) {
      console.error('更新账户失败:', error)

      throw error
    }
  }

  async deleteAccount(id: string, displayName: string): Promise<boolean> {
    try {
      await ElMessageBox.confirm(
        `确定要删除账户 "${displayName}" 吗？此操作不可撤销。`,
        '删除确认',
        {
          confirmButtonText: '确定删除',
          cancelButtonText: '取消',
          type: 'warning',
          confirmButtonClass: 'el-button--danger'
        }
      )

      const success = await accountApi.deleteAccount(id)
      if (!success) {
        ElMessage.error('账户删除失败')
        return false
      }
      ElMessage.success('账户删除成功')
      return true
    } catch (error) {
      if (error !== 'cancel') {
        console.error('删除账户失败:', error)
        ElMessage.error('删除账户失败')
      }
      return false
    }
  }

  async loginAccount(id: string, displayName: string, proxyId?: string): Promise<boolean> {
    try {
      const result = await accountApi.loginAccount({ account_id: id, proxy_id: proxyId, async_login: false })
      if (result.login_successful) {
        ElMessage.success(`账户 "${displayName}" 登录成功`)
        return true
      } else {
        ElMessage.error(`账户 "${displayName}" 登录失败`)
        return false
      }
    } catch (error) {
      console.error('账户登录失败:', error)
      ElMessage.error(`账户 "${displayName}" 登录失败`)
      return false
    }
  }

  async getAccount(id: string): Promise<Account> {
    try {
      const account = await accountApi.getAccountById(id)
      return account
    } catch (error) {
      console.error('获取账户详情失败:', error)
      ElMessage.error('获取账户详情失败')
      throw error
    }
  }

  validateAccountData(data: AccountCreateParams | AccountUpdateParams, isEdit: boolean): string[] {
    const errors: string[] = []

    // 验证邮箱格式
    if ('email' in data && data.email) {
      const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/
      if (!emailRegex.test(data.email)) {
        errors.push('邮箱格式不正确')
      }
    }

    switch (data.login_method) {
      case 'GOOGLE':
        if (!data.email) {
          errors.push('Google登录必须设置邮箱')
        }
        if (!data.email_password && !isEdit) {
          errors.push('Google登录必须设置密码')
        }
        break
      case 'TWITTER':
        if (!data.username) {
          errors.push('Twitter登录必须设置用户名')
        }
        if (!data.password && !isEdit) {
          errors.push('Twitter登录必须设置密码')
        }
        break
    }

    return errors
  }
}

export const accountService = new AccountService() 