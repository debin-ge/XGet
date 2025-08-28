import * as authApi from '@/api/auth'
import type { LoginParams, RegisterParams, User, LoginResponse } from '@/types/auth'
import { ElMessage } from 'element-plus'

class AuthService {
  private readonly TOKEN_KEY = 'access_token'
  private readonly REFRESH_TOKEN_KEY = 'refresh_token'
  private readonly USER_KEY = 'user_info'
  private readonly EXPIRES_AT_KEY = 'token_expires_at'

  /**
   * 用户登录
   */
  async login(loginData: LoginParams): Promise<LoginResponse> {
    try {
      const response = await authApi.login(loginData)
      // 保存token和用户信息
      this.setToken(response.access_token)
      this.setRefreshToken(response.refresh_token)
      this.setUserInfo(response.user)
      this.setTokenExpiresAt(response.expires_at)
      
      ElMessage.success('登录成功')
      return response
    } catch (error) {
      ElMessage.error('登录失败，请检查用户名和密码')
      throw error
    }
  }

  /**
   * 用户注册
   */
  async register(registerData: RegisterParams): Promise<void> {
    try {
      await authApi.register(registerData)
      ElMessage.success('注册成功，请登录')
    } catch (error) {
      ElMessage.error('注册失败，请检查输入信息')
      throw error
    }
  }

  /**
   * 用户登出
   */
  async logout(): Promise<void> {
    try {
      await authApi.logout()
    } catch (error) {
      console.error('Logout API call failed:', error)
    } finally {
      // 无论API调用是否成功，都清理本地数据
      this.clearAuthData()
      ElMessage.success('已安全退出')
    }
  }

  /**
   * 获取当前用户信息
   */
  async getCurrentUser(): Promise<User | null> {
    try {
      const response = await authApi.getCurrentUser()
      const user = response.data
      this.setUserInfo(user)
      return user
    } catch (error) {
      console.error('Failed to get current user:', error)
      this.clearAuthData()
      return null
    }
  }

  /**
   * 刷新token
   */
  async refreshToken(): Promise<boolean> {
    try {
      const response = await authApi.refreshToken()
      this.setToken(response.access_token)
      this.setRefreshToken(response.refresh_token)
      this.setUserInfo(response.user)
      this.setTokenExpiresAt(response.expires_at)
      return true
    } catch (error) {
      console.error('Token refresh failed:', error)
      this.clearAuthData()
      return false
    }
  }

  /**
   * 检查是否已登录
   */
  isAuthenticated(): boolean {
    return !!this.getToken()
  }

  /**
   * 获取access token
   */
  getAccessToken(): string | null {
    return this.getToken()
  }

  /**
   * 获取token (保持向后兼容)
   */
  getToken(): string | null {
    return localStorage.getItem(this.TOKEN_KEY)
  }

  /**
   * 设置tokens
   */
  setTokens(accessToken: string, refreshToken: string): void {
    this.setToken(accessToken)
    this.setRefreshToken(refreshToken)
  }

  /**
   * 设置token
   */
  private setToken(token: string): void {
    localStorage.setItem(this.TOKEN_KEY, token)
  }

  /**
   * 获取刷新token
   */
  getRefreshToken(): string | null {
    return localStorage.getItem(this.REFRESH_TOKEN_KEY)
  }

  /**
   * 设置刷新token
   */
  private setRefreshToken(token: string): void {
    localStorage.setItem(this.REFRESH_TOKEN_KEY, token)
  }

  /**
   * 获取用户信息
   */
  getUserInfo(): User | null {
    const userStr = localStorage.getItem(this.USER_KEY)
    if (userStr) {
      try {
        return JSON.parse(userStr)
      } catch (error) {
        console.error('Failed to parse user info:', error)
        return null
      }
    }
    return null
  }

  /**
   * 设置用户信息
   */
  setUserInfo(user: User): void {
    localStorage.setItem(this.USER_KEY, JSON.stringify(user))
  }

  /**
   * 检查token是否即将过期（3分钟内）
   */
  isTokenExpiringSoon(): boolean {
    const expiresAt = this.getTokenExpiresAt()
    if (!expiresAt) return false
    
    const now = new Date().getTime()
    // 解析格式为 "%Y-%m-%d %H:%M:%S" 的时间字符串
    const expiresTime = new Date(expiresAt.replace(' ', 'T') + 'Z').getTime()
    const threeMinutes = 3 * 60 * 1000 // 3分钟毫秒数
    
    return expiresTime - now <= threeMinutes
  }

  /**
   * 获取token过期时间
   */
  getTokenExpiresAt(): string | null {
    return localStorage.getItem(this.EXPIRES_AT_KEY)
  }

  /**
   * 设置token过期时间
   */
  private setTokenExpiresAt(expiresAt: string): void {
    localStorage.setItem(this.EXPIRES_AT_KEY, expiresAt)
  }

  /**
   * 清理认证数据
   */
  private clearAuthData(): void {
    localStorage.removeItem(this.TOKEN_KEY)
    localStorage.removeItem(this.REFRESH_TOKEN_KEY)
    localStorage.removeItem(this.USER_KEY)
    localStorage.removeItem(this.EXPIRES_AT_KEY)
  }
}

// 导出单例实例
export const authService = new AuthService()
export default authService 