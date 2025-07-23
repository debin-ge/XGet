from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, BinaryIO, List, Union
import logging

logger = logging.getLogger(__name__)

class StorageBackendBase(ABC):
    """存储后端基类，定义所有存储后端必须实现的接口"""
    
    @abstractmethod
    async def initialize(self) -> bool:
        """
        初始化存储后端
        
        Returns:
            初始化是否成功
        """
        pass
    
    @abstractmethod
    async def store(self, key: str, data: Union[bytes, str, Dict[str, Any]], metadata: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        存储数据
        
        Args:
            key: 存储键
            data: 要存储的数据
            metadata: 元数据
            
        Returns:
            存储结果信息
        """
        pass
    
    @abstractmethod
    async def retrieve(self, key: str) -> Optional[Dict[str, Any]]:
        """
        检索数据
        
        Args:
            key: 存储键
            
        Returns:
            检索到的数据和元数据
        """
        pass
    
    @abstractmethod
    async def delete(self, key: str) -> bool:
        """
        删除数据
        
        Args:
            key: 存储键
            
        Returns:
            删除是否成功
        """
        pass
    
    @abstractmethod
    async def exists(self, key: str) -> bool:
        """
        检查数据是否存在
        
        Args:
            key: 存储键
            
        Returns:
            数据是否存在
        """
        pass
    
    @abstractmethod
    async def list_keys(self, prefix: Optional[str] = None, limit: int = 100, offset: int = 0) -> List[str]:
        """
        列出键
        
        Args:
            prefix: 键前缀
            limit: 限制数量
            offset: 偏移量
            
        Returns:
            键列表
        """
        pass
    
    @abstractmethod
    async def get_stats(self) -> Dict[str, Any]:
        """
        获取存储统计信息
        
        Returns:
            统计信息
        """
        pass
    
    @abstractmethod
    async def health_check(self) -> Dict[str, Any]:
        """
        健康检查
        
        Returns:
            健康状态信息
        """
        pass 