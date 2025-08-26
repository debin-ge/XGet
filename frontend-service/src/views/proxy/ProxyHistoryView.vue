<template>
  <div class="proxy-history">
    <div class="page-header">
      <h1>代理历史记录</h1>
      <p>查看代理使用历史和性能表现</p>
    </div>

    <div class="toolbar">
      <div class="search-box">
        <el-input
          v-model="accountEmailQuery"
          placeholder="搜索账户邮箱"
          :prefix-icon="Search"
          clearable
          style="width: 200px"
        />
        <el-input
          v-model="taskNameQuery"
          placeholder="搜索任务名称"
          :prefix-icon="Search"
          clearable
          style="width: 200px"
        />
      </div>
      <div class="filter-box">
        <el-select v-model="statusFilter" placeholder="状态筛选" style="width: 120px">
          <el-option label="全部" value="" />
          <el-option label="成功" value="SUCCESS" />
          <el-option label="失败" value="FAILED" />
          <el-option label="超时" value="TIMEOUT" />
        </el-select>
        <el-select v-model="serviceFilter" placeholder="服务筛选" style="width: 150px">
          <el-option label="全部服务" value="" />
          <el-option label="scraper-service" value="scraper-service" />
          <el-option label="account-service" value="account-service" />
          <el-option label="user-service" value="user-service" />
        </el-select>
        <el-date-picker
          v-model="dateRange"
          type="datetimerange"
          range-separator="至"
          start-placeholder="开始日期"
          end-placeholder="结束日期"
          format="YYYY-MM-DD HH:mm:ss"
          value-format="YYYY-MM-DD HH:mm:ss"
          style="width: 350px"
        />
      </div>
      <div class="actions">
        <el-button :icon="Refresh" @click="loadHistoryData">
          刷新
        </el-button>
        <el-button :icon="Download" @click="exportHistory">
          导出
        </el-button>
      </div>
    </div>

    <div class="content-card">
      <el-table
        v-loading="loading"
        :data="historyData"
        stripe
        style="width: 100%"
        :default-sort="{ prop: 'createdAt', order: 'descending' }"
      >
        <el-table-column prop="proxy_ip" label="代理IP"/>
        
        <el-table-column prop="account_username_email" label="账户/邮箱">
          <template #default="{ row }">
            {{ row.account_username_email}}
          </template>
        </el-table-column>
        
        <el-table-column prop="task_name" label="任务名称">
          <template #default="{ row }">
            {{ row.task_name}}
          </template>
        </el-table-column>
        
        <el-table-column prop="service_name" label="服务名称">
          <template #default="{ row }">
            <el-tag :type="getServiceTagType(row.service_name)">
              {{ row.service_name }}
            </el-tag>
          </template>
        </el-table-column>
        
        <el-table-column prop="success" label="状态">
          <template #default="{ row }">
            <el-tag :type="getSuccessTagType(row.success)">
              {{ getSuccessText(row.success) }}
            </el-tag>
          </template>
        </el-table-column>
        
        <el-table-column prop="response_time" label="响应时长" sortable>
          <template #default="{ row }">
            <span :class="getResponseTimeClass(row.response_time)">
              {{ row.response_time }}ms
            </span>
          </template>
        </el-table-column>
        
        <el-table-column prop="created_at" label="创建时间" sortable>
          <template #default="{ row }">
            <span>{{ formatDate(row.created_at) }}</span>
          </template>
        </el-table-column>
      </el-table>

      <div class="pagination">
        <el-pagination
          :current-page="currentPage"
          :page-size="pageSize"
          :page-sizes="[10, 20, 50, 100]"
          :total="total"
          layout="total, sizes, prev, pager, next, jumper"
          @size-change="handleSizeChange"
          @current-change="handleCurrentChange"
        />
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import { getProxyHistory } from '../../api/proxies'
import type { ProxyHistoryItem, ProxyHistoryListParams } from '../../types/proxy'
import { watchDebounced } from '@vueuse/core'

const loading = ref(false)
const accountEmailQuery = ref('')
const taskNameQuery = ref('')
const statusFilter = ref('')
const serviceFilter = ref('')
const dateRange = ref<[string, string] | null>(null)
const currentPage = ref(1)
const pageSize = ref(20)
const total = ref(0)

const historyData = ref<ProxyHistoryItem[]>([])

// 使用 watchDebounced 监听搜索和状态过滤变化
watchDebounced(
  [accountEmailQuery, taskNameQuery, statusFilter, serviceFilter, dateRange],
  () => {
    currentPage.value = 1 // 重置到第一页
    loadHistoryData()
  },
  { debounce: 500 }
)

