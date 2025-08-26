<template>
  <div class="task-list">
    <div class="page-header">
      <h1>任务管理</h1>
      <p>管理和监控数据采集任务</p>
    </div>

    <div class="toolbar">
      <div class="search-box">
        <el-input
          v-model="searchQuery"
          placeholder="搜索任务..."
          :prefix-icon="Search"
          clearable
          @input="handleSearch"
        />
      </div>
      <div class="filters">
        <el-select
          v-model="statusFilter"
          placeholder="状态筛选"
          clearable
          @change="loadTasks"
        >
          <el-option label="等待中" value="PENDING" />
          <el-option label="运行中" value="RUNNING" />
          <el-option label="已完成" value="COMPLETED" />
          <el-option label="失败" value="FAILED" />
          <el-option label="已停止" value="STOPPED" />
        </el-select>
        <el-select
          v-model="typeFilter"
          placeholder="类型筛选"
          clearable
          @change="loadTasks"
        >
          <el-option label="用户推文" value="USER_TWEETS" />
          <el-option label="搜索推文" value="SEARCH" />
          <el-option label="话题推文" value="TOPIC" />
          <el-option label="粉丝列表" value="FOLLOWERS" />
          <el-option label="关注列表" value="FOLLOWING" />
          <el-option label="用户信息" value="USER_INFO" />
        </el-select>
      </div>
      <div class="actions">
        <el-button type="primary" :icon="Plus" @click="createTask">
          创建任务
        </el-button>
        <el-button :icon="Refresh" @click="loadTasks">
          刷新
        </el-button>
      </div>
    </div>

    <div class="content-card">
      <el-table
        v-loading="loading"
        :data="tasks"
        stripe
        style="width: 100%"
      >
        <el-table-column prop="task_name" label="任务名称" width="200" />
        <el-table-column prop="task_type" label="任务类型" width="120">
          <template #default="{ row }">
            <el-tag :type="getTypeTagType(row.task_type)">
              {{ getTypeText(row.task_type) }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="status" label="状态" width="100">
          <template #default="{ row }">
            <el-tag :type="getStatusTagType(row.status)">
              {{ getStatusText(row.status) }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="describe" label="描述" min-width="150">
          <template #default="{ row }">
            {{ row.describe || '-' }}
          </template>
        </el-table-column>
        <el-table-column prop="created_at" label="创建时间" width="180">
          <template #default="{ row }">
            {{ formatDate(row.created_at) }}
          </template>
        </el-table-column>
        <el-table-column prop="updated_at" label="更新时间" width="180">
          <template #default="{ row }">
            {{ formatDate(row.updated_at) }}
          </template>
        </el-table-column>
        <el-table-column label="操作" width="250" fixed="right">
          <template #default="{ row }">
            <el-button size="small" @click="viewTask(row)">
              查看
            </el-button>
            <el-button
              v-if="row.status === 'RUNNING'"
              size="small"
              type="warning"
              @click="stopTask(row)"
            >
              停止
            </el-button>
            <el-button
              v-else-if="['PENDING', 'FAILED', 'STOPPED'].includes(row.status)"
              size="small"
              type="primary"
              @click="startTask(row)"
            >
              启动
            </el-button>
            <el-button size="small" type="danger" @click="deleteTask(row)">
              删除
            </el-button>
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
import { ref, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Search, Plus, Refresh } from '@element-plus/icons-vue'
import * as taskApi from '../../api/tasks'
import type { Task, TaskType, TaskStatus } from '../../types/task'

const router = useRouter()
const loading = ref(false)
const searchQuery = ref('')
const statusFilter = ref('')
const typeFilter = ref('')
const currentPage = ref(1)
const pageSize = ref(20)
const total = ref(0)

const tasks = ref<Task[]>([])

const loadTasks = async () => {
  loading.value = true
  try {
    const response = await taskApi.getTasks({
      page: currentPage.value,
      size: pageSize.value,
      status: statusFilter.value || undefined,
      task_type: (typeFilter.value as TaskType) || undefined
    })

    tasks.value = response.items
    total.value = response.total
  } catch (error) {
    console.error('加载任务列表失败:', error)
    ElMessage.error('加载任务列表失败')
  } finally {
    loading.value = false
  }
}

const handleSearch = () => {
  // 简单的前端搜索，实际项目中应该在后端实现
  if (!searchQuery.value) {
    loadTasks()
    return
  }
  
  const filtered = tasks.value.filter(task =>
    task.task_name.toLowerCase().includes(searchQuery.value.toLowerCase()) ||
    task.task_type.toLowerCase().includes(searchQuery.value.toLowerCase()) ||
    (task.describe && task.describe.toLowerCase().includes(searchQuery.value.toLowerCase()))
  )
  
  tasks.value = filtered
}

const createTask = () => {
  router.push('/tasks/create')
}

const viewTask = (task: Task) => {
  router.push(`/tasks/${task.id}`)
}

const startTask = async (task: Task) => {
  try {
    await taskApi.startTask(task.id)
    ElMessage.success(`任务 "${task.task_name}" 启动成功`)
    loadTasks() // 重新加载列表
  } catch (error) {
    console.error('启动任务失败:', error)
    ElMessage.error('启动任务失败')
  }
}

const stopTask = async (task: Task) => {
  try {
    await taskApi.stopTask(task.id)
    ElMessage.success(`任务 "${task.task_name}" 停止成功`)
    loadTasks() // 重新加载列表
  } catch (error) {
    console.error('停止任务失败:', error)
    ElMessage.error('停止任务失败')
  }
}

const deleteTask = async (task: Task) => {
  try {
    await ElMessageBox.confirm(
      `确定要删除任务 "${task.task_name}" 吗？此操作将同时删除任务的所有结果数据。`,
      '确认删除',
      {
        confirmButtonText: '确定',
        cancelButtonText: '取消',
        type: 'warning'
      }
    )
    
    await taskApi.deleteTask(task.id)
    ElMessage.success('删除成功')
    loadTasks() // 重新加载列表
  } catch (error) {
    if (error !== 'cancel') {
      console.error('删除任务失败:', error)
      ElMessage.error('删除任务失败')
    }
  }
}

const handleSizeChange = (size: number) => {
  pageSize.value = size
  currentPage.value = 1 // 重置到第一页
  loadTasks()
}

const handleCurrentChange = (page: number) => {
  currentPage.value = page
  loadTasks()
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

const formatDate = (dateStr: string) => {
  if (!dateStr) return '-'
  return new Date(dateStr).toLocaleString('zh-CN')
}

onMounted(() => {
  loadTasks()
})
</script>

<style lang="scss" scoped>
.task-list {
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
      width: 300px;
    }
    
    .filters {
      display: flex;
      gap: 12px;
      
      .el-select {
        width: 120px;
      }
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
}

:deep(.el-table) {
  .el-button {
    margin-right: 8px;
    
    &:last-child {
      margin-right: 0;
    }
  }
}
</style> 