"""
状态快照与回滚模块

提供系统状态快照创建、存储和回滚功能，包括：
- 数据库备份与恢复
- 配置文件备份与恢复
- 对象存储集成（OSS/S3）
- 定时自动备份
- 灾难恢复
"""
from .models import SnapshotInfo, SnapshotStatus, SnapshotMetadata
from .config import SnapshotConfig
from .storage import StorageBackend, LocalStorage, S3Storage, OSSStorage
from .backup import BackupManager
from .restore import RestoreManager
from .scheduler import SnapshotScheduler

__all__ = [
    "SnapshotInfo",
    "SnapshotStatus",
    "SnapshotMetadata",
    "SnapshotConfig",
    "StorageBackend",
    "LocalStorage",
    "S3Storage",
    "OSSStorage",
    "BackupManager",
    "RestoreManager",
    "SnapshotScheduler",
]
