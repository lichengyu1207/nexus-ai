"""
配置模块
"""
from typing import Optional, List
from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field


class GatewayConfig(BaseSettings):
    model_config = SettingsConfigDict(
        env_prefix="GATEWAY_",
        env_file=".env",
        extra="ignore",
    )

    PORT: int = Field(default=18790, description="网关监听端口")
    BACKEND_URL: str = Field(default="http://localhost:8000", description="后端服务 URL")
    VIP: str = Field(default="192.168.1.100", description="虚拟 IP")
    INTERFACE: str = Field(default="eth0", description="网络接口")
    PRIORITY: int = Field(default=50, description="Keepalived 优先级")
    STATE: str = Field(default="BACKUP", description="节点状态 (MASTER/BACKUP)")
    VIRTUAL_ROUTER_ID: int = Field(default=51, description="虚拟路由 ID")
    AUTH_PASSWORD: str = Field(default="1234", description="VRRP 认证密码")
    CHECK_INTERVAL: int = Field(default=2, description="健康检查间隔（秒）")
    CHECK_TIMEOUT: int = Field(default=5, description="请求超时时间（秒）")
    MAX_CONNECTIONS: int = Field(default=1000, description="最大连接数")
    WEBHOOK_URL: Optional[str] = Field(default=None, description="告警 Webhook URL")
    WEBHOOK_TYPE: str = Field(default="feishu", description="Webhook 类型 (feishu/dingtalk)")


settings = GatewayConfig()
