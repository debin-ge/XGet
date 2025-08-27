<template>
  <div class="proxy-quality">
    <div class="page-header">
      <h1>代理质量</h1>
      <p>监控代理性能指标，评估代理质量状况</p>
    </div>

    <div class="toolbar">
      <div class="search-box">
        <el-input
          v-model="searchQuery"
          placeholder="搜索代理地址..."
          :prefix-icon="Search"
          clearable
        />
      </div>
      <div class="actions">
        <el-select v-model="statusFilter" placeholder="状态筛选" style="width: 150px">
          <el-option label="全部" value="" />
          <el-option label="活跃" value="ACTIVE" />
          <el-option label="非活跃" value="INACTIVE" />
        </el-select>
        <el-select v-model="qualityFilter" placeholder="质量筛选" style="width: 150px">
          <el-option label="全部" value="" />
          <el-option label="优秀 (>=90)" value="0.9" />
          <el-option label="良好 (70-89)" value="0.7" />
          <el-option label="一般 (50-69)" value="0.5" />
          <el-option label="较差 (<50)" value="0" />
        </el-select>
        <el-button :icon="Refresh" @click="loadQualityData">
          刷新
        </el-button>
      </div>
    </div>

    <div class="content-card">
      <el-table
        v-loading="loading"
        :data="qualityData"
        stripe
        style="width: 100%"
        :default-sort="{ prop: 'quality_score', order: 'descending' }"
      >
        <el-table-column prop="proxy_address" label="代理地址" min-width="150">
          <template #default="{ row }">
            {{ row.ip }}:{{ row.port }}
          </template>
        </el-table-column>
        
        <el-table-column prop="success_rate" label="成功率" sortable>
          <template #default="{ row }">
            <div class="progress-cell">
              <el-progress
                :percentage="Math.round(row.success_rate * 100)"
                :color="getSuccessRateColor(Math.round(row.success_rate * 100))"
                :show-text="false"
                style="width: 60px"
              />
              <span class="percentage-text">{{ Math.round(row.success_rate * 100) }}%</span>
            </div>
          </template>
        </el-table-column>
        
        <el-table-column prop="total_usage" label="使用次数" sortable />
        
        <el-table-column prop="success_count" label="成功次数" sortable />
        
        <el-table-column prop="quality_score" label="质量分数" sortable>
          <template #default="{ row }">
            <div class="quality-score">
              <el-tag :type="getQualityTagType(Math.round(row.quality_score * 100))">
                {{ Math.round(row.quality_score * 100) }}
              </el-tag>
              <span class="score-label">{{ getQualityLabel(Math.round(row.quality_score * 100)) }}</span>
            </div>
          </template>
        </el-table-column>
        
        <el-table-column prop="latency" label="延迟时间" sortable>
          <template #default="{ row }">
            {{ row.latency || '-' }}ms
          </template>
        </el-table-column>
        
        <el-table-column prop="status" label="状态" sortable>
          <template #default="{ row }">
            <el-tag :type="row.status === 'ACTIVE' ? 'success' : 'danger'">
              {{ row.status === 'ACTIVE' ? '活跃' : '非活跃' }}
            </el-tag>
          </template>
        </el-table-column>
        
        <el-table-column prop="last_used" label="最近使用时间" min-width="180">
          <template #default="{ row }">
            {{ formatDate(row.last_used) }}
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
import { ref, reactive, computed, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import type { ProxyQuality } from '../../types/proxy'
import { getProxyQuality } from '../../api/proxies'
import { watchDebounced } from '@vueuse/core'
import { Search, Refresh } from '@element-plus/icons-vue'

const loading = ref(false)
const searchQuery = ref('')
const qualityFilter = ref('')
const statusFilter = ref('')
const currentPage = ref(1)
const pageSize = ref(20)
const total = ref(0)

const qualityData = ref<ProxyQuality[]>([])

// 使用 watchDebounced 监听搜索和状态过滤变化
watchDebounced(
  [searchQuery, qualityFilter, statusFilter],
  () => {
    currentPage.value = 1 // 重置到第一页
    loadQualityData()
  },
  { debounce: 500 }
)

const loadQualityData = async () => {
  loading.value = true
  try {
    const params = {
      page: currentPage.value,
      size: pageSize.value,
      ip: searchQuery.value || undefined,
      min_quality_score: qualityFilter.value || undefined,
      status: statusFilter.value || undefined
    }
    
    const response = await getProxyQuality(params)
    qualityData.value = response.items as unknown as ProxyQuality[]
    total.value = response.total
  } catch (error) {
    console.error('获取代理质量数据失败:', error)
    ElMessage.error('获取代理质量数据失败')
  } finally {
    loading.value = false
  }
}

const handleSizeChange = (size: number) => {
  pageSize.value = size
  loadQualityData()
}

const handleCurrentChange = (page: number) => {
  currentPage.value = page
  loadQualityData()
}

const getSuccessRateColor = (rate: number): string => {
  if (rate >= 90) return '#67c23a'
  if (rate >= 70) return '#e6a23c'
  if (rate >= 50) return '#f56c6c'
  return '#909399'
}



const getQualityTagType = (score: number): 'primary' | 'success' | 'warning' | 'danger' | 'info' | undefined => {
  if (score >= 90) return 'success'
  if (score >= 70) return 'primary'
  if (score >= 50) return 'warning'
  return 'danger'
}

const getQualityLabel = (score: number): string => {
  if (score >= 90) return '优秀'
  if (score >= 70) return '良好'
  if (score >= 50) return '一般'
  return '较差'
}

const formatDate = (dateStr?: string | null) => {
  return dateStr || '-'
}

onMounted(() => {
  loadQualityData()
})
</script>

<style lang="scss" scoped>
.proxy-quality {
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
    
    .search-box {
      width: 300px;
    }
    
    .actions {
      display: flex;
      gap: 12px;
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

  .progress-cell {
    display: flex;
    align-items: center;
    gap: 8px;

    .percentage-text {
      font-size: 12px;
      color: #606266;
    }
  }

  .quality-score {
    display: flex;
    align-items: center;
    gap: 8px;

    .score-label {
      font-size: 12px;
      color: #909399;
    }
  }

  .proxy-details {
    .el-descriptions {
      margin-top: 16px;
    }
  }
}

:deep(.el-table) {
  .el-progress {
    .el-progress-bar__outer {
      height: 6px;
    }
  }
}
</style> 