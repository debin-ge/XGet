# XGet 微服务架构设计文档

## 1. 项目概述

XGet是一个基于微服务架构的社交媒体数据采集和分析平台，专注于Twitter(X)数据的获取、处理和分析。该系统通过分布式架构设计，提供高可用、高扩展性的数据采集服务，并对外提供标准化的API接口。

### 1.1 项目目标

- 构建可扩展的社交媒体数据采集平台
- 支持多种登录方式和账号管理
- 提供高性能的数据采集和处理能力
- 支持分布式部署和水平扩展
- 提供标准化的RESTful API和GraphQL接口
- 实现完善的监控、日志和告警系统

## 2. 系统架构

### 2.1 整体架构图

```
┌───────────────────┐     ┌───────────────────┐
│   API Gateway     │     │  用户管理服务       │
│  (FastAPI)        │────▶│  (User Service)   │
└─────────┬─────────┘     └───────────────────┘
          │
          ▼
┌───────────────────┐     ┌───────────────────┐     ┌───────────────────┐
│  账号管理服务 　    │     │  代理管理服务       │     │  数据采集服务       │
│ (Account Service) │────▶│  (Proxy Service)  │────▶│ (Scraper Service) │
└───────────────────┘     └───────────────────┘     └─────────┬─────────┘
          │                         │                         │
          │                         ▼                         │
          │               ┌───────────────────┐               │
          │               │  前端服务          │               │
          │               │ (Frontend Service)│               │
          │               └───────────────────┘               │
          │                                                   │
          ▼                                                   ▼
┌───────────────────┐     ┌───────────────────┐     ┌───────────────────┐
│  数据存储服务       │     │  数据处理服务       │     │  监控告警服务       │
│ (Storage Service) │◀─── │(Processing Service)│     │(Monitoring Service)│
└───────────────────┘     └───────────────────┘     └───────────────────┘
```

### 2.2 微服务组件

#### ✅ 已完全实现并运行的服务

1. **API网关服务 (API Gateway)** - 端口 8000
   - 请求路由和负载均衡
   - 请求限流和熔断
   - API版本管理
   - JWT认证中间件

2. **账号管理服务 (Account Service)** - 端口 8001
   - Twitter账号管理
   - Google账号管理
   - 账号状态监控
   - Cookie和会话管理
   - Playwright自动化集成

3. **代理管理服务 (Proxy Service)** - 端口 8002
   - 代理池管理
   - 代理质量监控
   - 代理自动轮换
   - 地理位置分布管理

4. **数据采集服务 (Scraper Service)** - 端口 8003
   - Twitter数据采集任务管理
   - 自动化浏览器管理
   - 采集任务调度
   - Kafka消息队列集成
   - MongoDB数据存储

5. **用户管理服务 (User Service)** - 端口 8007
   - 用户注册和管理
   - JWT令牌管理
   - 用户认证和授权
   - Redis会话管理

6. **前端服务 (Frontend Service)** - 端口 3000
   - Vue.js 3前端界面
   - 用户仪表板
   - 任务管理界面
   - 实时状态监控

#### ⏳ 计划中的服务

7. **数据处理服务 (Processing Service)** - 端口 8004
   - 数据清洗和标准化
   - 数据转换和结构化
   - Kafka异步处理
   - 数据去重和合并

8. **数据存储服务 (Storage Service)** - 端口 8005
   - 多后端存储管理 (MongoDB, S3兼容存储, Elasticsearch)
   - 数据索引和查询优化
   - 数据生命周期管理

#### ⏳ 计划中的服务

9. **数据分析服务 (Analytics Service)**
   - 数据统计和聚合
   - 趋势分析
   - 情感分析
   - 用户画像

10. **监控告警服务 (Monitoring Service)**
    - 系统监控
    - 服务健康检查
    - 性能指标收集
    - 告警通知

## 3. 技术栈选型

### 3.1 基础设施

- **容器化**: Docker + Docker Compose
- **服务编排**: 内置服务发现和负载均衡

### 3.2 后端技术

- **编程语言**: Python 3.12+
- **API框架**: FastAPI (所有服务)
- **异步框架**: asyncio + asyncpg
- **消息队列**: Kafka + aiokafka
- **缓存**: Redis
- **数据库**:
  - **关系型**: PostgreSQL (所有服务的元数据存储)
  - **文档型**: MongoDB (采集结果数据存储)

