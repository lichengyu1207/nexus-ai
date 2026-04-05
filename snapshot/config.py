"""
快照模块配置
"""
from enum import Enum
from typing import List, Optional

from pydantic_settings import BaseSettings


class StorageType(Enum):
    """存储类型"""
    LOCAL = "local"
    S3 = "s3"
    OSS = "oss"


class SnapshotConfig(BaseSettings):
    """快照配置"""
    
    storage_type: StorageType = StorageType.LOCAL
    
    local_storage_path: str = "/tmp/snapshots"
    
    s3_bucket: str = "fangdudu-snapshots"
    s3_endpoint: str = ""
    s3_access_key: str = ""
    s3_secret_key: str = ""
    s3_region: str = "us-east-1"
    
    oss_bucket: str = "fangdudu-snapshots"
    oss_endpoint: str = "oss-cn-hangzhou.aliyuncs.com"
    oss_access_key_id: str = ""
    oss_access_key_secret: str = ""
    
    db_host: str = "localhost"
    db_port: int = 5432
    db_name: str = "fangdudu"
    db_user: str = "postgres"
    db_password: str = ""
    
    config_path: str = "/opt/fangdudu/configs/current"
    
    redis_host: str = "localhost"
    redis_port: int = 6379
    redis_db: int = 0
    redis_password: Optional[str] = None
    
    max_snapshots: int = 7
    retention_days: int = 7
    
    services: List[str] = ["fangdudu-api", "nginx", "gatekeeper"]
    
    temp_dir: str = "/tmp/snapshot_temp"
    
    snapshot_prefix: str = "snapshots/snapshot_"
    
    schedule_hour: int = 2
    schedule_minute: int = 0
    
    backup_tables: List[str] = [
        "agents",
        "tools",
        "tool_permissions",
        "audit_logs",
    ]
    
    class Config:
        env_prefix = "SNAPSHOT_"
        env_file = ".env"
        extra = "ignore"
    
    def get_snapshot_filename(self, timestamp: str) -> str:
        """获取快照文件名"""
        return f"snapshot_{timestamp}.tar.gz"
    
    def get_snapshot_path(self, filename: str) -> str:
        """获取快照完整路径"""
        if filename.startswith("snapshots/"):
            return filename
        return f"snapshots/{filename}"
