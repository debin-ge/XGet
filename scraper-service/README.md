# XGet 数据采集服务

XGet 数据采集服务是一个基于微服务架构的 Twitter 数据采集系统的核心组件。它负责管理和执行数据采集任务，与账号管理服务和代理管理服务协同工作，实现高效、可靠的数据采集功能。

## 功能特点

- 支持多种数据采集类型：用户信息、用户推文、关键词搜索、话题采集、用户关注/粉丝
- 异步任务处理，支持高并发采集
- 多用户支持，任务隔离管理
- 任务执行记录跟踪，详细的执行历史
- 结果存储在 MongoDB 中，支持灵活查询
- RESTful API 接口，方便集成
- 支持任务状态监控和结果导出
- 基于 Kafka 的异步消息处理

## 架构设计

### 核心组件

- **Task 表**: 存储任务基本信息（任务名称、描述、类型、参数等）
- **TaskExecution 表**: 记录任务执行详情（执行时间、使用的账号/代理等）
- **TaskWorker**: 异步任务处理器，通过 Kafka 消费任务
- **API Layer**: RESTful API 接口层
- **Service Layer**: 业务逻辑处理层

### 数据流

1. 用户通过 API 创建任务 → Task 表
2. 任务信息发送到 Kafka 队列
3. TaskWorker 消费任务并创建 TaskExecution 记录
4. 执行采集任务，结果存储到 MongoDB
5. 更新任务状态和执行记录

## API 接口

### 任务管理

- `POST /api/v1/tasks` - 创建采集任务
- `GET /api/v1/tasks` - 获取任务列表（支持用户筛选）
- `GET /api/v1/tasks/{task_id}` - 获取任务详情
- `PUT /api/v1/tasks/{task_id}` - 更新任务信息
- `DELETE /api/v1/tasks/{task_id}` - 删除任务
- `POST /api/v1/tasks/{task_id}/start` - 启动任务
- `POST /api/v1/tasks/{task_id}/stop` - 停止任务
- `GET /api/v1/tasks/{task_id}/results` - 获取任务结果
- `POST /api/v1/tasks/batch` - 批量创建任务
- `GET /api/v1/tasks/search/results` - 搜索结果
- `POST /api/v1/tasks/export/{task_id}` - 导出任务结果

### 任务执行管理

- `GET /api/v1/task-executions` - 获取任务执行记录
- `GET /api/v1/task-executions/{execution_id}` - 获取执行详情
- `GET /api/v1/task-executions/task/{task_id}` - 获取特定任务的执行历史

## 数据模型

### Task 任务模型

```json
{
  "id": "string",           // 任务唯一标识
  "task_name": "string",    // 任务名称
  "describe": "string",     // 任务描述（可选）
  "task_type": "string",    // 任务类型
  "parameters": {},         // 任务参数
  "account_id": "string",   // 关联账号ID（可选）
  "proxy_id": "string",     // 关联代理ID（可选）
  "user_id": "string",      // 用户ID
  "status": "string",       // 任务状态
  "error_message": "string", // 错误信息（可选）
  "created_at": "datetime", // 创建时间
  "updated_at": "datetime"  // 更新时间
}
```

### TaskExecution 执行记录模型

```json
{
  "id": "string",           // 执行记录ID
  "task_id": "string",      // 关联任务ID
  "account_id": "string",   // 使用的账号ID
  "proxy_id": "string",     // 使用的代理ID
  "status": "string",       // 执行状态
  "error_message": "string", // 错误信息
  "started_at": "datetime", // 开始时间
  "completed_at": "datetime", // 完成时间
  "duration": "float",      // 执行时长（秒）
  "result_count": "integer" // 结果数量
}
```

## 使用示例

### 创建采集任务

```bash
curl -X POST "http://localhost:8003/api/v1/tasks" \
  -H "Content-Type: application/json" \
  -d '{
    "task_name": "采集埃隆马斯克推文",
    "describe": "采集埃隆马斯克最新50条推文，不包含回复和转发",
    "task_type": "USER_TWEETS",
    "parameters": {
      "username": "elonmusk",
      "limit": 50,
      "include_replies": false,
      "include_retweets": false
    },
    "account_id": "your-account-id",
    "proxy_id": "your-proxy-id",
    "user_id": "your-user-id"
  }'
```

### 获取任务列表（支持筛选）

```bash
# 获取所有任务
curl "http://localhost:8003/api/v1/tasks?page=1&size=20"

# 按用户筛选
curl "http://localhost:8003/api/v1/tasks?user_id=user123&status=PENDING"

# 按任务类型筛选
curl "http://localhost:8003/api/v1/tasks?task_type=USER_TWEETS&page=1&size=10"
```

### 获取任务状态

```bash
curl "http://localhost:8003/api/v1/tasks/{task_id}"
```

### 启动任务

```bash
curl -X POST "http://localhost:8003/api/v1/tasks/{task_id}/start"
```

### 获取任务结果

```bash
curl "http://localhost:8003/api/v1/tasks/{task_id}/results?limit=20"
```

### 获取任务执行历史

```bash
curl "http://localhost:8003/api/v1/task-executions/task/{task_id}"
```

## 任务类型

支持的任务类型包括：

- `USER_INFO` - 采集用户基本信息
- `USER_TWEETS` - 采集用户推文
- `KEYWORD_SEARCH` - 关键词搜索
- `HASHTAG_SEARCH` - 话题标签搜索
- `USER_FOLLOWERS` - 采集用户粉丝
- `USER_FOLLOWING` - 采集用户关注

## 任务状态

- `PENDING` - 等待执行
- `RUNNING` - 正在执行
- `COMPLETED` - 执行完成
- `FAILED` - 执行失败
- `STOPPED` - 已停止

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
- `KAFKA_TOPIC_TASKS` - 任务队列主题名
- `KAFKA_TOPIC_RESULTS` - 结果队列主题名

## 开发和部署

### 本地开发

1. 安装依赖：`pip install -r requirements.txt`
2. 配置环境变量
3. 启动服务：`uvicorn app.main:app --host 0.0.0.0 --port 8003`

### Docker 部署

```bash
docker build -t scraper-service .
docker run -p 8003:8003 scraper-service
```

## 监控和日志

- 任务执行状态实时监控
- 详细的执行日志记录
- 性能指标收集
- 错误告警机制
