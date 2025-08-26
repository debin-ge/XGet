import { defineStore } from 'pinia'
import { ref } from 'vue'

interface Breadcrumb {
  name: string
  path?: string
}

export const useAppStore = defineStore('app', () => {
  // 状态
  const sidebarCollapsed = ref(false)
  const pageLoading = ref(false)
  const breadcrumbs = ref<Breadcrumb[]>([])
  
  const config = {
    title: 'XGet Platform'
  }

  // 动作
  const toggleSidebar = () => {
    sidebarCollapsed.value = !sidebarCollapsed.value
  }

  const setPageLoading = (loading: boolean) => {
    pageLoading.value = loading
  }

  const setBreadcrumbs = (newBreadcrumbs: Breadcrumb[]) => {
    breadcrumbs.value = newBreadcrumbs
  }

  return {
    // 状态
    sidebarCollapsed,
    pageLoading,
    breadcrumbs,
    config,
    // 动作
    toggleSidebar,
    setPageLoading,
    setBreadcrumbs,
  }
}) 