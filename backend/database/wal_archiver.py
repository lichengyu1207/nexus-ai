"""
WAL归档与PITR (Point-in-Time Recovery) 模块
支持时间点恢复、增量备份、灾难恢复
"""

from enum import Enum
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field
from datetime import datetime, timedelta
import asyncio
import asyncpg
import os
import shutil
import logging
import json
import gzip
from pathlib import Path

logger = logging.getLogger(__name__)


class BackupType(Enum):
    FULL = "full"
    INCREMENTAL = "incremental"
    WAL = "wal"


class RecoveryTarget(Enum):
    TIME = "time"
    XID = "xid"
    NAME = "name"
    LSN = "lsn"


@dataclass
class BackupConfig:
    archive_dir: str
    backup_dir: str
    wal_keep_segments: int = 32
    archive_timeout: int = 300
    max_wal_senders: int = 3
    retention_days: int = 30
    compress_wal: bool = True
    compress_level: int = 6
    schedule_cron: Optional[str] = None


@dataclass
class BackupInfo:
    backup_id: str
    backup_type: BackupType
    start_time: datetime
    end_time: Optional[datetime] = None
    start_wal: str = ""
    end_wal: str = ""
    start_lsn: str = ""
    end_lsn: str = ""
    size_bytes: int = 0
    status: str = "running"
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class WALArchiveInfo:
    wal_file: str
    archived_at: datetime
    size_bytes: int
    compressed: bool = False
    checksum: str = ""


@dataclass
class RecoveryPoint:
    target_type: RecoveryTarget
    target_value: str
    description: str = ""
    created_at: datetime = field(default_factory=datetime.now)


