# 数据存储服务 (Storage Service)

数据存储服务是XGet微服务架构中的关键组件，负责管理系统中所有数据的持久化存储、检索和生命周期管理。该服务提供统一的存储接口，支持多种存储介质和数据类型。

## 功能特点

- **数据存储**：将处理后的数据持久化到适当的存储系统
- **数据检索**：提供高效的数据查询和检索机制
- **数据分类**：根据数据类型和用途组织存储结构
- **数据版本控制**：管理数据的多个版本
- **数据生命周期管理**：实现数据的自动归档和过期处理
- **数据压缩和优化**：优化存储空间使用
- **数据备份和恢复**：确保数据安全和可靠性
- **访问控制和权限管理**：保护敏感数据
- **存储统计和监控**：提供存储使用情况的统计和监控

## 技术栈

- **后端框架**：FastAPI
- **数据库**：
  - PostgreSQL（元数据和索引）
  - MongoDB（非结构化和半结构化数据）
  - MinIO/S3兼容存储（大型文件和媒体）
- **消息队列**：Kafka
- **缓存**：Redis
- **搜索引擎**：Elasticsearch

## API端点

### 数据存储API

- `POST /api/v1/storage` - 存储数据
- `POST /api/v1/storage/batch` - 批量存储数据

### 数据检索API

- `GET /api/v1/storage/{data_id}` - 根据ID获取数据
- `GET /api/v1/storage/search` - 搜索数据
- `POST /api/v1/storage/search` - 高级搜索

### 元数据管理API

- `GET /api/v1/storage/{data_id}/metadata` - 获取数据元数据
- `PATCH /api/v1/storage/{data_id}/metadata` - 更新数据元数据

### 生命周期管理API

- `GET /api/v1/storage/{data_id}/lifecycle` - 获取数据生命周期信息
- `PUT /api/v1/storage/{data_id}/lifecycle` - 更新数据生命周期策略

### 存储管理API

- `GET /api/v1/storage/stats` - 获取存储统计信息
- `GET /api/v1/storage/health` - 获取存储健康状态

## 环境变量

| 变量名 | 描述 | 默认值 |
|--------|------|--------|
| `POSTGRES_SERVER` | PostgreSQL服务器地址 | postgres |
| `POSTGRES_USER` | PostgreSQL用户名 | postgres |
| `POSTGRES_PASSWORD` | PostgreSQL密码 | postgres |
| `POSTGRES_DB` | PostgreSQL数据库名 | storage_db |
| `MONGODB_URI` | MongoDB连接URI | mongodb://mongodb:27017/storage |
| `MINIO_ROOT_USER` | MinIO用户名 | minioadmin |
| `MINIO_ROOT_PASSWORD` | MinIO密码 | minioadmin |
| `MINIO_ENDPOINT` | MinIO端点 | minio:9000 |
| `KAFKA_BOOTSTRAP_SERVERS` | Kafka服务器地址 | kafka:9092 |
| `REDIS_HOST` | Redis服务器地址 | redis |
| `REDIS_PORT` | Redis服务器端口 | 6379 |
| `ELASTICSEARCH_HOST` | Elasticsearch主机 | elasticsearch |
| `ELASTICSEARCH_PORT` | Elasticsearch端口 | 9200 |
| `PROCESSING_SERVICE_URL` | 处理服务URL | http://processing-service:8000/api/v1 |

## 安装和运行

### 使用Docker

```bash
# 构建镜像
docker build -t xget-storage-service .

# 运行容器
docker run -p 8005:8000 --name storage-service xget-storage-service
```

### 使用Docker Compose

```bash
# 在项目根目录下运行
docker-compose up -d storage-service
```

## 开发

### 本地环境设置

```bash
# 创建虚拟环境
python -m venv venv
source venv/bin/activate  # Linux/Mac
venv\Scripts\activate  # Windows

# 安装依赖
pip install -r requirements.txt

# 运行开发服务器
uvicorn app.main:app --reload
```

## 测试

```bash
# 运行单元测试
pytest

# 运行覆盖率测试
pytest --cov=app
```

## 项目结构

```
storage-service/
├── app/
│   ├── api/           # API路由
│   ├── core/          # 核心配置
│   ├── db/            # 数据库连接
│   ├── models/        # 数据库模型
│   ├── schemas/       # Pydantic模型
│   ├── services/      # 业务逻辑
│   ├── storage/       # 存储后端实现
│   ├── utils/         # 工具函数
│   └── main.py        # 应用入口
├── tests/             # 测试
├── Dockerfile         # Docker配置
├── requirements.txt   # 依赖列表
└── README.md          # 项目说明
``` 