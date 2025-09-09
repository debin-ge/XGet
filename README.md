# XGet 微服务数据采集平台

XGet是一个基于微服务架构的社交媒体数据采集和分析平台，专注于Twitter(X)数据的获取、处理和分析。该系统通过分布式架构设计，提供高可用、高扩展性的数据采集服务，并对外提供标准化的API接口。

## 🚀 当前实现状态

### ✅ 已完全实现并运行的服务
- **API网关服务** (端口 8000) - 请求路由、认证和限流
- **账号管理服务** (端口 8001) - Twitter/Google账号管理
- **代理管理服务** (端口 8002) - 代理池管理和监控
- **数据采集服务** (端口 8003) - Twitter数据采集任务管理
- **用户管理服务** (端口 8007) - 用户认证和授权
- **前端服务** (端口 3000) - Vue.js用户界面

### ⏳ 计划中的服务
- **数据处理服务** (端口 8004) - 数据清洗和转换
- **数据存储服务** (端口 8005) - 多后端存储管理

## 🛠️ 技术栈

- **后端框架**: FastAPI + Python 3.12+
- **数据库**: PostgreSQL (元数据) + MongoDB (采集数据)
- **缓存**: Redis
- **消息队列**: Kafka + aiokafka
- **前端**: Vue.js 3 + TypeScript + Element Plus
- **容器化**: Docker + Docker Compose
- **自动化**: Playwright + httpx

## ⚡ 快速开始

### 前置条件
- Docker 和 Docker Compose
- Python 3.12+ (用于本地开发)

### 安装和运行

1. **克隆项目**
   ```bash
   git clone https://github.com/debin-ge/XGet.git
   cd XGet
   ```

2. **启动所有服务**
   ```bash
   docker-compose up -d
   ```

3. **访问应用**
   - 前端界面: http://localhost:3000
   - API网关: http://localhost:8000
   - Kafka管理界面: http://localhost:9000

4. **检查服务状态**
   ```bash
   curl http://localhost:8000/health
   ```


## 📁 项目结构

```
XGet/
├── api-gateway/           # API网关服务 (端口 8000)
├── account-service/       # 账号管理服务 (端口 8001)
├── proxy-service/         # 代理管理服务 (端口 8002)
├── scraper-service/       # 数据采集服务 (端口 8003)
├── user-service/          # 用户管理服务 (端口 8007)
├── frontend-service/      # 前端服务 (端口 3000)
├── processing-service/    # 数据处理服务 (端口 8004) - 计划中
├── storage-service/       # 数据存储服务 (端口 8005) - 计划中
├── monitoring-service/    # 监控服务 - 计划中
├── docs/                  # 项目文档
└── docker-compose.yml     # Docker编排配置
```

## 📚 文档

- [详细架构设计文档](./docs/XGet_Architecture.md)
- [开发指南](./docs/XGet_Implementation_Guide.md)
- [API接口文档](http://localhost:8000/docs) (运行后访问)

## 🔧 开发命令

### Docker命令
```bash
# 启动所有服务
docker-compose up -d

# 停止所有服务
docker-compose down

# 查看服务日志
docker-compose logs [service-name]

# 重建特定服务
docker-compose up -d --build [service-name]
```

### 服务健康检查
```bash
curl http://localhost:8000/health        # API网关
curl http://localhost:8001/health        # 账号服务
curl http://localhost:8002/health        # 代理服务
curl http://localhost:8003/health        # 采集服务
curl http://localhost:8007/health        # 用户服务
```

## 🤝 贡献指南

1. Fork项目
2. 创建特性分支 (`git checkout -b feature/amazing-feature`)
3. 提交更改 (`git commit -m 'Add some amazing feature'`)
4. 推送到分支 (`git push origin feature/amazing-feature`)
5. 创建Pull Request
