"""
回滚恢复模块
负责从快照恢复系统状态
"""
import json
import logging
import os
import shutil
import time
from datetime import datetime
from pathlib import Path
from typing import List, Optional

from .config import SnapshotConfig
from .models import RestoreProgress, RestoreResult, SnapshotMetadata
from .storage import StorageBackend
from .utils import (
    ServiceManager,
    cleanup_dir,
    drop_and_create_schema,
    ensure_dir,
    extract_tarball,
    run_pg_restore,
)

logger = logging.getLogger(__name__)


class RestoreManager:
    """
    恢复管理器
    
    负责从快照恢复系统状态，包括：
    - 下载快照
    - 停止服务
    - 恢复数据库
    - 恢复配置文件
    - 重启服务
    """
    
    def __init__(self, config: SnapshotConfig, storage: StorageBackend):
        self.config = config
        self.storage = storage
        self.service_manager = ServiceManager(config.services)
        self._progress: Optional[RestoreProgress] = None
        self._restoring = False
    
    def get_progress(self) -> Optional[RestoreProgress]:
        """获取当前恢复进度"""
        return self._progress
    
    def is_restoring(self) -> bool:
        """是否正在恢复"""
        return self._restoring
    
    async def restore(
        self,
        filename: str,
        confirm: bool = False
    ) -> RestoreResult:
        """
        从快照恢复
        
        Args:
            filename: 快照文件名
            confirm: 是否已确认
            
        Returns:
            恢复结果
        """
        if self._restoring:
            return RestoreResult(
                success=False,
                error_message="已有恢复任务在进行中"
            )
        
        self._restoring = True
        start_time = time.time()
        
        self._progress = RestoreProgress(
            status="started",
            started_at=datetime.now()
        )
        
        try:
            remote_path = self.config.get_snapshot_path(filename)
            
            if not await self.storage.exists(remote_path):
                return RestoreResult(
                    success=False,
                    filename=filename,
                    error_message=f"快照不存在: {filename}"
                )
            
            temp_dir = Path(self.config.temp_dir) / "restore"
            cleanup_dir(str(temp_dir))
            ensure_dir(str(temp_dir))
            
            self._update_progress("downloading", "下载快照文件", 1)
            tarball_path = temp_dir / filename
            download_success = await self.storage.download(remote_path, str(tarball_path))
            if not download_success:
                return RestoreResult(
                    success=False,
                    filename=filename,
                    error_message="下载快照失败"
                )
            
            self._update_progress("extracting", "解压快照文件", 2)
            extract_dir = temp_dir / "extracted"
            ensure_dir(str(extract_dir))
            extract_success = extract_tarball(str(tarball_path), str(extract_dir))
            if not extract_success:
                return RestoreResult(
                    success=False,
                    filename=filename,
                    error_message="解压快照失败"
                )
            
            metadata = await self._load_metadata(extract_dir)
            
            self._update_progress("stopping_services", "停止服务", 3)
            stop_results = await self.service_manager.stop_services()
            logger.info(f"停止服务结果: {stop_results}")
            
            self._update_progress("restoring", "恢复数据", 4)
            
            db_success = await self._restore_database(extract_dir)
            if not db_success:
                logger.warning("数据库恢复失败，继续其他恢复")
            
            config_success = await self._restore_configs(extract_dir)
            
            self._update_progress("restarting_services", "重启服务", 5)
            start_results = await self.service_manager.start_services()
            logger.info(f"启动服务结果: {start_results}")
            
            services_restarted = [svc for svc, success in start_results.items() if success]
            
            duration = time.time() - start_time
            
            self._progress.status = "completed"
            self._progress.completed_at = datetime.now()
            
            logger.info(f"恢复完成: {filename}, 耗时: {duration:.2f} 秒")
            
            return RestoreResult(
                success=True,
                filename=filename,
                duration_seconds=duration,
                services_restarted=services_restarted
            )
            
        except Exception as e:
            logger.error(f"恢复失败: {e}")
            
            if self._progress:
                self._progress.status = "failed"
                self._progress.error_message = str(e)
                self._progress.completed_at = datetime.now()
            
            try:
                await self.service_manager.start_services()
            except Exception:
                pass
            
            return RestoreResult(
                success=False,
                filename=filename,
                error_message=str(e)
            )
        finally:
            self._restoring = False
            temp_dir = Path(self.config.temp_dir) / "restore"
            if temp_dir.exists():
                shutil.rmtree(temp_dir, ignore_errors=True)
    
    def _update_progress(self, status: str, step: str, completed: int) -> None:
        """更新进度"""
        if self._progress:
            self._progress.status = status
            self._progress.current_step = step
            self._progress.completed_steps = completed
    
    async def _load_metadata(self, extract_dir: Path) -> Optional[SnapshotMetadata]:
        """加载快照元数据"""
        metadata_path = extract_dir / "metadata.json"
        if metadata_path.exists():
            try:
                with open(metadata_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                return SnapshotMetadata.from_dict(data)
            except Exception as e:
                logger.error(f"加载元数据失败: {e}")
        return None
    
    async def _restore_database(self, extract_dir: Path) -> bool:
        """
        恢复数据库
        
        Args:
            extract_dir: 解压目录
            
        Returns:
            是否成功
        """
        db_dump_path = extract_dir / "database" / "db.dump"
        
        if not db_dump_path.exists():
            logger.warning(f"数据库备份文件不存在: {db_dump_path}")
            return False
        
        try:
            drop_success = await drop_and_create_schema(
                host=self.config.db_host,
                port=self.config.db_port,
                database=self.config.db_name,
                user=self.config.db_user,
                password=self.config.db_password
            )
            
            if not drop_success:
                logger.warning("重建 schema 失败，尝试直接恢复")
            
            restore_success = await run_pg_restore(
                host=self.config.db_host,
                port=self.config.db_port,
                database=self.config.db_name,
                user=self.config.db_user,
                password=self.config.db_password,
                input_path=str(db_dump_path),
                clean=True
            )
            
            if restore_success:
                logger.info("数据库恢复成功")
            else:
                logger.error("数据库恢复失败")
            
            return restore_success
            
        except Exception as e:
            logger.error(f"数据库恢复异常: {e}")
            return False
    
    async def _restore_configs(self, extract_dir: Path) -> bool:
        """
        恢复配置文件
        
        Args:
            extract_dir: 解压目录
            
        Returns:
            是否成功
        """
        config_source = extract_dir / "configs" / "current"
        config_dest = Path(self.config.config_path)
        
        if not config_source.exists():
            logger.warning(f"配置文件备份不存在: {config_source}")
            return False
        
        try:
            if config_dest.exists():
                backup_path = config_dest.parent / f"current_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
                shutil.move(str(config_dest), str(backup_path))
                logger.info(f"原配置已备份到: {backup_path}")
            
            shutil.copytree(config_source, config_dest)
            logger.info(f"配置文件恢复成功: {config_dest}")
            return True
            
        except Exception as e:
            logger.error(f"配置文件恢复失败: {e}")
            return False
    
    async def verify_snapshot(self, filename: str) -> dict:
        """
        验证快照
        
        Args:
            filename: 快照文件名
            
        Returns:
            验证结果
        """
        remote_path = self.config.get_snapshot_path(filename)
        
        result = {
            "exists": False,
            "downloadable": False,
            "metadata": None,
            "error": None
        }
        
        try:
            result["exists"] = await self.storage.exists(remote_path)
            
            if result["exists"]:
                temp_dir = Path(self.config.temp_dir) / "verify"
                ensure_dir(str(temp_dir))
                tarball_path = temp_dir / filename
                
                result["downloadable"] = await self.storage.download(
                    remote_path, str(tarball_path)
                )
                
                if result["downloadable"]:
                    extract_dir = temp_dir / "extracted"
                    extract_tarball(str(tarball_path), str(extract_dir))
                    result["metadata"] = await self._load_metadata(extract_dir)
                    if result["metadata"]:
                        result["metadata"] = result["metadata"].to_dict()
                
                shutil.rmtree(temp_dir, ignore_errors=True)
            
        except Exception as e:
            result["error"] = str(e)
        
        return result
