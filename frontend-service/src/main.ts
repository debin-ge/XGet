import { createApp } from 'vue'
import App from './App.vue'
import router from './router'
import pinia from './store'
import { setupRouterGuards } from './router/guards'

// ECharts 配置
import * as echarts from 'echarts/core'
import { BarChart } from 'echarts/charts'
import { GridComponent, TooltipComponent } from 'echarts/components'
import { CanvasRenderer } from 'echarts/renderers'
import VueECharts from 'vue-echarts'

// 注册 ECharts 组件
echarts.use([BarChart, GridComponent, TooltipComponent, CanvasRenderer])

// 样式文件
import 'element-plus/dist/index.css'
import './styles/global.scss'

const app = createApp(App)

// 安装插件
app.use(pinia)
app.use(router)

// 注册全局组件
app.component('VueECharts', VueECharts)

// 设置路由守卫
setupRouterGuards(router)

// 挂载应用
app.mount('#app') 