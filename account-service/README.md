# XGet 账号管理服务 (Account Service)

账号管理服务是XGet微服务架构中的核心组件之一，负责管理社交媒体账号的创建、更新、删除和登录操作。该服务提供了完整的API接口，支持Twitter和Google两种登录方式，并与代理管理服务集成，实现高效的账号管理和自动化登录。

## 功能特点

- **账号管理**：创建、查询、更新和删除社交媒体账号
- **多种登录方式**：支持Twitter原生登录和Google账号登录
- **自动化登录**：使用Playwright进行自动化登录，获取并保存cookies
- **代理集成**：与代理管理服务集成，支持指定代理或自动选择可用代理
- **登录历史记录**：详细记录每次登录尝试，包括成功/失败状态、响应时间等信息
- **异步登录支持**：支持同步和异步登录模式，提高系统响应速度
- **错误处理和日志**：完善的错误处理和日志记录机制

## 技术栈

- **后端框架**：FastAPI
- **数据库**：PostgreSQL
- **ORM**：SQLAlchemy
- **自动化工具**：Playwright
- **API文档**：Swagger UI / ReDoc

## 安装和运行

### 使用Docker

```bash
# 在项目根目录下运行
docker-compose -f docker/docker-compose.yml up -d account-service
```

### 本地开发

```bash
# 安装依赖
pip install -r requirements.txt

# 运行服务
cd xget/account-service
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

## 环境变量

| 变量名 | 描述 | 默认值 |
|--------|------|--------|
| POSTGRES_SERVER | PostgreSQL服务器地址 | postgres |
| POSTGRES_USER | PostgreSQL用户名 | postgres |
| POSTGRES_PASSWORD | PostgreSQL密码 | postgres |
| POSTGRES_DB | PostgreSQL数据库名 | account_db |
| DATABASE_URL | 数据库连接URL(可选) | - |
| REDIS_URL | Redis连接URL | redis://redis:6379/0 |
| PROXY_SERVICE_URL | 代理服务URL | http://proxy-service:8000 |

## API接口

### 账号管理

#### 创建账号

```
POST /api/v1/accounts
```

请求体:
```json
{
  "username": "twitter_user",
  "password": "secure_password",
  "email": "user@example.com",
  "email_password": "email_password",
  "login_method": "TWITTER"
}
```

响应:
```json
{
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "username": "twitter_user",
  "email": "user@example.com",
  "login_method": "TWITTER",
  "active": false,
  "created_at": "2023-06-01T12:00:00",
  "updated_at": "2023-06-01T12:00:00"
}
```

#### 获取账号列表

```
GET /api/v1/accounts?skip=0&limit=100&active=true
```

响应:
```json
[
  {
    "id": "550e8400-e29b-41d4-a716-446655440000",
    "username": "twitter_user",
    "email": "user@example.com",
    "login_method": "TWITTER",
    "active": true,
    "proxy_id": "550e8400-e29b-41d4-a716-446655440001",
    "last_used": "2023-06-01T12:30:00",
    "created_at": "2023-06-01T12:00:00",
    "updated_at": "2023-06-01T12:30:00"
  }
]
```

#### 获取单个账号

```
GET /api/v1/accounts/{account_id}
```

响应:
```json
{
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "username": "twitter_user",
  "email": "user@example.com",
  "login_method": "TWITTER",
  "active": true,
  "proxy_id": "550e8400-e29b-41d4-a716-446655440001",
  "last_used": "2023-06-01T12:30:00",
  "created_at": "2023-06-01T12:00:00",
  "updated_at": "2023-06-01T12:30:00"
}
```

#### 更新账号

```
PUT /api/v1/accounts/{account_id}
```

请求体:
```json
{
  "email": "new_email@example.com",
  "active": false
}
```

响应:
```json
{
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "username": "twitter_user",
  "email": "new_email@example.com",
  "login_method": "TWITTER",
  "active": false,
  "proxy_id": "550e8400-e29b-41d4-a716-446655440001",
  "last_used": "2023-06-01T12:30:00",
  "created_at": "2023-06-01T12:00:00",
  "updated_at": "2023-06-01T13:00:00"
}
```

#### 删除账号

```
DELETE /api/v1/accounts/{account_id}
```

响应:
```json
{
  "message": "Account deleted successfully"
}
```

#### 登录账号

```
POST /api/v1/accounts/{account_id}/login
```

请求体:
```json
{
  "proxy_id": "550e8400-e29b-41d4-a716-446655440001",
  "async_login": false
}
```

响应:
```json
{
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "username": "twitter_user",
  "active": true,
  "login_successful": true,
  "cookies_obtained": true,
  "last_used": "2023-06-01T13:30:00",
  "message": "登录成功"
}
```

### 登录历史记录

#### 获取登录历史列表

```
GET /api/v1/login-history?skip=0&limit=100&account_id={account_id}&status=SUCCESS
```

响应:
```json
[
  {
    "id": "550e8400-e29b-41d4-a716-446655440002",
    "account_id": "550e8400-e29b-41d4-a716-446655440000",
    "proxy_id": "550e8400-e29b-41d4-a716-446655440001",
    "login_time": "2023-06-01T13:30:00",
    "status": "SUCCESS",
    "cookies_count": 15,
    "response_time": 5230
  }
]
```

#### 获取单个账号的登录历史

```
GET /api/v1/login-history/account/{account_id}?skip=0&limit=10
```

响应:
```json
[
  {
    "id": "550e8400-e29b-41d4-a716-446655440002",
    "account_id": "550e8400-e29b-41d4-a716-446655440000",
    "proxy_id": "550e8400-e29b-41d4-a716-446655440001",
    "login_time": "2023-06-01T13:30:00",
    "status": "SUCCESS",
    "cookies_count": 15,
    "response_time": 5230
  },
  {
    "id": "550e8400-e29b-41d4-a716-446655440003",
    "account_id": "550e8400-e29b-41d4-a716-446655440000",
    "proxy_id": "550e8400-e29b-41d4-a716-446655440001",
    "login_time": "2023-06-01T12:30:00",
    "status": "FAILED",
    "error_msg": "登录失败，未获取到cookies",
    "cookies_count": 0,
    "response_time": 4500
  }
]
```

## 使用示例

### 创建账号并登录

```python
import requests
import json

