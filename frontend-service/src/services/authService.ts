import * as authApi from '@/api/auth'
import type { LoginParams, RegisterParams, User, LoginResponse } from '@/types/auth'
import { ElMessage } from 'element-plus'

class AuthService {
  private readonly TOKEN_KEY = 'access_token'
  private readonly REFRESH_TOKEN_KEY = 'refresh_token'
  private readonly USER_KEY = 'user_info'

  // Cookie工具函数
  private setCookie(name: string, value: string, days = 7): void {
    const date = new Date()
    date.setTime(date.getTime() + (days * 24 * 60 * 60 * 1000))
    const expires = `expires=${date.toUTCString()}`
    document.cookie = `${name}=${encodeURIComponent(value)}; ${expires}; path=/`
  }

  // 设置带特定过期时间的cookie（用于token）
  private setCookieWithExpiration(name: string, value: string, expirationMinutes: number): void {
    const date = new Date()
    date.setTime(date.getTime() + (expirationMinutes * 60 * 1000))
    const expires = `expires=${date.toUTCString()}`
    document.cookie = `${name}=${encodeURIComponent(value)}; ${expires}; path=/`
  }

  private getCookie(name: string): string | null {
    const nameEQ = name + '='
    const ca = document.cookie.split(';')
    for (let i = 0; i < ca.length; i++) {
      let c = ca[i]
      while (c.charAt(0) === ' ') c = c.substring(1, c.length)
      if (c.indexOf(nameEQ) === 0) return decodeURIComponent(c.substring(nameEQ.length, c.length))
    }
    return null
  }

  private deleteCookie(name: string): void {
    document.cookie = `${name}=; expires=Thu, 01 Jan 1970 00:00:00 UTC; path=/;`
  }

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
    return this.getCookie(this.TOKEN_KEY)
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
    // access token 通常有效期较短，设置为30分钟
    this.setCookieWithExpiration(this.TOKEN_KEY, token, 30)
  }

  /**
   * 获取刷新token
   */
  getRefreshToken(): string | null {
    return this.getCookie(this.REFRESH_TOKEN_KEY)
  }

  /**
   * 设置刷新token
   */
  private setRefreshToken(token: string): void {
    // refresh token 有效期较长，设置为7天
    this.setCookieWithExpiration(this.REFRESH_TOKEN_KEY, token, 7 * 24 * 60)
  }

  /**
   * 获取用户信息
   */
  getUserInfo(): User | null {
    const userStr = this.getCookie(this.USER_KEY)
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
    // 用户信息与refresh token有效期一致
    this.setCookieWithExpiration(this.USER_KEY, JSON.stringify(user), 7 * 24 * 60)
  }

  /**
   * 检查token是否即将过期（3分钟内）
   */
  isTokenExpiringSoon(): boolean {
    const token = this.getToken()
    if (!token) return false
    
    // 从cookie中获取过期时间
    const cookieStr = document.cookie
    const tokenCookie = cookieStr.split(';').find(c => c.trim().startsWith(`${this.TOKEN_KEY}=`))
    if (!tokenCookie) return false
    
    // 查找expires参数
    const expiresMatch = cookieStr.match(new RegExp(`${this.TOKEN_KEY}=[^;]*;\s*expires=([^;]+)`))
    if (!expiresMatch) return false
    
    const expiresTime = new Date(expiresMatch[1]).getTime()
    const now = new Date().getTime()
    const threeMinutes = 3 * 60 * 1000 // 3分钟毫秒数
    
    return expiresTime - now <= threeMinutes
  }

  /**
   * 清理认证数据
   */
  clearAuthData(): void {
    this.deleteCookie(this.TOKEN_KEY)
    this.deleteCookie(this.REFRESH_TOKEN_KEY)
    this.deleteCookie(this.USER_KEY)
  }
}

// 导出单例实例
export const authService = new AuthService()
export default authService 