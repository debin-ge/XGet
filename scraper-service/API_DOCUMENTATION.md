# XGet Scraper Service API 文档

## 概览

XGet 数据采集服务提供了完整的 RESTful API，用于管理数据采集任务和执行记录。本文档详细描述了所有可用的 API 端点、请求/响应格式和使用示例。

## 基础信息

- **Base URL**: `http://localhost:8003/api/v1`
- **Content-Type**: `application/json`
- **认证方式**: 待定（当前版本暂无认证）

## 数据模型

### Task 任务模型

```json
{
  "id": "string",
  "task_name": "string",
  "describe": "string|null",
  "task_type": "string",
  "parameters": "object",
  "account_id": "string|null",
  "proxy_id": "string|null",
  "user_id": "string",
  "status": "string",
  "error_message": "string|null",
  "created_at": "string (ISO 8601)",
  "updated_at": "string (ISO 8601)|null"
}
```

### TaskExecution 执行记录模型

```json
{
  "id": "string",
  "task_id": "string",
  "account_id": "string|null",
  "proxy_id": "string|null",
  "status": "string",
  "error_message": "string|null",
  "started_at": "string (ISO 8601)",
  "completed_at": "string (ISO 8601)|null",
  "duration": "number|null",
  "result_count": "integer|null"
}
```

### 分页响应模型

```json
{
  "items": "array",
  "total": "integer",
  "page": "integer",
  "size": "integer",
  "pages": "integer"
}
```

## API 端点

### 1. 任务管理

#### 1.1 创建任务

**POST** `/tasks`

创建一个新的数据采集任务。

**请求体:**
```json
{
  "task_name": "采集用户推文",
  "describe": "采集指定用户的最新推文",
  "task_type": "USER_TWEETS",
  "parameters": {
    "username": "elonmusk",
    "limit": 50,
    "include_replies": false,
    "include_retweets": false
  },
  "account_id": "account-123",
  "proxy_id": "proxy-456",
  "user_id": "user-789"
}
```

**响应 (201 Created):**
```json
{
  "id": "task-abc123",
  "task_name": "采集用户推文",
  "describe": "采集指定用户的最新推文",
  "task_type": "USER_TWEETS",
  "parameters": {
    "username": "elonmusk",
    "limit": 50,
    "include_replies": false,
    "include_retweets": false
  },
  "account_id": "account-123",
  "proxy_id": "proxy-456",
  "user_id": "user-789",
  "status": "PENDING",
  "error_message": null,
  "created_at": "2024-01-15T10:30:00Z",
  "updated_at": null
}
```

#### 1.2 获取任务列表

**GET** `/tasks`

获取任务列表，支持分页和筛选。

**查询参数:**
- `page` (int, optional): 页码，默认 1
- `size` (int, optional): 每页数量，默认 20，最大 100
- `status` (string, optional): 按状态筛选
- `task_type` (string, optional): 按任务类型筛选
- `user_id` (string, optional): 按用户ID筛选

**请求示例:**
```
GET /tasks?page=1&size=10&status=PENDING&user_id=user-789
```

**响应 (200 OK):**
```json
{
  "items": [
    {
      "id": "task-abc123",
      "task_name": "采集用户推文",
      "describe": "采集指定用户的最新推文",
      "task_type": "USER_TWEETS",
      "parameters": {
        "username": "elonmusk",
        "limit": 50
      },
      "account_id": "account-123",
      "proxy_id": "proxy-456",
      "user_id": "user-789",
      "status": "PENDING",
      "error_message": null,
      "created_at": "2024-01-15T10:30:00Z",
      "updated_at": null
    }
  ],
  "total": 1,
  "page": 1,
  "size": 10,
  "pages": 1
}
```

#### 1.3 获取任务详情

**GET** `/tasks/{task_id}`

获取指定任务的详细信息。

**路径参数:**
- `task_id` (string): 任务ID

**响应 (200 OK):**
```json
{
  "id": "task-abc123",
  "task_name": "采集用户推文",
  "describe": "采集指定用户的最新推文",
  "task_type": "USER_TWEETS",
  "parameters": {
    "username": "elonmusk",
    "limit": 50,
    "include_replies": false,
    "include_retweets": false
  },
  "account_id": "account-123",
  "proxy_id": "proxy-456",
  "user_id": "user-789",
  "status": "RUNNING",
  "error_message": null,
  "created_at": "2024-01-15T10:30:00Z",
  "updated_at": "2024-01-15T10:35:00Z"
}
```

**错误响应 (404 Not Found):**
```json
{
  "detail": "Task not found"
}
```

#### 1.4 更新任务

**PUT** `/tasks/{task_id}`

更新指定任务的信息。

**路径参数:**
- `task_id` (string): 任务ID

**请求体:**
```json
{
  "task_name": "更新后的任务名称",
  "describe": "更新后的任务描述",
  "parameters": {
    "username": "elonmusk",
    "limit": 100
  },
  "status": "PENDING"
}
```

