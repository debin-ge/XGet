<template>
  <el-dialog
    v-model="dialogVisible"
    title="账户异常日志"
    width="70%"
    :before-close="handleClose"
  >
    <div class="error-log-container">
      <div class="header-info">
        <div class="account-info">
          <el-tag :type="getPlatformTagType(account?.method)" size="large">
            {{ getPlatformText(account?.method) }}
          </el-tag>
          <span class="username">{{ account?.username }}</span>
          <el-tag
            v-if="account?.errorMessage"
            type="danger"
            size="small"
          >
            当前错误
          </el-tag>
        </div>
        
        <div class="actions">
          <el-button
            type="primary"
            size="small"
            :icon="Refresh"
            @click="loadErrorLogs"
          >
            刷新
          </el-button>
          <el-button
            v-if="account?.status === 'error'"
            type="success"
            size="small"
            :loading="clearLoading"
            @click="handleClearError"
          >
            清除错误状态
          </el-button>
        </div>
      </div>

      <div class="current-error" v-if="account?.errorMessage">
        <h4>当前错误信息</h4>
        <el-alert
          :title="account.errorMessage"
          type="error"
          :closable="false"
          show-icon
        />
      </div>

      <div class="log-list">
        <h4>历史错误日志</h4>
        
        <div v-loading="loading" class="logs-container">
          <div v-if="errorLogs.length === 0 && !loading" class="empty-state">
            <el-empty description="暂无错误日志" />
          </div>
          
          <div
            v-for="(log, index) in errorLogs"
            :key="index"
            class="log-item"
          >
            <div class="log-header">
              <span class="timestamp">{{ formatTime(log.timestamp) }}</span>
              <el-tag type="danger" size="small">错误</el-tag>
            </div>
            
            <div class="log-content">
              <div class="message">{{ log.message }}</div>
              <div v-if="log.details" class="details">
                <el-collapse>
                  <el-collapse-item title="详细信息" name="details">
                    <pre class="error-details">{{ log.details }}</pre>
                  </el-collapse-item>
                </el-collapse>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>

    <template #footer>
      <div class="dialog-footer">
        <el-button @click="handleClose">关闭</el-button>
        <el-button type="primary" @click="exportLogs">导出日志</el-button>
      </div>
    </template>
  </el-dialog>
</template>

<script setup lang="ts">
import { ref, watch } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Refresh } from '@element-plus/icons-vue'
import accountService from '@/services/accountService'
import type { Account } from '@/types/account'

interface ErrorLog {
  timestamp: string
  message: string
  details?: string
}

interface Props {
  visible: boolean
  account: Account | null
}

interface Emits {
  (e: 'update:visible', value: boolean): void
  (e: 'error-cleared'): void
}

const props = defineProps<Props>()
const emit = defineEmits<Emits>()

const dialogVisible = ref(false)
const loading = ref(false)
const clearLoading = ref(false)
const errorLogs = ref<ErrorLog[]>([])

watch(
  () => props.visible,
  (newValue) => {
    dialogVisible.value = newValue
    if (newValue && props.account) {
      loadErrorLogs()
    }
  }
)

watch(dialogVisible, (newValue) => {
  if (!newValue) {
    emit('update:visible', false)
  }
})

const loadErrorLogs = async () => {
  if (!props.account) return
  
  loading.value = true
  try {
    errorLogs.value = await accountService.getAccountErrorLogs(props.account.id)
  } catch (error) {
    console.error('加载错误日志失败:', error)
  } finally {
    loading.value = false
  }
}

const handleClearError = async () => {
  if (!props.account) return
  
  try {
    await ElMessageBox.confirm(
      '确定要清除当前账户的错误状态吗？这将重置账户状态为活跃。',
      '确认操作',
      {
        confirmButtonText: '确定',
        cancelButtonText: '取消',
        type: 'warning'
      }
    )
    
    clearLoading.value = true
    await accountService.clearAccountError(props.account.id)
    emit('error-cleared')
    handleClose()
  } catch (error) {
    if (error !== 'cancel') {
      console.error('清除错误状态失败:', error)
    }
  } finally {
    clearLoading.value = false
  }
}

const exportLogs = () => {
  if (!props.account || errorLogs.value.length === 0) {
    ElMessage.warning('没有可导出的日志')
    return
  }
  
  const logContent = errorLogs.value.map(log => {
    let content = `时间: ${formatTime(log.timestamp)}\n错误: ${log.message}`
    if (log.details) {
      content += `\n详细信息:\n${log.details}`
    }
    return content
  }).join('\n\n' + '='.repeat(50) + '\n\n')
  
  const blob = new Blob([logContent], { type: 'text/plain;charset=utf-8' })
  const url = window.URL.createObjectURL(blob)
  const link = document.createElement('a')
  link.href = url
  link.download = `${props.account.username}_error_logs_${new Date().toISOString().split('T')[0]}.txt`
  document.body.appendChild(link)
  link.click()
  document.body.removeChild(link)
  window.URL.revokeObjectURL(url)
  
  ElMessage.success('日志导出成功')
}

const handleClose = () => {
  dialogVisible.value = false
}

const formatTime = (timeStr: string): string => {
  return accountService.formatTime(timeStr)
}

const getPlatformText = (platform?: string): string => {
  return accountService.getPlatformText(platform || '')
}

const getPlatformTagType = (platform?: string): string => {
  return accountService.getPlatformTagType(platform || '')
}
</script>

<style lang="scss" scoped>
.error-log-container {
  .header-info {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 20px;
    padding-bottom: 16px;
    border-bottom: 1px solid #ebeef5;
    
    .account-info {
      display: flex;
      align-items: center;
      gap: 12px;
      
      .username {
        font-weight: 500;
        color: #303133;
      }
    }
    
    .actions {
      display: flex;
      gap: 8px;
    }
  }
  
  .current-error {
    margin-bottom: 24px;
    
    h4 {
      margin: 0 0 12px 0;
      color: #303133;
      font-size: 16px;
    }
  }
  
  .log-list {
    h4 {
      margin: 0 0 16px 0;
      color: #303133;
      font-size: 16px;
    }
    
    .logs-container {
      max-height: 400px;
      overflow-y: auto;
      
      .empty-state {
        display: flex;
        justify-content: center;
        padding: 40px 0;
      }
      
      .log-item {
        margin-bottom: 16px;
        padding: 16px;
        background: #f8f9fa;
        border-radius: 8px;
        border-left: 4px solid #f56c6c;
        
        .log-header {
          display: flex;
          justify-content: space-between;
          align-items: center;
          margin-bottom: 8px;
          
          .timestamp {
            color: #909399;
            font-size: 14px;
          }
        }
        
        .log-content {
          .message {
            color: #303133;
            line-height: 1.5;
            margin-bottom: 8px;
          }
          
          .details {
            .error-details {
              background: #f5f5f5;
              padding: 12px;
              border-radius: 4px;
              font-size: 12px;
              line-height: 1.4;
              color: #666;
              white-space: pre-wrap;
              word-break: break-all;
              max-height: 200px;
              overflow-y: auto;
            }
          }
        }
      }
    }
  }
}

.dialog-footer {
  display: flex;
  justify-content: flex-end;
  gap: 12px;
}

@media (max-width: 768px) {
  .error-log-container {
    .header-info {
      flex-direction: column;
      align-items: stretch;
      gap: 12px;
      
      .account-info {
        justify-content: center;
      }
      
      .actions {
        justify-content: center;
      }
    }
  }
}
</style> 