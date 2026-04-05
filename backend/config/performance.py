"""
性能优化配置模块
提供批量任务处理的性能优化配置
"""
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any
from enum import Enum
import os


class QueueType(str, Enum):
    """队列类型"""
    MEMORY = "memory"
    REDIS = "redis"
    RABBITMQ = "rabbitmq"


class ExecutionMode(str, Enum):
    """执行模式"""
    SEQUENTIAL = "sequential"
    PARALLEL = "parallel"
    ADAPTIVE = "adaptive"


@dataclass
class BatchTaskConfig:
    """批量任务配置"""
    max_batch_size: int = 50
    max_concurrent_tasks: int = 10
    task_timeout_seconds: int = 300
    retry_attempts: int = 3
    retry_delay_seconds: int = 5
    queue_type: QueueType = QueueType.MEMORY
    execution_mode: ExecutionMode = ExecutionMode.ADAPTIVE
    
    enable_priority_queue: bool = True
    enable_task_deduplication: bool = True
    enable_auto_scaling: bool = False
    
    min_workers: int = 2
    max_workers: int = 20
    scale_up_threshold: float = 0.8
    scale_down_threshold: float = 0.3
    
    result_cache_ttl_seconds: int = 3600
    progress_update_interval_ms: int = 500
    
    @classmethod
    def from_env(cls) -> "BatchTaskConfig":
        """从环境变量加载配置"""
        return cls(
            max_batch_size=int(os.getenv("BATCH_MAX_SIZE", "50")),
            max_concurrent_tasks=int(os.getenv("BATCH_MAX_CONCURRENT", "10")),
            task_timeout_seconds=int(os.getenv("BATCH_TASK_TIMEOUT", "300")),
            retry_attempts=int(os.getenv("BATCH_RETRY_ATTEMPTS", "3")),
            retry_delay_seconds=int(os.getenv("BATCH_RETRY_DELAY", "5")),
            queue_type=QueueType(os.getenv("BATCH_QUEUE_TYPE", "memory")),
            execution_mode=ExecutionMode(os.getenv("BATCH_EXECUTION_MODE", "adaptive")),
            enable_priority_queue=os.getenv("BATCH_PRIORITY_QUEUE", "true").lower() == "true",
            enable_task_deduplication=os.getenv("BATCH_DEDUP", "true").lower() == "true",
            enable_auto_scaling=os.getenv("BATCH_AUTO_SCALING", "false").lower() == "true",
            min_workers=int(os.getenv("BATCH_MIN_WORKERS", "2")),
            max_workers=int(os.getenv("BATCH_MAX_WORKERS", "20")),
            scale_up_threshold=float(os.getenv("BATCH_SCALE_UP_THRESHOLD", "0.8")),
            scale_down_threshold=float(os.getenv("BATCH_SCALE_DOWN_THRESHOLD", "0.3")),
            result_cache_ttl_seconds=int(os.getenv("BATCH_RESULT_CACHE_TTL", "3600")),
            progress_update_interval_ms=int(os.getenv("BATCH_PROGRESS_INTERVAL", "500")),
        )


@dataclass
class RateLimitConfig:
    """限流配置"""
    enabled: bool = True
    requests_per_second: int = 10
    requests_per_minute: int = 100
    requests_per_hour: int = 1000
    burst_size: int = 20
    
    ip_whitelist: List[str] = field(default_factory=list)
    ip_blacklist: List[str] = field(default_factory=list)
    
    user_daily_limit: int = 500
    api_key_daily_limit: int = 5000
    
    @classmethod
    def from_env(cls) -> "RateLimitConfig":
        """从环境变量加载配置"""
        return cls(
            enabled=os.getenv("RATE_LIMIT_ENABLED", "true").lower() == "true",
            requests_per_second=int(os.getenv("RATE_LIMIT_RPS", "10")),
            requests_per_minute=int(os.getenv("RATE_LIMIT_RPM", "100")),
            requests_per_hour=int(os.getenv("RATE_LIMIT_RPH", "1000")),
            burst_size=int(os.getenv("RATE_LIMIT_BURST", "20")),
            ip_whitelist=os.getenv("RATE_LIMIT_WHITELIST", "").split(",") if os.getenv("RATE_LIMIT_WHITELIST") else [],
            ip_blacklist=os.getenv("RATE_LIMIT_BLACKLIST", "").split(",") if os.getenv("RATE_LIMIT_BLACKLIST") else [],
            user_daily_limit=int(os.getenv("RATE_LIMIT_USER_DAILY", "500")),
            api_key_daily_limit=int(os.getenv("RATE_LIMIT_API_KEY_DAILY", "5000")),
        )


@dataclass
class CacheConfig:
    """缓存配置"""
    enabled: bool = True
    backend: str = "redis"
    redis_url: str = "redis://localhost:6379/0"
    default_ttl_seconds: int = 3600
    max_memory_mb: int = 256
    
    task_result_cache_ttl: int = 7200
    user_session_ttl: int = 86400
    api_response_cache_ttl: int = 300
    
    @classmethod
    def from_env(cls) -> "CacheConfig":
        """从环境变量加载配置"""
        return cls(
            enabled=os.getenv("CACHE_ENABLED", "true").lower() == "true",
            backend=os.getenv("CACHE_BACKEND", "redis"),
            redis_url=os.getenv("REDIS_URL", "redis://localhost:6379/0"),
            default_ttl_seconds=int(os.getenv("CACHE_DEFAULT_TTL", "3600")),
            max_memory_mb=int(os.getenv("CACHE_MAX_MEMORY", "256")),
            task_result_cache_ttl=int(os.getenv("CACHE_TASK_RESULT_TTL", "7200")),
            user_session_ttl=int(os.getenv("CACHE_SESSION_TTL", "86400")),
            api_response_cache_ttl=int(os.getenv("CACHE_API_TTL", "300")),
        )


