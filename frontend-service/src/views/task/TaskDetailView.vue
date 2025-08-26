<template>
  <div class="task-detail" v-loading="loading">
    <div class="page-header">
      <div class="header-left">
        <h1>{{ task?.task_name || '任务详情' }}</h1>
        <p>任务ID: {{ taskId }}</p>
      </div>
      <div class="header-right">
        <el-button @click="goBack">返回</el-button>
        <el-button type="primary" @click="refreshData">刷新</el-button>
      </div>
    </div>

    <div class="task-info" v-if="task">
      <div class="info-cards">
        <div class="info-card">
          <div class="card-header">
            <span class="card-title">基本信息</span>
          </div>
          <div class="card-content">
            <div class="info-row">
              <span class="label">任务名称：</span>
              <span class="value">{{ task.task_name }}</span>
            </div>
            <div class="info-row">
              <span class="label">任务类型：</span>
              <el-tag :type="getTypeTagType(task.task_type)">
                {{ getTypeText(task.task_type) }}
              </el-tag>
            </div>
            <div class="info-row">
              <span class="label">任务状态：</span>
              <el-tag :type="getStatusTagType(task.status)">
                {{ getStatusText(task.status) }}
              </el-tag>
            </div>
            <div class="info-row">
              <span class="label">描述：</span>
              <span class="value">{{ task.describe || '无' }}</span>
            </div>
            <div class="info-row">
              <span class="label">创建时间：</span>
              <span class="value">{{ formatDate(task.created_at) }}</span>
            </div>
            <div class="info-row">
              <span class="label">更新时间：</span>
              <span class="value">{{ formatDate(task.updated_at) }}</span>
            </div>
          </div>
        </div>

        <div class="info-card">
          <div class="card-header">
            <span class="card-title">任务参数</span>
          </div>
          <div class="card-content">
            <pre class="config-content">{{ JSON.stringify(task.parameters, null, 2) }}</pre>
          </div>
        </div>

        <div class="info-card">
          <div class="card-header">
            <span class="card-title">任务操作</span>
          </div>
          <div class="card-content">
            <div class="action-buttons">
              <el-button
                v-if="task.status === 'RUNNING'"
                type="warning"
                @click="stopTask"
                :loading="actionLoading"
              >
                停止任务
              </el-button>
              <el-button
                v-else-if="['PENDING', 'FAILED', 'STOPPED'].includes(task.status)"
                type="primary"
                @click="startTask"
                :loading="actionLoading"
              >
                启动任务
              </el-button>
              <el-button
                type="danger"
                @click="deleteTask"
                :loading="actionLoading"
              >
                删除任务
              </el-button>
            </div>
          </div>
        </div>
      </div>

      <!-- 任务结果 -->
      <div class="results-section">
        <div class="section-header">
          <h3>任务结果</h3>
          <div class="header-actions">
            <el-button size="small" @click="loadResults">刷新结果</el-button>
            <el-button 
              size="small" 
              type="primary" 
              @click="exportResults"
              :disabled="!results.length"
            >
              导出结果
            </el-button>
          </div>
        </div>
        <div class="results-container">
          <div v-if="resultsLoading" class="loading-container">
            <el-skeleton :rows="5" animated />
          </div>
          <div v-else-if="results.length === 0" class="no-results">
            <el-empty description="暂无结果数据" />
          </div>
          <div v-else class="results-list">
            <div
              v-for="result in results"
              :key="result._id"
              class="result-item"
            >
              <div class="result-header">
                <span class="result-type">{{ result.data_type }}</span>
                <span class="result-time">{{ formatDate(result.created_at) }}</span>
              </div>
              <div class="result-content">
                <pre>{{ JSON.stringify(result.data, null, 2) }}</pre>
              </div>
            </div>
          </div>
          
          <!-- 分页 -->
          <div v-if="results.length > 0" class="pagination">
            <el-pagination
              :current-page="currentPage"
              :page-size="pageSize"
              :total="totalResults"
              layout="total, prev, pager, next"
              @current-change="handlePageChange"
            />
          </div>
        </div>
      </div>

      <!-- 错误信息 -->
      <div v-if="task.error_message" class="error-section">
        <div class="section-header">
          <h3>错误信息</h3>
        </div>
        <div class="error-container">
          <el-alert
            :title="task.error_message"
            type="error"
            :closable="false"
            show-icon
          />
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import * as taskApi from '../../api/tasks'
import type { Task, TaskType, TaskStatus, TaskResult } from '../../types/task'

