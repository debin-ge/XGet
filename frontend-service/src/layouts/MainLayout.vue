<template>
  <div class="main-layout">
    <el-container>
      <!-- 侧边栏 -->
      <el-aside :width="sidebarWidth">
        <div class="sidebar">
          <div class="logo">
            <h2>XGet Platform</h2>
          </div>
          
          <el-menu
            :default-active="$route.path"
            router
            :collapse="sidebarCollapsed"
            background-color="#304156"
            text-color="#bfcbd9"
            active-text-color="#409EFF"
          >
            <el-menu-item index="/dashboard">
              <el-icon><House /></el-icon>
              <span>仪表盘</span>
            </el-menu-item>
            
            <el-menu-item index="/accounts">
              <el-icon><User /></el-icon>
              <span>账户管理</span>
            </el-menu-item>
            
            <el-sub-menu index="/proxies">
              <template #title>
                <el-icon><Connection /></el-icon>
                <span>代理管理</span>
              </template>
              <el-menu-item index="/proxies">
                <span>代理列表</span>
              </el-menu-item>
              <el-menu-item index="/proxies/quality">
                <span>代理质量</span>
              </el-menu-item>
              <el-menu-item index="/proxies/history">
                <span>历史记录</span>
              </el-menu-item>
            </el-sub-menu>
            
            <el-menu-item index="/tasks">
              <el-icon><List /></el-icon>
              <span>任务管理</span>
            </el-menu-item>
          </el-menu>
        </div>
      </el-aside>
      
      <!-- 主内容区 -->
      <el-container>
        <!-- 顶部导航栏 -->
        <el-header class="header">
          <div class="header-left">
            <el-button
              :icon="sidebarCollapsed ? Expand : Fold"
              @click="toggleSidebar"
            />
            
            <!-- 面包屑导航 -->
            <el-breadcrumb separator="/">
              <el-breadcrumb-item
                v-for="breadcrumb in breadcrumbs"
                :key="breadcrumb.name"
                :to="breadcrumb.path"
              >
                {{ breadcrumb.name }}
              </el-breadcrumb-item>
            </el-breadcrumb>
          </div>
          
          <div class="header-right">
            <!-- 用户菜单 -->
            <el-dropdown @command="handleUserCommand">
              <span class="user-dropdown">
                <el-avatar :size="32" icon="User" />
                <span class="username">{{ userName }}</span>
                <el-icon><ArrowDown /></el-icon>
              </span>
              <template #dropdown>
                <el-dropdown-menu>
                  <el-dropdown-item command="profile">个人资料</el-dropdown-item>
                  <el-dropdown-item command="settings">设置</el-dropdown-item>
                  <el-dropdown-item divided command="logout">退出登录</el-dropdown-item>
                </el-dropdown-menu>
              </template>
            </el-dropdown>
          </div>
        </el-header>
        
        <!-- 主内容 -->
        <el-main class="main-content">
          <router-view v-slot="{ Component }">
            <transition name="fade-transform" mode="out-in">
              <component :is="Component" />
            </transition>
          </router-view>
        </el-main>
      </el-container>
    </el-container>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '@/store/auth'
import { useAppStore } from '@/store/app'
import {
  House,
  User,
  Connection,
  List,
  Fold,
  Expand,
  ArrowDown
} from '@element-plus/icons-vue'

const router = useRouter()
const authStore = useAuthStore()
const appStore = useAppStore()

const sidebarCollapsed = computed(() => appStore.sidebarCollapsed)
const sidebarWidth = computed(() => sidebarCollapsed.value ? '64px' : '200px')
const userName = computed(() => authStore.userName || '用户')
const breadcrumbs = computed(() => appStore.breadcrumbs)

const toggleSidebar = () => {
  appStore.toggleSidebar()
}

const handleUserCommand = async (command: string) => {
  switch (command) {
    case 'profile':
      // 跳转到个人资料页面
      break
    case 'settings':
      // 跳转到设置页面
      break
    case 'logout':
      try {
        await authStore.logout()
        router.push('/login')
      } catch (error) {
        console.error('退出登录失败:', error)
        // 即使API调用失败，也强制清理本地数据并跳转
        authStore.user = null
        authStore.token = null
        authStore.refreshToken = null
        router.push('/login')
      }
      break
  }
}
</script>

<style lang="scss" scoped>
.main-layout {
  height: 100vh;
  
  .el-container {
    height: 100%;
  }
  
  .sidebar {
    height: 100%;
    background-color: #304156;
    
    .logo {
      height: 60px;
      display: flex;
      align-items: center;
      justify-content: center;
      background-color: #2b3748;
      
      h2 {
        color: white;
        margin: 0;
        font-size: 18px;
        font-weight: 600;
      }
    }
    
    .el-menu {
      border-right: none;
    }
  }
  
  .header {
    height: 60px !important;
    background-color: white;
    border-bottom: 1px solid #e4e7ed;
    display: flex;
    align-items: center;
    justify-content: space-between;
    padding: 0 20px;
    
    .header-left {
      display: flex;
      align-items: center;
      gap: 16px;
    }
    
    .header-right {
      .user-dropdown {
        display: flex;
        align-items: center;
        gap: 8px;
        cursor: pointer;
        padding: 8px 12px;
        border-radius: 4px;
        transition: background-color 0.3s;
        
        &:hover {
          background-color: #f5f7fa;
        }
        
        .username {
          font-size: 14px;
          color: #303133;
        }
      }
    }
  }
  
  .main-content {
    background-color: #f0f2f5;
    overflow-y: auto;
  }
}

// 页面切换动画
.fade-transform-enter-active,
.fade-transform-leave-active {
  transition: all 0.3s;
}

.fade-transform-enter-from {
  opacity: 0;
  transform: translateX(30px);
}

.fade-transform-leave-to {
  opacity: 0;
  transform: translateX(-30px);
}

@media (max-width: 768px) {
  .main-layout {
    .header {
      padding: 0 16px;
      
      .header-left {
        gap: 12px;
      }
      
      .el-breadcrumb {
        display: none;
      }
    }
  }
}
</style> 