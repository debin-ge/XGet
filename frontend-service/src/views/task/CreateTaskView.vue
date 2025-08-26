<template>
  <div class="create-task">
    <div class="page-header">
      <h1>创建任务</h1>
      <p>配置新的数据采集任务</p>
    </div>

    <div class="content-card">
      <el-form
        ref="formRef"
        :model="form"
        :rules="rules"
        label-width="120px"
        style="max-width: 800px"
      >
        <el-form-item label="任务名称" prop="task_name">
          <el-input
            v-model="form.task_name"
            placeholder="输入任务名称"
            maxlength="50"
            show-word-limit
          />
        </el-form-item>

        <el-form-item label="任务类型" prop="task_type">
          <el-select
            v-model="form.task_type"
            placeholder="选择任务类型"
            @change="handleTypeChange"
          >
            <el-option label="用户推文" value="USER_TWEETS" />
            <el-option label="搜索推文" value="SEARCH" />
            <el-option label="话题推文" value="TOPIC" />
            <el-option label="粉丝列表" value="FOLLOWERS" />
            <el-option label="关注列表" value="FOLLOWING" />
            <el-option label="用户信息" value="USER_INFO" />
          </el-select>
        </el-form-item>

        <el-form-item label="描述" prop="describe">
          <el-input
            v-model="form.describe"
            type="textarea"
            placeholder="输入任务描述"
            :rows="3"
            maxlength="200"
            show-word-limit
          />
        </el-form-item>

        <!-- 账户选择（必选） -->
        <el-form-item label="选择账户" prop="account_id">
          <el-select
            v-model="form.account_id"
            placeholder="选择用于执行任务的账户"
            filterable
            :loading="accountsLoading"
          >
            <el-option
              v-for="account in accounts"
              :key="account.id"
              :label="`${account.username ? account.username : account.email} (${account.login_method})`"
              :value="account.id"
            >
              <div class="account-option">
                <span>{{ account.username ? account.username : account.email}}({{account.login_method}})</span>
                <el-tag size="small" :type="account.active ? 'success' : 'danger'">
                  {{ account.active ? '活跃' : '非活跃' }}
                </el-tag>
              </div>
            </el-option>
          </el-select>
          <div class="form-tip">选择一个活跃的账户来执行此任务</div>
        </el-form-item>

        <!-- 代理选择（可选） -->
        <el-form-item label="选择代理" prop="proxy_id">
          <el-select
            v-model="form.proxy_id"
            placeholder="选择代理（可选）"
            filterable
            clearable
            :loading="proxiesLoading"
          >
            <el-option
              v-for="proxy in proxies"
              :key="proxy.id"
              :label="`${proxy.ip}:${proxy.port} (${proxy.country || 'Unknown'})`"
              :value="proxy.id"
            >
              <div class="proxy-option">
                <span>{{ proxy.ip }}:{{ proxy.port }}</span>
                <el-tag size="small" type="info">{{ proxy.type }}</el-tag>
                <el-tag size="small" :type="proxy.status === 'ACTIVE' ? 'success' : 'warning'">
                  {{ proxy.status }}
                </el-tag>
              </div>
            </el-option>
          </el-select>
          <div class="form-tip">可选择代理来执行任务，留空则使用默认配置</div>
        </el-form-item>

        <!-- 用户推文配置 -->
        <template v-if="form.task_type === 'USER_TWEETS'">
          <el-form-item label="用户名" prop="parameters.uid">
            <el-input
              v-model="form.parameters.uid"
              placeholder="输入Twitter用户名或用户ID"
            />
            <div class="form-tip">输入要采集推文的用户名（如：elonmusk）或用户ID</div>
          </el-form-item>
          
          <el-form-item label="采集数量" prop="parameters.limit">
            <el-input-number
              v-model="form.parameters.limit"
              :min="1"
              :max="1000"
              placeholder="采集推文数量"
            />
            <div class="form-tip">最多采集的推文数量（默认10条）</div>
          </el-form-item>

          <el-form-item label="包含回复">
            <el-switch v-model="form.parameters.include_replies" />
            <div class="form-tip">是否包含用户的回复推文</div>
          </el-form-item>

          <el-form-item label="包含转发">
            <el-switch v-model="form.parameters.include_retweets" />
            <div class="form-tip">是否包含用户的转发推文</div>
          </el-form-item>
        </template>

        <!-- 搜索推文配置 -->
        <template v-if="form.task_type === 'SEARCH'">
          <el-form-item label="搜索关键词" prop="parameters.query">
            <el-input
              v-model="form.parameters.query"
              placeholder="输入搜索关键词"
            />
            <div class="form-tip">支持Twitter搜索语法，如：#hashtag、from:username等</div>
          </el-form-item>
          
          <el-form-item label="采集数量" prop="parameters.limit">
            <el-input-number
              v-model="form.parameters.limit"
              :min="1"
              :max="1000"
              placeholder="最大结果数量"
            />
            <div class="form-tip">最多采集的推文数量（默认10条）</div>
          </el-form-item>
        </template>

        <!-- 话题推文配置 -->
        <template v-if="form.task_type === 'TOPIC'">
          <el-form-item label="话题标签" prop="parameters.topic">
            <el-input
              v-model="form.parameters.topic"
              placeholder="输入话题标签（不需要#号）"
            />
            <div class="form-tip">话题标签，如：AI、blockchain等，系统会自动添加#号</div>
          </el-form-item>
          
          <el-form-item label="采集数量" prop="parameters.limit">
            <el-input-number
              v-model="form.parameters.limit"
              :min="1"
              :max="1000"
              placeholder="最大结果数量"
            />
            <div class="form-tip">最多采集的推文数量（默认10条）</div>
          </el-form-item>
        </template>

        <!-- 粉丝列表配置 -->
        <template v-if="form.task_type === 'FOLLOWERS'">
          <el-form-item label="目标用户" prop="parameters.uid">
            <el-input
              v-model="form.parameters.uid"
              placeholder="输入用户名或用户ID"
            />
            <div class="form-tip">要获取粉丝列表的目标用户</div>
          </el-form-item>
          
          <el-form-item label="采集数量" prop="parameters.limit">
            <el-input-number
              v-model="form.parameters.limit"
              :min="1"
              :max="1000"
              placeholder="采集粉丝数量"
            />
            <div class="form-tip">最多采集的粉丝数量（默认10条）</div>
          </el-form-item>
        </template>

        <!-- 关注列表配置 -->
        <template v-if="form.task_type === 'FOLLOWING'">
          <el-form-item label="目标用户" prop="parameters.uid">
            <el-input
              v-model="form.parameters.uid"
              placeholder="输入用户名或用户ID"
            />
            <div class="form-tip">要获取关注列表的目标用户</div>
          </el-form-item>
          
          <el-form-item label="采集数量" prop="parameters.limit">
            <el-input-number
              v-model="form.parameters.limit"
              :min="1"
              :max="1000"
              placeholder="采集关注数量"
            />
            <div class="form-tip">最多采集的关注数量（默认10条）</div>
          </el-form-item>
        </template>

        <!-- 用户信息配置 -->
        <template v-if="form.task_type === 'USER_INFO'">
          <el-form-item label="用户名" prop="parameters.username">
            <el-input
              v-model="form.parameters.username"
              placeholder="输入Twitter用户名"
            />
            <div class="form-tip">输入要获取信息的Twitter用户名（如：elonmusk）</div>
          </el-form-item>
        </template>

        <el-form-item>
          <el-button type="primary" :loading="loading" @click="submitForm">
            创建任务
          </el-button>
          <el-button @click="resetForm">重置</el-button>
          <el-button @click="goBack">返回</el-button>
        </el-form-item>
      </el-form>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import type { FormInstance } from 'element-plus'
