<template>
  <div class="dashboard-container">
    <div class="dashboard-header">
      <h1>仪表盘</h1>
      <p>欢迎使用XGet数据采集平台</p>
    </div>
    
    <!-- 统计卡片 -->
    <el-row :gutter="20" class="stats-row">
      <el-col :xs="24" :sm="12" :md="6">
        <el-card class="stat-card">
          <div class="stat-content">
            <div class="stat-icon tasks">
              <el-icon><Document /></el-icon>
            </div>
            <div class="stat-info">
              <h3>{{ stats.tasks.total }}</h3>
              <p>总任务数</p>
            </div>
          </div>
        </el-card>
      </el-col>
      
      <el-col :xs="24" :sm="12" :md="6">
        <el-card class="stat-card">
          <div class="stat-content">
            <div class="stat-icon accounts">
              <el-icon><User /></el-icon>
            </div>
            <div class="stat-info">
              <h3>{{ stats.accounts.total }}</h3>
              <p>总账户数</p>
            </div>
          </div>
        </el-card>
      </el-col>
      
      <el-col :xs="24" :sm="12" :md="6">
        <el-card class="stat-card">
          <div class="stat-content">
            <div class="stat-icon proxies">
              <el-icon><Connection /></el-icon>
            </div>
            <div class="stat-info">
              <h3>{{ stats.proxies.total }}</h3>
              <p>总代理数</p>
            </div>
          </div>
        </el-card>
      </el-col>
      
      <el-col :xs="24" :sm="12" :md="6">
        <el-card class="stat-card">
          <div class="stat-content">
            <div class="stat-icon results">
              <el-icon><DataLine /></el-icon>
            </div>
            <div class="stat-info">
              <h3>{{ formatNumber(stats.results.totalCount) }}</h3>
              <p>总结果数</p>
            </div>
          </div>
        </el-card>
      </el-col>
    </el-row>
    
    <!-- 图表和活动 -->
    <el-row :gutter="20" class="charts-row">
      <el-col :xs="24" :md="16">
        <el-card>
          <template #header>
            <span>任务趋势</span>
          </template>
          <div class="chart-container">
            <VueECharts 
              :option="chartOptions" 
              :autoresize="true"
              style="height: 300px; width: 100%;"
              v-if="taskTrends.length > 0"
            />
            <div class="chart-placeholder" v-else>
              <el-icon><TrendCharts /></el-icon>
              <p>加载任务趋势数据...</p>
            </div>
          </div>
        </el-card>
      </el-col>
      
      <el-col :xs="24" :md="8">
        <el-card>
          <template #header>
            <span>最近活动</span>
          </template>
          <div class="activities-list">
            <div v-for="activity in activities" :key="activity.id" class="activity-item">
              <div class="activity-icon">
                <el-icon><Clock /></el-icon>
              </div>
              <div class="activity-content">
                <p class="activity-title">{{ activity.title }}</p>
                <p class="activity-time">{{ formatTime(activity.timestamp) }}</p>
              </div>
            </div>
          </div>
        </el-card>
      </el-col>
    </el-row>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import dashboardService from '@/services/dashboardService'
import type { DashboardStats, Activity, TrendDataPoint } from '@/types/dashboard'

const stats = ref<DashboardStats>({
  tasks: { total: 0, running: 0, completed: 0, failed: 0, todayCount: 0 },
  accounts: { total: 0, active: 0, inactive: 0, suspended: 0 },
  proxies: { total: 0, active: 0, inactive: 0, averageSpeed: 0 },
  results: { totalCount: 0, todayCount: 0, weekCount: 0, monthCount: 0 },
})

const activities = ref<Activity[]>([])
const taskTrends = ref<TrendDataPoint[]>([])
const chartOptions = ref({})

const formatNumber = (num: number): string => {
  if (num >= 1000000) {
    return (num / 1000000).toFixed(1) + 'M'
  } else if (num >= 1000) {
    return (num / 1000).toFixed(1) + 'K'
  }
  return num.toString()
}

