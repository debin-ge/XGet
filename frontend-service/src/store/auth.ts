import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import type { User, UserRole } from '@/types/auth'
import authService from '@/services/authService'

export const useAuthStore = defineStore('auth', () => {
  // 状态
  const user = ref<User | null>(null)
  const token = ref<string | null>(null)
  const refreshToken = ref<string | null>(null)
  const isLoading = ref(false)

  // 计算属性
  const isAuthenticated = computed(() => !!token.value)
  const isAdmin = computed(() => user.value?.is_superuser || false)
  const userRole = computed((): UserRole => user.value?.is_superuser ? 'admin' : 'user')
  const userName = computed(() => user.value?.username || '')
  const userFullName = computed(() => {
    if (!user.value) return ''
    return `${user.value.first_name} ${user.value.last_name}`.trim()
  })

  // 动作
  const login = async (loginData: { username: string; password: string }) => {
    isLoading.value = true
    try {
      const response = await authService.login(loginData)
      
      // 保存用户信息和令牌
      user.value = response.user
      token.value = response.access_token
      refreshToken.value = response.refresh_token
      
      // 保存到本地存储
      authService.setTokens(response.access_token, response.refresh_token)
      authService.setUserInfo(response.user)
      
      return response.user
    } finally {
      isLoading.value = false
    }
  }

  const logout = async () => {
    isLoading.value = true
    try {
      await authService.logout()
    } finally {
      user.value = null
      token.value = null
      refreshToken.value = null
      isLoading.value = false
    }
  }

  const getCurrentUser = async () => {
    if (!authService.isAuthenticated()) {
      return null
    }

    isLoading.value = true
    try {
      const userData = await authService.getCurrentUser()
      if (userData) {
        user.value = userData
        token.value = authService.getAccessToken()
        refreshToken.value = authService.getRefreshToken()
      }
      return userData
    } finally {
      isLoading.value = false
    }
  }

  const refreshAuthToken = async () => {
    const success = await authService.refreshToken()
    if (success) {
      token.value = authService.getAccessToken()
      refreshToken.value = authService.getRefreshToken()
    }
    return success
  }

  const initialize = () => {
    if (authService.isAuthenticated()) {
      token.value = authService.getAccessToken()
      refreshToken.value = authService.getRefreshToken()
      user.value = authService.getUserInfo()
    }
  }

  return {
    // 状态
    user,
    token,
    refreshToken,
    isLoading,
    // 计算属性
    isAuthenticated,
    isAdmin,
    userRole,
    userName,
    userFullName,
    // 动作
    login,
    logout,
    getCurrentUser,
    refreshAuthToken,
    initialize,
  }
}) 