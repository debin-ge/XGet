<template>
  <div class="account-form">
    <div class="page-header">
      <div class="header-left">
        <el-button :icon="ArrowLeft" @click="goBack">返回</el-button>
        <div class="title-section">
          <h1>{{ isEdit ? '编辑账户' : '添加账户' }}</h1>
          <p>{{ isEdit ? '修改账户信息' : '创建新的数据采集账户' }}</p>
        </div>
      </div>
    </div>

    <div class="form-container">
      <el-card>
        <el-form
          ref="formRef"
          :model="form"
          :rules="rules"
          label-width="120px"
          size="large"
          @submit.prevent="handleSubmit"
        >
          <el-row :gutter="24">
            <el-col :span="12">
              <el-form-item label="平台" prop="method">
                <el-select
                  v-model="form.login_method"
                  placeholder="选择采集平台"
                  style="width: 100%"
                >
                  <el-option
                    v-for="option in platformOptions"
                    :key="option.value"
                    :label="option.label"
                    :value="option.value"
                  >
                    <div class="platform-option">
                      <el-tag size="small">
                        {{ option.label }}
                      </el-tag>
                    </div>
                  </el-option>
                </el-select>
              </el-form-item>
            </el-col>
            
            <el-col :span="12">
              <el-form-item label="用户名" prop="username">
                <el-input
                  v-model="form.username"
                  placeholder="输入账户用户名"
                  clearable
                  :disabled="form.login_method === 'GOOGLE'"
                />
              </el-form-item>
            </el-col>
          </el-row>

          <el-row :gutter="24">
            <el-col :span="12">
              <el-form-item label="账户密码" prop="password">
                <el-input
                  v-model="form.password"
                  type="password"
                  placeholder="输入账户密码"
                  show-password
                  clearable
                  :disabled="form.login_method === 'GOOGLE'"
                />
              </el-form-item>
            </el-col>
            
            <el-col :span="12">
              <el-form-item label="邮箱地址" prop="email">
                <el-input
                  v-model="form.email"
                  placeholder="输入邮箱地址"
                  clearable
                  :disabled="form.login_method === 'TWITTER'"
                />
              </el-form-item>
            </el-col>
          </el-row>

          <el-row :gutter="24">
            <el-col :span="12">
              <el-form-item label="邮箱密码" prop="email_password">
                <el-input
                  v-model="form.email_password"
                  type="password"
                  placeholder="输入邮箱密码"
                  show-password
                  clearable
                  :disabled="form.login_method === 'TWITTER'"
                />
              </el-form-item>
            </el-col>
            
            <el-col :span="12">
              <el-form-item label="代理选择" prop="proxyId">
                <el-select
                  v-model="form.proxy_id"
                  placeholder="选择代理（可选）"
                  clearable
                  style="width: 100%"
                  @focus="loadProxies"
                >
                  <el-option label="不使用代理" value="" />
                  <el-option
                    v-for="proxy in proxyOptions"
                    :key="proxy.id"
                    :label="`${proxy.ip}:${proxy.port} (${proxy.type})`"
                    :value="proxy.id"
                  >
                    <div class="proxy-option">
                      <span>{{ proxy.ip }}:{{ proxy.port }}</span>
                      <el-tag
                        :type="proxy.status === 'ACTIVE' ? 'success' : 'danger'"
                        size="small"
                        style="margin-left: 8px"
                      >
                        {{ proxy.status === 'ACTIVE' ? '正常' : '异常' }}
                      </el-tag>
                    </div>
                  </el-option>
                </el-select>
              </el-form-item>
            </el-col>
          </el-row>

          <el-form-item label="备注信息" prop="notes">
            <el-input
              v-model="form.notes"
              type="textarea"
              :rows="4"
              placeholder="输入备注信息（可选）"
              maxlength="500"
              show-word-limit
            />
          </el-form-item>

          <div class="form-actions">
            <el-button size="large" @click="goBack">取消</el-button>
            <el-button
              type="primary"
              size="large"
              :loading="submitLoading"
              @click="handleSubmit"
            >
              {{ isEdit ? '保存修改' : '创建账户' }}
            </el-button>
          </div>
        </el-form>
      </el-card>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted, computed } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import type { FormInstance, FormRules } from 'element-plus'
import { ArrowLeft } from '@element-plus/icons-vue'
import { accountService } from '@/services/accountService'
import { proxyService } from '@/services/proxyService'
import type { Account, AccountCreateParams, AccountUpdateParams, AccountPlatform } from '@/types/account'
import type { Proxy } from '@/types/proxy'

const router = useRouter()
const route = useRoute()

const formRef = ref<FormInstance>()
const submitLoading = ref(false)
const proxyOptions = ref<Proxy[]>([])

const accountId = computed(() => route.params.id as string)
const isEdit = computed(() => !!accountId.value && accountId.value !== 'new')

