"""
Token自动回滚定时任务
定期检查并回滚长时间pending的Token预扣记录
"""
import asyncio
import logging
from datetime import datetime

logger = logging.getLogger(__name__)

_token_rollback_scheduler = None


class TokenRollbackScheduler:
    """Token自动回滚调度器"""
    
    def __init__(self, interval_minutes: int = 5, timeout_minutes: int = 30):
        self.interval_minutes = interval_minutes
        self.timeout_minutes = timeout_minutes
        self._running = False
        self._task = None
    
    async def start(self):
        """启动定时任务"""
        if self._running:
            logger.warning("Token rollback scheduler already running")
            return
        
        self._running = True
        self._task = asyncio.create_task(self._run_loop())
        logger.info(f"Token rollback scheduler started (interval={self.interval_minutes}min, timeout={self.timeout_minutes}min)")
    
    async def stop(self):
        """停止定时任务"""
        self._running = False
        if self._task:
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass
        logger.info("Token rollback scheduler stopped")
    
    async def _run_loop(self):
        """运行循环"""
        while self._running:
            try:
                await self._check_and_rollback()
            except Exception as e:
                logger.error(f"Token rollback check failed: {e}")
            
            await asyncio.sleep(self.interval_minutes * 60)
    
    async def _check_and_rollback(self):
        """检查并回滚pending记录"""
        from ..services.token_service import token_service
        
        try:
            rolled_back = await token_service.auto_rollback_pending(
                timeout_minutes=self.timeout_minutes
            )
            
            if rolled_back > 0:
                logger.info(f"Auto rolled back {rolled_back} pending token reservations")
        except Exception as e:
            logger.error(f"Failed to auto rollback tokens: {e}")


async def setup_token_rollback_scheduler():
    """设置Token自动回滚调度器"""
    global _token_rollback_scheduler
    
    if _token_rollback_scheduler is not None:
        logger.warning("Token rollback scheduler already set up")
        return
    
    _token_rollback_scheduler = TokenRollbackScheduler(
        interval_minutes=5,
        timeout_minutes=30
    )
    await _token_rollback_scheduler.start()


async def shutdown_token_rollback_scheduler():
    """关闭Token自动回滚调度器"""
    global _token_rollback_scheduler
    
    if _token_rollback_scheduler:
        await _token_rollback_scheduler.stop()
        _token_rollback_scheduler = None