# API基础URL
base_url = "http://localhost:8000/api/v1"

# 创建账号
account_data = {
    "username": "twitter_user",
    "password": "secure_password",
    "email": "user@example.com",
    "email_password": "email_password",
    "login_method": "TWITTER"
}

response = requests.post(f"{base_url}/accounts", json=account_data)
account = response.json()
account_id = account["id"]

print(f"账号创建成功: {account_id}")

# 登录账号
login_data = {
    "async_login": False
}

response = requests.post(f"{base_url}/accounts/{account_id}/login", json=login_data)
login_result = response.json()

print(f"登录结果: {login_result['message']}")
print(f"登录状态: {'成功' if login_result['login_successful'] else '失败'}")
print(f"获取到cookies: {'是' if login_result['cookies_obtained'] else '否'}")
```

### 获取活跃账号列表

```python
import requests

# API基础URL
base_url = "http://localhost:8000/api/v1"

# 获取活跃账号
response = requests.get(f"{base_url}/accounts?active=true&limit=10")
accounts = response.json()

print(f"找到 {len(accounts)} 个活跃账号:")
for account in accounts:
    print(f"- {account['username']} (上次使用: {account['last_used']})")
```

### 查看账号登录历史

```python
import requests

# API基础URL
base_url = "http://localhost:8000/api/v1"
account_id = "550e8400-e29b-41d4-a716-446655440000"

# 获取账号登录历史
response = requests.get(f"{base_url}/login-history/account/{account_id}?limit=5")
history = response.json()

print(f"账号登录历史:")
for entry in history:
    status = "成功" if entry["status"] == "SUCCESS" else "失败"
    time = entry["login_time"]
    msg = f"- {time}: 登录{status}"
    
    if entry["status"] == "SUCCESS":
        msg += f", 获取到 {entry['cookies_count']} 个cookies"
        msg += f", 响应时间: {entry['response_time']}ms"
    else:
        msg += f", 错误: {entry['error_msg']}"
    
    print(msg)
```

## 数据模型

### Account

| 字段 | 类型 | 描述 |
|------|------|------|
| id | String | 主键，UUID |
| username | String | 用户名 |
| password | String | 密码 |
| email | String | 邮箱 |
| email_password | String | 邮箱密码 |
| login_method | String | 登录方式 (TWITTER, GOOGLE) |
| proxy_id | String | 代理ID |
| cookies | JSON | 登录后的cookies |
| headers | JSON | 自定义请求头 |
| user_agent | String | 用户代理 |
| active | Boolean | 是否活跃 |
| last_used | DateTime | 上次使用时间 |
| error_msg | String | 错误信息 |
| created_at | DateTime | 创建时间 |
| updated_at | DateTime | 更新时间 |

### LoginHistory

| 字段 | 类型 | 描述 |
|------|------|------|
| id | String | 主键，UUID |
| account_id | String | 账号ID |
| proxy_id | String | 代理ID |
| login_time | DateTime | 登录时间 |
| status | String | 状态 (SUCCESS, FAILED) |
| error_msg | String | 错误信息 |
| cookies_count | Integer | cookies数量 |
| response_time | Integer | 响应时间(毫秒) |

## 开发和贡献

1. Fork项目
2. 创建特性分支 (`git checkout -b feature/amazing-feature`)
3. 提交更改 (`git commit -m 'Add some amazing feature'`)
4. 推送到分支 (`git push origin feature/amazing-feature`)
5. 创建Pull Request
