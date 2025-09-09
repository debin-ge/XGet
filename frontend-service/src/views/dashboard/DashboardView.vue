<template>
  <div class="dashboard-container">
    <div class="dashboard-header">
      <h1>仪表盘</h1>
      <p>欢迎使用XGet数据采集平台</p>
      <el-button 
        v-if="error" 
        type="primary" 
        size="small" 
        :loading="loading"
        @click="loadDashboardData"
      >
        重新加载
      </el-button>
    </div>
    
    <!-- 错误提示 -->
    <el-alert
      v-if="error"
      :title="error"
      type="error"
      show-icon
      :closable="false"
      style="margin-bottom: 20px;"
    />
    
    <!-- 统计卡片 -->
    <el-row :gutter="20" class="stats-row">
      <el-col :xs="24" :sm="8" :md="8">
        <el-card class="stat-card task-card">
          <div class="stat-content">
            <div class="stat-icon tasks">
              <el-icon><Document /></el-icon>
            </div>
            <div class="stat-info">
              <h3>
                <template v-if="loading">--</template>
                <template v-else>{{ stats.tasks.total }}</template>
              </h3>
              <p>总任务数</p>
              <div class="stat-details" v-if="!loading">
                <span class="completed">{{ stats.tasks.completed }} 完成</span>
                <span class="failed">{{ stats.tasks.failed }} 失败</span>
              </div>
            </div>
          </div>
        </el-card>
      </el-col>
      
      <el-col :xs="24" :sm="8" :md="8">
        <el-card class="stat-card account-card">
          <div class="stat-content">
            <div class="stat-icon accounts">
              <el-icon><User /></el-icon>
            </div>
            <div class="stat-info">
              <h3>
                <template v-if="loading">--</template>
                <template v-else>{{ stats.accounts.total }}</template>
              </h3>
              <p>总账户数</p>
              <div class="stat-details" v-if="!loading && stats.accounts.total > 0">
                <span class="success-rate">
                  成功率: {{ Math.round(stats.accounts.loginSuccessRate) }}%
                </span>
              </div>
            </div>
          </div>
        </el-card>
      </el-col>
      
      <el-col :xs="24" :sm="8" :md="8">
        <el-card class="stat-card proxy-card">
          <div class="stat-content">
            <div class="stat-icon proxies">
              <el-icon><Connection /></el-icon>
            </div>
            <div class="stat-info">
              <h3>
                <template v-if="loading">--</template>
                <template v-else>{{ stats.proxies.total }}</template>
              </h3>
              <p>总代理数</p>
              <div class="stat-details" v-if="!loading">
                <span class="active">{{ stats.proxies.active }} 活跃</span>
                <span class="latency" v-if="stats.proxies.averageSpeed > 0">
                  平均: {{ Math.round(stats.proxies.averageSpeed) }}ms
                </span>
              </div>
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
              v-if="taskTrends.time_labels && taskTrends.time_labels.length > 0 && !loading"
            />
            <div class="chart-placeholder" v-else>
              <el-icon><TrendCharts /></el-icon>
              <p>{{ loading ? '正在加载数据...' : '暂无趋势数据' }}</p>
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
            <template v-if="loading">
              <div v-for="i in 5" :key="i" class="activity-item loading">
                <div class="activity-icon">
                  <el-icon><Clock /></el-icon>
                </div>
                <div class="activity-content">
                  <p class="activity-title loading-placeholder">加载中...</p>
                  <p class="activity-time loading-placeholder">--</p>
                </div>
              </div>
            </template>
            <template v-else>
              <div v-for="activity in activities" :key="activity.id" class="activity-item">
                <div 
                  class="activity-icon" 
                  :class="{ 
                    'status-success': activity.status === 'SUCCESS' || activity.status === 'COMPLETED',
                    'status-failed': activity.status === 'FAILED',
                    'status-other': !['SUCCESS', 'COMPLETED', 'FAILED'].includes(activity.status)
                  }"
                >
                  <el-icon><Clock /></el-icon>
                </div>
                <div class="activity-content">
                  <p class="activity-title">{{ activity.title }}</p>
                  <p class="activity-time">{{ formatTime(activity.timestamp) }}</p>
                </div>
              </div>
              <div v-if="activities.length === 0" class="no-activities">
                <p>暂无活动记录</p>
              </div>
            </template>
          </div>
        </el-card>
      </el-col>
    </el-row>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import dashboardService from '@/services/dashboardService'
