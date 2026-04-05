"""
快照数据模型
"""
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional


class SnapshotStatus(Enum):
    """快照状态"""
    CREATING = "creating"
    AVAILABLE = "available"
    RESTORING = "restoring"
    FAILED = "failed"
    DELETING = "deleting"


@dataclass
class SnapshotInfo:
    """快照信息"""
    filename: str
    created_at: datetime
    size_bytes: int = 0
    description: str = ""
    status: SnapshotStatus = SnapshotStatus.AVAILABLE
    created_by: str = "system"
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "filename": self.filename,
            "created_at": self.created_at.isoformat(),
            "size_bytes": self.size_bytes,
            "description": self.description,
            "status": self.status.value,
            "created_by": self.created_by,
            "metadata": self.metadata,
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "SnapshotInfo":
        """从字典创建"""
        return cls(
            filename=data["filename"],
            created_at=datetime.fromisoformat(data["created_at"]) if isinstance(data["created_at"], str) else data["created_at"],
            size_bytes=data.get("size_bytes", 0),
            description=data.get("description", ""),
            status=SnapshotStatus(data.get("status", "available")),
            created_by=data.get("created_by", "system"),
            metadata=data.get("metadata", {}),
        )


@dataclass
class SnapshotMetadata:
    """快照元数据（存储在快照内部）"""
    version: str = "1.0"
    created_at: datetime = field(default_factory=datetime.now)
    description: str = ""
    created_by: str = "system"
    db_version: str = ""
    config_files: List[str] = field(default_factory=list)
    tables: List[str] = field(default_factory=list)
    checksum: str = ""
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "version": self.version,
            "created_at": self.created_at.isoformat(),
            "description": self.description,
            "created_by": self.created_by,
            "db_version": self.db_version,
            "config_files": self.config_files,
            "tables": self.tables,
            "checksum": self.checksum,
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "SnapshotMetadata":
        """从字典创建"""
        return cls(
            version=data.get("version", "1.0"),
            created_at=datetime.fromisoformat(data["created_at"]) if isinstance(data.get("created_at"), str) else data.get("created_at", datetime.now()),
            description=data.get("description", ""),
            created_by=data.get("created_by", "system"),
            db_version=data.get("db_version", ""),
            config_files=data.get("config_files", []),
            tables=data.get("tables", []),
            checksum=data.get("checksum", ""),
        )


@dataclass
class RestoreProgress:
    """恢复进度"""
    status: str = "pending"
    current_step: str = ""
    total_steps: int = 5
    completed_steps: int = 0
    error_message: str = ""
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "status": self.status,
            "current_step": self.current_step,
            "total_steps": self.total_steps,
            "completed_steps": self.completed_steps,
            "error_message": self.error_message,
            "started_at": self.started_at.isoformat() if self.started_at else None,
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
            "progress_percent": (self.completed_steps / self.total_steps * 100) if self.total_steps > 0 else 0,
        }


@dataclass
class BackupResult:
    """备份结果"""
    success: bool
    filename: str = ""
    size_bytes: int = 0
    error_message: str = ""
    duration_seconds: float = 0.0
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "success": self.success,
            "filename": self.filename,
            "size_bytes": self.size_bytes,
            "error_message": self.error_message,
            "duration_seconds": self.duration_seconds,
        }


@dataclass
class RestoreResult:
    """恢复结果"""
    success: bool
    filename: str = ""
    error_message: str = ""
    duration_seconds: float = 0.0
    services_restarted: List[str] = field(default_factory=list)
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "success": self.success,
            "filename": self.filename,
            "error_message": self.error_message,
            "duration_seconds": self.duration_seconds,
            "services_restarted": self.services_restarted,
        }
