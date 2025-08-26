# XGet Frontend Service

基于 Vue 3 + TypeScript + Element Plus 的现代化前端应用，为 XGet 数据采集平台提供用户界面。

## 🚀 技术栈

- **框架**: Vue 3 (Composition API + `<script setup>`)
- **语言**: TypeScript
- **UI库**: Element Plus
- **状态管理**: Pinia
- **路由**: Vue Router 4
- **HTTP客户端**: Axios
- **构建工具**: Vite
- **样式**: SCSS

## 📁 项目结构

```
frontend-service/
├── public/                         # 静态资源
├── src/
│   ├── api/                        # 数据访问层
│   │   ├── index.ts               # Axios 配置和拦截器
│   │   ├── auth.ts                # 认证相关API
│   │   ├── accounts.ts            # 账户管理API
│   │   ├── proxies.ts             # 代理管理API
│   │   ├── tasks.ts               # 任务管理API
│   │   └── dashboard.ts           # 仪表盘数据API
│   ├── components/                 # 可复用UI组件
│   │   ├── common/                # 通用组件
│   │   ├── forms/                 # 表单组件
│   │   ├── tables/                # 表格组件
│   │   └── charts/                # 图表组件
│   ├── composables/               # 组合式函数
│   ├── router/                    # 路由配置
│   ├── services/                  # 业务逻辑层
│   │   ├── authService.ts         # 认证服务
│   │   ├── accountService.ts      # 账户管理服务
│   │   ├── proxyService.ts        # 代理管理服务
│   │   ├── taskService.ts         # 任务管理服务
│   │   └── dashboardService.ts    # 仪表盘服务
│   ├── store/                     # 状态管理
│   ├── styles/                    # 样式文件
│   ├── types/                     # TypeScript类型定义
│   ├── utils/                     # 工具函数
│   ├── views/                     # 页面级组件
│   ├── App.vue                    # 根组件
│   └── main.ts                    # 应用入口
├── .env.development               # 开发环境配置
├── .env.production                # 生产环境配置
├── package.json
├── tsconfig.json
├── vite.config.ts
└── README.md
```

## 🏗️ 架构设计

### 分层架构

1. **表示层 (Views)**: 页面级组件，负责UI展示和用户交互
2. **业务逻辑层 (Services)**: 封装业务逻辑，调用API层
3. **数据访问层 (API)**: 封装HTTP请求，与后端通信
4. **状态管理层 (Store)**: 全局状态管理

### 数据流向

```
Views → Services → API → Backend
  ↕       ↕        ↕
Store ←  Store  ← Store
```

## 🛠️ 开发指南

### 安装依赖

```bash
cd frontend-service
npm install
```

### 启动开发服务器

```bash
npm run dev
```

开发服务器将在 `http://localhost:3000` 启动。

### 构建生产版本

```bash
npm run build
```

### 代码检查和格式化

```bash
# 代码检查
npm run lint

# 代码格式化
npm run format
```

## 📋 核心功能模块

### 1. 仪表盘模块
- 系统总览和关键指标展示
- 实时数据更新
- 图表展示和趋势分析

### 2. 账户管理模块
- CRUD操作界面
- 账户状态管理
- 批量操作支持
- 连接测试功能

### 3. 代理管理模块
- 代理池管理
- 健康检查功能
- 性能监控
- 批量操作

### 4. 任务管理模块
- 动态任务创建表单
- 实时任务状态监控
- 任务结果查看和导出
- 日志查看

## 🔧 开发规范

### 命名约定

- **组件**: PascalCase (如 `AccountManagementView.vue`)
- **文件**: camelCase (如 `accountService.ts`)
- **API文件**: 复数形式 (如 `accounts.ts`)
- **类型定义**: PascalCase接口 (如 `Account`, `AccountCreateParams`)

### 代码结构

```typescript
// 组件示例
<template>
  <!-- UI 结构 -->
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import accountService from '@/services/accountService'
import type { Account } from '@/types/account'

// 响应式数据
const accounts = ref<Account[]>([])
const loading = ref(false)

// 方法
const loadAccounts = async () => {
  loading.value = true
  try {
    const data = await accountService.getAccounts({})
    accounts.value = data.items
  } finally {
    loading.value = false
  }
}

// 生命周期
onMounted(() => {
  loadAccounts()
})
</script>

<style lang="scss" scoped>
/* 组件样式 */
</style>
```

### 业务逻辑层规范

```typescript
// 服务层示例
class AccountService {
  async getAccounts(params: PaginationParams) {
    try {
      return await accountApi.getAccounts(params)
    } catch (error) {
      ElMessage.error('获取账户列表失败')
      throw error
    }
  }

  async createAccount(data: AccountCreateParams) {
    try {
      const account = await accountApi.createAccount(data)
      ElMessage.success('账户创建成功')
      return account
    } catch (error) {
      ElMessage.error('账户创建失败')
      throw error
    }
  }
}
```

## 🔌 API 集成

### 环境配置

```bash
# .env.development
VITE_API_BASE_URL=http://localhost:8000/api
VITE_APP_TITLE=XGet数据采集平台

# .env.production
VITE_API_BASE_URL=https://api.xget.com/api
VITE_APP_TITLE=XGet数据采集平台
```

### 微服务对应关系

- **账户管理** ↔ `account-service`
- **代理管理** ↔ `proxy-service`
- **任务管理** ↔ `scraper-service`
- **用户认证** ↔ `user-service`

## 🎨 UI/UX 设计原则

### Element Plus 组件使用

- 统一使用 Element Plus 组件保证视觉一致性
- 遵循 Element Plus 设计规范
- 自定义主题配置

### 响应式设计

- 支持移动端和桌面端
- 使用 Element Plus 的栅格系统
- 适配不同屏幕尺寸

### 用户体验

- 明确的操作反馈 (Message/Notification)
- 加载状态提示
- 友好的错误处理
- 直观的导航和面包屑

## 🚦 状态管理

### Pinia Store 结构

```typescript
// auth store 示例
export const useAuthStore = defineStore('auth', () => {
  const user = ref<User | null>(null)
  const isAuthenticated = computed(() => !!user.value)
  
  const login = async (credentials) => {
    // 登录逻辑
  }
  
  return { user, isAuthenticated, login }
})
```

## 🛣️ 路由配置

### 路由守卫

- 认证检查
- 权限验证
- 页面标题设置
- 面包屑更新

### 懒加载

```typescript
{
  path: '/accounts',
  component: () => import('@/views/account/AccountManagementView.vue')
}
```

## 📱 部署

### Docker 部署

```dockerfile
FROM node:18-alpine as builder
WORKDIR /app
COPY package*.json ./
RUN npm ci
COPY . .
RUN npm run build

FROM nginx:alpine
COPY --from=builder /app/dist /usr/share/nginx/html
COPY nginx.conf /etc/nginx/nginx.conf
EXPOSE 80
CMD ["nginx", "-g", "daemon off;"]
```

### Nginx 配置

```nginx
server {
  listen 80;
  location / {
    root /usr/share/nginx/html;
    index index.html;
    try_files $uri $uri/ /index.html;
  }
  
  location /api {
    proxy_pass http://api-gateway:8000;
  }
}
```

## 🤝 贡献指南

1. Fork 项目
2. 创建功能分支
3. 提交更改
4. 创建 Pull Request

## 📄 许可证

MIT License

---

**注意**: 这是一个完整的前端架构模板。在实际开发中，请根据具体需求调整和扩展功能模块。