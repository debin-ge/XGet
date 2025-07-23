# XGet 数据采集服务

XGet 数据采集服务是一个基于微服务架构的 Twitter 数据采集系统的核心组件。它负责管理和执行数据采集任务，与账号管理服务和代理管理服务协同工作，实现高效、可靠的数据采集功能。

## 功能特点

- 支持多种数据采集类型：用户信息、用户推文、关键词搜索、话题采集、用户关注/粉丝
- 异步任务处理，支持高并发采集
- 结果存储在 MongoDB 中，支持灵活查询
- RESTful API 接口，方便集成
- 支持任务状态监控和结果导出

## API 接口

### 任务管理

- `POST /api/v1/tasks` - 创建采集任务
- `GET /api/v1/tasks` - 获取任务列表
- `GET /api/v1/tasks/{task_id}` - 获取任务详情
- `PUT /api/v1/tasks/{task_id}` - 更新任务信息
- `DELETE /api/v1/tasks/{task_id}` - 删除任务
- `POST /api/v1/tasks/{task_id}/start` - 启动任务
- `POST /api/v1/tasks/{task_id}/stop` - 停止任务
- `GET /api/v1/tasks/{task_id}/results` - 获取任务结果
- `POST /api/v1/tasks/batch` - 批量创建任务
- `GET /api/v1/tasks/search/results` - 搜索结果
- `POST /api/v1/tasks/export/{task_id}` - 导出任务结果

## 使用示例

### 创建采集任务

```bash
curl -X POST "http://localhost:8003/api/v1/tasks" \
  -H "Content-Type: application/json" \
  -d '{
    "task_type": "USER_TWEETS",
    "parameters": {
      "username": "elonmusk",
      "limit": 50,
      "include_replies": false,
      "include_retweets": false
    },
    "account_id": "your-account-id",
    "proxy_id": "your-proxy-id"
  }'
```

### 获取任务状态

```bash
curl "http://localhost:8003/api/v1/tasks/{task_id}"
```

### 获取任务结果

```bash
curl "http://localhost:8003/api/v1/tasks/{task_id}/results?limit=20"
```

## 环境变量

- `POSTGRES_SERVER` - PostgreSQL 服务器地址
- `POSTGRES_USER` - PostgreSQL 用户名
- `POSTGRES_PASSWORD` - PostgreSQL 密码
- `POSTGRES_DB` - PostgreSQL 数据库名
- `REDIS_URL` - Redis 连接 URL
- `MONGODB_URL` - MongoDB 连接 URL
- `ACCOUNT_SERVICE_URL` - 账号管理服务 URL
- `PROXY_SERVICE_URL` - 代理管理服务 URL
- `KAFKA_BOOTSTRAP_SERVERS` - Kafka 服务器地址
