# AIOKafka 配置说明

## 重要说明

**AIOKafka 0.10.0 只支持有限的配置参数**，与 kafka-python 库不同。

## 支持的参数

### AIOKafkaProducer 支持的参数
- `bootstrap_servers`: Kafka服务器地址
- `value_serializer`: 值序列化器
- `key_serializer`: 键序列化器
- `acks`: 确认机制 ('0', '1', 'all')
- `client_id`: 客户端ID
- `request_timeout_ms`: 请求超时时间
- `metadata_max_age_ms`: 元数据最大年龄
- `max_request_size`: 最大请求大小
- `receive_buffer_bytes`: 接收缓冲区大小
- `send_buffer_bytes`: 发送缓冲区大小

### AIOKafkaConsumer 支持的参数
- `bootstrap_servers`: Kafka服务器地址
- `group_id`: 消费者组ID
- `value_deserializer`: 值反序列化器
- `key_deserializer`: 键反序列化器
- `auto_offset_reset`: 偏移量重置策略 ('earliest', 'latest')
- `enable_auto_commit`: 是否自动提交偏移量
- `max_poll_records`: 每次拉取的最大记录数
- `session_timeout_ms`: 会话超时时间
- `heartbeat_interval_ms`: 心跳间隔
- `fetch_max_wait_ms`: 拉取等待时间
- `fetch_min_bytes`: 最小拉取字节数
- `fetch_max_bytes`: 最大拉取字节数

## 不支持的参数

以下参数在 AIOKafka 中**不支持**：
- `batch_size`: 批量大小
- `linger_ms`: 等待时间
- `compression_type`: 压缩类型
- `retries`: 重试次数

## 主题配置

### 使用的主题

1. **任务队列主题** (`scraper-tasks`)
   - 用途：传递新创建的采集任务
   - 分区数：3（可配置）
   - 副本数：1
   - 保留策略：删除
   - 保留时间：7天（可配置）

2. **控制消息主题** (`scraper-control`)
   - 用途：传递任务控制命令（停止、暂停等）
   - 分区数：3（可配置）
   - 副本数：1
   - 保留策略：删除
   - 保留时间：1天（可配置）

### 主题配置参数

```python
# 环境变量配置
KAFKA_TOPIC_TASKS = "scraper-tasks"
KAFKA_TOPIC_CONTROL = "scraper-control"
KAFKA_TOPIC_PARTITIONS = 3
KAFKA_TOPIC_RETENTION_MS = "604800000"  # 7天
KAFKA_TOPIC_MAX_MESSAGE_BYTES = "1048576"  # 1MB
```

## 消息结构

### 任务消息结构 (scraper-tasks 主题)

```json
{
  "task_id": "string",
  "task_name": "string",
  "task_type": "string",
  "parameters": {
    "username": "string",
    "limit": "integer",
    "include_replies": "boolean",
    "include_retweets": "boolean"
  },
  "account_id": "string|null",
  "proxy_id": "string|null",
  "user_id": "string",
  "created_at": "string (ISO 8601)"
}
```

### 控制消息结构 (scraper-control 主题)

```json
{
  "task_id": "string",
  "command": "string",  // "STOP", "PAUSE", "RESUME"
  "timestamp": "string (ISO 8601)",
  "user_id": "string"
}
```

## 当前配置

### 生产者配置
```python
AIOKafkaProducer(
    bootstrap_servers=settings.KAFKA_BOOTSTRAP_SERVERS,
    value_serializer=lambda v: json.dumps(v).encode('utf-8'),
    acks='all'  # 确保消息被所有副本确认
)
```

### 任务消费者配置
```python
AIOKafkaConsumer(
    settings.KAFKA_TOPIC_TASKS,
    bootstrap_servers=settings.KAFKA_BOOTSTRAP_SERVERS,
    group_id="scraper-worker",
    value_deserializer=lambda m: json.loads(m.decode('utf-8')),
    auto_offset_reset='earliest',  # 从最早的消息开始消费
    enable_auto_commit=False,  # 手动提交偏移量
    max_poll_records=settings.KAFKA_MAX_POLL_RECORDS,
    session_timeout_ms=settings.KAFKA_SESSION_TIMEOUT_MS,
    heartbeat_interval_ms=settings.KAFKA_HEARTBEAT_INTERVAL_MS,
    fetch_max_wait_ms=settings.KAFKA_FETCH_MAX_WAIT_MS,
    fetch_min_bytes=settings.KAFKA_FETCH_MIN_BYTES,
    fetch_max_bytes=settings.KAFKA_FETCH_MAX_BYTES
)
```

