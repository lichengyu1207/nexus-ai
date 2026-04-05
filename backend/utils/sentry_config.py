"""
Sentry错误追踪配置
用于捕获前端和后端错误
"""

import sentry_sdk
from sentry_sdk.integrations.fastapi import FastApiIntegration
from sentry_sdk.integrations.sqlalchemy import SqlalchemyIntegration
import os

SENTRY_DSN = os.getenv("SENTRY_DSN", "")
ENVIRONMENT = os.getenv("ENVIRONMENT", "development")

def init_sentry():
    """初始化Sentry"""
    if not SENTRY_DSN:
        print("[Sentry] DSN未配置，跳过初始化")
        return False
    
    sentry_sdk.init(
        dsn=SENTRY_DSN,
        environment=ENVIRONMENT,
        traces_sample_rate=0.1,
        profiles_sample_rate=0.1,
        integrations=[
            FastApiIntegration(),
            SqlalchemyIntegration(),
        ],
        before_send=filter_sensitive_data,
    )
    print(f"[Sentry] 初始化完成 - 环境: {ENVIRONMENT}")
    return True

def filter_sensitive_data(event, hint):
    """过滤敏感数据"""
    if 'request' in event:
        headers = event['request'].get('headers', {})
        if 'authorization' in headers:
            headers['authorization'] = '[Filtered]'
        if 'cookie' in headers:
            headers['cookie'] = '[Filtered]'
    return event

def capture_exception(error: Exception, context: dict = None):
    """捕获异常并添加上下文"""
    if context:
        for key, value in context.items():
            sentry_sdk.set_context(key, value)
    sentry_sdk.capture_exception(error)

def capture_message(message: str, level: str = "info"):
    """捕获消息"""
    sentry_sdk.capture_message(message, level=level)

def set_user_context(user_id: str, email: str = None, username: str = None):
    """设置用户上下文"""
    sentry_sdk.set_user({
        "id": user_id,
        "email": email,
        "username": username
    })

def clear_user_context():
    """清除用户上下文"""
    sentry_sdk.set_user(None)