### 3.3 前端技术

- **框架**: Vue.js 3 + TypeScript
- **UI组件库**: Element Plus
- **构建工具**: Vite
- **状态管理**: Pinia

### 3.4 自动化技术

- **浏览器自动化**: Playwright
- **HTTP客户端**: httpx
- **数据采集**: 自定义采集引擎

### 3.5 监控和工具

- **Kafka管理**: Kafdrop (端口 9000)
- **数据库管理**: 原生客户端工具
- **API文档**: Swagger/OpenAPI (集成到每个服务)

### 3.6 服务端口映射

| 服务名称 | 容器端口 | 主机端口 | 状态 |
|---------|---------|---------|------|
| API网关服务 | 8000 | 8000 | ✅ 运行中 |
| 账号管理服务 | 8000 | 8001 | ✅ 运行中 |
| 代理管理服务 | 8000 | 8002 | ✅ 运行中 |
| 数据采集服务 | 8000 | 8003 | ✅ 运行中 |
| 用户管理服务 | 8000 | 8007 | ✅ 运行中 |
| 前端服务 | 3000 | 3000 | ✅ 运行中 |
| 数据处理服务 | 8000 | 8004 | ⏳ 计划中 |
| 数据存储服务 | 8000 | 8005 | ⏳ 计划中 |
| PostgreSQL | 5432 | 5432 | ✅ 运行中 |
| MongoDB | 27017 | 27017 | ✅ 运行中 |
| Redis | 6379 | 6379 | ✅ 运行中 |
| Kafka | 9092 | 9092 | ✅ 运行中 |
| Kafdrop | 9000 | 9000 | ✅ 运行中 |

## 4. 详细服务设计

### 4.1 账号管理服务 (Account Service)

#### 功能描述
管理Twitter和Google账号，提供账号注册、登录、状态监控和Cookie管理等功能。

#### API端点
- `POST /accounts` - 创建新账号
- `GET /accounts` - 获取账号列表
- `GET /accounts/{id}` - 获取账号详情
- `PUT /accounts/{id}` - 更新账号信息
- `DELETE /accounts/{id}` - 删除账号
- `POST /accounts/{id}/login` - 账号登录
- `GET /accounts/{id}/status` - 获取账号状态
- `POST /accounts/import` - 批量导入账号

#### 数据模型
```json
{
  "id": "uuid",
  "username": "string",
  "password": "string (encrypted)",
  "email": "string",
  "email_password": "string (encrypted)",
  "login_method": "enum (TWITTER, GOOGLE)",
  "proxy_id": "uuid",
  "cookies": "json",
  "headers": "json",
  "user_agent": "string",
  "active": "boolean",
  "last_used": "datetime",
  "error_msg": "string",
  "is_deleted": "boolean",
  "deleted_at": "datetime",
  "created_at": "datetime",
  "updated_at": "datetime"
}
```

### 4.2 用户管理服务 (User Service)

#### 功能描述
管理用户账户、认证授权、角色权限和用户会话。

#### API端点
- `POST /users/register` - 用户注册
- `POST /users/login` - 用户登录
- `POST /users/logout` - 用户登出
- `GET /users/profile` - 获取用户信息
- `PUT /users/profile` - 更新用户信息
- `GET /users/sessions` - 获取用户会话列表
- `DELETE /users/sessions/{id}` - 终止用户会话
- `GET /users/roles` - 获取用户角色
- `POST /users/roles` - 分配用户角色

#### 数据模型
```json
{
  "id": "uuid",
  "username": "string",
  "email": "string",
  "password_hash": "string",
  "first_name": "string",
  "last_name": "string",
  "phone": "string",
  "avatar_url": "string",
  "is_active": "boolean",
  "is_verified": "boolean",
  "is_superuser": "boolean",
  "last_login": "datetime",
  "failed_login_attempts": "integer",
  "locked_until": "datetime",
  "preferences": "json",
  "timezone": "string",
  "language": "string",
  "created_at": "datetime",
  "updated_at": "datetime"
}
```

### 4.3 代理管理服务 (Proxy Service)

#### 功能描述
管理代理池，提供代理质量监控、自动轮换和地理位置分布管理等功能。

