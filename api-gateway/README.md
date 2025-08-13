# XGet API Gateway

XGet 数据抓取平台的 API 网关，提供统一的入口和认证、限流、监控等功能。

## 🚀 功能特性

### 核心功能
- **统一入口**: 所有客户端请求的单一入口点
- **服务路由**: 智能请求路由到对应的微服务
- **认证授权**: JWT令牌验证和基于角色的访问控制
- **限流保护**: 基于Redis的分布式限流
- **健康检查**: 后端服务健康状态监控
- **监控指标**: Prometheus指标收集
- **安全防护**: 安全头和请求验证

### 支持的服务
- **用户服务** (`/api/v1/users`): 用户管理和认证
- **认证服务** (`/api/v1/auth`): 登录、注册、令牌管理
- **账号服务** (`/api/v1/accounts`): 社交媒体账户管理
- **代理服务** (`/api/v1/proxies`): 代理池管理
- **采集服务** (`/api/v1/tasks`): 数据采集任务管理

## 📋 环境要求

- Python 3.12+
- Redis (用于限流和缓存)
- 后端微服务 (user-service, account-service, proxy-service, scraper-service)

## 🛠️ 安装和配置

### 1. 安装依赖

```bash
pip install -r requirements.txt
```

### 2. 环境变量配置

创建 `.env` 文件或设置以下环境变量：

```bash
# 基础配置
DEBUG=true
LOG_LEVEL=INFO
PROJECT_NAME="XGet API Gateway"

# 服务发现
SERVICE_DISCOVERY_TYPE=static

# 后端服务URL
ACCOUNT_SERVICE_URL=http://account-service:8000
PROXY_SERVICE_URL=http://proxy-service:8000
SCRAPER_SERVICE_URL=http://scraper-service:8000
USER_SERVICE_URL=http://user-service:8000

# Redis配置（限流）
REDIS_HOST=redis
REDIS_PORT=6379
REDIS_DB=0
REDIS_PASSWORD=
REDIS_URL=redis://redis:6379/0

# JWT认证
JWT_SECRET_KEY=your-secret-key-here
JWT_ALGORITHM=HS256
JWT_ACCESS_TOKEN_EXPIRE_MINUTES=30

# 限流配置
RATE_LIMIT_ENABLED=true
RATE_LIMIT_REQUESTS=100
RATE_LIMIT_PERIOD_SECONDS=60
RATE_LIMIT_BURST=10

# 代理和转发 (针对网络不稳定优化的默认值)
PROXY_TIMEOUT_SECONDS=45.0                # 读取超时 (默认45秒)
PROXY_CONNECT_TIMEOUT_SECONDS=15.0        # 连接超时 (默认15秒)
PROXY_WRITE_TIMEOUT_SECONDS=15.0          # 写入超时 (默认15秒)
PROXY_POOL_TIMEOUT_SECONDS=10.0           # 连接池超时 (默认10秒)
PROXY_RETRIES=5                           # 重试次数 (默认5次)
PROXY_RETRY_DELAY_SECONDS=2.0             # 重试延迟 (默认2秒)
PROXY_MAX_KEEPALIVE_CONNECTIONS=15        # 最大保活连接 (默认15)
PROXY_MAX_CONNECTIONS=75                  # 最大连接数 (默认75)
PROXY_KEEPALIVE_EXPIRY=60.0               # 连接保活时间 (默认60秒)

# 健康检查
HEALTH_CHECK_ENABLED=true
HEALTH_CHECK_INTERVAL_SECONDS=30
HEALTH_CHECK_TIMEOUT_SECONDS=5

# 监控
METRICS_ENABLED=true
METRICS_PATH=/metrics

# 安全
SECURITY_HEADERS_ENABLED=true
```

### 3. Docker 配置

使用 Docker Compose 启动：

```bash
docker-compose up -d api-gateway
```

## 🔧 使用方法

### 启动应用

```bash
# 开发模式
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload

# 生产模式
uvicorn app.main:app --host 0.0.0.0 --port 8000
```

### API 端点

#### 基础信息
- `GET /` - API 根信息
- `GET /api/v1` - API 版本信息
- `GET /health` - 健康检查
- `GET /metrics` - Prometheus 指标 (需启用)