import type { DashboardStats, Activity, TrendDataPoint } from '@/types/dashboard'
import { User, Document, Connection, TrendCharts, Clock } from '@element-plus/icons-vue'

const stats = ref<DashboardStats>({
  tasks: { total: 0, running: 0, completed: 0, failed: 0, todayCount: 0 },
  accounts: { total: 0, active: 0, inactive: 0, suspended: 0, loginSuccessRate: 0 },
  proxies: { total: 0, active: 0, inactive: 0, averageSpeed: 0, successRate: 0 },
})

const activities = ref<Activity[]>([])
const taskTrends = ref<any>({})
const chartOptions = ref({})
const loading = ref(true)
const error = ref<string | null>(null)

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

const updateChartOptions = (trendsData: any) => {
  const { time_labels, series_data } = trendsData
  
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
      data: time_labels,
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
        name: '已完成任务',
        type: 'bar',
        data: series_data.completed_tasks || [],
        stack: 'x',
        itemStyle: {
          color: '#10B981'
        }
      },
      {
        name: '失败任务',
        type: 'bar',
        data: series_data.failed_tasks || [],
        stack: 'x',
        itemStyle: {
          color: '#EF4444'
        }
      },
      {
        name: '进行中任务',
        type: 'bar',
        data: series_data.running_tasks || [],
        stack: 'x',
        itemStyle: {
          color: '#F59E0B'
        }
      },
      {
        name: '待处理任务',
        type: 'bar',
        data: series_data.pending_tasks || [],
        stack: 'x',
        itemStyle: {
          color: '#6B7280'
        }
      }
    ],
    legend: {
      data: ['已完成任务', '失败任务', '进行中任务', '待处理任务'],
    }
  }
}

const loadDashboardData = async () => {
  loading.value = true
  error.value = null
  
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
  } catch (err) {
    console.error('Failed to load dashboard data:', err)
    error.value = '无法加载仪表盘数据，请检查各服务连接是否正常'
    ElMessage.error('加载仪表盘数据失败')
  } finally {
    loading.value = false
  }
}

onMounted(() => {
  loadDashboardData()
})
</script>

<style lang="scss" scoped>
.dashboard-container {
  padding: 24px;
  background: #f8fafc;
}

.dashboard-header {
  margin-bottom: 32px;
  
  h1 {
    font-size: 28px;
    font-weight: 600;
    color: #1f2937;
    margin-bottom: 8px;
  }
  
  p {
    color: #6b7280;
    font-size: 16px;
    line-height: 1.5;
  }
}

.stats-row {
  margin-bottom: 32px;
}