@dataclass
class DatabasePoolConfig:
    """数据库连接池配置"""
    min_connections: int = 5
    max_connections: int = 20
    connection_timeout_seconds: int = 30
    idle_timeout_seconds: int = 300
    max_lifetime_seconds: int = 3600
    
    enable_connection_pooling: bool = True
    enable_statement_cache: bool = True
    statement_cache_size: int = 100
    
    @classmethod
    def from_env(cls) -> "DatabasePoolConfig":
        """从环境变量加载配置"""
        return cls(
            min_connections=int(os.getenv("DB_MIN_CONNECTIONS", "5")),
            max_connections=int(os.getenv("DB_MAX_CONNECTIONS", "20")),
            connection_timeout_seconds=int(os.getenv("DB_CONNECTION_TIMEOUT", "30")),
            idle_timeout_seconds=int(os.getenv("DB_IDLE_TIMEOUT", "300")),
            max_lifetime_seconds=int(os.getenv("DB_MAX_LIFETIME", "3600")),
            enable_connection_pooling=os.getenv("DB_POOLING", "true").lower() == "true",
            enable_statement_cache=os.getenv("DB_STATEMENT_CACHE", "true").lower() == "true",
            statement_cache_size=int(os.getenv("DB_STATEMENT_CACHE_SIZE", "100")),
        )


@dataclass
class PerformanceConfig:
    """性能配置总集"""
    batch_task: BatchTaskConfig = field(default_factory=BatchTaskConfig)
    rate_limit: RateLimitConfig = field(default_factory=RateLimitConfig)
    cache: CacheConfig = field(default_factory=CacheConfig)
    database: DatabasePoolConfig = field(default_factory=DatabasePoolConfig)
    
    debug_mode: bool = False
    enable_profiling: bool = False
    log_slow_queries_ms: int = 1000
    
    @classmethod
    def from_env(cls) -> "PerformanceConfig":
        """从环境变量加载所有配置"""
        return cls(
            batch_task=BatchTaskConfig.from_env(),
            rate_limit=RateLimitConfig.from_env(),
            cache=CacheConfig.from_env(),
            database=DatabasePoolConfig.from_env(),
            debug_mode=os.getenv("DEBUG", "false").lower() == "true",
            enable_profiling=os.getenv("ENABLE_PROFILING", "false").lower() == "true",
            log_slow_queries_ms=int(os.getenv("LOG_SLOW_QUERIES_MS", "1000")),
        )
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "batch_task": {
                "max_batch_size": self.batch_task.max_batch_size,
                "max_concurrent_tasks": self.batch_task.max_concurrent_tasks,
                "task_timeout_seconds": self.batch_task.task_timeout_seconds,
                "retry_attempts": self.batch_task.retry_attempts,
                "queue_type": self.batch_task.queue_type.value,
                "execution_mode": self.batch_task.execution_mode.value,
                "enable_priority_queue": self.batch_task.enable_priority_queue,
                "enable_auto_scaling": self.batch_task.enable_auto_scaling,
            },
            "rate_limit": {
                "enabled": self.rate_limit.enabled,
                "requests_per_second": self.rate_limit.requests_per_second,
                "requests_per_minute": self.rate_limit.requests_per_minute,
                "burst_size": self.rate_limit.burst_size,
            },
            "cache": {
                "enabled": self.cache.enabled,
                "backend": self.cache.backend,
                "default_ttl_seconds": self.cache.default_ttl_seconds,
            },
            "database": {
                "min_connections": self.database.min_connections,
                "max_connections": self.database.max_connections,
                "enable_connection_pooling": self.database.enable_connection_pooling,
            },
            "debug_mode": self.debug_mode,
            "enable_profiling": self.enable_profiling,
        }


_performance_config: Optional[PerformanceConfig] = None


def get_performance_config() -> PerformanceConfig:
    """获取全局性能配置"""
    global _performance_config
    if _performance_config is None:
        _performance_config = PerformanceConfig.from_env()
    return _performance_config


def reload_config() -> PerformanceConfig:
    """重新加载配置"""
    global _performance_config
    _performance_config = PerformanceConfig.from_env()
    return _performance_config


CONFIG_VALIDATION_RULES = {
    "max_batch_size": {"min": 1, "max": 100},
    "max_concurrent_tasks": {"min": 1, "max": 50},
    "task_timeout_seconds": {"min": 10, "max": 3600},
    "retry_attempts": {"min": 0, "max": 10},
    "min_workers": {"min": 1, "max": 100},
    "max_workers": {"min": 1, "max": 100},
}


def validate_config(config: PerformanceConfig) -> List[str]:
    """验证配置"""
    errors = []
    
    for field_name, rules in CONFIG_VALIDATION_RULES.items():
        value = getattr(config.batch_task, field_name, None)
        if value is not None:
            if value < rules["min"]:
                errors.append(f"{field_name} must be >= {rules['min']}, got {value}")
            if value > rules["max"]:
                errors.append(f"{field_name} must be <= {rules['max']}, got {value}")
    
    if config.batch_task.min_workers > config.batch_task.max_workers:
        errors.append("min_workers cannot be greater than max_workers")
    
    if config.rate_limit.burst_size > config.rate_limit.requests_per_minute:
        errors.append("burst_size cannot be greater than requests_per_minute")
    
    return errors