### 控制消息消费者配置
```python
AIOKafkaConsumer(
    settings.KAFKA_TOPIC_CONTROL,
    bootstrap_servers=settings.KAFKA_BOOTSTRAP_SERVERS,
    group_id="scraper-control",
    value_deserializer=lambda m: json.loads(m.decode('utf-8')),
    auto_offset_reset='latest',  # 只消费最新的控制消息
    enable_auto_commit=True,  # 自动提交偏移量
    max_poll_records=1  # 每次只处理一条控制消息
)
```

## 环境变量配置

### Kafka 连接配置
```bash
KAFKA_BOOTSTRAP_SERVERS=kafka:9092
KAFKA_TOPIC_TASKS=scraper-tasks
KAFKA_TOPIC_CONTROL=scraper-control
```

### 消费者性能配置
```bash
KAFKA_MAX_POLL_RECORDS=10
KAFKA_SESSION_TIMEOUT_MS=30000
KAFKA_HEARTBEAT_INTERVAL_MS=3000
KAFKA_FETCH_MAX_WAIT_MS=500
KAFKA_FETCH_MIN_BYTES=1
KAFKA_FETCH_MAX_BYTES=52428800  # 50MB
```

### 主题配置
```bash
KAFKA_TOPIC_PARTITIONS=3
KAFKA_TOPIC_RETENTION_MS=604800000  # 7天
KAFKA_TOPIC_MAX_MESSAGE_BYTES=1048576  # 1MB
```

## 重试机制

由于 AIOKafka 不支持内置重试，我们在业务逻辑中实现了重试机制：

```python
async def send_task(self, task_data: Dict[str, Any], retry: bool = True) -> bool:
    """发送任务消息，支持重试"""
    for attempt in range(self._retry_count if retry else 1):
        try:
            producer = await self.get_producer()
            await producer.send_and_wait(settings.KAFKA_TOPIC_TASKS, task_data)
            return True
        except Exception as e:
            logger.error(f"发送任务消息失败 (尝试 {attempt + 1}/{self._retry_count}): {e}")
            if attempt < self._retry_count - 1:
                await asyncio.sleep(self._retry_delay * (attempt + 1))
            else:
                return False

async def send_control_message(self, control_data: Dict[str, Any]) -> bool:
    """发送控制消息"""
    try:
        producer = await self.get_producer()
        await producer.send_and_wait(settings.KAFKA_TOPIC_CONTROL, control_data)
        return True
    except Exception as e:
        logger.error(f"发送控制消息失败: {e}")
        return False
```

## 消费者组策略

### 任务消费者组 (`scraper-worker`)
- **目的**: 处理采集任务
- **策略**: 多个实例并行处理，负载均衡
- **偏移量管理**: 手动提交，确保任务处理完成后再提交
- **错误处理**: 失败的任务会记录错误并更新状态

### 控制消费者组 (`scraper-control`)
- **目的**: 处理控制命令
- **策略**: 实时处理，优先级高
- **偏移量管理**: 自动提交
- **错误处理**: 记录日志，不影响主要任务流程

## 监控指标

### 生产者指标
- 消息发送速率
- 发送失败率
- 发送延迟

### 消费者指标
- 消息消费速率
- 消费延迟
- 积压消息数量
- 消费者组状态

## 性能优化建议

1. **分区策略**: 根据任务类型或用户ID进行分区，提高并行度
2. **批量处理**: 在应用层实现批量发送以提高吞吐量
3. **连接池**: 使用连接池管理 producer 实例，减少连接开销
4. **异步处理**: 充分利用异步特性，避免阻塞操作
5. **错误处理**: 实现完善的错误处理和重试机制
6. **监控告警**: 设置适当的监控指标和告警阈值

## 故障处理

### 常见问题及解决方案

1. **消费者组重平衡**
   - 原因：消费者实例启动/停止
   - 解决：优化心跳间隔和会话超时配置

2. **消息积压**
   - 原因：消费速度慢于生产速度
   - 解决：增加消费者实例或优化处理逻辑

3. **连接超时**
   - 原因：网络不稳定或Kafka服务器负载高
   - 解决：调整超时配置和重试策略

4. **序列化错误**
   - 原因：消息格式不兼容
   - 解决：统一消息格式规范和版本管理 