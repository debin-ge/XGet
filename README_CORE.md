# XGet 核心服务使用指南

XGet微服务架构目前已实现以下核心服务：

1. **账号管理服务(Account Service)**：管理社交媒体账号和登录信息
2. **代理管理服务(Proxy Service)**：管理和监控代理服务器
3. **数据采集服务(Scraper Service)**：执行数据采集任务

## 快速启动

使用提供的启动脚本可以快速启动所有核心服务：

```bash
# 确保脚本有执行权限
chmod +x start_core_services.sh

# 运行启动脚本
./start_core_services.sh
```

或者，您可以手动使用Docker Compose启动服务：

```bash
cd docker
docker-compose up -d account-service proxy-service scraper-service postgres mongodb redis kafka
```

## 服务访问

启动后，您可以通过以下URL访问各个服务的API：

- **账号管理服务**：http://localhost:8001/api/v1/docs
- **代理管理服务**：http://localhost:8002/api/v1/docs
- **数据采集服务**：http://localhost:8003/api/v1/docs

## 核心功能使用流程

### 1. 添加代理

首先，向代理管理服务添加代理：

```bash
curl -X POST http://localhost:8002/api/v1/proxies \
  -H "Content-Type: application/json" \
  -d '{
    "host": "proxy.example.com",
    "port": 8080,
    "protocol": "http",
    "username": "proxy_user",
    "password": "proxy_pass"
  }'
```

### 2. 创建账号

然后，向账号管理服务添加社交媒体账号：

```bash
curl -X POST http://localhost:8001/api/v1/accounts \
  -H "Content-Type: application/json" \
  -d '{
    "username": "twitter_user",
    "password": "secure_password",
    "email": "user@example.com",
    "email_password": "email_password",
    "login_method": "TWITTER"
  }'
```

### 3. 登录账号

使用刚创建的账号ID和代理ID进行登录：

```bash
curl -X POST http://localhost:8001/api/v1/accounts/{account_id}/login \
  -H "Content-Type: application/json" \
  -d '{
    "proxy_id": "{proxy_id}",
    "async_login": false
  }'
```

### 4. 创建采集任务

最后，使用登录成功的账号创建数据采集任务：

```bash
curl -X POST http://localhost:8003/api/v1/tasks \
  -H "Content-Type: application/json" \
  -d '{
    "task_type": "USER_TWEETS",
    "parameters": {
      "username": "elonmusk",
      "limit": 100
    },
    "priority": "high",
    "schedule": "once"
  }'
```

## 服务监控

您可以通过以下命令查看服务日志：

```bash
# 查看所有服务日志
docker-compose logs -f

# 查看特定服务日志
docker-compose logs -f account-service
docker-compose logs -f proxy-service
docker-compose logs -f scraper-service
```

## 停止服务

使用以下命令停止所有服务：

```bash
cd docker
docker-compose down
```

## 数据持久化

所有数据都存储在Docker卷中，即使停止服务也不会丢失：

- PostgreSQL数据：`postgres_data`卷
- MongoDB数据：`mongodb_data`卷

## 下一步计划

未来将实现以下服务：

1. **认证授权服务(Auth Service)**
2. **用户管理服务(User Service)**
3. **API网关(API Gateway)**
4. **监控告警服务(Monitoring Service)** 