const formatTime = (timestamp: string): string => {
  return dashboardService.formatActivityTime(timestamp)
}

const updateChartOptions = (trends: TrendDataPoint[]) => {
  chartOptions.value = {
    tooltip: {
      trigger: 'axis',
      axisPointer: {
        type: 'shadow'
      }
    },
    grid: {
      left: '3%',
      right: '4%',
      bottom: '3%',
      containLabel: true
    },
    xAxis: {
      type: 'category',
      data: trends.map(item => item.label || item.date),
      axisLabel: {
        rotate: 45
      }
    },
    yAxis: {
      type: 'value',
      name: '任务数量'
    },
    series: [
      {
        name: '任务数量',
        type: 'bar',
        data: trends.map(item => item.value),
        itemStyle: {
          color: '#409EFF'
        }
      }
    ]
  }
}

const loadDashboardData = async () => {
  try {
    const [statsData, activitiesData, trendsData] = await Promise.all([
      dashboardService.getDashboardStats(),
      dashboardService.getRecentActivities(5),
      dashboardService.getTaskTrends(7),
    ])
    
    stats.value = statsData
    activities.value = activitiesData
    taskTrends.value = trendsData
    updateChartOptions(trendsData)
  } catch (error) {
    console.error('Failed to load dashboard data:', error)
  }
}

onMounted(() => {
  loadDashboardData()
})
</script>

<style lang="scss" scoped>
.dashboard-container {
  padding: 20px;
}

.dashboard-header {
  margin-bottom: 20px;
  
  h1 {
    font-size: 24px;
    color: #303133;
    margin-bottom: 8px;
  }
  
  p {
    color: #909399;
  }
}

.stats-row {
  margin-bottom: 20px;
}

.stat-card {
  .stat-content {
    display: flex;
    align-items: center;
    
    .stat-icon {
      width: 60px;
      height: 60px;
      border-radius: 50%;
      display: flex;
      align-items: center;
      justify-content: center;
      margin-right: 16px;
      
      .el-icon {
        font-size: 24px;
        color: white;
      }
      
      &.tasks {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
      }
      
      &.accounts {
        background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%);
      }
      
      &.proxies {
        background: linear-gradient(135deg, #4facfe 0%, #00f2fe 100%);
      }
      
      &.results {
        background: linear-gradient(135deg, #43e97b 0%, #38f9d7 100%);
      }
    }
    
    .stat-info {
      h3 {
        font-size: 24px;
        color: #303133;
        margin-bottom: 4px;
      }
      
      p {
        color: #909399;
        font-size: 14px;
      }
    }
  }
}

.charts-row {
  margin-bottom: 20px;
}

.chart-container {
  height: 300px;
  
  .chart-placeholder {
    height: 100%;
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
    color: #909399;
    
    .el-icon {
      font-size: 48px;
      margin-bottom: 16px;
    }
  }
}

.activities-list {
  height: 300px;
  overflow-y: auto;
  
  .activity-item {
    display: flex;
    padding: 12px 0;
    border-bottom: 1px solid #f0f0f0;
    
    &:last-child {
      border-bottom: none;
    }
    
    .activity-icon {
      width: 32px;
      height: 32px;
      background: #f5f7fa;
      border-radius: 50%;
      display: flex;
      align-items: center;
      justify-content: center;
      margin-right: 12px;
      
      .el-icon {
        font-size: 16px;
        color: #909399;
      }
    }
    
    .activity-content {
      flex: 1;
      
      .activity-title {
        color: #303133;
        font-size: 14px;
        margin-bottom: 4px;
      }
      
      .activity-time {
        color: #909399;
        font-size: 12px;
      }
    }
  }
}

.status-row {
  .status-item {
    margin-bottom: 16px;
    
    h4 {
      color: #303133;
      font-size: 14px;
      margin-bottom: 8px;
    }
  }
}
</style> 