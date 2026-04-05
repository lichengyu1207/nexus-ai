"""
日志配置模块
提供统一的日志记录功能
"""
import sys
import os
from pathlib import Path
from datetime import datetime
from typing import Optional
import logging
from logging.handlers import RotatingFileHandler, TimedRotatingFileHandler
import json


class JSONFormatter(logging.Formatter):
    """JSON 格式日志格式化器"""
    
    def format(self, record: logging.LogRecord) -> str:
        log_data = {
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno,
        }
        
        if record.exc_info:
            log_data["exception"] = self.formatException(record.exc_info)
        
        if hasattr(record, "request_id"):
            log_data["request_id"] = record.request_id
        
        if hasattr(record, "user_id"):
            log_data["user_id"] = record.user_id
        
        if hasattr(record, "extra_data"):
            log_data["extra"] = record.extra_data
        
        return json.dumps(log_data, ensure_ascii=False)


class ColoredFormatter(logging.Formatter):
    """彩色控制台日志格式化器"""
    
    COLORS = {
        "DEBUG": "\033[36m",     # Cyan
        "INFO": "\033[32m",      # Green
        "WARNING": "\033[33m",   # Yellow
        "ERROR": "\033[31m",     # Red
        "CRITICAL": "\033[35m",  # Magenta
    }
    RESET = "\033[0m"
    
    def format(self, record: logging.LogRecord) -> str:
        color = self.COLORS.get(record.levelname, self.RESET)
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        formatted = f"{color}[{timestamp}] [{record.levelname:8}] [{record.name}]{self.RESET} {record.getMessage()}"
        
        if record.exc_info:
            formatted += f"\n{self.formatException(record.exc_info)}"
        
        return formatted


def setup_logging(
    log_level: str = "INFO",
    log_dir: str = "/var/log/property-ai",
    enable_file_logging: bool = True,
    enable_json_logging: bool = False,
    max_bytes: int = 10 * 1024 * 1024,  # 10MB
    backup_count: int = 5,
) -> logging.Logger:
    """
    配置日志系统
    
    Args:
        log_level: 日志级别
        log_dir: 日志目录
        enable_file_logging: 是否启用文件日志
        enable_json_logging: 是否使用 JSON 格式
        max_bytes: 单个日志文件最大大小
        backup_count: 保留的日志文件数量
        
    Returns:
        logging.Logger: 配置好的根日志器
    """
    root_logger = logging.getLogger()
    root_logger.setLevel(getattr(logging, log_level.upper(), logging.INFO))
    
    root_logger.handlers.clear()
    
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(logging.DEBUG)
    console_handler.setFormatter(ColoredFormatter())
    root_logger.addHandler(console_handler)
    
    if enable_file_logging:
        log_path = Path(log_dir)
        log_path.mkdir(parents=True, exist_ok=True)
        
        info_handler = RotatingFileHandler(
            log_path / "app.log",
            maxBytes=max_bytes,
            backupCount=backup_count,
            encoding="utf-8"
        )
        info_handler.setLevel(logging.INFO)
        if enable_json_logging:
            info_handler.setFormatter(JSONFormatter())
        else:
            info_handler.setFormatter(logging.Formatter(
                "%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
                datefmt="%Y-%m-%d %H:%M:%S"
            ))
        root_logger.addHandler(info_handler)
        
        error_handler = RotatingFileHandler(
            log_path / "error.log",
            maxBytes=max_bytes,
            backupCount=backup_count,
            encoding="utf-8"
        )
        error_handler.setLevel(logging.ERROR)
        if enable_json_logging:
            error_handler.setFormatter(JSONFormatter())
        else:
            error_handler.setFormatter(logging.Formatter(
                "%(asctime)s | %(levelname)-8s | %(name)s | %(funcName)s:%(lineno)d | %(message)s\n%(exc_info)s",
                datefmt="%Y-%m-%d %H:%M:%S"
            ))
        root_logger.addHandler(error_handler)
        
        access_handler = RotatingFileHandler(
            log_path / "access.log",
            maxBytes=max_bytes,
            backupCount=backup_count,
            encoding="utf-8"
        )
        access_handler.setLevel(logging.INFO)
        access_handler.setFormatter(JSONFormatter())
        access_logger = logging.getLogger("access")
        access_logger.addHandler(access_handler)
        access_logger.propagate = False
    
    logging.getLogger("uvicorn").setLevel(logging.WARNING)
    logging.getLogger("uvicorn.access").setLevel(logging.WARNING)
    logging.getLogger("sqlalchemy.engine").setLevel(logging.WARNING)
    
    return root_logger


def get_logger(name: str) -> logging.Logger:
    """
    获取指定名称的日志器
    
    Args:
        name: 日志器名称
        
    Returns:
        logging.Logger: 日志器实例
    """
    return logging.getLogger(name)


class RequestLogger:
    """请求日志记录器"""
    
    def __init__(self, request_id: str, user_id: Optional[str] = None):
        self.request_id = request_id
        self.user_id = user_id
        self.logger = get_logger("request")
    
    def _log(self, level: int, message: str, **kwargs):
        extra = {
            "request_id": self.request_id,
            "user_id": self.user_id,
            "extra_data": kwargs if kwargs else None
        }
        self.logger.log(level, message, extra={k: v for k, v in extra.items() if v is not None})
    
    def info(self, message: str, **kwargs):
        self._log(logging.INFO, message, **kwargs)
    
    def warning(self, message: str, **kwargs):
        self._log(logging.WARNING, message, **kwargs)
    
    def error(self, message: str, **kwargs):
        self._log(logging.ERROR, message, **kwargs)
    
    def debug(self, message: str, **kwargs):
        self._log(logging.DEBUG, message, **kwargs)


logger = get_logger("property-ai")
