<template>
  <div id="app">
    <router-view />
  </div>
</template>

<script setup lang="ts">
import { onMounted } from 'vue'
import { useAuthStore } from '@/store/auth'

const authStore = useAuthStore()
onMounted(() => {
  // 初始化认证状态
  authStore.initialize()
})
</script>

<style>
#app {
  width: 100%;
  height: 100vh;
  font-family: 'Helvetica Neue', Arial, sans-serif;
}
</style> 