#### API端点
- `POST /proxies` - 添加新代理
- `GET /proxies` - 获取代理列表
- `GET /proxies/{id}` - 获取代理详情
- `PUT /proxies/{id}` - 更新代理信息
- `DELETE /proxies/{id}` - 删除代理
- `GET /proxies/available` - 获取可用代理
- `POST /proxies/check` - 检查代理可用性
- `POST /proxies/import` - 批量导入代理

#### 数据模型
```json
{
  "id": "uuid",
  "type": "string",
  "ip": "string",
  "port": "integer",
  "username": "string",
  "password": "string (encrypted)",
  "country": "string",
  "city": "string",
  "isp": "string",
  "latency": "integer",
  "success_rate": "float",
  "last_check": "datetime",
  "status": "enum (ACTIVE, INACTIVE, CHECKING)",
  "created_at": "datetime",
  "updated_at": "datetime"
}
```

### 4.3 数据采集服务 (Scraper Service)

#### 功能描述
管理Twitter数据采集任务，提供自动化浏览器管理、任务调度和状态监控等功能。

#### API端点
- `POST /tasks` - 创建采集任务
- `GET /tasks` - 获取任务列表
- `GET /tasks/{id}` - 获取任务详情
- `PUT /tasks/{id}` - 更新任务信息
- `DELETE /tasks/{id}` - 删除任务
- `POST /tasks/{id}/start` - 启动任务
- `POST /tasks/{id}/stop` - 停止任务
- `GET /tasks/{id}/status` - 获取任务状态
- `GET /tasks/{id}/results` - 获取任务结果

#### 数据采集类型
- 用户信息采集
- 用户推文采集
- 关键词搜索
- 话题采集
- 用户关注/粉丝采集

#### 数据模型
```json
{
  "id": "uuid",
  "task_name": "string",
  "describe": "string",
  "task_type": "enum (USER_INFO, USER_TWEETS, SEARCH, TOPIC, FOLLOWERS)",
  "parameters": "json",
  "account_id": "uuid",
  "proxy_id": "uuid",
  "user_id": "uuid",
  "status": "enum (PENDING, RUNNING, COMPLETED, FAILED)",
  "progress": "float",
  "result_count": "integer",
  "error_message": "string",
  "created_at": "datetime",
  "updated_at": "datetime",
  "started_at": "datetime",
  "completed_at": "datetime"
}
```

#### 数据存储策略
- **任务元数据**: 存储在PostgreSQL中（任务信息、执行记录等）
- **采集结果**: 存储在MongoDB中（推文、用户信息等非结构化数据）
- **任务状态**: 实时更新到PostgreSQL数据库

### 4.4 数据存储服务 (Storage Service)

#### 功能描述
管理数据存储，提供结构化和非结构化数据存储、索引和查询优化等功能。

#### API端点
- `POST /data` - 存储数据
- `GET /data` - 查询数据
- `GET /data/{id}` - 获取数据详情
- `PUT /data/{id}` - 更新数据
- `DELETE /data/{id}` - 删除数据
- `POST /data/batch` - 批量存储数据
- `GET /data/search` - 搜索数据

#### 数据模型
根据不同的数据类型（用户、推文、话题等）定义不同的数据模型。

## 5. 系统集成

### 5.1 服务间通信

- **同步通信**: RESTful API, gRPC
- **异步通信**: 消息队列 (RabbitMQ/Kafka)
- **事件驱动**: 发布/订阅模式

### 5.2 数据流

1. 用户通过API网关发起请求
2. 认证服务验证用户身份和权限
3. 请求路由到相应的微服务
4. 微服务处理请求并返回结果
5. 数据采集服务从Twitter获取数据
6. 数据处理服务清洗和转换数据
7. 数据存储服务保存数据
8. 数据分析服务分析数据并生成报告

### 5.3 故障处理

- **服务降级**: 当依赖服务不可用时，提供降级功能
- **断路器模式**: 防止级联故障
- **重试机制**: 自动重试失败的请求
- **幂等性**: 确保重复请求不会导致数据不一致

## 6. API文档

详细的API文档将使用Swagger/OpenAPI规范生成，并通过API网关提供访问。

## 7. 总结

XGet微服务架构设计旨在构建一个高可用、高扩展性的社交媒体数据采集和分析平台。通过微服务架构，系统可以实现各个组件的独立开发、部署和扩展，提高系统的可维护性和可靠性。同时，系统提供标准化的API接口，方便第三方系统集成和使用。 