const form = reactive<AccountCreateParams & { id?: string }>({
  username: '',
  password: '',
  email: '',
  email_password: '',
  login_method: 'GOOGLE' as AccountPlatform,
  proxy_id: '',
  notes: ''
})

const platformOptions = [
  { label: 'Google', value: 'GOOGLE' },
  { label: 'Twitter', value: 'TWITTER' }
]

const rules: FormRules = {
  login_method: [
    { required: true, message: '请选择采集平台', trigger: 'change' }
  ],
  username: [
    { message: '请输入用户名', trigger: 'blur' },
    { min: 3, max: 50, message: '用户名长度在 3 到 50 个字符', trigger: 'blur' }
  ],
  password: [
    { message: '请输入账户密码', trigger: 'blur' },
    { min: 6, max: 100, message: '密码长度在 6 到 100 个字符', trigger: 'blur' }
  ],
  email: [
    { message: '请输入邮箱地址', trigger: 'blur' },
    { type: 'email', message: '请输入正确的邮箱格式', trigger: 'blur' }
  ],
  email_password: [
    { message: '请输入邮箱密码', trigger: 'blur' },
    { min: 6, max: 100, message: '邮箱密码长度在 6 到 100 个字符', trigger: 'blur' }
  ]
}

const loadAccountData = async () => {
  if (!isEdit.value) return
  
  try {
    const account = await accountService.getAccount(accountId.value)
    Object.assign(form, {
      username: account.username,
      password: '',
      email: account.email,
      email_password: '',
      login_method: account.login_method as AccountPlatform,
      proxy_id: account.proxy_id || '',
      notes: '' // 备注字段目前后端没有
    })
  } catch (error) {
    ElMessage.error('加载账户数据失败')
    goBack()
  }
}

const loadProxies = async () => {
  if (proxyOptions.value.length > 0) return
  
  try {
    const result = await proxyService.getProxies({ page: 1, pageSize: 100 })
    proxyOptions.value = result
  } catch (error) {
    console.error('加载代理列表失败:', error)
  }
}

const handleSubmit = async () => {
  if (!formRef.value) return
  
  const valid = await formRef.value.validate()
  if (!valid) return
  
  // 验证表单数据
  const errors = accountService.validateAccountData(form, isEdit.value)
  if (errors.length > 0) {
    ElMessage.error(errors[0])
    return
  }
  
  submitLoading.value = true
  
  try {
    if (isEdit.value) {
      // 更新账户
      const updateData: AccountUpdateParams = {
        id: accountId.value,
        username: form.username,
        password: form.password,
        email: form.email,
        email_password: form.email_password,
        login_method: form.login_method,
        proxy_id: form.proxy_id || undefined,
        notes: form.notes
      }
      await accountService.updateAccount(accountId.value, updateData)
    } else {
      // 创建账户
      const createData: AccountCreateParams = {
        username: form.username,
        password: form.password,
        email: form.email,
        email_password: form.email_password,
        login_method: form.login_method,
        proxy_id: form.proxy_id || undefined,
        notes: form.notes
      }
      await accountService.createAccount(createData)
    }
    
    ElMessage.success(isEdit.value ? '账户更新成功' : '账户创建成功')
    goBack()
  } catch (error) {
    ElMessage.error('提交失败')
    console.error('提交失败:', error)
  } finally {
    submitLoading.value = false
  }
}

const goBack = () => {
  router.push('/accounts')
}

onMounted(() => {
  loadAccountData()
  loadProxies()
})
</script>

<style lang="scss" scoped>
.account-form {
  .page-header {
    margin-bottom: 24px;
    
    .header-left {
      display: flex;
      align-items: center;
      gap: 16px;
      
      .title-section {
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
    }
  }
  
  .form-container {
    max-width: 800px;
    
    .el-card {
      box-shadow: 0 2px 12px rgba(0, 0, 0, 0.1);
      
      :deep(.el-card__body) {
        padding: 32px;
      }
    }
  }
  
  .platform-option {
    display: flex;
    align-items: center;
  }
  
  .proxy-option {
    display: flex;
    align-items: center;
    justify-content: space-between;
    width: 100%;
  }
  
  .form-actions {
    margin-top: 32px;
    padding-top: 24px;
    border-top: 1px solid #ebeef5;
    display: flex;
    gap: 16px;
    justify-content: flex-end;
  }
}

@media (max-width: 768px) {
  .account-form {
    .page-header .header-left {
      flex-direction: column;
      align-items: flex-start;
      gap: 12px;
    }
    
    .form-container {
      .el-card :deep(.el-card__body) {
        padding: 20px;
      }
    }
    
    .form-actions {
      flex-direction: column;
      
      .el-button {
        width: 100%;
      }
    }
  }
}
</style> 