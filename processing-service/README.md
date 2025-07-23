# 数据处理服务 (Processing Service)

数据处理服务是XGet微服务架构中的核心组件之一，负责对从数据采集服务获取的原始数据进行清洗、转换、分析和结构化处理。

## 功能特点

- **数据清洗**：过滤无效数据、去重、修复损坏数据
- **数据转换**：将不同来源的数据转换为统一的格式和结构
- **数据分析**：提取关键信息、生成摘要、识别实体和关系
- **数据结构化**：将非结构化数据转换为结构化数据
- **数据验证**：确保数据符合预定义的质量标准和业务规则
- **数据富化**：通过外部API或其他数据源补充额外信息
- **数据分类**：根据内容和元数据对数据进行分类
- **批量处理**：支持大规模数据的批处理操作

## 技术栈

- **后端框架**：FastAPI
- **数据处理库**：Pandas, NumPy, NLTK/spaCy
- **消息队列**：Kafka
- **数据库**：PostgreSQL (任务元数据), MongoDB (处理后数据)
- **缓存**：Redis

## API端点

### 处理任务API

- `POST /api/v1/processing-tasks` - 创建处理任务
- `GET /api/v1/processing-tasks/{task_id}` - 获取任务状态
- `GET /api/v1/processing-tasks` - 获取任务列表
- `DELETE /api/v1/processing-tasks/{task_id}` - 取消任务

### 处理规则API

- `GET /api/v1/processing-rules` - 获取可用处理规则
- `POST /api/v1/processing-rules` - 创建或更新处理规则

### 处理结果API

- `GET /api/v1/processing-results/{task_id}` - 获取处理结果
- `GET /api/v1/processing-stats` - 获取处理统计信息

## 环境变量

| 变量名 | 描述 | 默认值 |
|--------|------|--------|
| `POSTGRES_SERVER` | PostgreSQL服务器地址 | postgres |
| `POSTGRES_USER` | PostgreSQL用户名 | postgres |
| `POSTGRES_PASSWORD` | PostgreSQL密码 | postgres |
| `POSTGRES_DB` | PostgreSQL数据库名 | processing_db |
| `MONGODB_URI` | MongoDB连接URI | mongodb://mongodb:27017/processing |
| `KAFKA_BOOTSTRAP_SERVERS` | Kafka服务器地址 | kafka:9092 |
| `REDIS_HOST` | Redis服务器地址 | redis |
| `REDIS_PORT` | Redis服务器端口 | 6379 |
| `STORAGE_SERVICE_URL` | 存储服务URL | http://storage-service:8000/api/v1 |
| `SCRAPER_SERVICE_URL` | 数据采集服务URL | http://scraper-service:8000/api/v1 |

## 安装和运行

### 使用Docker

```bash
# 构建镜像
docker build -t xget-processing-service .

# 运行容器
docker run -p 8004:8000 --name processing-service xget-processing-service
```

### 使用Docker Compose

```bash
# 在项目根目录下运行
docker-compose up -d processing-service
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
processing-service/
├── app/
│   ├── api/           # API路由
│   ├── core/          # 核心配置
│   ├── db/            # 数据库连接
│   ├── models/        # 数据库模型
│   ├── schemas/       # Pydantic模型
│   ├── services/      # 业务逻辑
│   ├── tasks/         # 后台任务
│   ├── utils/         # 工具函数
│   └── main.py        # 应用入口
├── tests/             # 测试
├── Dockerfile         # Docker配置
├── requirements.txt   # 依赖列表
└── README.md          # 项目说明
``` 