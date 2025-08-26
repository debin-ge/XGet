<template>
  <div class="proxy-management">
    <div class="page-header">
      <h1>代理列表</h1>
      <p>管理代理IP池，确保数据采集的稳定性</p>
    </div>

    <div class="toolbar">
      <div class="search-box">
        <el-input
          v-model="searchQuery"
          placeholder="搜索代理..."
          :prefix-icon="Search"
          clearable
        />
      </div>
      <div class="filters">
        <el-select
          v-model="statusFilter"
          placeholder="状态过滤"
          clearable
          style="width: 120px"
        >
          <el-option label="全部" value="" />
          <el-option label="活跃" value="ACTIVE" />
          <el-option label="未活跃" value="INACTIVE" />
        </el-select>
      </div>
      <div class="actions">
        <el-button type="primary" :icon="Plus" @click="showCreateDialog">
          添加代理
        </el-button>
        <el-button :icon="Refresh" @click="loadProxies">
          刷新
        </el-button>
      </div>
    </div>

    <div class="content-card">
      <el-table
        v-loading="loading"
        :data="filteredProxies"
        stripe
        style="width: 100%"
      >
        <el-table-column prop="ip" label="IP地址" min-width="150" />
        <el-table-column prop="port" label="端口" min-width="80" />
        <el-table-column prop="type" label="类型" min-width="100">
          <template #default="{ row }">
            <el-tag :type="getTypeTagType(row.type)">
              {{ row.type.toUpperCase() }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="status" label="状态" min-width="100">
          <template #default="{ row }">
            <el-tag :type="getStatusTagType(row.status)">
              {{ getStatusText(row.status) }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="country" label="国家" >
          <template #default="{ row }">
            {{ row.country || '-' }}
          </template>
        </el-table-column>
        <el-table-column prop="city" label="城市" >
          <template #default="{ row }">
            {{ row.city || '-' }}
          </template>
        </el-table-column>
        <el-table-column prop="isp" label="ISP">
          <template #default="{ row }">
            {{ row.isp || '-' }}
          </template>
        </el-table-column>
        <el-table-column prop="latency" label="网络延迟" min-width="100">
          <template #default="{ row }">
            {{ row.latency ? row.latency + 'ms' : '-' }}
          </template>
        </el-table-column>
        <el-table-column prop="success_rate" label="成功率" min-width="100">
          <template #default="{ row }">
            {{ row.success_rate ? (row.success_rate * 100).toFixed(1) + '%' : '-' }}
          </template>
        </el-table-column>
        <el-table-column prop="created_at" label="创建时间" min-width="180">
          <template #default="{ row }">
            {{ formatDate(row.created_at) }}
          </template>
        </el-table-column>
        <el-table-column label="操作" min-width="200" fixed="right">
          <template #default="{ row }">
            <el-button size="small" @click="checkProxy(row)">
              检测
            </el-button>
            <el-button size="small" type="primary" @click="editProxy(row)">
              编辑
            </el-button>
            <el-button size="small" type="danger" @click="deleteProxy(row)">
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

    <!-- 创建/编辑对话框 -->
    <el-dialog
      v-model="dialogVisible"
      :title="dialogTitle"
      width="500px"
      @close="resetForm"
    >
      <el-form
        ref="formRef"
        :model="form"
        :rules="rules"
        label-width="80px"
      >
        <el-form-item label="IP地址" prop="ip">
          <el-input v-model="form.ip" placeholder="输入IP地址" />
        </el-form-item>
        
        <el-form-item label="端口" prop="port">
          <el-input-number
            v-model="form.port"
            :min="1"
            :max="65535"
            placeholder="输入端口号"
            style="width: 100%"
          />
        </el-form-item>
        
        <el-form-item label="类型" prop="type">
          <el-select v-model="form.type" placeholder="选择代理类型">
            <el-option label="HTTP" value="HTTP" />
            <el-option label="HTTPS" value="HTTPS" />
            <el-option label="SOCKS4" value="SOCKS4" />
            <el-option label="SOCKS5" value="SOCKS5" />
          </el-select>
        </el-form-item>
        
        <el-form-item label="用户名" prop="username">
          <el-input v-model="form.username" placeholder="输入用户名（可选）" />
        </el-form-item>
        
        <el-form-item label="密码" prop="password">
          <el-input
            v-model="form.password"
            type="password"
            placeholder="输入密码（可选）"
            show-password
          />
        </el-form-item>
      </el-form>
      
      <template #footer>
        <el-button @click="dialogVisible = false">取消</el-button>
        <el-button type="primary" :loading="submitLoading" @click="submitForm">
          确定
        </el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, computed, onMounted } from 'vue'
import { watchDebounced } from '@vueuse/core'
import { ElMessage, ElMessageBox } from 'element-plus'
import type { FormInstance } from 'element-plus'
import { Search, Plus, Refresh } from '@element-plus/icons-vue'
import { proxyService } from '../../services/proxyService'
import * as proxyApi from '../../api/proxies'
import type { Proxy, ProxyCreateParams, ProxyUpdateParams } from '../../types/proxy'
import type { ProxyListParams } from '../../api/proxies'

const formRef = ref<FormInstance>()
const loading = ref(false)
const submitLoading = ref(false)
const dialogVisible = ref(false)
const searchQuery = ref('')
const currentPage = ref(1)
const pageSize = ref(20)
const total = ref(0)
const statusFilter = ref<'ACTIVE' | 'INACTIVE' | ''>('')

const proxies = ref<Proxy[]>([])
const editingProxy = ref<Proxy | null>(null)

const form = reactive({
  ip: '',
  port: 8080,
  type: 'HTTP' as 'HTTP' | 'HTTPS' | 'SOCKS4' | 'SOCKS5',
  username: '',
  password: '',
  country: '',
  city: '',
  isp: ''
})

const rules = {
  ip: [{ required: true, message: '请输入IP地址', trigger: 'blur' }],
  port: [{ required: true, message: '请输入端口号', trigger: 'blur' }],
  type: [{ required: true, message: '请选择代理类型', trigger: 'change' }]
}

const dialogTitle = computed(() => {
  return editingProxy.value ? '编辑代理' : '添加代理'
})

const filteredProxies = computed(() => {
  return proxies.value // 现在服务端已经处理了过滤，直接返回
})

const loadProxies = async () => {
  try {
    loading.value = true
    
    const params: ProxyListParams = {
      page: currentPage.value,
      size: pageSize.value,
    }
    
    // 添加状态过滤
    if (statusFilter.value) {
      params.status = statusFilter.value
    }
    
    // 添加搜索
    if (searchQuery.value) {
      params.ip = searchQuery.value
    }
    
    const data = await proxyApi.getProxies(params)
    proxies.value = data.items as unknown as Proxy[]
    total.value = data.total
  } catch (error) {
    console.error('加载代理列表失败:', error)
    ElMessage.error('加载代理列表失败')
  } finally {
    loading.value = false
  }
}

// 使用 watchDebounced 监听搜索和状态过滤变化
watchDebounced(
  [searchQuery, statusFilter],
  () => {
    currentPage.value = 1 // 重置到第一页
    loadProxies()
  },
  { debounce: 500 }
)

const showCreateDialog = () => {
  editingProxy.value = null
  resetForm()
  dialogVisible.value = true
}

const editProxy = (proxy: Proxy) => {
  editingProxy.value = proxy
  form.ip = proxy.ip
  form.port = proxy.port
  form.type = proxy.type
  form.username = proxy.username || ''
  form.password = proxy.password || ''
  form.country = proxy.country || ''
  form.city = proxy.city || ''
  form.isp = proxy.isp || ''
  dialogVisible.value = true
}

const deleteProxy = async (proxy: Proxy) => {
  try {
    const success = await proxyService.deleteProxy(proxy.id, `${proxy.ip}:${proxy.port}`)
    if (success) {
      await loadProxies() // 重新加载数据
    }
  } catch (error) {
    console.error('删除代理失败:', error)
  }
}

const checkProxy = async (proxy: Proxy) => {
  try {
    const success = await proxyService.checkProxy(proxy.id)
    if (success) {
      await loadProxies() // 重新加载数据以获取更新的状态
    }
  } catch (error) {
    console.error('测试代理失败:', error)
  }
}

const submitForm = async () => {
  if (!formRef.value) return
  
  try {
    const valid = await formRef.value.validate()
    if (!valid) return

    submitLoading.value = true
    
    const formData: ProxyCreateParams | ProxyUpdateParams = {
      ip: form.ip,
      port: form.port,
      type: form.type,
      username: form.username || undefined,
      password: form.password || undefined,
      country: form.country || undefined,
      city: form.city || undefined,
      isp: form.isp || undefined
    }
    
    if (editingProxy.value) {
      // 编辑模式
      await proxyService.updateProxy(editingProxy.value.id, formData as ProxyUpdateParams)
    } else {
      // 创建模式
      await proxyService.createProxy(formData as ProxyCreateParams)
    }
    
    dialogVisible.value = false
    resetForm()
    await loadProxies() // 重新加载数据
  } catch (error) {
    console.error('表单提交失败:', error)
  } finally {
    submitLoading.value = false
  }
}

const resetForm = () => {
  if (formRef.value) {
    formRef.value.resetFields()
  }
  form.ip = ''
  form.port = 8080
  form.type = 'HTTP'
  form.username = ''
  form.password = ''
  form.country = ''
  form.city = ''
  form.isp = ''
}

const handleSizeChange = (size: number) => {
  pageSize.value = size
  currentPage.value = 1 // 重置到第一页
  loadProxies()
}

const handleCurrentChange = (page: number) => {
  currentPage.value = page
  loadProxies()
}

const getTypeTagType = (type: string): 'primary' | 'success' | 'warning' | 'info' | 'danger' | undefined => {
  const typeMap: Record<string, 'primary' | 'success' | 'warning' | 'info' | 'danger'> = {
    HTTP: 'primary',
    HTTPS: 'success',
    SOCKS4: 'warning',
    SOCKS5: 'info'
  }
  return typeMap[type]
}

const getStatusTagType = (status: string): 'primary' | 'success' | 'warning' | 'info' | 'danger' | undefined => {
  const typeMap: Record<string, 'primary' | 'success' | 'warning' | 'info' | 'danger'> = {
    ACTIVE: 'success',
    INACTIVE: 'warning'
  }
  return typeMap[status]
}

const getStatusText = (status: string) => {
  const textMap: Record<string, string> = {
    ACTIVE: '活跃',
    INACTIVE: '未活跃'
  }
  return textMap[status] || status
}

const formatDate = (dateStr: string) => {
  if (!dateStr) return '-'
  return new Date(dateStr).toLocaleString('zh-CN')
}

onMounted(() => {
  loadProxies()
})
</script>

<style lang="scss" scoped>
.proxy-management {
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
    
    .filters {
      margin-right: 12px;
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