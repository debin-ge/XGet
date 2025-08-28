<template>
  <div class="account-management">
    <div class="page-header">
      <h1>账户管理</h1>
      <p>管理用于数据采集的社交媒体账户</p>
    </div>

    <div class="toolbar">
      <div class="search-and-filter">
        <el-input
          v-model="searchQuery"
          placeholder="搜索用户名、邮箱..."
          :prefix-icon="Search"
          clearable
          class="search-input"
        />
        <el-select
          v-model="filterMethod"
          placeholder="平台"
          clearable
          style="width: 120px"
        >
          <el-option label="Google" value="google" />
          <el-option label="Twitter" value="twitter" />
        </el-select>
        <el-select
          v-model="filterStatus"
          placeholder="状态"
          clearable
          style="width: 120px"
        >
          <el-option label="活跃" value="active" />
          <el-option label="非活跃" value="inactive" />
        </el-select>
      </div>
      <div class="actions">
        <el-button type="primary" :icon="Plus" @click="goToAddAccount">
          添加账户
        </el-button>
        <el-button :icon="Refresh" @click="loadAccounts">
          刷新
        </el-button>
      </div>
    </div>

    <div class="content-card">
      <el-table
        v-loading="loading"
        :data="accounts"
        stripe
        style="width: 100%"
        @selection-change="handleSelectionChange"
      >
        <el-table-column type="selection" width="55" />
        
        <el-table-column prop="login_method" label="平台" width="100">
          <template #default="{ row }">
            <el-tag>
              {{ getPlatformText(row.login_method) }}
            </el-tag>
          </template>
        </el-table-column>
        
        <el-table-column prop="username" label="用户名" min-width="150" />
        
        <el-table-column prop="email" label="邮箱" min-width="200" />
        
        <el-table-column prop="active" label="状态" width="100">
          <template #default="{ row }">
            <el-tag :type="row.active ? 'success' : 'warning'">
              {{ row.active ? '活跃' : '非活跃' }}
            </el-tag>
          </template>
        </el-table-column>
        
        <el-table-column prop="proxy_id" label="代理" width="150">
          <template #default="{ row }">
            <span v-if="row.proxy_id">
              {{ row.proxy_id }}
            </span>
            <el-tag v-else type="info" size="small">未使用</el-tag>
          </template>
        </el-table-column>
        
        <el-table-column prop="last_used" label="最后使用" width="180">
          <template #default="{ row }">
            {{ formatTime(row.last_used) }}
          </template>
        </el-table-column>
        
        <el-table-column prop="error_msg" label="异常" width="120">
          <template #default="{ row }">
            <el-button
              v-if="row.error_msg"
              type="danger"
              size="small"
              text
              @click="showErrorDialog(row)"
            >
              查看异常
            </el-button>
            <span v-else>-</span>
          </template>
        </el-table-column>
        
        <el-table-column label="操作" width="300" fixed="right">
          <template #default="{ row }">
            <el-button
              size="small"
              :loading="row.loginLoading"
              @click="handleLogin(row)"
            >
              登录
            </el-button>
            <el-button
              size="small"
              type="primary"
              @click="goToEditAccount(row.id)"
            >
              编辑
            </el-button>
            <el-button
              size="small"
              type="danger"
              @click="handleDelete(row)"
            >
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

    <!-- 异常消息对话框 -->
    <el-dialog
      v-model="errorDialogVisible"
      title="查看异常信息"
      width="500px"
    >
      <div v-if="selectedErrorAccount">
        <p><strong>账户:</strong> {{ selectedErrorAccount.username }}</p>
        <p><strong>错误信息:</strong></p>
        <pre>{{ selectedErrorAccount.error_msg }}</pre>
      </div>
      <template #footer>
        <el-button @click="errorDialogVisible = false">关闭</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { watchDebounced } from '@vueuse/core'
import { ElMessage, ElMessageBox } from 'element-plus'
import { accountService } from '../../services/accountService'
import * as accountApi from '../../api/accounts'
import type { Account, AccountListParams } from '../../types/account'
import { Search, Plus, Refresh } from '@element-plus/icons-vue'

const router = useRouter()