import * as taskApi from '../../api/tasks'
import * as accountApi from '../../api/accounts'
import * as proxyApi from '../../api/proxies'
import type { TaskCreateParams, TaskType, Account, Proxy } from '../../types/task'

const router = useRouter()
const formRef = ref<FormInstance>()
const loading = ref(false)
const accountsLoading = ref(false)
const proxiesLoading = ref(false)
const accounts = ref<Account[]>([])
const proxies = ref<Proxy[]>([])

const form = reactive<TaskCreateParams>({
  task_name: '',
  task_type: '' as TaskType,
  describe: '',
  account_id: '',
  proxy_id: '',
  parameters: {
    // 用户推文
    uid: '',
    limit: 10,
    include_replies: false,
    include_retweets: false,
    // 搜索推文
    query: '',
    // 话题推文
    topic: '',
    // 用户信息
    username: ''
  }
})

const rules = {
  task_name: [
    { required: true, message: '请输入任务名称', trigger: 'blur' },
    { min: 2, max: 50, message: '长度在 2 到 50 个字符', trigger: 'blur' }
  ],
  task_type: [
    { required: true, message: '请选择任务类型', trigger: 'change' }
  ],
  account_id: [
    { required: true, message: '请选择执行任务的账户', trigger: 'change' }
  ],
  'parameters.uid': [
    { required: true, message: '请输入目标用户', trigger: 'blur' }
  ],
  'parameters.query': [
    { required: true, message: '请输入搜索关键词', trigger: 'blur' }
  ],
  'parameters.topic': [
    { required: true, message: '请输入话题标签', trigger: 'blur' }
  ],
  'parameters.username': [
    { required: true, message: '请输入用户名', trigger: 'blur' }
  ]
}

