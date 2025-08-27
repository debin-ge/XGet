import type { Router } from 'vue-router'
import { useAuthStore } from '@/store/auth'
import { useAppStore } from '@/store/app'
import { ElMessage } from 'element-plus'

export function setupRouterGuards(router: Router) {
  // 全局前置守卫
  router.beforeEach(async (to, from, next) => {
    const authStore = useAuthStore()
    const appStore = useAppStore()
    
    // 设置页面加载状态
    appStore.setPageLoading(true)
    
    // 设置页面标题
    if (to.meta?.title) {
      document.title = `${to.meta.title} - ${appStore.config.title}`
    }
    
    // 检查是否需要认证
    const requiresAuth = to.meta?.requiresAuth !== false
    if (requiresAuth) {
      // 需要认证的页面
      if (!authStore.isAuthenticated) {
        // 未登录，重定向到登录页
        ElMessage.warning('请先登录')
        next({
          name: 'Login',
          query: { redirect: to.fullPath },
        })
        return
      }
      
      // 已登录但用户信息为空，尝试获取用户信息
      if (!authStore.user) {
        try {
          await authStore.getCurrentUser()
        } catch (error) {
          // 获取用户信息失败，可能token已过期
          ElMessage.error('登录状态已过期，请重新登录')
          await authStore.logout()
          next({
            name: 'Login',
            query: { redirect: to.fullPath },
          })
          return
        }
      }
    } else {
      // 不需要认证的页面
      if (authStore.isAuthenticated && (to.name === 'Login' || to.name === 'Register')) {
        // 已登录用户访问登录/注册页，重定向到首页
        next({ name: 'Dashboard' })
        return
      }
    }
    
    next()
  })
  
  // 全局后置钩子
  router.afterEach((to, from) => {
    const appStore = useAppStore()
    
    // 设置面包屑导航
    const breadcrumbs = generateBreadcrumbs(to)
    appStore.setBreadcrumbs(breadcrumbs)
    
    // 关闭页面加载状态
    appStore.setPageLoading(false)
  })
  
  // 路由错误处理
  router.onError((error) => {
    console.error('Router error:', error)
    ElMessage.error('页面加载失败')
  })
}

// 生成面包屑导航
function generateBreadcrumbs(route: any) {
  const breadcrumbs: Array<{ name: string; path?: string }> = []
  
  // 添加首页
  breadcrumbs.push({ name: '首页', path: '/dashboard' })
  
  // 根据路由添加面包屑
  const routeMap: Record<string, string> = {
    'Dashboard': '仪表盘',
    'AccountManagement': '账户管理',
    'ProxyManagement': '代理管理',
    'TaskList': '任务列表',
    'CreateTask': '创建任务',
    'TaskDetail': '任务详情',
  }
  
  if (route.name && route.name !== 'Dashboard') {
    const routeName = routeMap[route.name as string]
    if (routeName) {
      breadcrumbs.push({ name: routeName })
    }
  }
  
  return breadcrumbs
} 