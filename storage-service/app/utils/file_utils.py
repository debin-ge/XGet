import os
import hashlib
import logging
import magic
import base64
from typing import Dict, Any, Optional, Tuple, BinaryIO
from pathlib import Path

logger = logging.getLogger(__name__)

class FileUtils:
    """文件处理工具类"""
    
    @staticmethod
    def get_file_hash(file_path: str) -> str:
        """
        计算文件的MD5哈希值
        
        Args:
            file_path: 文件路径
            
        Returns:
            MD5哈希值
        """
        hash_md5 = hashlib.md5()
        with open(file_path, "rb") as f:
            for chunk in iter(lambda: f.read(4096), b""):
                hash_md5.update(chunk)
        return hash_md5.hexdigest()
    
    @staticmethod
    def get_content_hash(content: bytes) -> str:
        """
        计算内容的MD5哈希值
        
        Args:
            content: 二进制内容
            
        Returns:
            MD5哈希值
        """
        hash_md5 = hashlib.md5()
        hash_md5.update(content)
        return hash_md5.hexdigest()
    
    @staticmethod
    def get_file_mime_type(file_path: str) -> str:
        """
        获取文件的MIME类型
        
        Args:
            file_path: 文件路径
            
        Returns:
            MIME类型
        """
        try:
            mime = magic.Magic(mime=True)
            return mime.from_file(file_path)
        except Exception as e:
            logger.error(f"获取文件MIME类型失败: {str(e)}")
            return "application/octet-stream"
    
    @staticmethod
    def get_content_mime_type(content: bytes) -> str:
        """
        获取内容的MIME类型
        
        Args:
            content: 二进制内容
            
        Returns:
            MIME类型
        """
        try:
            mime = magic.Magic(mime=True)
            return mime.from_buffer(content)
        except Exception as e:
            logger.error(f"获取内容MIME类型失败: {str(e)}")
            return "application/octet-stream"
    
    @staticmethod
    def encode_to_base64(content: bytes) -> str:
        """
        将二进制内容编码为Base64字符串
        
        Args:
            content: 二进制内容
            
        Returns:
            Base64字符串
        """
        return base64.b64encode(content).decode("utf-8")
    
    @staticmethod
    def decode_from_base64(base64_str: str) -> bytes:
        """
        从Base64字符串解码为二进制内容
        
        Args:
            base64_str: Base64字符串
            
        Returns:
            二进制内容
        """
        return base64.b64decode(base64_str)
    
    @staticmethod
    def ensure_directory(directory: str) -> bool:
        """
        确保目录存在，如果不存在则创建
        
        Args:
            directory: 目录路径
            
        Returns:
            是否成功
        """
        try:
            os.makedirs(directory, exist_ok=True)
            return True
        except Exception as e:
            logger.error(f"创建目录失败: {str(e)}")
            return False
    
    @staticmethod
    def get_file_size(file_path: str) -> int:
        """
        获取文件大小（字节）
        
        Args:
            file_path: 文件路径
            
        Returns:
            文件大小
        """
        try:
            return os.path.getsize(file_path)
        except Exception as e:
            logger.error(f"获取文件大小失败: {str(e)}")
            return 0
    
    @staticmethod
    def get_file_extension(file_path: str) -> str:
        """
        获取文件扩展名
        
        Args:
            file_path: 文件路径
            
        Returns:
            文件扩展名
        """
        return os.path.splitext(file_path)[1].lower()
    
    @staticmethod
    def get_safe_filename(filename: str) -> str:
        """
        获取安全的文件名（移除不安全字符）
        
        Args:
            filename: 原始文件名
            
        Returns:
            安全的文件名
        """
        # 移除路径分隔符和其他不安全字符
        return "".join(c for c in filename if c.isalnum() or c in "._- ")
    
    @staticmethod
    def split_file(file_path: str, chunk_size: int = 1024 * 1024) -> Dict[str, Any]:
        """
        将文件分割为多个块
        
        Args:
            file_path: 文件路径
            chunk_size: 块大小（字节）
            
        Returns:
            分割信息
        """
        try:
            file_size = os.path.getsize(file_path)
            chunks = []
            
            with open(file_path, "rb") as f:
                chunk_index = 0
                while True:
                    chunk_data = f.read(chunk_size)
                    if not chunk_data:
                        break
                    
                    chunk_hash = hashlib.md5(chunk_data).hexdigest()
                    chunks.append({
                        "index": chunk_index,
                        "size": len(chunk_data),
                        "hash": chunk_hash
                    })
                    chunk_index += 1
            
            return {
                "file_path": file_path,
                "file_size": file_size,
                "chunk_size": chunk_size,
                "chunk_count": len(chunks),
                "chunks": chunks
            }
        except Exception as e:
            logger.error(f"分割文件失败: {str(e)}")
            return {
                "error": str(e)
            } 