const route = useRoute()
const router = useRouter()

const loading = ref(false)
const actionLoading = ref(false)
const resultsLoading = ref(false)
const task = ref<Task | null>(null)
const results = ref<TaskResult[]>([])
const currentPage = ref(1)
const pageSize = ref(10)
const totalResults = ref(0)

const taskId = route.params.id as string

const loadTask = async () => {
  loading.value = true
  try {
    task.value = await taskApi.getTaskById(taskId)
  } catch (error) {
    console.error('加载任务详情失败:', error)
    ElMessage.error('加载任务详情失败')
  } finally {
    loading.value = false
  }
}

const loadResults = async () => {
  resultsLoading.value = true
  try {
    const response = await taskApi.getTaskResults(taskId, {
      skip: (currentPage.value - 1) * pageSize.value,
      limit: pageSize.value
    })
    
    results.value = response.items
    totalResults.value = response.total
  } catch (error) {
    console.error('加载任务结果失败:', error)
    ElMessage.error('加载任务结果失败')
  } finally {
    resultsLoading.value = false
  }
}

const startTask = async () => {
  if (!task.value) return
  
  actionLoading.value = true
  try {
    await taskApi.startTask(task.value.id)
    ElMessage.success('任务启动成功')
    await loadTask() // 重新加载任务信息
  } catch (error) {
    console.error('启动任务失败:', error)
    ElMessage.error('启动任务失败')
  } finally {
    actionLoading.value = false
  }
}

const stopTask = async () => {
  if (!task.value) return
  
  actionLoading.value = true
  try {
    await taskApi.stopTask(task.value.id)
    ElMessage.success('任务停止成功')
    await loadTask() // 重新加载任务信息
  } catch (error) {
    console.error('停止任务失败:', error)
    ElMessage.error('停止任务失败')
  } finally {
    actionLoading.value = false
  }
}

const deleteTask = async () => {
  if (!task.value) return
  
  try {
    await ElMessageBox.confirm(
      `确定要删除任务 "${task.value.task_name}" 吗？此操作将同时删除任务的所有结果数据。`,
      '确认删除',
      {
        confirmButtonText: '确定',
        cancelButtonText: '取消',
        type: 'warning'
      }
    )
    
    actionLoading.value = true
    await taskApi.deleteTask(task.value.id)
    ElMessage.success('删除成功')
    router.push('/tasks')
  } catch (error) {
    if (error !== 'cancel') {
      console.error('删除任务失败:', error)
      ElMessage.error('删除任务失败')
    }
  } finally {
    actionLoading.value = false
  }
}

const exportResults = async () => {
  if (!task.value) return
  
  try {
    const blob = await taskApi.exportTaskResults(task.value.id, 'json')
    const url = window.URL.createObjectURL(blob)
    const link = document.createElement('a')
    link.href = url
    link.download = `task_${task.value.id}_results.json`
    link.click()
    window.URL.revokeObjectURL(url)
    ElMessage.success('导出成功')
  } catch (error) {
    console.error('导出失败:', error)
    ElMessage.error('导出失败')
  }
}

const handlePageChange = (page: number) => {
  currentPage.value = page
  loadResults()
}

const refreshData = () => {
  loadTask()
  loadResults()
}

const goBack = () => {
  router.back()
}

const getTypeTagType = (type: TaskType): 'primary' | 'success' | 'warning' | 'info' | 'danger' => {
  const typeMap: Record<TaskType, 'primary' | 'success' | 'warning' | 'info' | 'danger'> = {
    USER_TWEETS: 'primary',
    SEARCH: 'success',
    TOPIC: 'warning',
    FOLLOWERS: 'info',
    FOLLOWING: 'info',
    USER_INFO: 'primary'
  }
  return typeMap[type] || 'info'
}

const getTypeText = (type: TaskType) => {
  const textMap: Record<TaskType, string> = {
    USER_TWEETS: '用户推文',
    SEARCH: '搜索推文',
    TOPIC: '话题推文',
    FOLLOWERS: '粉丝列表',
    FOLLOWING: '关注列表',
    USER_INFO: '用户信息'
  }
  return textMap[type] || type
}