**响应 (200 OK):**
```json
{
  "id": "task-abc123",
  "task_name": "更新后的任务名称",
  "describe": "更新后的任务描述",
  "task_type": "USER_TWEETS",
  "parameters": {
    "username": "elonmusk",
    "limit": 100
  },
  "account_id": "account-123",
  "proxy_id": "proxy-456",
  "user_id": "user-789",
  "status": "PENDING",
  "error_message": null,
  "created_at": "2024-01-15T10:30:00Z",
  "updated_at": "2024-01-15T11:00:00Z"
}
```

#### 1.5 删除任务

**DELETE** `/tasks/{task_id}`

删除指定任务及其相关结果。

**路径参数:**
- `task_id` (string): 任务ID

**响应 (200 OK):**
```json
{
  "message": "Task and related results deleted successfully"
}
```

#### 1.6 启动任务

**POST** `/tasks/{task_id}/start`

启动指定任务的执行。

**路径参数:**
- `task_id` (string): 任务ID

**响应 (200 OK):**
```json
{
  "id": "task-abc123",
  "task_name": "采集用户推文",
  "status": "RUNNING",
  "error_message": null,
  "created_at": "2024-01-15T10:30:00Z",
  "updated_at": "2024-01-15T11:05:00Z"
}
```

#### 1.7 停止任务

**POST** `/tasks/{task_id}/stop`

停止正在执行的任务。

**路径参数:**
- `task_id` (string): 任务ID

**响应 (200 OK):**
```json
{
  "id": "task-abc123",
  "task_name": "采集用户推文",
  "status": "STOPPED",
  "error_message": null,
  "created_at": "2024-01-15T10:30:00Z",
  "updated_at": "2024-01-15T11:10:00Z"
}
```

#### 1.8 获取任务结果

**GET** `/tasks/{task_id}/results`

获取指定任务的采集结果。

**路径参数:**
- `task_id` (string): 任务ID

**查询参数:**
- `skip` (int, optional): 跳过的记录数，默认 0
- `limit` (int, optional): 返回的记录数，默认 100，最大 1000
- `data_type` (string, optional): 数据类型筛选

**响应 (200 OK):**
```json
{
  "items": [
    {
      "id": "result-123",
      "task_id": "task-abc123",
      "data_type": "tweet",
      "data": {
        "id": "tweet-456",
        "text": "Hello world!",
        "user": {
          "username": "elonmusk",
          "name": "Elon Musk"
        },
        "created_at": "2024-01-15T10:00:00Z"
      },
      "metadata": {
        "source": "twitter",
        "scraped_at": "2024-01-15T10:30:00Z"
      },
      "created_at": "2024-01-15T10:30:00Z"
    }
  ],
  "total": 50,
  "page": 1,
  "size": 100,
  "pages": 1
}
```

#### 1.9 批量创建任务

**POST** `/tasks/batch`

批量创建多个任务。

**请求体:**
```json
[
  {
    "task_name": "任务1",
    "task_type": "USER_TWEETS",
    "parameters": {"username": "user1"},
    "user_id": "user-789"
  },
  {
    "task_name": "任务2",
    "task_type": "USER_INFO",
    "parameters": {"username": "user2"},
    "user_id": "user-789"
  }
]
```

**响应 (200 OK):**
```json
[
  {
    "id": "task-def456",
    "task_name": "任务1",
    "task_type": "USER_TWEETS",
    "parameters": {"username": "user1"},
    "user_id": "user-789",
    "status": "PENDING",
    "created_at": "2024-01-15T11:00:00Z"
  },
  {
    "id": "task-ghi789",
    "task_name": "任务2",
    "task_type": "USER_INFO",
    "parameters": {"username": "user2"},
    "user_id": "user-789",
    "status": "PENDING",
    "created_at": "2024-01-15T11:00:01Z"
  }
]
```

#### 1.10 搜索结果

**GET** `/tasks/search/results`

在所有任务结果中搜索。

**查询参数:**
- `query` (string, required): 搜索查询字符串，格式：`key1:value1,key2:value2`
- `data_type` (string, optional): 数据类型筛选
- `skip` (int, optional): 跳过的记录数，默认 0
- `limit` (int, optional): 返回的记录数，默认 100，最大 1000

**请求示例:**
```
GET /tasks/search/results?query=username:elonmusk,text:tesla&limit=50
```

**响应 (200 OK):**
```json
{
  "items": [
    {
      "id": "result-789",
      "task_id": "task-abc123",
      "data_type": "tweet",
      "data": {
        "text": "Tesla is the future!",
        "user": {"username": "elonmusk"}
      },
      "created_at": "2024-01-15T10:30:00Z"
    }
  ],
  "total": 1,
  "page": 1,
  "size": 50,
  "pages": 1
}
```

