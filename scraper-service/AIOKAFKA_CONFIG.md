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

## 当前配置

### 生产者配置
```python
AIOKafkaProducer(
    bootstrap_servers=settings.KAFKA_BOOTSTRAP_SERVERS,
    value_serializer=lambda v: json.dumps(v).encode('utf-8'),
    acks='all'  # 确保消息被所有副本确认
)
```

### 消费者配置
```python
AIOKafkaConsumer(
    settings.KAFKA_TOPIC_TASKS,
    bootstrap_servers=settings.KAFKA_BOOTSTRAP_SERVERS,
    group_id="scraper-worker",
    value_deserializer=lambda m: json.loads(m.decode('utf-8')),
    auto_offset_reset='earliest',
    enable_auto_commit=False,
    max_poll_records=settings.KAFKA_MAX_POLL_RECORDS,
    session_timeout_ms=settings.KAFKA_SESSION_TIMEOUT_MS,
    heartbeat_interval_ms=settings.KAFKA_HEARTBEAT_INTERVAL_MS,
    fetch_max_wait_ms=settings.KAFKA_FETCH_MAX_WAIT_MS,
    fetch_min_bytes=settings.KAFKA_FETCH_MIN_BYTES,
    fetch_max_bytes=settings.KAFKA_FETCH_MAX_BYTES
)
```

## 重试机制

由于 AIOKafka 不支持内置重试，我们在业务逻辑中实现了重试机制：

```python
async def send_message(self, topic: str, message: Dict[str, Any], retry: bool = True) -> bool:
    """发送消息到指定主题，支持重试"""
    for attempt in range(self._retry_count if retry else 1):
        try:
            producer = await self.get_producer()
            await producer.send_and_wait(topic, message)
            return True
        except Exception as e:
            if attempt < self._retry_count - 1:
                await asyncio.sleep(self._retry_delay * (attempt + 1))
            else:
                return False
```

## 性能优化建议

1. **批量处理**: 在应用层实现批量发送
2. **连接池**: 使用连接池管理 producer 实例
3. **异步处理**: 充分利用异步特性
4. **错误处理**: 实现完善的错误处理和重试机制 