const loadHistoryData = async () => {
  loading.value = true
  try {
    const params: ProxyHistoryListParams = {
      page: currentPage.value,
      size: pageSize.value
    }

    if (accountEmailQuery.value) {
      params.account_email = accountEmailQuery.value
    }
    
    if (taskNameQuery.value) {
      params.task_name = taskNameQuery.value
    }
    
    if (statusFilter.value) {
      params.success = statusFilter.value as 'SUCCESS' | 'FAILED' | 'TIMEOUT'
    }
    
    if (serviceFilter.value) {
      params.service_name = serviceFilter.value as 'scraper-service' | 'account-service' | 'user-service' | 'proxy-service'
    }
    
    if (dateRange.value && dateRange.value.length === 2) {
      params.start_date = new Date(dateRange.value[0]).toISOString()
      params.end_date = new Date(dateRange.value[1]).toISOString()
    }
    
    const response = await getProxyHistory(params)
    console.log(response)
    historyData.value = response.items
    total.value = response.total
  } catch (error) {
    console.error('加载代理历史记录失败:', error)
    ElMessage.error('加载代理历史记录失败')
  } finally {
    loading.value = false
  }
}

const getSuccessTagType = (success: 'SUCCESS' | 'FAILED' | 'TIMEOUT'): 'primary' | 'success' | 'warning' | 'info' | 'danger' | undefined => {
  switch (success) {
    case 'SUCCESS':
      return 'success'
    case 'FAILED':
      return 'danger'
    case 'TIMEOUT':
      return 'warning'
    default:
      return 'info'
  }
}

const getSuccessText = (success: 'SUCCESS' | 'FAILED' | 'TIMEOUT'): string => {
  switch (success) {
    case 'SUCCESS':
      return '成功'
    case 'FAILED':
      return '失败'
    case 'TIMEOUT':
      return '超时'
    default:
      return '未知'
  }
}

const exportHistory = () => {
  ElMessage.info('导出功能开发中...')
}

const handleSizeChange = (size: number) => {
  pageSize.value = size
  currentPage.value = 1
  loadHistoryData()
}

const handleCurrentChange = (page: number) => {
  currentPage.value = page
  loadHistoryData()
}

const getServiceTagType = (serviceName: string): 'primary' | 'success' | 'warning' | 'info' | 'danger' | undefined => {
  const serviceMap: Record<string, 'primary' | 'success' | 'warning' | 'info' | 'danger'> = {
    'scraper-service': 'primary',
    'account-service': 'success',
    'user-service': 'info',
    'proxy-service': 'warning'
  }
  return serviceMap[serviceName]
}

const getResponseTimeClass = (responseTime: number): string => {
  if (responseTime <= 200) return 'fast-response'
  if (responseTime <= 500) return 'normal-response'
  if (responseTime <= 1000) return 'slow-response'
  return 'very-slow-response'
}

const formatDate = (dateStr: string) => {
  return dateStr ? new Date(dateStr).toLocaleString() : '-'
}

onMounted(() => {
  loadHistoryData()
})
</script>

<style lang="scss" scoped>
.proxy-history {
  .page-header {
    margin-bottom: 24px;
    
    h1 {
      margin: 0 0 8px 0;
      color: #303133;
      font-size: 24px;
      font-weight: 600;
    }
    
    p {
      margin: 0;
      color: #909399;
      font-size: 14px;
    }
  }
  
  .toolbar {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 16px;
    gap: 16px;
    
    .search-box {
      flex-shrink: 0;
    }
    
    .filter-box {
      display: flex;
      gap: 12px;
      flex: 1;
      justify-content: center;
    }
    
    .actions {
      display: flex;
      gap: 12px;
      flex-shrink: 0;
    }
  }
  
  .content-card {
    background: white;
    border-radius: 8px;
    padding: 24px;
    box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
    
    .pagination {
      margin-top: 16px;
      display: flex;
      justify-content: center;
    }
  }

  .error-message {
    color: #f56c6c;
    font-size: 12px;
    max-width: 200px;
    overflow: hidden;
    text-overflow: ellipsis;
    white-space: nowrap;
  }

  .success-text {
    color: #909399;
  }

  .fast-response {
    color: #67c23a;
    font-weight: 500;
  }

  .normal-response {
    color: #409eff;
  }

  .slow-response {
    color: #e6a23c;
  }

  .very-slow-response {
    color: #f56c6c;
    font-weight: 500;
  }

  .history-details {
    .error-message-detail {
      color: #f56c6c;
      background: #fef0f0;
      padding: 8px 12px;
      border-radius: 4px;
      font-size: 13px;
      line-height: 1.4;
    }
  }

  .task-details {
    .task-id-display {
      margin: 16px 0;
      padding: 12px;
      background: #f5f7fa;
      border-radius: 4px;
      font-size: 14px;
    }
  }
}

:deep(.el-table) {
  .el-button {
    margin-right: 0;
  }
}
</style> 