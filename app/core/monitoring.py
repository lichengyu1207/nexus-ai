"""
Prometheus监控配置
用于系统性能监控和告警
"""
from prometheus_client import Counter, Histogram, Gauge, CollectorRegistry
import time
from functools import wraps
import logging

logger = logging.getLogger(__name__)

# 创建注册表
registry = CollectorRegistry()

# ========== 指标定义 ==========

# 请求计数器
REQUEST_COUNT = Counter(
    'http_requests_total',
    'Total HTTP requests',
    ['method', 'endpoint', 'status'],
    registry=registry
)

# 请求延迟直方图
REQUEST_LATENCY = Histogram(
    'http_request_duration_seconds',
    'HTTP request latency',
    ['method', 'endpoint'],
    registry=registry
)

# 任务计数器
TASK_COUNT = Counter(
    'tasks_total',
    'Total tasks',
    ['status', 'style'],
    registry=registry
)

# 任务执行时间
TASK_DURATION = Histogram(
    'task_duration_seconds',
    'Task execution duration',
    ['agent_name'],
    registry=registry
)

# 活跃任务数
ACTIVE_TASKS = Gauge(
    'active_tasks',
    'Number of active tasks',
    registry=registry
)

# 代理状态
AGENT_STATUS = Gauge(
    'agent_status',
    'Agent status (0=idle, 1=working, 2=error)',
    ['agent_name'],
    registry=registry
)

# 缓存命中率
CACHE_HIT_RATE = Gauge(
    'cache_hit_rate',
    'Cache hit rate',
    registry=registry
)

# 数据库连接数
DB_CONNECTIONS = Gauge(
    'db_connections',
    'Number of database connections',
    registry=registry
)


# ========== 监控装饰器 ==========

def monitor_request(func):
    """
    监控HTTP请求的装饰器
    """
    @wraps(func)
    async def wrapper(*args, **kwargs):
        start_time = time.time()
        
        try:
            # 执行请求
            result = await func(*args, **kwargs)
            
            # 记录成功请求
            REQUEST_COUNT.labels(
                method='GET',  # 可以从request对象获取
                endpoint=func.__name__,
                status=200
            ).inc()
            
            return result
            
        except Exception as e:
            # 记录失败请求
            REQUEST_COUNT.labels(
                method='GET',
                endpoint=func.__name__,
                status=500
            ).inc()
            
            raise
            
        finally:
            # 记录延迟
            duration = time.time() - start_time
            REQUEST_LATENCY.labels(
                method='GET',
                endpoint=func.__name__
            ).observe(duration)
    
    return wrapper


def monitor_task(func):
    """
    监控任务执行的装饰器
    """
    @wraps(func)
    async def wrapper(*args, **kwargs):
        start_time = time.time()
        
        try:
            # 增加活跃任务数
            ACTIVE_TASKS.inc()
            
            # 执行任务
            result = await func(*args, **kwargs)
            
            # 记录成功任务
            TASK_COUNT.labels(
                status='success',
                style=kwargs.get('style', 'balanced')
            ).inc()
            
            return result
            
        except Exception as e:
            # 记录失败任务
            TASK_COUNT.labels(
                status='failure',
                style=kwargs.get('style', 'balanced')
            ).inc()
            
            raise
            
        finally:
            # 减少活跃任务数
            ACTIVE_TASKS.dec()
            
            # 记录执行时间
            duration = time.time() - start_time
            TASK_DURATION.labels(
                agent_name=func.__name__
            ).observe(duration)
    
    return wrapper


# ========== 监控函数 ==========

def update_agent_status(agent_name: str, status: int):
    """
    更新代理状态
    
    Args:
        agent_name: 代理名称
        status: 状态（0=idle, 1=working, 2=error）
    """
    AGENT_STATUS.labels(agent_name=agent_name).set(status)


def update_cache_hit_rate(hit_rate: float):
    """
    更新缓存命中率
    
    Args:
        hit_rate: 命中率（0-1）
    """
    CACHE_HIT_RATE.set(hit_rate)


def update_db_connections(count: int):
    """
    更新数据库连接数
    
    Args:
        count: 连接数
    """
    DB_CONNECTIONS.set(count)


def get_metrics():
    """
    获取Prometheus格式的指标数据
    
    Returns:
        str: Prometheus格式的指标数据
    """
    from prometheus_client import generate_latest
    
    return generate_latest(registry)