#### 认证相关
```bash
# 用户注册
POST /api/v1/auth/register
POST /api/v1/users/register

# 用户登录
POST /api/v1/auth/login
POST /api/v1/users/login

# 刷新令牌
POST /api/v1/auth/refresh

# 获取当前用户信息
GET /api/v1/auth/me
GET /api/v1/users/me
```

#### 业务服务
```bash
# 账户管理
GET    /api/v1/accounts
POST   /api/v1/accounts
GET    /api/v1/accounts/{id}
PUT    /api/v1/accounts/{id}
DELETE /api/v1/accounts/{id}

# 代理管理
GET    /api/v1/proxies
POST   /api/v1/proxies
GET    /api/v1/proxies/{id}
PUT    /api/v1/proxies/{id}
DELETE /api/v1/proxies/{id}

# 采集任务
GET    /api/v1/tasks
POST   /api/v1/tasks
GET    /api/v1/tasks/{id}
PUT    /api/v1/tasks/{id}
DELETE /api/v1/tasks/{id}
```

## 🔐 认证和授权

### JWT 令牌

API网关使用JWT令牌进行认证。客户端需要在请求头中包含：

```
Authorization: Bearer <access_token>
```

### 公开路径

以下路径不需要认证：
- `/api/v1/auth/login`
- `/api/v1/auth/register`
- `/api/v1/users/login`
- `/api/v1/users/register`
- `/health`
- `/metrics`
- API文档相关路径

### 管理员权限

部分操作需要管理员权限：
- 用户管理
- 角色管理
- 批量导入账户/代理

## 📊 监控和指标

### Prometheus 指标

访问 `/metrics` 端点获取以下指标：

- `http_requests_total` - HTTP请求总数
- `http_request_duration_seconds` - 请求持续时间
- `http_requests_active` - 活跃请求数
- `service_requests_total` - 后端服务请求总数
- `service_request_duration_seconds` - 后端服务请求时间
- `rate_limit_hits_total` - 限流命中次数

### 健康检查

健康检查功能会：
- 定期检查所有后端服务状态
- 记录响应时间和错误信息
- 提供整体健康状态评估

## 🚦 限流机制

### 限流策略

- 基于IP地址和用户ID的复合限流
- 滑动窗口算法
- Redis分布式存储
- 可配置的限制和时间窗口

### 限流响应

当请求被限流时，返回HTTP 429状态码和相关信息：

```json
{
  "error": "Rate limit exceeded",
  "message": "Too many requests. Try again in 60 seconds.",
  "rate_limit": {
    "limit": 100,
    "remaining": 0,
    "reset": 1699123456,
    "reset_after": 60
  }
}
```

## 🔧 中间件

### 认证中间件
- JWT令牌验证
- 用户状态检查
- 权限验证

### 限流中间件
- 请求计数
- 滑动窗口限流
- Redis分布式存储

### 监控中间件
- 请求指标收集
- 响应时间统计
- 错误率监控

### 安全中间件
- 安全响应头
- 请求大小限制
- 请求ID生成

## 🏗️ 架构

### 目录结构

```
app/
├── __init__.py
├── main.py                 # 主应用文件
├── api/
│   ├── __init__.py
│   ├── router.py          # 主路由配置
│   └── routes/            # 各服务路由
│       ├── auth.py
│       ├── user.py
│       ├── account.py
│       ├── proxy.py
│       └── scraper.py
├── core/
│   ├── __init__.py
│   └── config.py          # 配置管理
├── middlewares/
│   ├── __init__.py
│   ├── auth.py            # 认证中间件
│   ├── rate_limit.py      # 限流中间件
│   ├── monitoring.py      # 监控中间件
│   ├── security.py        # 安全中间件
│   └── proxy.py           # 代理中间件
└── services/
    ├── __init__.py
    └── health_checker.py   # 健康检查服务
```

### 请求流程

1. **接收请求** - 客户端发送请求到API网关
2. **安全检查** - 安全头验证、请求大小检查
3. **认证验证** - JWT令牌验证（如需要）
4. **限流检查** - 检查是否超过限流阈值
5. **服务路由** - 将请求转发到对应的后端服务
6. **响应处理** - 处理后端响应并返回给客户端
7. **指标记录** - 记录监控指标

## 🚨 错误处理

### 标准错误响应

```json
{
  "error": "错误描述",
  "status_code": 400,
  "request_id": "uuid-string",
  "path": "/api/v1/example"
}
```

### 常见错误码

