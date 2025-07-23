# XGet 微服务系统

XGet是一个基于微服务架构的社交媒体数据采集和分析平台，专注于Twitter(X)数据的获取、处理和分析。该系统通过分布式架构设计，提供高可用、高扩展性的数据采集服务，并对外提供标准化的API接口。

## 系统架构

XGet微服务系统由以下核心服务组成：

- **API网关**：系统入口点，负责请求路由、认证和限流
- **账号管理服务**：管理社交媒体账号和登录信息
- **代理管理服务**：管理和监控代理服务器
- **数据采集服务**：执行数据采集任务，支持多种采集模式
- **认证授权服务**：处理用户认证和授权
- **用户管理服务**：管理系统用户和权限
- **数据存储服务**：管理采集数据的存储和检索
- **数据处理服务**：处理和转换采集的数据
- **数据分析服务**：分析和可视化采集的数据
- **监控告警服务**：监控系统状态和性能

## 技术栈

- **后端框架**：FastAPI
- **数据库**：PostgreSQL、MongoDB
- **缓存**：Redis
- **消息队列**：Kafka
- **容器化**：Docker、Docker Compose
- **监控**：Prometheus、Grafana
- **自动化工具**：Playwright、twscrape

## 快速开始

### 前置条件

- Docker 和 Docker Compose
- Python 3.12+（本地开发）

### 安装步骤

1. 克隆仓库
   ```bash
   git clone https://github.com/debin-ge/XGet.git
   cd xget
   ```

## 项目结构

```
xget/
├── api-gateway/                  # API网关服务
├── auth-service/                 # 认证授权服务
├── account-service/              # 账号管理服务
├── proxy-service/                # 代理管理服务
├── scraper-service/              # 数据采集服务
├── user-service/                 # 用户管理服务
├── processing-service/           # 数据处理服务
├── storage-service/              # 数据存储服务
├── analytics-service/            # 数据分析服务
├── monitoring-service/           # 监控告警服务
├── shared/                       # 共享代码
│   ├── models/                   # 共享数据模型
│   ├── utils/                    # 共享工具类
│   └── config/                   # 共享配置
├── docker/                       # Docker相关文件
├── k8s/                          # Kubernetes配置
└── docs/                         # 项目文档
```

## 文档

- [架构设计文档](./docs/XGet_Architecture.md)

## 贡献指南

1. Fork项目
2. 创建特性分支 (`git checkout -b feature/amazing-feature`)
3. 提交更改 (`git commit -m 'Add some amazing feature'`)
4. 推送到分支 (`git push origin feature/amazing-feature`)
5. 创建Pull Request

## 许可证

本项目采用MIT许可证 - 详见 [LICENSE](LICENSE) 文件 