// 加载账户列表
const loadAccounts = async () => {
  accountsLoading.value = true
  try {
    accounts.value = await accountApi.getActiveAccounts()
  } catch (error) {
    console.error('加载账户列表失败:', error)
    ElMessage.error('加载账户列表失败')
  } finally {
    accountsLoading.value = false
  }
}

// 加载代理列表
const loadProxies = async () => {
  proxiesLoading.value = true
  try {
    proxies.value = await proxyApi.getAvailableProxies()
  } catch (error) {
    console.error('加载代理列表失败:', error)
    ElMessage.error('加载代理列表失败')
  } finally {
    proxiesLoading.value = false
  }
}

const handleTypeChange = () => {
  // 重置参数配置
  form.parameters = {
    uid: '',
    limit: 10,
    include_replies: false,
    include_retweets: false,
    query: '',
    topic: '',
    username: ''
  }
}

const submitForm = async () => {
  if (!formRef.value) return
  
  try {
    const valid = await formRef.value.validate()
    if (!valid) return

    loading.value = true
    
    // 清理不需要的参数
    const cleanParameters: any = { limit: form.parameters.limit }
    
    switch (form.task_type) {
      case 'USER_TWEETS':
        cleanParameters.uid = form.parameters.uid
        cleanParameters.include_replies = form.parameters.include_replies
        cleanParameters.include_retweets = form.parameters.include_retweets
        break
      case 'SEARCH':
        cleanParameters.query = form.parameters.query
        break
      case 'TOPIC':
        cleanParameters.topic = form.parameters.topic
        break
      case 'FOLLOWERS':
      case 'FOLLOWING':
        cleanParameters.uid = form.parameters.uid
        break
      case 'USER_INFO':
        cleanParameters.username = form.parameters.username
        // 用户信息不需要limit参数
        delete cleanParameters.limit
        break
    }

    const taskData: TaskCreateParams = {
      task_name: form.task_name,
      task_type: form.task_type,
      describe: form.describe,
      account_id: form.account_id,
      proxy_id: form.proxy_id || undefined,
      parameters: cleanParameters
    }

    await taskApi.createTask(taskData)
    ElMessage.success('任务创建成功')
    router.push('/tasks')
  } catch (error) {
    console.error('创建任务失败:', error)
    ElMessage.error('创建任务失败')
  } finally {
    loading.value = false
  }
}

const resetForm = () => {
  if (formRef.value) {
    formRef.value.resetFields()
  }
}

const goBack = () => {
  router.back()
}

onMounted(() => {
  loadAccounts()
  loadProxies()
})
</script>

<style lang="scss" scoped>
.create-task {
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
  
  .content-card {
    background: white;
    border-radius: 8px;
    padding: 24px;
    box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
  }
  
  .form-tip {
    color: #909399;
    font-size: 12px;
    margin-top: 4px;
  }
  
  .account-option, .proxy-option {
    display: flex;
    align-items: center;
    justify-content: space-between;
    width: 100%;
    
    .el-tag {
      margin-left: 8px;
    }
  }
}

:deep(.el-form-item__content) {
  flex-direction: column;
  align-items: flex-start;
}

:deep(.el-select) {
  width: 100%;
}
</style> 