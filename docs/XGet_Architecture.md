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
┌───────────────────┐     ┌───────────────────┐     ┌───────────────────┐
│   API Gateway     │     │  认证授权服务     │     │  用户管理服务     │
│  (Kong/Traefik)   │────▶│  (Auth Service)   │────▶│  (User Service)   │
└─────────┬─────────┘     └───────────────────┘     └───────────────────┘
          │
          ▼
┌───────────────────┐     ┌───────────────────┐     ┌───────────────────┐
│  账号管理服务     │     │  代理管理服务     │     │  数据采集服务     │
│ (Account Service) │────▶│  (Proxy Service)  │────▶│ (Scraper Service) │
└───────────────────┘     └───────────────────┘     └─────────┬─────────┘
                                                              │
                                                              ▼
┌───────────────────┐     ┌───────────────────┐     ┌───────────────────┐
│  数据处理服务     │     │  数据存储服务     │     │  数据分析服务     │
│(Processing Service)│◀───│ (Storage Service) │◀───│(Analytics Service) │
└───────────────────┘     └───────────────────┘     └───────────────────┘
          │                         │                         │
          └─────────────────────────┼─────────────────────────┘
                                    ▼
                          ┌───────────────────┐
                          │  监控告警服务     │
                          │(Monitoring Service)│
                          └───────────────────┘
```

### 2.2 微服务组件

1. **API网关服务 (API Gateway)**
   - 请求路由和负载均衡
   - 请求限流和熔断
   - API版本管理
   - 请求/响应转换

2. **认证授权服务 (Auth Service)**
   - 用户认证和授权
   - JWT令牌管理
   - OAuth2.0集成
   - 权限控制

3. **用户管理服务 (User Service)**
   - 用户注册和管理
   - 用户权限和角色管理
   - 用户配置和偏好设置

4. **账号管理服务 (Account Service)**
   - Twitter账号管理
   - Google账号管理
   - 账号状态监控
   - 账号轮换策略

5. **代理管理服务 (Proxy Service)**
   - 代理池管理
   - 代理质量监控
   - 代理自动轮换
   - 地理位置分布管理

6. **数据采集服务 (Scraper Service)**
   - Twitter数据采集
   - 自动化浏览器管理
   - 采集任务调度
   - 采集状态监控

7. **数据处理服务 (Processing Service)**
   - 数据清洗和标准化
   - 数据转换和结构化
   - 数据去重和合并

8. **数据存储服务 (Storage Service)**
   - 结构化数据存储
   - 非结构化数据存储
   - 数据索引和查询优化
   - 数据备份和恢复

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

- **容器化**: Docker
- **容器编排**: Kubernetes
- **服务网格**: Istio
- **CI/CD**: GitLab CI/Jenkins
- **配置管理**: HashiCorp Vault, ConfigMap

### 3.2 后端技术

- **编程语言**: Python 3.12+
- **API框架**: FastAPI
- **异步框架**: asyncio
- **消息队列**: RabbitMQ/Kafka
- **缓存**: Redis
- **数据库**:
  - **关系型**: PostgreSQL
  - **文档型**: MongoDB
  - **搜索引擎**: Elasticsearch

### 3.3 自动化技术

- **浏览器自动化**: Playwright
- **数据采集库**: twscrape, httpx

### 3.4 监控和日志

- **监控**: Prometheus, Grafana
- **日志**: ELK Stack (Elasticsearch, Logstash, Kibana)
- **分布式追踪**: Jaeger

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
  "created_at": "datetime",
  "updated_at": "datetime"
}
```

### 4.2 代理管理服务 (Proxy Service)

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
  "task_type": "enum (USER_INFO, USER_TWEETS, SEARCH, TOPIC, FOLLOWERS)",
  "parameters": "json",
  "account_id": "uuid",
  "proxy_id": "uuid",
  "status": "enum (PENDING, RUNNING, COMPLETED, FAILED)",
  "progress": "float",
  "result_count": "integer",
  "error_msg": "string",
  "created_at": "datetime",
  "updated_at": "datetime",
  "started_at": "datetime",
  "completed_at": "datetime"
}
```

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