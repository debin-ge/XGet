import json
import logging
from typing import Dict, Any, List, Optional, Union, Set
import re
import pandas as pd
from datetime import datetime

logger = logging.getLogger(__name__)

class JsonProcessor:
    """JSON数据处理工具类"""
    
    @staticmethod
    def flatten_json(nested_json: Dict[str, Any], separator: str = '.') -> Dict[str, Any]:
        """
        将嵌套的JSON扁平化
        
        Args:
            nested_json: 嵌套的JSON对象
            separator: 键名分隔符
            
        Returns:
            扁平化后的JSON对象
        """
        out = {}
        
        def flatten(x: Union[Dict, List], name: str = ''):
            if isinstance(x, dict):
                for a in x:
                    flatten(x[a], name + a + separator)
            elif isinstance(x, list):
                for i, a in enumerate(x):
                    flatten(a, name + str(i) + separator)
            else:
                out[name[:-1]] = x
        
        flatten(nested_json)
        return out
    
    @staticmethod
    def extract_fields(json_data: Dict[str, Any], fields: List[str]) -> Dict[str, Any]:
        """
        从JSON中提取指定字段
        
        Args:
            json_data: JSON数据
            fields: 要提取的字段列表，支持点号分隔的路径
            
        Returns:
            包含提取字段的新JSON对象
        """
        result = {}
        
        for field in fields:
            # 处理嵌套字段
            if '.' in field:
                parts = field.split('.')
                current = json_data
                valid_path = True
                
                # 遍历路径
                for part in parts[:-1]:
                    if isinstance(current, dict) and part in current:
                        current = current[part]
                    else:
                        valid_path = False
                        break
                
                # 如果路径有效，提取值
                if valid_path and isinstance(current, dict) and parts[-1] in current:
                    result[field] = current[parts[-1]]
            # 处理顶层字段
            elif field in json_data:
                result[field] = json_data[field]
        
        return result
    
    @staticmethod
    def transform_json(json_data: Dict[str, Any], mapping: Dict[str, str]) -> Dict[str, Any]:
        """
        根据映射转换JSON字段
        
        Args:
            json_data: 原始JSON数据
            mapping: 字段映射，格式为 {"原字段": "新字段"}
            
        Returns:
            转换后的JSON对象
        """
        result = {}
        
        # 首先复制所有字段
        for key, value in json_data.items():
            if key in mapping:
                result[mapping[key]] = value
            else:
                result[key] = value
        
        return result
    
    @staticmethod
    def filter_json(json_data: Dict[str, Any], conditions: Dict[str, Any]) -> bool:
        """
        根据条件过滤JSON
        
        Args:
            json_data: JSON数据
            conditions: 过滤条件，格式为 {"字段": 值} 或 {"字段": {"op": "操作符", "value": 值}}
            
        Returns:
            如果JSON满足条件则返回True，否则返回False
        """
        for field, condition in conditions.items():
            # 处理嵌套字段
            if '.' in field:
                parts = field.split('.')
                current = json_data
                valid_path = True
                
                # 遍历路径
                for part in parts[:-1]:
                    if isinstance(current, dict) and part in current:
                        current = current[part]
                    else:
                        valid_path = False
                        break
                
                # 如果路径无效，条件不满足
                if not valid_path or not isinstance(current, dict) or parts[-1] not in current:
                    return False
                
                field_value = current[parts[-1]]
            # 处理顶层字段
            elif field in json_data:
                field_value = json_data[field]
            else:
                # 字段不存在，条件不满足
                return False
            
            # 处理条件
            if isinstance(condition, dict) and "op" in condition and "value" in condition:
                op = condition["op"]
                value = condition["value"]
                
                if op == "eq" and field_value != value:
                    return False
                elif op == "ne" and field_value == value:
                    return False
                elif op == "gt" and not (isinstance(field_value, (int, float)) and field_value > value):
                    return False
                elif op == "lt" and not (isinstance(field_value, (int, float)) and field_value < value):
                    return False
                elif op == "gte" and not (isinstance(field_value, (int, float)) and field_value >= value):
                    return False
                elif op == "lte" and not (isinstance(field_value, (int, float)) and field_value <= value):
                    return False
                elif op == "contains" and not (isinstance(field_value, str) and value in field_value):
                    return False
                elif op == "in" and field_value not in value:
                    return False
            else:
                # 简单相等比较
                if field_value != condition:
                    return False
        
        return True
    
    @staticmethod
    def merge_json_objects(objects: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        合并多个JSON对象
        
        Args:
            objects: JSON对象列表
            
        Returns:
            合并后的JSON对象
        """
        result = {}
        
        for obj in objects:
            for key, value in obj.items():
                if key in result and isinstance(result[key], dict) and isinstance(value, dict):
                    # 递归合并嵌套字典
                    result[key] = JsonProcessor.merge_json_objects([result[key], value])
                elif key in result and isinstance(result[key], list) and isinstance(value, list):
                    # 合并列表
                    result[key].extend(value)
                else:
                    # 简单覆盖
                    result[key] = value
        
        return result
    
    @staticmethod
    def json_to_dataframe(json_data: Union[Dict[str, Any], List[Dict[str, Any]]]) -> pd.DataFrame:
        """
        将JSON转换为Pandas DataFrame
        
        Args:
            json_data: JSON对象或JSON对象列表
            
        Returns:
            Pandas DataFrame
        """
        if isinstance(json_data, dict):
            # 单个对象，转换为单行DataFrame
            return pd.DataFrame([json_data])
        elif isinstance(json_data, list):
            # 对象列表，转换为多行DataFrame
            return pd.DataFrame(json_data)
        else:
            # 不支持的类型
            raise ValueError("输入必须是字典或字典列表")
    
    @staticmethod
    def normalize_json(json_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        标准化JSON数据（处理日期、数字等）
        
        Args:
            json_data: 原始JSON数据
            
        Returns:
            标准化后的JSON对象
        """
        result = {}
        
        for key, value in json_data.items():
            if isinstance(value, dict):
                # 递归处理嵌套字典
                result[key] = JsonProcessor.normalize_json(value)
            elif isinstance(value, list):
                # 处理列表
                result[key] = [
                    JsonProcessor.normalize_json(item) if isinstance(item, dict) else item
                    for item in value
                ]
            elif isinstance(value, str):
                # 尝试转换日期字符串
                date_pattern = r'^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(\.\d+)?(Z|[+-]\d{2}:\d{2})?$'
                if re.match(date_pattern, value):
                    try:
                        # 尝试解析ISO格式日期
                        result[key] = datetime.fromisoformat(value.replace('Z', '+00:00'))
                    except ValueError:
                        result[key] = value
                else:
                    # 尝试转换数字字符串
                    try:
                        if '.' in value:
                            result[key] = float(value)
                        else:
                            result[key] = int(value)
                    except ValueError:
                        result[key] = value
            else:
                # 保持原值
                result[key] = value
        
        return result 