const loading = ref(false)
const searchQuery = ref('')
const filterMethod = ref('')
const filterStatus = ref('')
const currentPage = ref(1)
const pageSize = ref(20)
const total = ref(0)
const selectedAccounts = ref<Account[]>([])
const errorDialogVisible = ref(false)
const selectedErrorAccount = ref<Account | null>(null)

const accounts = ref<Account[]>([])

// 使用 watchDebounced 监听搜索和过滤变化
watchDebounced(
  [searchQuery, filterMethod, filterStatus],
  () => {
    currentPage.value = 1 // 重置到第一页
    loadAccounts()
  },
  { debounce: 500 }
)

const loadAccounts = async () => {
  loading.value = true
  try {
    const params: AccountListParams = {
      page: currentPage.value,
      size: pageSize.value,
    }
    
    // 添加搜索
    if (searchQuery.value) {
      params.search = searchQuery.value
    }
    
    // 添加平台过滤
    if (filterMethod.value) {
      params.login_method = filterMethod.value
    }
    
    // 添加状态过滤
    if (filterStatus.value) {
      params.active = filterStatus.value === 'active' ? true : filterStatus.value === 'inactive' ? false : undefined
    }

    const data = await accountApi.getAccounts(params)
    accounts.value = data.items as Account[]
    total.value = data.total
  } catch (error) {
    console.error('加载账户列表失败:', error)
    ElMessage.error('加载账户列表失败')
  } finally {
    loading.value = false
  }
}

const goToAddAccount = () => {
  router.push('/accounts/new')
}

const goToEditAccount = (id: string) => {
  router.push(`/accounts/${id}`)
}

const handleLogin = async (account: Account) => {
  account.loginLoading = true
  try {
    const success = await accountService.loginAccount(account.id, account.username || account.email, account.proxy_id)
    if (success) {
      await loadAccounts()
    }
  } catch (error) {
    console.error('账户登录失败:', error)
  } finally {
    account.loginLoading = false
  }
}

const handleDelete = async (account: Account) => {
  try {
    const success = await accountService.deleteAccount(account.id, account.username)
    if (success) {
      await loadAccounts()
    }
  } catch (error) {
    console.error('删除账户失败:', error)
  }
}

const showErrorDialog = (account: Account) => {
  selectedErrorAccount.value = account
  errorDialogVisible.value = true
}


const handleSelectionChange = (selection: Account[]) => {
  selectedAccounts.value = selection
}



const handleSizeChange = (size: number) => {
  pageSize.value = size
  currentPage.value = 1
  loadAccounts()
}

const handleCurrentChange = (page: number) => {
  currentPage.value = page
  loadAccounts()
}

const getPlatformText = (platform: string): string => {
  const platformMap: Record<string, string> = {
    GOOGLE: 'Google',
    TWITTER: 'Twitter'
  }
  return platformMap[platform] || platform
}

const formatTime = (timeStr?: string): string => {
  if (!timeStr) return '-'
  try {
    return new Date(timeStr).toLocaleString('zh-CN', {
      year: 'numeric',
      month: '2-digit',
      day: '2-digit',
      hour: '2-digit',
      minute: '2-digit'
    })
  } catch {
    return timeStr
  }
}

onMounted(() => {
  loadAccounts()
})
</script>

<style lang="scss" scoped>
.account-management {
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
    
    .search-and-filter {
      display: flex;
      gap: 12px;
      align-items: center;
      
      .search-input {
        width: 300px;
      }
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
}

:deep(.el-table) {
  .el-button {
    margin-right: 8px;
    
    &:last-child {
      margin-right: 0;
    }
  }
}

@media (max-width: 1200px) {
  .account-management {
    .toolbar {
      flex-direction: column;
      align-items: stretch;
      gap: 16px;
      
      .search-and-filter {
        justify-content: flex-start;
        flex-wrap: wrap;
        
        .search-input {
          width: 250px;
        }
      }
      
      .actions {
        justify-content: flex-end;
        flex-wrap: wrap;
      }
    }
  }
}

@media (max-width: 768px) {
  .account-management {
    .toolbar {
      .search-and-filter {
        .search-input {
          width: 100%;
        }
      }
      
      .actions {
        justify-content: stretch;
        
        .el-button {
          flex: 1;
        }
      }
    }
    
    .content-card {
      padding: 16px;
      overflow-x: auto;
    }
  }
}
</style> 