class WALArchiver:
    def __init__(self, config: BackupConfig):
        self.config = config
        self._archive_path = Path(config.archive_dir)
        self._backup_path = Path(config.backup_dir)
        self._backups: Dict[str, BackupInfo] = {}
        self._wal_archives: List[WALArchiveInfo] = []
        
    async def initialize(self):
        self._archive_path.mkdir(parents=True, exist_ok=True)
        self._backup_path.mkdir(parents=True, exist_ok=True)
        
        (self._archive_path / "wal").mkdir(exist_ok=True)
        (self._backup_path / "full").mkdir(exist_ok=True)
        (self._backup_path / "incremental").mkdir(exist_ok=True)
        
        await self._load_backup_history()
        
        logger.info(f"WALArchiver initialized: archive={self._archive_path}, backup={self._backup_path}")
        
    async def _load_backup_history(self):
        history_file = self._backup_path / "backup_history.json"
        if history_file.exists():
            with open(history_file, "r") as f:
                data = json.load(f)
                for backup_data in data.get("backups", []):
                    backup = BackupInfo(
                        backup_id=backup_data["backup_id"],
                        backup_type=BackupType(backup_data["backup_type"]),
                        start_time=datetime.fromisoformat(backup_data["start_time"]),
                        end_time=datetime.fromisoformat(backup_data["end_time"]) if backup_data.get("end_time") else None,
                        start_wal=backup_data.get("start_wal", ""),
                        end_wal=backup_data.get("end_wal", ""),
                        start_lsn=backup_data.get("start_lsn", ""),
                        end_lsn=backup_data.get("end_lsn", ""),
                        size_bytes=backup_data.get("size_bytes", 0),
                        status=backup_data.get("status", "completed"),
                        metadata=backup_data.get("metadata", {})
                    )
                    self._backups[backup.backup_id] = backup
                    
    async def _save_backup_history(self):
        history_file = self._backup_path / "backup_history.json"
        data = {
            "backups": [
                {
                    "backup_id": b.backup_id,
                    "backup_type": b.backup_type.value,
                    "start_time": b.start_time.isoformat(),
                    "end_time": b.end_time.isoformat() if b.end_time else None,
                    "start_wal": b.start_wal,
                    "end_wal": b.end_wal,
                    "start_lsn": b.start_lsn,
                    "end_lsn": b.end_lsn,
                    "size_bytes": b.size_bytes,
                    "status": b.status,
                    "metadata": b.metadata
                }
                for b in self._backups.values()
            ]
        }
        with open(history_file, "w") as f:
            json.dump(data, f, indent=2)
            
    async def archive_wal(self, wal_path: str) -> WALArchiveInfo:
        wal_file = os.path.basename(wal_path)
        archive_dest = self._archive_path / "wal" / wal_file
        
        if self.config.compress_wal:
            archive_dest = archive_dest.with_suffix(".gz")
            with open(wal_path, "rb") as f_in:
                with gzip.open(archive_dest, "wb", compresslevel=self.config.compress_level) as f_out:
                    shutil.copyfileobj(f_in, f_out)
        else:
            shutil.copy2(wal_path, archive_dest)
            
        size = archive_dest.stat().st_size
        checksum = await self._calculate_checksum(str(archive_dest))
        
        info = WALArchiveInfo(
            wal_file=wal_file,
            archived_at=datetime.now(),
            size_bytes=size,
            compressed=self.config.compress_wal,
            checksum=checksum
        )
        
        self._wal_archives.append(info)
        
        logger.info(f"Archived WAL file: {wal_file} -> {archive_dest}")
        return info
    
    async def _calculate_checksum(self, file_path: str) -> str:
        import hashlib
        sha256 = hashlib.sha256()
        with open(file_path, "rb") as f:
            for chunk in iter(lambda: f.read(8192), b""):
                sha256.update(chunk)
        return sha256.hexdigest()
    
    async def create_base_backup(self, conn: asyncpg.Connection) -> BackupInfo:
        backup_id = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        backup = BackupInfo(
            backup_id=backup_id,
            backup_type=BackupType.FULL,
            start_time=datetime.now(),
            status="running"
        )
        
        self._backups[backup_id] = backup
        await self._save_backup_history()
        
        try:
            start_info = await conn.fetchrow("SELECT pg_start_backup($1, true, false)", backup_id)
            backup.start_lsn = start_info["pg_start_backup"]
            
            backup_dir = self._backup_path / "full" / backup_id
            backup_dir.mkdir(exist_ok=True)
            
            data_dir = os.environ.get("PGDATA", "/var/lib/postgresql/data")
            
            for item in Path(data_dir).iterdir():
                if item.name in ["postmaster.pid", "postmaster.opts", "pg_wal", "pg_stat_tmp"]:
                    continue
                    
                dest = backup_dir / item.name
                if item.is_dir():
                    shutil.copytree(item, dest)
                else:
                    shutil.copy2(item, dest)
                    
            stop_info = await conn.fetchrow("SELECT pg_stop_backup(false)")
            backup.end_lsn = stop_info["pg_stop_backup"]
            backup.end_wal = stop_info["labelfile"].split("\n")[0].split(":")[1].strip()
            
            backup.size_bytes = sum(
                f.stat().st_size for f in backup_dir.rglob("*") if f.is_file()
            )
            
            backup.end_time = datetime.now()
            backup.status = "completed"
            
            label_file = backup_dir / "backup_label"
            with open(label_file, "w") as f:
                f.write(f"START WAL LOCATION: {backup.start_lsn}\n")
                f.write(f"START TIME: {backup.start_time.isoformat()}\n")
                f.write(f"BACKUP METHOD: pg_start_backup\n")
                f.write(f"BACKUP FROM: primary\n")
                
        except Exception as e:
            backup.status = "failed"
            backup.metadata["error"] = str(e)
            logger.error(f"Base backup failed: {e}")
            raise
            
        finally:
            await self._save_backup_history()
            
        logger.info(f"Base backup completed: {backup_id}")
        return backup
    
    async def create_incremental_backup(
        self, 
        conn: asyncpg.Connection,
        base_backup_id: str
    ) -> BackupInfo:
        if base_backup_id not in self._backups:
            raise ValueError(f"Base backup not found: {base_backup_id}")
            
        base_backup = self._backups[base_backup_id]
        if base_backup.backup_type != BackupType.FULL:
            raise ValueError("Base backup must be a full backup")
            
        backup_id = f"{base_backup_id}_inc_{datetime.now().strftime('%H%M%S')}"
        
        backup = BackupInfo(
            backup_id=backup_id,
            backup_type=BackupType.INCREMENTAL,
            start_time=datetime.now(),
            status="running",
            metadata={"base_backup_id": base_backup_id}
        )
        
        self._backups[backup_id] = backup
        
        try:
            current_lsn = await conn.fetchval("SELECT pg_current_wal_lsn()")
            backup.start_lsn = current_lsn
            
            inc_dir = self._backup_path / "incremental" / backup_id
            inc_dir.mkdir(exist_ok=True)
            
            wal_start = base_backup.end_wal
            wal_files = list((self._archive_path / "wal").glob("*"))
            
            for wal_file in wal_files:
                if self._compare_wal_names(wal_file.stem, wal_start) >= 0:
                    dest = inc_dir / wal_file.name
                    shutil.copy2(wal_file, dest)
                    
            backup.size_bytes = sum(
                f.stat().st_size for f in inc_dir.rglob("*") if f.is_file()
            )
            
            backup.end_time = datetime.now()
            backup.end_lsn = current_lsn
            backup.status = "completed"
            
        except Exception as e:
            backup.status = "failed"
            backup.metadata["error"] = str(e)
            raise
            
        finally:
            await self._save_backup_history()
            
        return backup
    
    def _compare_wal_names(self, wal1: str, wal2: str) -> int:
        def parse_wal(name: str) -> tuple:
            if len(name) >= 24:
                return (int(name[:8], 16), int(name[8:16], 16))
            return (0, 0)
            
        w1 = parse_wal(wal1.replace(".gz", ""))
        w2 = parse_wal(wal2.replace(".gz", ""))
        
        if w1 < w2:
            return -1
        elif w1 > w2:
            return 1
        return 0
    
    async def list_recovery_points(self) -> List[RecoveryPoint]:
        recovery_points = []
        
        for backup in self._backups.values():
            if backup.status == "completed":
                recovery_points.append(RecoveryPoint(
                    target_type=RecoveryTarget.TIME,
                    target_value=backup.end_time.isoformat() if backup.end_time else "",
                    description=f"Backup: {backup.backup_id} ({backup.backup_type.value})"
                ))
                
        wal_dir = self._archive_path / "wal"
        if wal_dir.exists():
            wal_files = sorted(wal_dir.glob("*"))
            if wal_files:
                first_wal = wal_files[0].stem.replace(".gz", "")
                last_wal = wal_files[-1].stem.replace(".gz", "")
                
                recovery_points.append(RecoveryPoint(
                    target_type=RecoveryTarget.LSN,
                    target_value=first_wal,
                    description=f"Earliest WAL: {first_wal}"
                ))
                
                recovery_points.append(RecoveryPoint(
                    target_type=RecoveryTarget.LSN,
                    target_value=last_wal,
                    description=f"Latest WAL: {last_wal}"
                ))
                
        return recovery_points
    
    async def prepare_recovery(
        self,
        target: RecoveryPoint,
        recovery_dir: str
    ) -> Dict[str, Any]:
        recovery_path = Path(recovery_dir)
        recovery_path.mkdir(parents=True, exist_ok=True)
        
        if target.target_type == RecoveryTarget.TIME:
            target_time = datetime.fromisoformat(target.target_value)
            suitable_backups = [
                b for b in self._backups.values()
                if b.status == "completed" 
                and b.end_time 
                and b.end_time <= target_time
            ]
            
            if not suitable_backups:
                raise ValueError(f"No backup found before {target.target_value}")
                
            base_backup = max(suitable_backups, key=lambda b: b.end_time or datetime.min)
            
        else:
            full_backups = [
                b for b in self._backups.values()
                if b.status == "completed" and b.backup_type == BackupType.FULL
            ]
            if not full_backups:
                raise ValueError("No full backup available")
            base_backup = max(full_backups, key=lambda b: b.end_time or datetime.min)
            
        base_dir = self._backup_path / "full" / base_backup.backup_id
        if not base_dir.exists():
            raise ValueError(f"Base backup not found: {base_backup.backup_id}")
            
        for item in base_dir.iterdir():
            dest = recovery_path / item.name
            if item.is_dir():
                shutil.copytree(item, dest)
            else:
                shutil.copy2(item, dest)
                
        wal_recovery_dir = recovery_path / "pg_wal"
        wal_recovery_dir.mkdir(exist_ok=True)
        
        wal_archive_dir = self._archive_path / "wal"
        if wal_archive_dir.exists():
            for wal_file in wal_archive_dir.iterdir():
                dest = wal_recovery_dir / wal_file.stem.replace(".gz", "")
                if wal_file.suffix == ".gz":
                    with gzip.open(wal_file, "rb") as f_in:
                        with open(dest, "wb") as f_out:
                            shutil.copyfileobj(f_in, f_out)
                else:
                    shutil.copy2(wal_file, dest)
                    
        recovery_conf = recovery_path / "recovery.signal"
        recovery_conf.touch()
        
        postgresql_conf = recovery_path / "postgresql.conf"
        with open(postgresql_conf, "a") as f:
            if target.target_type == RecoveryTarget.TIME:
                f.write(f"\nrestore_command = 'cp {self._archive_path}/wal/%f %p'\n")
                f.write(f"recovery_target_time = '{target.target_value}'\n")
            elif target.target_type == RecoveryTarget.LSN:
                f.write(f"\nrestore_command = 'cp {self._archive_path}/wal/%f %p'\n")
                f.write(f"recovery_target_lsn = '{target.target_value}'\n")
            elif target.target_type == RecoveryTarget.XID:
                f.write(f"\nrestore_command = 'cp {self._archive_path}/wal/%f %p'\n")
                f.write(f"recovery_target_xid = '{target.target_value}'\n")
                
            f.write("recovery_target_action = 'promote'\n")
            
        return {
            "recovery_dir": str(recovery_path),
            "base_backup": base_backup.backup_id,
            "target": target.target_value,
            "target_type": target.target_type.value
        }
    
    async def cleanup_old_backups(self):
        cutoff = datetime.now() - timedelta(days=self.config.retention_days)
        
        to_remove = [
            backup_id for backup_id, backup in self._backups.items()
            if backup.end_time and backup.end_time < cutoff
        ]
        
        for backup_id in to_remove:
            backup = self._backups[backup_id]
            
            if backup.backup_type == BackupType.FULL:
                backup_dir = self._backup_path / "full" / backup_id
            else:
                backup_dir = self._backup_path / "incremental" / backup_id
                
            if backup_dir.exists():
                shutil.rmtree(backup_dir)
                
            del self._backups[backup_id]
            logger.info(f"Removed old backup: {backup_id}")
            
        await self._save_backup_history()
        
        return to_remove
    
    async def get_backup_status(self) -> Dict[str, Any]:
        total_size = sum(b.size_bytes for b in self._backups.values())
        
        wal_size = sum(
            f.stat().st_size 
            for f in (self._archive_path / "wal").glob("*") 
            if f.is_file()
        ) if (self._archive_path / "wal").exists() else 0
        
        return {
            "backups": {
                "total": len(self._backups),
                "full": len([b for b in self._backups.values() if b.backup_type == BackupType.FULL]),
                "incremental": len([b for b in self._backups.values() if b.backup_type == BackupType.INCREMENTAL]),
                "total_size_bytes": total_size
            },
            "wal_archives": {
                "count": len(list((self._archive_path / "wal").glob("*"))) if (self._archive_path / "wal").exists() else 0,
                "total_size_bytes": wal_size
            },
            "config": {
                "archive_dir": str(self._archive_path),
                "backup_dir": str(self._backup_path),
                "retention_days": self.config.retention_days,
                "compress_wal": self.config.compress_wal
            },
            "latest_backup": max(
                [b for b in self._backups.values() if b.end_time],
                key=lambda b: b.end_time or datetime.min,
                default=None
            )
        }


async def create_wal_archiver(config: BackupConfig) -> WALArchiver:
    archiver = WALArchiver(config)
    await archiver.initialize()
    return archiver