- `400` - 请求参数错误
- `401` - 未认证或令牌无效
- `403` - 权限不足
- `404` - 资源不存在
- `429` - 请求过于频繁
- `500` - 服务器内部错误
- `503` - 后端服务不可用

## 🔍 日志

### 日志级别

- `DEBUG` - 调试信息
- `INFO` - 一般信息
- `WARNING` - 警告信息
- `ERROR` - 错误信息

### 日志格式

```
%(asctime)s - %(name)s - %(levelname)s - %(message)s
```

## 🧪 测试

### 健康检查测试

```bash
curl http://localhost:8000/health
```

### 认证测试

```bash
# 登录获取令牌
curl -X POST http://localhost:8000/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username": "test", "password": "test123"}'

# 使用令牌访问受保护的资源
curl -H "Authorization: Bearer <token>" \
  http://localhost:8000/api/v1/users/me
```

## 📝 开发指南

### 添加新服务

1. 在 `config.py` 中添加服务URL配置
2. 在 `app/api/routes/` 中创建新的路由文件
3. 在 `app/api/router.py` 中注册新路由
4. 更新认证中间件的公开路径（如需要）

### 自定义中间件

参考现有中间件实现，实现自定义逻辑并在 `main.py` 中注册。

## 🤝 贡献

1. Fork 项目
2. 创建特性分支
3. 提交更改
4. 推送到分支
5. 创建 Pull Request

## 📄 许可证

本项目采用 MIT 许可证。

## 🔧 故障排除

### 常见错误及解决方案

#### "Too little data for declared Content-Length"

这个错误通常由网络连接不稳定或HTTP响应不完整引起。

**解决方案：**
1. 检查网络连接稳定性
2. 调整超时配置：
   ```bash
   PROXY_TIMEOUT_SECONDS=60.0
   PROXY_CONNECT_TIMEOUT_SECONDS=15.0
   PROXY_RETRIES=5
   ```
3. 减少并发连接：
   ```bash
   PROXY_MAX_CONNECTIONS=50
   PROXY_MAX_KEEPALIVE_CONNECTIONS=10
   ```

#### 服务不可用 (503错误)

当后端服务无响应时会出现此错误。

**解决方案：**
1. 检查后端服务状态：`curl http://service-url/health`
2. 查看服务日志
3. 增加重试次数：`PROXY_RETRIES=5`
4. 调整健康检查间隔：`HEALTH_CHECK_INTERVAL_SECONDS=10`

#### 认证失败 (401错误)

JWT令牌验证失败。

**解决方案：**
1. 检查JWT密钥配置：`JWT_SECRET_KEY`
2. 确认令牌未过期
3. 验证令牌格式：`Authorization: Bearer <token>`

#### 限流错误 (429错误)

请求频率超过限制。

**解决方案：**
1. 调整限流配置：
   ```bash
   RATE_LIMIT_REQUESTS=200
   RATE_LIMIT_PERIOD_SECONDS=60
   RATE_LIMIT_BURST=20
   ```
2. 检查Redis连接
3. 实现客户端退避重试

### 性能优化

#### HTTP客户端优化

```bash
# 增加连接池大小
PROXY_MAX_CONNECTIONS=200
PROXY_MAX_KEEPALIVE_CONNECTIONS=50

# 优化超时设置
PROXY_TIMEOUT_SECONDS=45.0
PROXY_CONNECT_TIMEOUT_SECONDS=10.0
PROXY_WRITE_TIMEOUT_SECONDS=15.0

# 增加连接保活时间
PROXY_KEEPALIVE_EXPIRY=60.0
```

#### 限流优化

```bash
# 根据实际需求调整
RATE_LIMIT_REQUESTS=500
RATE_LIMIT_PERIOD_SECONDS=60
RATE_LIMIT_BURST=50
```

### 日志分析

查看特定类型的错误：

```bash
# 查看服务不可用错误
grep "Service unavailable" logs/api-gateway.log

# 查看网络错误
grep "Too little data\|Connection\|Timeout" logs/api-gateway.log

# 查看限流情况
grep "Rate limit" logs/api-gateway.log
```

### 监控和警报

建议监控以下指标：

- HTTP错误率（特别是5xx错误）
- 平均响应时间
- 服务健康状态
- 限流命中率
- 活跃连接数

## 📞 支持

如有问题或建议，请创建 Issue 或联系开发团队。 