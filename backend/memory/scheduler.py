"""
记忆系统定时任务调度器
使用APScheduler定期执行记忆整理任务
"""
import asyncio
import logging
from datetime import datetime
from typing import List, Dict, Any
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from apscheduler.triggers.interval import IntervalTrigger

from ..memory.service import memory_service
from ..memory.consolidation import consolidator
from ..database import get_db_connection

logger = logging.getLogger(__name__)

scheduler = AsyncIOScheduler()

class MemoryScheduler:
    def __init__(self):
        self.scheduler = scheduler
        self._running = False
    
    async def start(self):
        if self._running:
            logger.warning("Memory scheduler already running")
            return
        
        self.scheduler.add_job(
            self.consolidate_all_users,
            CronTrigger(hour=3, minute=0),
            id="consolidate_memories_daily",
            name="每日记忆整理",
            replace_existing=True
        )
        
        self.scheduler.add_job(
            self.cleanup_old_memories,
            CronTrigger(hour=4, minute=0),
            id="cleanup_old_memories",
            name="清理过期记忆",
            replace_existing=True
        )
        
        self.scheduler.add_job(
            self.update_user_profiles,
            IntervalTrigger(hours=6),
            id="update_user_profiles",
            name="更新用户画像",
            replace_existing=True
        )
        
        self.scheduler.add_job(
            self.collect_memory_stats,
            IntervalTrigger(hours=1),
            id="collect_memory_stats",
            name="收集记忆统计",
            replace_existing=True
        )
        
        self.scheduler.start()
        self._running = True
        logger.info("Memory scheduler started")
    
    async def stop(self):
        if not self._running:
            return
        
        self.scheduler.shutdown(wait=True)
        self._running = False
        logger.info("Memory scheduler stopped")
    
    async def consolidate_all_users(self):
        logger.info("Starting daily memory consolidation...")
        
        try:
            conn = await get_db_connection()
            cursor = await conn.execute(
                "SELECT DISTINCT user_id FROM memory_entries"
            )
            rows = await cursor.fetchall()
            user_ids = [row[0] for row in rows]
            await conn.close()
            
            results = {
                "total_users": len(user_ids),
                "processed": 0,
                "failed": 0,
                "total_memories_merged": 0,
                "total_memories_forgotten": 0,
            }
            
            for user_id in user_ids:
                try:
                    result = await consolidator.consolidate_user_memories(user_id)
                    results["processed"] += 1
                    results["total_memories_merged"] += result.get("memories_merged", 0)
                    results["total_memories_forgotten"] += result.get("memories_forgotten", 0)
                except Exception as e:
                    logger.error(f"Failed to consolidate memories for user {user_id}: {e}")
                    results["failed"] += 1
            
            logger.info(f"Memory consolidation completed: {results}")
            return results
            
        except Exception as e:
            logger.error(f"Memory consolidation failed: {e}")
            return {"error": str(e)}
    
    async def cleanup_old_memories(self):
        logger.info("Starting cleanup of old memories...")
        
        try:
            conn = await get_db_connection()
            
            cursor = await conn.execute("""
                DELETE FROM memory_entries 
                WHERE importance < 2.0 
                AND access_count = 0 
                AND created_at < datetime('now', '-180 days')
            """)
            deleted_count = cursor.rowcount
            await conn.commit()
            await conn.close()
            
            logger.info(f"Cleaned up {deleted_count} old memories")
            return {"deleted_count": deleted_count}
            
        except Exception as e:
            logger.error(f"Memory cleanup failed: {e}")
            return {"error": str(e)}
    
    async def update_user_profiles(self):
        logger.info("Starting user profile updates...")
        
        try:
            conn = await get_db_connection()
            cursor = await conn.execute("""
                SELECT DISTINCT user_id FROM memory_entries
                WHERE created_at > datetime('now', '-7 days')
            """)
            rows = await cursor.fetchall()
            user_ids = [row[0] for row in rows]
            await conn.close()
            
            updated = 0
            for user_id in user_ids:
                try:
                    memories = await memory_service.retrieve(user_id, "", limit=20)
                    if memories:
                        preferences = {}
                        for memory in memories:
                            tags = memory.get("tags", "[]")
                            try:
                                tag_list = eval(tags) if isinstance(tags, str) else tags
                                for tag in tag_list:
                                    if ":" in tag:
                                        key, value = tag.split(":", 1)
                                        preferences[key] = value
                            except:
                                pass
                        
                        if preferences:
                            await memory_service.update_user_profile(user_id, {
                                "preferences": preferences
                            })
                            updated += 1
                except Exception as e:
                    logger.warning(f"Failed to update profile for user {user_id}: {e}")
            
            logger.info(f"Updated {updated} user profiles")
            return {"updated_profiles": updated}
            
        except Exception as e:
            logger.error(f"User profile update failed: {e}")
            return {"error": str(e)}
    
    async def collect_memory_stats(self):
        try:
            conn = await get_db_connection()
            
            cursor = await conn.execute(
                "SELECT COUNT(*) FROM memory_entries"
            )
            total_memories = (await cursor.fetchone())[0]
            
            cursor = await conn.execute(
                "SELECT COUNT(DISTINCT user_id) FROM memory_entries"
            )
            total_users = (await cursor.fetchone())[0]
            
            cursor = await conn.execute("""
                SELECT category, COUNT(*) as count 
                FROM memory_entries 
                GROUP BY category
            """)
            category_stats = dict(await cursor.fetchall())
            
            cursor = await conn.execute("""
                SELECT COUNT(*) FROM memory_entries
                WHERE created_at > datetime('now', '-1 day')
            """)
            daily_new = (await cursor.fetchone())[0]
            
            await conn.close()
            
            stats = {
                "total_memories": total_memories,
                "total_users": total_users,
                "category_distribution": category_stats,
                "daily_new_memories": daily_new,
                "collected_at": datetime.utcnow().isoformat()
            }
            
            logger.info(f"Memory stats collected: {stats}")
            return stats
            
        except Exception as e:
            logger.error(f"Failed to collect memory stats: {e}")
            return {"error": str(e)}
    
    def get_jobs(self) -> List[Dict[str, Any]]:
        jobs = []
        for job in self.scheduler.get_jobs():
            jobs.append({
                "id": job.id,
                "name": job.name,
                "next_run": str(job.next_run_time) if job.next_run_time else None,
                "trigger": str(job.trigger),
            })
        return jobs
    
    async def run_job_now(self, job_id: str):
        job = self.scheduler.get_job(job_id)
        if job:
            await job.func()
            return {"message": f"Job {job_id} executed"}
        return {"error": f"Job {job_id} not found"}

memory_scheduler = MemoryScheduler()

async def start_memory_scheduler():
    await memory_scheduler.start()

async def stop_memory_scheduler():
    await memory_scheduler.stop()
