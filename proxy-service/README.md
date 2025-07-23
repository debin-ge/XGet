# XGet 代理管理服务

XGet 代理管理服务是一个基于微服务架构的代理池管理系统。它负责管理和监控代理的可用性，提供高质量的代理给其他服务使用。

## 功能特点

- 代理池管理：添加、更新、删除代理
- 代理可用性检查：自动检查代理是否可用
- 代理质量监控：记录代理延迟和成功率
- 代理轮换：提供可用代理轮换功能
- 批量导入：支持从文件导入代理
- 定时任务：定期检查代理可用性

## API 接口

### 代理管理

- `POST /api/v1/proxies` - 创建新代理
- `GET /api/v1/proxies` - 获取代理列表
- `GET /api/v1/proxies/{proxy_id}` - 获取代理详情
- `PUT /api/v1/proxies/{proxy_id}` - 更新代理信息
- `DELETE /api/v1/proxies/{proxy_id}` - 删除代理
- `GET /api/v1/proxies/available` - 获取可用代理
- `POST /api/v1/proxies/check` - 检查代理可用性
- `POST /api/v1/proxies/import` - 批量导入代理
- `POST /api/v1/proxies/import/file` - 从文件导入代理
- `POST /api/v1/proxies/{proxy_id}/check` - 检查单个代理可用性
- `GET /api/v1/proxies/stats/summary` - 获取代理统计信息
- `POST /api/v1/proxies/rotate` - 轮换代理
- `POST /api/v1/proxies/batch-check` - 批量检查代理可用性

## 使用示例

### 创建代理

```bash
curl -X POST "http://localhost:8002/api/v1/proxies" \
  -H "Content-Type: application/json" \
  -d '{
    "type": "SOCKS5",
    "ip": "192.168.1.1",
    "port": 1080,
    "username": "user",
    "password": "pass",
    "country": "US",
    "city": "New York"
  }'
```

### 获取可用代理

```bash
curl "http://localhost:8002/api/v1/proxies/available?limit=5&min_success_rate=0.8"
```

### 检查代理可用性

```bash
curl -X POST "http://localhost:8002/api/v1/proxies/check" \
  -H "Content-Type: application/json" \
  -d '{
    "proxy_ids": ["proxy-id-1", "proxy-id-2"]
  }'
```

## 环境变量

- `POSTGRES_SERVER` - PostgreSQL 服务器地址
- `POSTGRES_USER` - PostgreSQL 用户名
- `POSTGRES_PASSWORD` - PostgreSQL 密码
- `POSTGRES_DB` - PostgreSQL 数据库名
- `REDIS_URL` - Redis 连接 URL

## 代理文件格式

从文件导入代理时，支持以下格式：

### 自定义格式 (TXT)

|type|ip|port|username|password|country|city|
| ---- | ---- | ---- | ---- | ---- | ---- | ---- |
|SOCKS5|192.168.1.1|1080|user|pass|US|New York|
|HTTP|192.168.1.2|8080|||||




### CSV 格式

```csv
type,ip,port,username,password,country,city
SOCKS5,192.168.1.1,1080,user,pass,US,New York
HTTP,192.168.1.2,8080,,,, 
```

## 定时任务

代理管理服务包含一个定时任务，会定期检查代理可用性：

- 活跃代理每30分钟检查一次
- 非活跃代理每2小时检查一次
- 检查中的代理（可能是上次检查异常）每10分钟检查一次

## 部署

### Docker 部署

```bash
docker build -t xget-proxy-service .
docker run -p 8002:8000 \
  -e POSTGRES_SERVER=postgres \
  -e POSTGRES_USER=xget \
  -e POSTGRES_PASSWORD=xget \
  -e POSTGRES_DB=xget \
  -e REDIS_URL=redis://redis:6379/0 \
  xget-proxy-service
```

### Docker Compose 部署

参见项目根目录的 docker-compose.yml 文件