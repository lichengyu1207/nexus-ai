"""
定时任务调度
负责定时执行快照创建和清理
"""
import asyncio
import logging
from datetime import datetime
from typing import Callable, List, Optional

from .backup import BackupManager
from .config import SnapshotConfig
from .storage import StorageBackend

logger = logging.getLogger(__name__)


class SnapshotScheduler:
    """
    快照调度器
    
    负责定时执行：
    - 每日自动快照
    - 旧快照清理
    """
    
    def __init__(
        self,
        config: SnapshotConfig,
        backup_manager: BackupManager,
        on_snapshot_created: Optional[Callable] = None,
        on_snapshot_deleted: Optional[Callable] = None
    ):
        self.config = config
        self.backup_manager = backup_manager
        self.on_snapshot_created = on_snapshot_created
        self.on_snapshot_deleted = on_snapshot_deleted
        
        self._scheduler: Optional[any] = None
        self._running = False
        self._task: Optional[asyncio.Task] = None
    
    def start(self) -> None:
        """启动调度器"""
        if self._running:
            return
        
        self._running = True
        
        try:
            from apscheduler.schedulers.asyncio import AsyncIOScheduler
            from apscheduler.triggers.cron import CronTrigger
            
            self._scheduler = AsyncIOScheduler()
            
            self._scheduler.add_job(
                self._create_daily_snapshot,
                CronTrigger(
                    hour=self.config.schedule_hour,
                    minute=self.config.schedule_minute
                ),
                id='daily_snapshot',
                name='每日快照',
                replace_existing=True
            )
            
            self._scheduler.add_job(
                self._cleanup_old_snapshots,
                CronTrigger(hour=3, minute=0),
                id='cleanup_snapshots',
                name='清理旧快照',
                replace_existing=True
            )
            
            self._scheduler.start()
            logger.info(
                f"调度器已启动，每日快照时间: "
                f"{self.config.schedule_hour:02d}:{self.config.schedule_minute:02d}"
            )
            
        except ImportError:
            logger.warning("未安装 APScheduler，使用简单定时任务")
            self._task = asyncio.create_task(self._simple_scheduler())
    
    def stop(self) -> None:
        """停止调度器"""
        self._running = False
        
        if self._scheduler:
            self._scheduler.shutdown()
            self._scheduler = None
        
        if self._task:
            self._task.cancel()
            self._task = None
        
        logger.info("调度器已停止")
    
    async def _create_daily_snapshot(self) -> None:
        """创建每日快照"""
        logger.info("开始执行每日快照任务")
        
        try:
            result = await self.backup_manager.create_snapshot(
                description="自动每日备份",
                created_by="scheduler"
            )
            
            if result.success:
                logger.info(f"每日快照创建成功: {result.filename}")
                
                if self.on_snapshot_created:
                    try:
                        self.on_snapshot_created(result)
                    except Exception as e:
                        logger.error(f"快照创建回调失败: {e}")
            else:
                logger.error(f"每日快照创建失败: {result.error_message}")
                
        except Exception as e:
            logger.error(f"每日快照任务异常: {e}")
    
    async def _cleanup_old_snapshots(self) -> None:
        """清理旧快照"""
        logger.info("开始执行快照清理任务")
        
        try:
            deleted_count = await self.backup_manager.cleanup_old_snapshots()
            
            if deleted_count > 0:
                logger.info(f"已清理 {deleted_count} 个旧快照")
                
                if self.on_snapshot_deleted:
                    try:
                        self.on_snapshot_deleted(deleted_count)
                    except Exception as e:
                        logger.error(f"快照清理回调失败: {e}")
            else:
                logger.info("无需清理旧快照")
                
        except Exception as e:
            logger.error(f"快照清理任务异常: {e}")
    
    async def _simple_scheduler(self) -> None:
        """简单定时任务（无 APScheduler 时使用）"""
        while self._running:
            try:
                now = datetime.now()
                target_hour = self.config.schedule_hour
                target_minute = self.config.schedule_minute
                
                next_run = now.replace(
                    hour=target_hour,
                    minute=target_minute,
                    second=0,
                    microsecond=0
                )
                
                if next_run <= now:
                    from datetime import timedelta
                    next_run += timedelta(days=1)
                
                wait_seconds = (next_run - now).total_seconds()
                logger.info(f"下次快照时间: {next_run}, 等待 {wait_seconds:.0f} 秒")
                
                await asyncio.sleep(wait_seconds)
                
                if self._running:
                    await self._create_daily_snapshot()
                    await asyncio.sleep(60)
                    await self._cleanup_old_snapshots()
                    
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"简单调度器异常: {e}")
                await asyncio.sleep(60)
    
    def get_jobs(self) -> List[dict]:
        """获取所有任务"""
        if not self._scheduler:
            return []
        
        jobs = []
        for job in self._scheduler.get_jobs():
            jobs.append({
                "id": job.id,
                "name": job.name,
                "next_run": str(job.next_run_time) if job.next_run_time else None,
                "trigger": str(job.trigger),
            })
        return jobs
    
    def trigger_snapshot(self) -> bool:
        """手动触发快照"""
        if not self._scheduler:
            return False
        
        try:
            self._scheduler.modify_job('daily_snapshot', next_run_time=datetime.now())
            logger.info("已触发手动快照")
            return True
        except Exception as e:
            logger.error(f"触发快照失败: {e}")
            return False
    
    def trigger_cleanup(self) -> bool:
        """手动触发清理"""
        if not self._scheduler:
            return False
        
        try:
            self._scheduler.modify_job('cleanup_snapshots', next_run_time=datetime.now())
            logger.info("已触发手动清理")
            return True
        except Exception as e:
            logger.error(f"触发清理失败: {e}")
            return False
