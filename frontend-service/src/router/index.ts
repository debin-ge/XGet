import { createRouter, createWebHistory } from 'vue-router'
import type { RouteRecordRaw } from 'vue-router'

const routes: RouteRecordRaw[] = [
  {
    path: '/login',
    name: 'Login',
    component: () => import('@/views/auth/LoginView.vue'),
    meta: {
      title: '登录',
      requiresAuth: false,
    },
  },
  {
    path: '/register',
    name: 'Register',
    component: () => import('@/views/auth/RegisterView.vue'),
    meta: {
      title: '注册',
      requiresAuth: false,
    },
  },
  {
    path: '/',
    redirect: '/dashboard',
    component: () => import('@/layouts/MainLayout.vue'),
    meta: {
      requiresAuth: true,
    },
    children: [
      {
        path: '/dashboard',
        name: 'Dashboard',
        component: () => import('@/views/dashboard/DashboardView.vue'),
        meta: {
          title: '仪表盘',
          icon: 'Dashboard',
        },
      },
      {
        path: '/accounts',
        name: 'AccountManagement',
        component: () => import('@/views/account/AccountManagementView.vue'),
        meta: {
          title: '账户管理',
          icon: 'User',
        },
      },
      {
        path: '/accounts/new',
        name: 'CreateAccount',
        component: () => import('@/views/account/AccountFormView.vue'),
        meta: {
          title: '添加账户',
          hidden: true,
        },
      },
      {
        path: '/accounts/:id',
        name: 'EditAccount',
        component: () => import('@/views/account/AccountFormView.vue'),
        meta: {
          title: '编辑账户',
          hidden: true,
        },
      },
      {
        path: '/proxies',
        name: 'ProxyManagement',
        component: () => import('@/views/proxy/ProxyManagementView.vue'),
        meta: {
          title: '代理列表',
          icon: 'Connection',
          parent: '代理管理',
        },
      },
      {
        path: '/proxies/quality',
        name: 'ProxyQuality',
        component: () => import('@/views/proxy/ProxyQualityView.vue'),
        meta: {
          title: '代理质量',
          parent: '代理管理',
        },
      },
      {
        path: '/proxies/history',
        name: 'ProxyHistory',
        component: () => import('@/views/proxy/ProxyHistoryView.vue'),
        meta: {
          title: '历史记录',
          parent: '代理管理',
        },
      },
      {
        path: '/tasks',
        name: 'TaskList',
        component: () => import('@/views/task/TaskListView.vue'),
        meta: {
          title: '任务列表',
          icon: 'List',
        },
      },
      {
        path: '/tasks/create',
        name: 'CreateTask',
        component: () => import('@/views/task/CreateTaskView.vue'),
        meta: {
          title: '创建任务',
          icon: 'Plus',
          hidden: true,
        },
      },
      {
        path: '/tasks/:id',
        name: 'TaskDetail',
        component: () => import('@/views/task/TaskDetailView.vue'),
        meta: {
          title: '任务详情',
          hidden: true,
        },
      },
    ],
  },
  {
    path: '/:pathMatch(.*)*',
    name: 'NotFound',
    component: () => import('@/views/error/NotFoundView.vue'),
    meta: {
      title: '页面未找到',
    },
  },
]

const router = createRouter({
  history: createWebHistory(),
  routes,
  scrollBehavior(to, from, savedPosition) {
    if (savedPosition) {
      return savedPosition
    } else {
      return { top: 0 }
    }
  },
})

export default router 