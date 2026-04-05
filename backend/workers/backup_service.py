"""
自动备份服务
Automatic Backup Service

实现数据库自动备份和恢复功能
"""

import os
import json
import time
import asyncio
import logging
import subprocess
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from pathlib import Path
import shutil

logger = logging.getLogger(__name__)


class BackupConfig:
    backup_dir: str = "backups"
    retention_days: int = 30
    compress_backups: bool = True
    include_logs: bool = True
    database_url: str = "postgresql://postgres:postgres@localhost:5432/fangdu"
    schedule_hour: int = 3


class BackupService:
    
    def __init__(self, config: Optional[BackupConfig] = None):
        self.config = config or BackupConfig()
        self.backup_dir = Path(self.config.backup_dir)
        self.backup_dir.mkdir(parents=True, exist_ok=True)
        
        self.backup_history: List[Dict] = []
    
    async def create_backup(self, backup_type: str = "full") -> Dict:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_name = f"fangdu_{backup_type}_{timestamp}"
        backup_path = self.backup_dir / backup_name
        
        start_time = time.time()
        
        try:
            backup_path.mkdir(parents=True, exist_ok=True)
            
            await self._backup_database(backup_path)
            
            if self.config.include_logs:
                await self._backup_logs(backup_path)
            
            await self._backup_config(backup_path)
            
            if self.config.compress_backups:
                await self._compress_backup(backup_path)
            
            duration = time.time() - start_time
            
            backup_info = {
                "name": backup_name,
                "type": backup_type,
                "path": str(backup_path),
                "created_at": datetime.now().isoformat(),
                "duration_seconds": duration,
                "size_bytes": self._get_backup_size(backup_path),
                "status": "success"
            }
            
            self.backup_history.append(backup_info)
            
            await self._cleanup_old_backups()
            
            logger.info(f"Backup created successfully: {backup_name}")
            
            return backup_info
            
        except Exception as e:
            logger.error(f"Backup failed: {e}")
            
            backup_info = {
                "name": backup_name,
                "type": backup_type,
                "path": str(backup_path),
                "created_at": datetime.now().isoformat(),
                "status": "failed",
                "error": str(e)
            }
            
            self.backup_history.append(backup_info)
            
            raise
    
    async def _backup_database(self, backup_path: Path):
        db_backup_path = backup_path / "database"
        db_backup_path.mkdir(parents=True, exist_ok=True)
        
        env = os.environ.copy()
        env["PGPASSWORD"] = self._parse_db_url()["password"]
        
        cmd = [
            "pg_dump",
            "-h", self._parse_db_url()["host"],
            "-p", str(self._parse_db_url()["port"]),
            "-U", self._parse_db_url()["user"],
            "-d", self._parse_db_url()["database"],
            "-F", "c",
            "-f", str(db_backup_path / "full_backup.sql")
        ]
        
        process = await asyncio.create_subprocess_exec(
            *cmd,
            env=env,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )
        
        stdout, stderr = await process.communicate()
        
        if process.returncode != 0:
            raise Exception(f"pg_dump failed: {stderr.decode()}")
        
        logger.info(f"Database backup created at {db_backup_path}")
    
    def _parse_db_url(self) -> Dict:
        url = self.config.database_url
        url = url.replace("postgresql://", "")
        
        auth, host_db = url.split("@")
        user, password = auth.split(":")
        host_port, database = host_db.split("/")
        
        if ":" in host_port:
            host, port = host_port.split(":")
        else:
            host = host_port
            port = 5432
        
        return {
            "user": user,
            "password": password,
            "host": host,
            "port": int(port),
            "database": database
        }
    
    async def _backup_logs(self, backup_path: Path):
        logs_backup_path = backup_path / "logs"
        logs_backup_path.mkdir(parents=True, exist_ok=True)
        
        log_dirs = ["logs", "data/logs"]
        
        for log_dir in log_dirs:
            log_path = Path(log_dir)
            if log_path.exists():
                dest_path = logs_backup_path / log_path.name
                if log_path.is_dir():
                    shutil.copytree(log_path, dest_path)
                else:
                    shutil.copy2(log_path, dest_path)
        
        logger.info(f"Logs backup created at {logs_backup_path}")
    
    async def _backup_config(self, backup_path: Path):
        config_backup_path = backup_path / "config"
        config_backup_path.mkdir(parents=True, exist_ok=True)
        
        config_files = [
            ".env",
            "config.json",
            "docker-compose.yml",
            "nginx.conf"
        ]
        
        for config_file in config_files:
            config_path = Path(config_file)
            if config_path.exists():
                shutil.copy2(config_path, config_backup_path / config_file)
        
        logger.info(f"Config backup created at {config_backup_path}")
    
    async def _compress_backup(self, backup_path: Path):
        archive_path = str(backup_path) + ".tar.gz"
        
        cmd = ["tar", "-czf", archive_path, "-C", str(backup_path.parent), backup_path.name]
        
        process = await asyncio.create_subprocess_exec(
            *cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )
        
        stdout, stderr = await process.communicate()
        
        if process.returncode != 0:
            raise Exception(f"Compression failed: {stderr.decode()}")
        
        shutil.rmtree(backup_path)
        
        logger.info(f"Backup compressed to {archive_path}")
    
    def _get_backup_size(self, backup_path: Path) -> int:
        if backup_path.is_file():
            return backup_path.stat().st_size
        elif backup_path.is_dir():
            return sum(f.stat().st_size for f in backup_path.rglob("*") if f.is_file())
        return 0
    
    async def _cleanup_old_backups(self):
        cutoff_date = datetime.now() - timedelta(days=self.config.retention_days)
        
        for backup in list(self.backup_history):
            backup_time = datetime.fromisoformat(backup["created_at"])
            if backup_time < cutoff_date:
                backup_path = Path(backup["path"])
                if backup_path.exists():
                    if backup_path.is_dir():
                        shutil.rmtree(backup_path)
                    else:
                        backup_path.unlink()
                
                self.backup_history.remove(backup)
                logger.info(f"Removed old backup: {backup['name']}")
    
    async def restore_backup(self, backup_name: str) -> Dict:
        backup_path = self.backup_dir / backup_name
        
        if not backup_path.exists():
            archive_path = Path(str(backup_path) + ".tar.gz")
            if archive_path.exists():
                cmd = ["tar", "-xzf", str(archive_path), "-C", str(self.backup_dir)]
                process = await asyncio.create_subprocess_exec(*cmd)
                await process.communicate()
        
        if not backup_path.exists():
            raise FileNotFoundError(f"Backup not found: {backup_name}")
        
        start_time = time.time()
        
        try:
            await self._restore_database(backup_path)
            
            duration = time.time() - start_time
            
            return {
                "backup_name": backup_name,
                "restored_at": datetime.now().isoformat(),
                "duration_seconds": duration,
                "status": "success"
            }
            
        except Exception as e:
            logger.error(f"Restore failed: {e}")
            raise
    
    async def _restore_database(self, backup_path: Path):
        db_backup_path = backup_path / "database"
        sql_file = db_backup_path / "full_backup.sql"
        
        if not sql_file.exists():
            raise FileNotFoundError(f"SQL backup file not found: {sql_file}")
        
        env = os.environ.copy()
        env["PGPASSWORD"] = self._parse_db_url()["password"]
        
        cmd = [
            "psql",
            "-h", self._parse_db_url()["host"],
            "-p", str(self._parse_db_url()["port"]),
            "-U", self._parse_db_url()["user"],
            "-d", self._parse_db_url()["database"],
            "-f", str(sql_file)
        ]
        
        process = await asyncio.create_subprocess_exec(
            *cmd,
            env=env,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )
        
        stdout, stderr = await process.communicate()
        
        if process.returncode != 0:
            raise Exception(f"psql restore failed: {stderr.decode()}")
        
        logger.info(f"Database restored from {sql_file}")
    
    def list_backups(self) -> List[Dict]:
        backups = []
        
        for item in self.backup_dir.iterdir():
            if item.is_dir() or item.suffix == ".gz":
                stat = item.stat()
                backups.append({
                    "name": item.stem if item.suffix == ".gz" else item.name,
                    "path": str(item),
                    "size_bytes": stat.st_size,
                    "created_at": datetime.fromtimestamp(stat.st_ctime).isoformat(),
                    "compressed": item.suffix == ".gz"
                })
        
        return sorted(backups, key=lambda x: x["created_at"], reverse=True)
    
    def get_backup_status(self) -> Dict:
        return {
            "backup_dir": str(self.backup_dir),
            "retention_days": self.config.retention_days,
            "total_backups": len(self.list_backups()),
            "last_backup": self.backup_history[-1] if self.backup_history else None
        }


backup_service = BackupService()


async def scheduled_backup():
    """定时备份任务"""
    return await backup_service.create_backup("scheduled")


async def manual_backup(backup_type: str = "manual"):
    """手动备份"""
    return await backup_service.create_backup(backup_type)
