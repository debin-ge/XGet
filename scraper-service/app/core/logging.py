"""
共享日志工具

提供统一的日志配置和工具函数，支持异步日志输出，基于loguru实现
"""
import logging
import sys
import os
from loguru import logger
from typing import Optional

# 自定义的 setup_logging 函数，替代 loguru.logging_intercept
def setup_logging(level=logging.INFO, propagate_exceptions=True):
    """
    拦截标准 logging 模块的日志，并重定向到 loguru
    
    Args:
        level: 设置标准 logging 被拦截后的最低级别
        propagate_exceptions: 是否允许 logging 内部的异常继续传播
    """
    class InterceptHandler(logging.Handler):
        def emit(self, record):
            # 获取对应的 Loguru 级别
            try:
                level = logger.level(record.levelname).name
            except ValueError:
                level = record.levelno

            # 查找调用者
            frame, depth = logging.currentframe(), 2
            while frame and frame.f_code.co_filename == logging.__file__:
                frame = frame.f_back
                depth += 1

            logger.opt(depth=depth, exception=record.exc_info).log(level, record.getMessage())

    # 移除所有已有的处理器
    logging.basicConfig(handlers=[InterceptHandler()], level=level)

def initialize_logging(
        log_level: str = "INFO", 
        log_dir: Optional[str] = None, 
    ):
    """
    初始化 Loguru 日志配置。

    Args:
        log_level (str): 终端和默认文件日志的最低级别 (e.g., "DEBUG", "INFO", "WARNING", "ERROR").
        log_dir (str): 日志文件存放的目录。
    """
    logger.remove()

    logger.add(
        sys.stderr,
        level=log_level,
        colorize=True,
        format="<green>{time:YYYY-MM-DD HH:mm:ss.SSS}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>"
    )

    if log_dir:
        os.makedirs(log_dir, exist_ok=True) # 确保日志目录存在
        log_file_path = os.path.join(log_dir, "app.log")
        
        logger.add(
            log_file_path,
            rotation="10 MB",     # 日志文件达到 10MB 时切割
            retention="7 days",   # 保留最近 7 天的日志文件
            compression="zip",    # 压缩切割后的日志文件
            level="DEBUG",        # 文件中记录 DEBUG 及以上的所有日志
            encoding="utf-8",     # 指定编码，避免中文乱码
            enqueue=True          # 启用异步写入，对性能非常重要，尤其是在多线程/异步环境中
        )
    
    # 这使得使用标准 logging 模块的第三方库的日志也能被 Loguru 处理
    setup_logging(
        level=getattr(logging, log_level),  # 使用传入的 log_level 参数设置级别
        propagate_exceptions=True  # 允许 logging 内部的异常继续传播
    )

    logger.info(f"Loguru 初始化完成，当前日志级别: {log_level}, 文件日志: {'启用' if log_dir else '禁用'}")