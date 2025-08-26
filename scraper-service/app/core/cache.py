from functools import wraps
import hashlib
from typing import Callable, Any
from .redis import RedisManager


def _serialize_object(obj: Any) -> Any:
    """将对象转换为可序列化的格式"""
    from datetime import datetime, date
    
    if isinstance(obj, (datetime, date)):
        # 处理datetime对象
        return {"__type__": "datetime", "value": obj.isoformat()}
    elif hasattr(obj, 'dict'):
        # Pydantic模型
        data = obj.dict()
        # 递归处理字典中的所有值
        serialized_data = {}
        for key, value in data.items():
            serialized_data[key] = _serialize_object(value)
        # 添加类型信息
        if hasattr(obj, '__class__'):
            serialized_data["__class__"] = obj.__class__.__name__
        return serialized_data
    elif hasattr(obj, '__dict__'):
        # 普通对象（如SQLAlchemy模型）
        data = {k: _serialize_object(v) for k, v in obj.__dict__.items() if not k.startswith('_')}
        # 添加类型信息
        if hasattr(obj, '__class__'):
            data["__class__"] = obj.__class__.__name__
        return data
    elif isinstance(obj, (list, tuple)):
        # 列表或元组
        return [_serialize_object(item) for item in obj]
    elif isinstance(obj, dict):
        # 字典
        return {k: _serialize_object(v) for k, v in obj.items()}
    else:
        # 基本类型
        return obj


def _deserialize_to_object(data: Any) -> Any:
    """将序列化数据转换回对象"""
    from datetime import datetime
    import re
    
    # 处理特殊格式的datetime对象
    if isinstance(data, dict) and "__type__" in data and data["__type__"] == "datetime":
        # 处理序列化的datetime对象
        try:
            return datetime.fromisoformat(data["value"].replace('Z', '+00:00'))
        except (ValueError, TypeError):
            return data["value"]  # 返回原始字符串如果转换失败
    
    # 处理datetime字符串（向后兼容）
    if isinstance(data, str):
        # 检查是否是ISO格式的datetime字符串
        datetime_pattern = r'^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(\.\d+)?(Z|[+-]\d{2}:\d{2})?$'
        if re.match(datetime_pattern, data):
            try:
                return datetime.fromisoformat(data.replace('Z', '+00:00'))
            except (ValueError, TypeError):
                pass
    
    # 处理Pydantic模型重建
    if isinstance(data, dict) and "__class__" in data:
        class_name = data["__class__"]
        if class_name == "TaskListResponse":
            from ..schemas.task import TaskListResponse
            processed_data = _deserialize_to_object(data)
            return TaskListResponse.parse_obj(processed_data)
        elif class_name == "TaskExecutionListResponse":
            from ..schemas.task_execution import TaskExecutionListResponse
            processed_data = _deserialize_to_object(data)
            return TaskExecutionListResponse.parse_obj(processed_data)
    
    # 处理SQLAlchemy模型重建
    if isinstance(data, dict) and "__class__" in data:
        class_name = data["__class__"]
        if class_name == "Task":
            from ..models.task import Task
            # 创建Task对象
            task = Task()
            for key, value in data.items():
                if key != "__class__" and hasattr(task, key):
                    # 递归处理嵌套对象
                    deserialized_value = _deserialize_to_object(value)
                    setattr(task, key, deserialized_value)
            return task
        elif class_name == "TaskExecution":
            from ..models.task_execution import TaskExecution
            # 创建TaskExecution对象
            execution = TaskExecution()
            for key, value in data.items():
                if key != "__class__" and hasattr(execution, key):
                    # 递归处理嵌套对象
                    deserialized_value = _deserialize_to_object(value)
                    setattr(execution, key, deserialized_value)
            return execution
    
    # 递归处理字典和列表
    if isinstance(data, dict):
        return {k: _deserialize_to_object(v) for k, v in data.items()}
    elif isinstance(data, list):
        return [_deserialize_to_object(item) for item in data]
    else:
        # 基本类型
        return data

class cache:
    """Redis缓存装饰器"""
    
    def __init__(self, prefix: str = "cache", expire: int = 300):
        self.prefix = prefix
        self.expire = expire
    
    def __call__(self, func: Callable) -> Callable:
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # 生成缓存key
            key = self._generate_key(func, *args, **kwargs)
            
            # 尝试从缓存获取
            cached = await RedisManager.get_json(key)
            if cached is not None:
                # 如果缓存存在，直接反序列化
                return _deserialize_to_object(cached)
            
            # 执行原函数
            result = await func(*args, **kwargs)
            
            # 缓存结果 - 转换为可序列化的格式
            if result is not None:
                cache_data = _serialize_object(result)
                await RedisManager.set_json(key, cache_data, self.expire)
            
            return result
        
        return wrapper
    
    def _generate_key(self, func: Callable, *args, **kwargs) -> str:
        """生成唯一的缓存key"""
        func_name = func.__name__
        module_name = func.__module__
        
        # 处理参数
        args_repr = repr(args)
        kwargs_repr = repr(sorted(kwargs.items()))
        
        # 生成hash
        key_str = f"{module_name}:{func_name}:{args_repr}:{kwargs_repr}"
        key_hash = hashlib.md5(key_str.encode()).hexdigest()
        
        return f"{self.prefix}:{key_hash}"