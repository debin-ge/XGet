# XGet Analytics Service

数据分析服务是XGet平台的核心统计分析组件，专注于四个核心数据领域的深度分析。

## 核心功能

### 1. 账户使用情况分析
- 实时监控账户活跃度、登录成功率、性能指标
- 历史趋势分析和健康度评分

### 2. 代理质量分析  
- 实时代理成功率、响应时间监控
- 地域性能对比和稳定性评估

### 3. 任务执行分析
- 任务完成率统计和执行效率分析
- 错误诊断和资源优化建议

### 4. 任务结果分析
- 数据质量评估和采集效率分析
- 内容洞察和特征分析

## 技术架构

- **Web框架**: FastAPI + Uvicorn
- **数据库**: PostgreSQL (统计结果存储)
- **缓存**: Redis
- **数据源**: PostgreSQL业务数据库 + MongoDB采集数据
- **异步处理**: 原生async/await (无后台任务调度器)

## 快速开始

### Docker启动 (推荐)

```bash
# 启动所有服务（包括分析服务）
docker-compose up -d

# 仅启动分析服务
docker-compose up -d analytics-service

# 查看服务日志
docker-compose logs analytics-service
```

### 开发模式

```bash
# 复制环境变量文件（可选，配置已在docker-compose中）
cp .env.example .env

# 安装依赖
pip install -r requirements.txt

# 启动开发服务器
uvicorn app.main:app --reload --host 0.0.0.0 --port 8005
```

## API接口

### 实时数据接口
- `GET /api/v1/analytics/accounts/realtime` - 账户实时统计
- `GET /api/v1/analytics/proxies/realtime` - 代理质量实时监控  
- `GET /api/v1/analytics/tasks/realtime` - 任务执行实时状态

### 历史统计接口
- `GET /api/v1/analytics/accounts/history` - 账户使用历史
- `GET /api/v1/analytics/proxies/history` - 代理性能历史
- `GET /api/v1/analytics/tasks/history` - 任务效率历史

### 管理接口
- `GET /api/v1/analytics/metrics` - 获取指标配置
- `POST /api/v1/analytics/metrics` - 创建统计指标
- `PUT /api/v1/analytics/metrics/{metric_id}` - 更新指标配置

### 健康检查
- `GET /health` - 服务健康状态

## 数据库架构

### 核心表结构

1. **analytics_metrics** - 统计指标配置表
2. **realtime_stats** - 实时统计结果表  
3. **historical_aggregates** - 历史聚合表

## 环境变量配置

所有配置已通过Docker Compose环境变量设置：

```yaml
# 数据库配置
POSTGRES_SERVER=postgres
POSTGRES_USER=postgres
POSTGRES_PASSWORD=${POSTGRES_PASSWORD:-postgres}
POSTGRES_DB=analytics_db

# Redis缓存配置
REDIS_URL=redis://redis:6379/0

# MongoDB数据源配置
MONGODB_URI=mongodb://mongodb:27017
MONGODB_DB=scraper_db

# 微服务地址配置
ACCOUNT_SERVICE_URL=http://account-service:8000
PROXY_SERVICE_URL=http://proxy-service:8000
SCRAPER_SERVICE_URL=http://scraper-service:8000
USER_SERVICE_URL=http://user-service:8000

# 分析服务配置
CACHE_TTL=300
```

## 项目结构

```
analytics-service/
├── app/
│   ├── api/           # API路由和端点
│   ├── core/          # 配置和共享工具
│   ├── db/            # 数据库连接和会话管理
│   ├── models/        # SQLAlchemy ORM数据模型
│   ├── schemas/       # Pydantic数据验证模型
│   ├── services/      # 业务逻辑服务层
│   └── main.py        # FastAPI应用入口
├── tests/             # 测试文件
├── requirements.txt   # Python依赖包
├── Dockerfile         # Docker容器配置
├── .env.example       # 环境变量示例
└── README.md          # 项目说明文档
```

## 开发指南

### 添加新的分析指标

1. 在 `app/models/analytics.py` 中定义数据模型
2. 在 `app/schemas/analytics.py` 中创建Pydantic模型
3. 在 `app/services/` 中实现业务逻辑
4. 在 `app/api/v1/endpoints/` 中添加API端点

### 使用缓存装饰器

```python
from app.core.cache import cache_response

@cache_response(expire=300, key_prefix="analytics:custom")
async def get_custom_analytics():
    # 业务逻辑
    return result
```

## 性能目标

- 实时查询: < 200ms
- 历史查询: < 1s (7天内数据)  
- 批量报表: < 30s (百万级数据)
- 并发查询: 100+ 并发请求
- 缓存命中率: > 90%

## 监控和日志

- 健康检查端点: `GET /health`
- 结构化日志输出
- 请求ID追踪
- 服务状态监控

## 相关服务

- [Account Service](../account-service/) - 账户管理服务
- [Proxy Service](../proxy-service/) - 代理管理服务  
- [Scraper Service](../scraper-service/) - 数据采集服务
- [User Service](../user-service/) - 用户管理服务
- [API Gateway](../api-gateway/) - API网关服务

## 部署信息

- **服务端口**: 8005 (主机) -> 8000 (容器)
- **健康检查**: http://localhost:8005/health
- **API文档**: http://localhost:8005/docs (开发模式)
- **依赖服务**: PostgreSQL, Redis, MongoDB, 其他微服务

## 故障排除

### 常见问题

1. **数据库连接失败**: 检查PostgreSQL服务状态和连接配置
2. **Redis连接失败**: 检查Redis服务状态和URL配置
3. **外部服务不可达**: 验证其他微服务的URL配置
4. **缓存不生效**: 检查Redis连接和缓存配置

### 日志查看

```bash
docker-compose logs analytics-service
docker-compose logs analytics-service --tail=100 --follow
```

## 版本信息

- **服务版本**: 1.0.0
- **FastAPI版本**: 0.104.1
- **Python版本**: 3.11
- **最后更新**: 2025-09-01