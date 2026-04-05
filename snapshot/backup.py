"""
备份创建模块
负责创建系统状态快照
"""
import json
import logging
import os
import time
from datetime import datetime
from pathlib import Path
from typing import List, Optional

from .config import SnapshotConfig
from .models import BackupResult, SnapshotMetadata, SnapshotInfo, SnapshotStatus
from .storage import StorageBackend
from .utils import (
    calculate_checksum,
    cleanup_dir,
    create_tarball,
    ensure_dir,
    format_timestamp,
    get_file_size,
    run_pg_dump,
)

logger = logging.getLogger(__name__)


class BackupManager:
    """
    备份管理器
    
    负责创建系统状态快照，包括：
    - 数据库备份
    - 配置文件备份
    - 元数据生成
    - 打包上传
    """
    
    def __init__(self, config: SnapshotConfig, storage: StorageBackend):
        self.config = config
        self.storage = storage
    
    async def create_snapshot(
        self,
        description: str = "",
        created_by: str = "system"
    ) -> BackupResult:
        """
        创建快照
        
        Args:
            description: 快照描述
            created_by: 创建者
            
        Returns:
            备份结果
        """
        start_time = time.time()
        timestamp = format_timestamp()
        filename = self.config.get_snapshot_filename(timestamp)
        
        logger.info(f"开始创建快照: {filename}")
        
        temp_dir = Path(self.config.temp_dir) / f"snapshot_{timestamp}"
        
        try:
            ensure_dir(str(temp_dir))
            
            db_success = await self._backup_database(temp_dir)
            if not db_success:
                logger.warning("数据库备份失败，继续其他备份")
            
            config_success = await self._backup_configs(temp_dir)
            
            metadata = await self._create_metadata(
                temp_dir,
                description,
                created_by,
                db_success
            )
            
            tarball_path = await self._create_tarball(temp_dir, timestamp)
            if not tarball_path:
                return BackupResult(
                    success=False,
                    error_message="创建压缩包失败"
                )
            
            remote_path = self.config.get_snapshot_path(filename)
            upload_success = await self.storage.upload(tarball_path, remote_path)
            if not upload_success:
                return BackupResult(
                    success=False,
                    error_message="上传到存储失败"
                )
            
            size_bytes = get_file_size(tarball_path)
            
            os.remove(tarball_path)
            
            duration = time.time() - start_time
            logger.info(f"快照创建成功: {filename}, 大小: {size_bytes} 字节, 耗时: {duration:.2f} 秒")
            
            return BackupResult(
                success=True,
                filename=filename,
                size_bytes=size_bytes,
                duration_seconds=duration
            )
            
        except Exception as e:
            logger.error(f"创建快照失败: {e}")
            return BackupResult(
                success=False,
                error_message=str(e)
            )
        finally:
            cleanup_dir(str(temp_dir.parent)) if temp_dir.parent.exists() else None
    
    async def _backup_database(self, temp_dir: Path) -> bool:
        """
        备份数据库
        
        Args:
            temp_dir: 临时目录
            
        Returns:
            是否成功
        """
        db_dir = temp_dir / "database"
        ensure_dir(str(db_dir))
        
        db_dump_path = db_dir / "db.dump"
        
        success = await run_pg_dump(
            host=self.config.db_host,
            port=self.config.db_port,
            database=self.config.db_name,
            user=self.config.db_user,
            password=self.config.db_password,
            output_path=str(db_dump_path),
            tables=self.config.backup_tables if self.config.backup_tables else None,
            format="custom"
        )
        
        if success:
            logger.info(f"数据库备份成功: {db_dump_path}")
        else:
            logger.error("数据库备份失败")
        
        return success
    
    async def _backup_configs(self, temp_dir: Path) -> bool:
        """
        备份配置文件
        
        Args:
            temp_dir: 临时目录
            
        Returns:
            是否成功
        """
        config_source = Path(self.config.config_path)
        config_dest = temp_dir / "configs"
        
        if not config_source.exists():
            logger.warning(f"配置目录不存在: {config_source}")
            ensure_dir(str(config_dest))
            return True
        
        try:
            import shutil
            shutil.copytree(config_source, config_dest / "current")
            logger.info(f"配置文件备份成功: {config_dest}")
            return True
        except Exception as e:
            logger.error(f"配置文件备份失败: {e}")
            return False
    
    async def _create_metadata(
        self,
        temp_dir: Path,
        description: str,
        created_by: str,
        db_success: bool
    ) -> SnapshotMetadata:
        """
        创建快照元数据
        
        Args:
            temp_dir: 临时目录
            description: 描述
            created_by: 创建者
            db_success: 数据库备份是否成功
            
        Returns:
            元数据对象
        """
        config_files = []
        config_dir = temp_dir / "configs" / "current"
        if config_dir.exists():
            for f in config_dir.rglob("*"):
                if f.is_file():
                    config_files.append(str(f.relative_to(config_dir)))
        
        metadata = SnapshotMetadata(
            version="1.0",
            created_at=datetime.now(),
            description=description,
            created_by=created_by,
            db_version="postgresql",
            config_files=config_files,
            tables=self.config.backup_tables,
        )
        
        metadata_path = temp_dir / "metadata.json"
        with open(metadata_path, 'w', encoding='utf-8') as f:
            json.dump(metadata.to_dict(), f, indent=2, ensure_ascii=False)
        
        logger.info(f"元数据创建成功: {metadata_path}")
        return metadata
    
    async def _create_tarball(self, temp_dir: Path, timestamp: str) -> Optional[str]:
        """
        创建压缩包
        
        Args:
            temp_dir: 临时目录
            timestamp: 时间戳
            
        Returns:
            压缩包路径
        """
        output_dir = Path(self.config.temp_dir)
        ensure_dir(str(output_dir))
        
        tarball_path = output_dir / f"snapshot_{timestamp}.tar.gz"
        
        source_paths = []
        for item in temp_dir.iterdir():
            source_paths.append(str(item))
        
        success = create_tarball(
            source_paths,
            str(tarball_path),
            base_dir=str(temp_dir)
        )
        
        if success:
            return str(tarball_path)
        return None
    
    async def list_snapshots(self) -> List[SnapshotInfo]:
        """
        列出所有快照
        
        Returns:
            快照列表
        """
        objects = await self.storage.list_objects(self.config.snapshot_prefix)
        
        snapshots = []
        for obj in objects:
            filename = os.path.basename(obj)
            metadata = await self.storage.get_metadata(obj)
            
            snapshot = SnapshotInfo(
                filename=filename,
                created_at=datetime.now(),
                size_bytes=metadata.get("size_bytes", 0) if metadata else 0,
                description=metadata.get("description", "") if metadata else "",
                status=SnapshotStatus.AVAILABLE,
                created_by=metadata.get("created_by", "system") if metadata else "system",
            )
            
            if filename.startswith("snapshot_"):
                ts_str = filename.replace("snapshot_", "").replace(".tar.gz", "")
                try:
                    snapshot.created_at = datetime.strptime(ts_str, "%Y%m%d_%H%M%S")
                except ValueError:
                    pass
            
            snapshots.append(snapshot)
        
        snapshots.sort(key=lambda x: x.created_at, reverse=True)
        return snapshots
    
    async def cleanup_old_snapshots(self) -> int:
        """
        清理旧快照
        
        Returns:
            删除的快照数量
        """
        snapshots = await self.list_snapshots()
        
        if len(snapshots) <= self.config.max_snapshots:
            return 0
        
        to_delete = snapshots[self.config.max_snapshots:]
        deleted_count = 0
        
        for snapshot in to_delete:
            remote_path = self.config.get_snapshot_path(snapshot.filename)
            if await self.storage.delete(remote_path):
                deleted_count += 1
                logger.info(f"已删除旧快照: {snapshot.filename}")
        
        return deleted_count
    
    async def get_snapshot_info(self, filename: str) -> Optional[SnapshotInfo]:
        """
        获取快照信息
        
        Args:
            filename: 快照文件名
            
        Returns:
            快照信息
        """
        remote_path = self.config.get_snapshot_path(filename)
        
        if not await self.storage.exists(remote_path):
            return None
        
        metadata = await self.storage.get_metadata(remote_path)
        
        snapshot = SnapshotInfo(
            filename=filename,
            created_at=datetime.now(),
            size_bytes=metadata.get("size_bytes", 0) if metadata else 0,
            description=metadata.get("description", "") if metadata else "",
            status=SnapshotStatus.AVAILABLE,
            created_by=metadata.get("created_by", "system") if metadata else "system",
        )
        
        if filename.startswith("snapshot_"):
            ts_str = filename.replace("snapshot_", "").replace(".tar.gz", "")
            try:
                snapshot.created_at = datetime.strptime(ts_str, "%Y%m%d_%H%M%S")
            except ValueError:
                pass
        
        return snapshot