.stat-card {
  border: none;
  border-radius: 12px;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1), 0 1px 2px rgba(0, 0, 0, 0.06);
  transition: all 0.2s ease;
  background: white;
  border-left: 4px solid transparent;
  
  &:hover {
    box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1), 0 1px 3px rgba(0, 0, 0, 0.08);
    transform: translateY(-1px);
  }
  
  &.task-card {
    border-left-color: #6366f1;
  }
  
  &.account-card {
    border-left-color: #ec4899;
  }
  
  &.proxy-card {
    border-left-color: #06b6d4;
  }
  
  .stat-content {
    display: flex;
    align-items: center;
    padding: 24px;
    
    .stat-icon {
      width: 56px;
      height: 56px;
      border-radius: 12px;
      display: flex;
      align-items: center;
      justify-content: center;
      margin-right: 16px;
      position: relative;
      
      .el-icon {
        font-size: 24px;
        color: white ;
      }
      
      &.tasks {
        background: linear-gradient(135deg, #6366f1 0%, #8b5cf6 100%);
      }
      
      &.accounts {
        background: linear-gradient(135deg, #ec4899 0%, #f43f5e 100%);
      }
      
      &.proxies {
        background: linear-gradient(135deg, #06b6d4 0%, #0ea5e9 100%);
      }
    }
    
    .stat-info {
      flex: 1;
      
      h3 {
        font-size: 28px;
        font-weight: 700;
        color: #111827;
        margin-bottom: 4px;
        line-height: 1;
      }
      
      p {
        color: #6b7280;
        font-size: 14px;
        font-weight: 500;
        margin-bottom: 12px;
      }
      
      .stat-details {
        display: flex;
        flex-wrap: wrap;
        gap: 8px;
        
        span {
          font-size: 12px;
          font-weight: 500;
          padding: 4px 8px;
          border-radius: 6px;
          display: inline-flex;
          align-items: center;
          
          &.completed {
            background: #f0fdf4;
            color: #16a34a;
            border: 1px solid #dcfce7;
          }
          
          &.failed {
            background: #fef2f2;
            color: #dc2626;
            border: 1px solid #fecaca;
          }
          
          &.success-rate {
            background: #eff6ff;
            color: #2563eb;
            border: 1px solid #dbeafe;
          }
          
          &.active {
            background: #f0fdf4;
            color: #16a34a;
            border: 1px solid #dcfce7;
          }
          
          &.latency {
            background: #f9fafb;
            color: #6b7280;
            border: 1px solid #e5e7eb;
          }
        }
      }
    }
  }
}

.charts-row {
  margin-bottom: 32px;
  
  .el-card {
    border: none;
    border-radius: 12px;
    box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1), 0 1px 2px rgba(0, 0, 0, 0.06);
    background: white;
    
    :deep(.el-card__header) {
      border-bottom: 1px solid #f3f4f6;
      padding: 20px 24px;
      
      span {
        font-size: 16px;
        font-weight: 600;
        color: #111827;
      }
    }
    
    :deep(.el-card__body) {
      padding: 20px 24px 24px;
    }
  }
}

.chart-container {
  height: 300px;
  
  .chart-placeholder {
    height: 100%;
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
    color: #9ca3af;
    
    .el-icon {
      font-size: 48px;
      margin-bottom: 12px;
      opacity: 0.5;
    }
    
    p {
      font-size: 14px;
      color: #9ca3af;
    }
  }
}

.activities-list {
  height: 300px;
  overflow-y: auto;
  
  .activity-item {
    display: flex;
    padding: 16px 0;
    border-bottom: 1px solid #f3f4f6;
    transition: all 0.2s ease;
    
    &:last-child {
      border-bottom: none;
    }
    
    &:hover {
      background: #f9fafb;
      border-radius: 8px;
      padding: 16px 12px;
      margin: 0 -12px;
    }
    
    &.loading {
      opacity: 0.6;
    }
  }
  
  .no-activities {
    text-align: center;
    padding: 48px 0;
    color: #9ca3af;
    
    p {
      font-size: 14px;
    }
  }
  
  .loading-placeholder {
    background: linear-gradient(90deg, #f9fafb 25%, #f3f4f6 50%, #f9fafb 75%);
    background-size: 200% 100%;
    animation: loading 1.5s infinite;
    border-radius: 6px;
    color: transparent !important;
    
    &.activity-title {
      width: 120px;
      height: 16px;
    }
    
    &.activity-time {
      width: 80px;
      height: 14px;
      margin-top: 6px;
    }
  }
  
  @keyframes loading {
    0% {
      background-position: 200% 0;
    }
    100% {
      background-position: -200% 0;
    }
  }
}

.activity-icon {
  width: 36px;
  height: 36px;
  background: #005cfb;
  border-radius: 8px;
  display: flex;
  align-items: center;
  justify-content: center;
  margin-right: 16px;
  flex-shrink: 0;
  
  &.status-success {
    background: #10b981;
  }
  
  &.status-failed {
    background: #ef4444;
  }
  
  &.status-other {
    background: #005cfb;
  }
  
  .el-icon {
    font-size: 16px;
    color: white;
  }
}
    
.activity-content {
  flex: 1;
  
  .activity-title {
    color: #111827;
    font-size: 14px;
    font-weight: 500;
    margin-bottom: 4px;
    line-height: 1.4;
  }
  
  .activity-time {
    color: #6b7280;
    font-size: 12px;
    font-weight: 400;
  }
}

</style> 