const getStatusTagType = (status: TaskStatus): 'primary' | 'success' | 'warning' | 'info' | 'danger' => {
  const typeMap: Record<TaskStatus, 'primary' | 'success' | 'warning' | 'info' | 'danger'> = {
    PENDING: 'info',
    RUNNING: 'warning',
    COMPLETED: 'success',
    FAILED: 'danger',
    STOPPED: 'info'
  }
  return typeMap[status] || 'info'
}

const getStatusText = (status: TaskStatus) => {
  const textMap: Record<TaskStatus, string> = {
    PENDING: '等待中',
    RUNNING: '运行中',
    COMPLETED: '已完成',
    FAILED: '失败',
    STOPPED: '已停止'
  }
  return textMap[status] || status
}

const formatDate = (dateStr?: string) => {
  if (!dateStr) return '-'
  return new Date(dateStr).toLocaleString('zh-CN')
}

onMounted(() => {
  loadTask()
  loadResults()
})
</script>

<style lang="scss" scoped>
.task-detail {
  .page-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 24px;
    
    .header-left {
      h1 {
        margin: 0 0 4px 0;
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
    
    .header-right {
      display: flex;
      gap: 12px;
    }
  }
  
  .task-info {
    .info-cards {
      display: grid;
      grid-template-columns: 1fr 1fr 1fr;
      gap: 16px;
      margin-bottom: 24px;
      
      @media (max-width: 1200px) {
        grid-template-columns: 1fr;
      }
    }
    
    .info-card {
      background: white;
      border-radius: 8px;
      box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
      
      .card-header {
        padding: 16px 20px 0;
        border-bottom: 1px solid #e4e7ed;
        
        .card-title {
          font-weight: 600;
          color: #303133;
        }
      }
      
      .card-content {
        padding: 20px;
        
        .info-row {
          display: flex;
          align-items: center;
          margin-bottom: 12px;
          
          &:last-child {
            margin-bottom: 0;
          }
          
          .label {
            color: #909399;
            margin-right: 8px;
            min-width: 80px;
          }
          
          .value {
            color: #303133;
          }
        }
        
        .config-content {
          background: #f5f7fa;
          padding: 12px;
          border-radius: 4px;
          font-size: 12px;
          color: #606266;
          white-space: pre-wrap;
          max-height: 200px;
          overflow-y: auto;
        }
        
        .action-buttons {
          display: flex;
          flex-direction: column;
          gap: 8px;
          
          .el-button {
            width: 100%;
          }
        }
      }
    }
    
    .results-section, .error-section {
      background: white;
      border-radius: 8px;
      box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
      margin-bottom: 24px;
      
      .section-header {
        display: flex;
        justify-content: space-between;
        align-items: center;
        padding: 20px 20px 0;
        border-bottom: 1px solid #e4e7ed;
        
        h3 {
          margin: 0;
          color: #303133;
          font-size: 16px;
          font-weight: 600;
        }
        
        .header-actions {
          display: flex;
          gap: 8px;
        }
      }
    }
    
    .results-container {
      padding: 20px;
      
      .loading-container {
        padding: 20px 0;
      }
      
      .no-results {
        padding: 40px 0;
      }
      
      .results-list {
        .result-item {
          border: 1px solid #e4e7ed;
          border-radius: 8px;
          margin-bottom: 16px;
          overflow: hidden;
          
          .result-header {
            background: #f5f7fa;
            padding: 12px 16px;
            display: flex;
            justify-content: space-between;
            align-items: center;
            border-bottom: 1px solid #e4e7ed;
            
            .result-type {
              font-weight: 600;
              color: #409EFF;
            }
            
            .result-time {
              color: #909399;
              font-size: 14px;
            }
          }
          
          .result-content {
            padding: 16px;
            
            pre {
              background: #f8f9fa;
              padding: 12px;
              border-radius: 4px;
              font-size: 12px;
              color: #606266;
              white-space: pre-wrap;
              max-height: 300px;
              overflow-y: auto;
              margin: 0;
            }
          }
        }
      }
      
      .pagination {
        margin-top: 20px;
        display: flex;
        justify-content: center;
      }
    }
    
    .error-container {
      padding: 20px;
    }
  }
}
</style> 