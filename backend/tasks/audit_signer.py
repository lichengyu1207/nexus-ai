"""
审计日志后台任务
定期签名未处理的审计日志
"""
import asyncio
import logging
from datetime import datetime, timedelta
from typing import Optional

from ..services.audit_verification import audit_verification

logger = logging.getLogger(__name__)


class AuditSignerScheduler:
    def __init__(self, batch_size: int = 100, interval_minutes: int = 60):
        self.batch_size = batch_size
        self.interval_minutes = interval_minutes
        self._running = False
        self._task: Optional[asyncio.Task] = None
    
    async def start(self):
        if self._running:
            logger.warning("Audit signer is already running")
            return
        
        self._running = True
        self._task = asyncio.create_task(self._run_loop())
        logger.info(f"Audit signer started (interval: {self.interval_minutes}min, batch: {self.batch_size})")
    
    async def stop(self):
        self._running = False
        if self._task:
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass
        logger.info("Audit signer stopped")
    
    async def _run_loop(self):
        while self._running:
            try:
                signed_count = await audit_verification.sign_unbatched_logs(self.batch_size)
                if signed_count > 0:
                    logger.info(f"Signed {signed_count} audit logs")
            except Exception as e:
                logger.error(f"Error signing audit logs: {e}")
            
            await asyncio.sleep(self.interval_minutes * 60)
    
    async def sign_now(self) -> int:
        return await audit_verification.sign_unbatched_logs(self.batch_size)


audit_signer = AuditSignerScheduler()


async def setup_audit_signer():
    await audit_signer.start()


async def shutdown_audit_signer():
    await audit_signer.stop()