#### 1.11 导出任务结果

**POST** `/tasks/export/{task_id}`

导出指定任务的结果为 JSON 或 CSV 格式。

**路径参数:**
- `task_id` (string): 任务ID

**查询参数:**
- `format` (string, optional): 导出格式，`json` 或 `csv`，默认 `json`

**响应 (JSON 格式):**
```json
{
  "data": [
    {
      "id": "result-123",
      "data": {"text": "Hello world!"},
      "created_at": "2024-01-15T10:30:00Z"
    }
  ],
  "total": 1
}
```

**响应 (CSV 格式):**
```
Content-Type: text/csv
Content-Disposition: attachment; filename=task_abc123_results.csv

id,data.text,created_at
result-123,Hello world!,2024-01-15T10:30:00Z
```

### 2. 任务执行管理

#### 2.1 获取任务执行记录

**GET** `/task-executions`

获取任务执行记录列表。

**查询参数:**
- `page` (int, optional): 页码，默认 1
- `size` (int, optional): 每页数量，默认 20
- `task_id` (string, optional): 按任务ID筛选
- `status` (string, optional): 按执行状态筛选

**响应 (200 OK):**
```json
{
  "items": [
    {
      "id": "exec-123",
      "task_id": "task-abc123",
      "account_id": "account-123",
      "proxy_id": "proxy-456",
      "status": "COMPLETED",
      "error_message": null,
      "started_at": "2024-01-15T10:30:00Z",
      "completed_at": "2024-01-15T10:35:00Z",
      "duration": 300.5,
      "result_count": 50
    }
  ],
  "total": 1,
  "page": 1,
  "size": 20,
  "pages": 1
}
```

#### 2.2 获取执行详情

**GET** `/task-executions/{execution_id}`

获取指定执行记录的详细信息。

**路径参数:**
- `execution_id` (string): 执行记录ID

**响应 (200 OK):**
```json
{
  "id": "exec-123",
  "task_id": "task-abc123",
  "account_id": "account-123",
  "proxy_id": "proxy-456",
  "status": "COMPLETED",
  "error_message": null,
  "started_at": "2024-01-15T10:30:00Z",
  "completed_at": "2024-01-15T10:35:00Z",
  "duration": 300.5,
  "result_count": 50
}
```

#### 2.3 获取任务执行历史

**GET** `/task-executions/task/{task_id}`

获取指定任务的所有执行记录。

**路径参数:**
- `task_id` (string): 任务ID

**响应 (200 OK):**
```json
[
  {
    "id": "exec-123",
    "task_id": "task-abc123",
    "status": "COMPLETED",
    "started_at": "2024-01-15T10:30:00Z",
    "completed_at": "2024-01-15T10:35:00Z",
    "duration": 300.5,
    "result_count": 50
  },
  {
    "id": "exec-124",
    "task_id": "task-abc123",
    "status": "FAILED",
    "error_message": "Account suspended",
    "started_at": "2024-01-15T09:00:00Z",
    "completed_at": "2024-01-15T09:01:00Z",
    "duration": 60.0,
    "result_count": 0
  }
]
```

## 状态码说明

- `200 OK` - 请求成功
- `201 Created` - 资源创建成功
- `400 Bad Request` - 请求参数错误
- `404 Not Found` - 资源不存在
- `422 Unprocessable Entity` - 请求数据验证失败
- `500 Internal Server Error` - 服务器内部错误

## 任务类型和参数

### USER_TWEETS - 用户推文采集
```json
{
  "username": "string",
  "limit": "integer",
  "include_replies": "boolean",
  "include_retweets": "boolean"
}
```

### USER_INFO - 用户信息采集
```json
{
  "username": "string"
}
```

### KEYWORD_SEARCH - 关键词搜索
```json
{
  "query": "string",
  "limit": "integer",
  "lang": "string"
}
```

### HASHTAG_SEARCH - 话题搜索
```json
{
  "hashtag": "string",
  "limit": "integer"
}
```

### USER_FOLLOWERS - 用户粉丝采集
```json
{
  "username": "string",
  "limit": "integer"
}
```

### USER_FOLLOWING - 用户关注采集
```json
{
  "username": "string",
  "limit": "integer"
}
```

## 错误处理

所有错误响应都遵循以下格式：

```json
{
  "detail": "错误描述信息"
}
```

或者对于验证错误：

```json
{
  "detail": [
    {
      "loc": ["field_name"],
      "msg": "错误信息",
      "type": "error_type"
    }
  ]
}
```

## 使用建议

1. **分页查询**: 对于大量数据，建议使用分页参数控制返回数据量
2. **状态监控**: 定期检查任务状态，及时处理失败任务
3. **错误处理**: 实现适当的错误处理和重试机制
4. **资源管理**: 合理分配账号和代理资源，避免资源冲突
5. **结果导出**: 对于大量结果，建议使用导出功能而不是 API 分页获取 