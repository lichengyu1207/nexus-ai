"""
审计日志归档任务
定期将超过保留期限的日志归档并清理
"""
import asyncio
import gzip
import hashlib
import json
import os
import uuid
from datetime import datetime, timedelta
from typing import Optional, Dict, Any, List
import logging

from ..database import get_db_connection

logger = logging.getLogger(__name__)


class AuditArchiveConfig:
    def __init__(self):
        self.enabled = True
        self.retention_days = 180
        self.archive_after_days = 150
        self.schedule_cron = "0 2 * * 0"
        self.storage_type = "local"
        self.storage_path = "./archives/audit"
        self.compress_format = "gzip"
        self.max_archive_size_mb = 100
    
    @classmethod
    async def load(cls) -> 'AuditArchiveConfig':
        config = cls()
        conn = await get_db_connection()
        try:
            cursor = await conn.execute(
                "SELECT * FROM audit_archive_config WHERE id = 'default'"
            )
            row = await cursor.fetchone()
            if row:
                row_dict = dict(row)
                config.enabled = bool(row_dict.get("enabled", 1))
                config.retention_days = row_dict.get("retention_days", 30)
                config.archive_after_days = row_dict.get("archive_after_days", 150)
                config.schedule_cron = row_dict.get("schedule_cron", "0 2 * * 0")
                config.storage_type = row_dict.get("storage_type", "local")
                config.storage_path = row_dict.get("storage_path", "./archives/audit")
                config.compress_format = row_dict.get("compress_format", "gzip")
                config.max_archive_size_mb = row_dict.get("max_archive_size_mb", 100)
        except Exception as e:
            logger.warning(f"Could not load audit archive config: {e}")
        finally:
            await conn.close()
        return config
    
    async def save(self, updated_by: Optional[str] = None):
        conn = await get_db_connection()
        try:
            await conn.execute("""
                UPDATE audit_archive_config SET
                    enabled = ?,
                    retention_days = ?,
                    archive_after_days = ?,
                    schedule_cron = ?,
                    storage_type = ?,
                    storage_path = ?,
                    compress_format = ?,
                    max_archive_size_mb = ?,
                    updated_at = CURRENT_TIMESTAMP,
                    updated_by = ?
                WHERE id = 'default'
            """, (
                self.enabled,
                self.retention_days,
                self.archive_after_days,
                self.schedule_cron,
                self.storage_type,
                self.storage_path,
                self.compress_format,
                self.max_archive_size_mb,
                updated_by
            ))
            await conn.commit()
        finally:
            await conn.close()


class AuditArchiver:
    def __init__(self, config: Optional[AuditArchiveConfig] = None):
        self.config = config or AuditArchiveConfig()
    
    async def run_archive(self) -> Dict[str, Any]:
        if not self.config.enabled:
            logger.info("Audit archiving is disabled")
            return {"status": "disabled", "message": "归档功能已禁用"}
        
        self.config = await AuditArchiveConfig.load()
        
        cutoff_date = datetime.utcnow() - timedelta(days=self.config.archive_after_days)
        logger.info(f"Starting audit log archiving, cutoff date: {cutoff_date}")
        
        result = {
            "status": "completed",
            "started_at": datetime.utcnow().isoformat(),
            "cutoff_date": cutoff_date.isoformat(),
            "archives_created": 0,
            "logs_archived": 0,
            "logs_deleted": 0,
            "errors": [],
        }
        
        try:
            os.makedirs(self.config.storage_path, exist_ok=True)
            
            while True:
                batch_result = await self._archive_batch(cutoff_date)
                
                if batch_result["log_count"] == 0:
                    break
                
                result["archives_created"] += 1
                result["logs_archived"] += batch_result["log_count"]
                result["logs_deleted"] += batch_result.get("deleted_count", 0)
                
                if batch_result.get("error"):
                    result["errors"].append(batch_result["error"])
                
                if batch_result["log_count"] < 10000:
                    break
            
            await self._cleanup_expired_archives()
            
        except Exception as e:
            logger.error(f"Archive failed: {e}")
            result["status"] = "failed"
            result["errors"].append(str(e))
        
        result["completed_at"] = datetime.utcnow().isoformat()
        
        await self._update_last_run_time()
        
        return result
    
    async def _archive_batch(self, cutoff_date: datetime) -> Dict[str, Any]:
        conn = await get_db_connection()
        try:
            cursor = await conn.execute("""
                SELECT * FROM audit_logs
                WHERE timestamp < ?
                ORDER BY timestamp ASC
                LIMIT 10000
            """, (cutoff_date.isoformat(),))
            
            logs = await cursor.fetchall()
            
            if not logs:
                return {"log_count": 0}
            
            logs_list = [dict(log) for log in logs]
            
            archive_id = str(uuid.uuid4())
            timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
            filename = f"audit_archive_{timestamp}_{archive_id[:8]}.jsonl.gz"
            file_path = os.path.join(self.config.storage_path, filename)
            
            file_checksum = await self._write_archive_file(logs_list, file_path)
            
            file_size = os.path.getsize(file_path)
            
            first_log = logs_list[0]
            last_log = logs_list[-1]
            
            await conn.execute("""
                INSERT INTO audit_archives
                (id, filename, file_path, file_size, compressed_size,
                 start_timestamp, end_timestamp, log_count,
                 first_log_id, last_log_id, first_hash, last_hash,
                 checksum, storage_type, storage_location, retention_days, status)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                archive_id,
                filename,
                file_path,
                sum(len(json.dumps(log, default=str)) for log in logs_list),
                file_size,
                first_log["timestamp"],
                last_log["timestamp"],
                len(logs_list),
                first_log["id"],
                last_log["id"],
                first_log.get("hash"),
                last_log.get("hash"),
                file_checksum,
                self.config.storage_type,
                self.config.storage_path,
                self.config.retention_days,
                "completed"
            ))
            
            log_ids = [log["id"] for log in logs_list]
            placeholders = ",".join("?" * len(log_ids))
            await conn.execute(
                f"DELETE FROM audit_logs WHERE id IN ({placeholders})",
                log_ids
            )
            
            await conn.commit()
            
            logger.info(f"Archived {len(logs_list)} logs to {filename}")
            
            return {
                "log_count": len(logs_list),
                "deleted_count": len(logs_list),
                "archive_id": archive_id,
                "filename": filename,
            }
            
        except Exception as e:
            logger.error(f"Batch archive failed: {e}")
            return {"log_count": 0, "error": str(e)}
        finally:
            await conn.close()
    
    async def _write_archive_file(self, logs: List[Dict], file_path: str) -> str:
        hasher = hashlib.sha256()
        
        with gzip.open(file_path, 'wt', encoding='utf-8') as f:
            for log in logs:
                line = json.dumps(log, default=str, ensure_ascii=False)
                f.write(line + "\n")
                hasher.update(line.encode('utf-8'))
        
        return hasher.hexdigest()
    
    async def _cleanup_expired_archives(self):
        conn = await get_db_connection()
        try:
            expiration_date = datetime.utcnow() - timedelta(days=self.config.retention_days)
            
            cursor = await conn.execute("""
                SELECT id, file_path FROM audit_archives
                WHERE archived_at < ?
            """, (expiration_date.isoformat(),))
            
            expired = await cursor.fetchall()
            
            for archive in expired:
                try:
                    if os.path.exists(archive["file_path"]):
                        os.remove(archive["file_path"])
                        logger.info(f"Deleted expired archive: {archive['file_path']}")
                except Exception as e:
                    logger.warning(f"Failed to delete archive file: {e}")
                
                await conn.execute(
                    "DELETE FROM audit_archives WHERE id = ?",
                    (archive["id"],)
                )
            
            await conn.commit()
            
            if expired:
                logger.info(f"Cleaned up {len(expired)} expired archives")
                
        finally:
            await conn.close()
    
    async def _update_last_run_time(self):
        conn = await get_db_connection()
        try:
            await conn.execute("""
                UPDATE audit_archive_config SET
                    last_run_at = CURRENT_TIMESTAMP
                WHERE id = 'default'
            """)
            await conn.commit()
        finally:
            await conn.close()
    
    async def restore_archive(self, archive_id: str, restored_by: Optional[str] = None) -> Dict[str, Any]:
        conn = await get_db_connection()
        try:
            cursor = await conn.execute(
                "SELECT * FROM audit_archives WHERE id = ?",
                (archive_id,)
            )
            archive = await cursor.fetchone()
            
            if not archive:
                return {"status": "failed", "error": "归档文件不存在"}
            
            archive_dict = dict(archive)
            file_path = archive_dict["file_path"]
            
            if not os.path.exists(file_path):
                return {"status": "failed", "error": "归档文件已丢失"}
            
            restore_id = str(uuid.uuid4())
            logs_restored = 0
            
            with gzip.open(file_path, 'rt', encoding='utf-8') as f:
                for line in f:
                    try:
                        log = json.loads(line.strip())
                        
                        await conn.execute("""
                            INSERT OR IGNORE INTO audit_logs
                            (id, timestamp, user_id, username, user_role,
                             ip_address, user_agent, action_type, resource_type,
                             resource_id, old_value, new_value, status, error_message,
                             hash, prev_hash, created_at)
                            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                        """, (
                            log.get("id"),
                            log.get("timestamp"),
                            log.get("user_id"),
                            log.get("username"),
                            log.get("user_role"),
                            log.get("ip_address"),
                            log.get("user_agent"),
                            log.get("action_type"),
                            log.get("resource_type"),
                            log.get("resource_id"),
                            json.dumps(log.get("old_value")) if log.get("old_value") else None,
                            json.dumps(log.get("new_value")) if log.get("new_value") else None,
                            log.get("status"),
                            log.get("error_message"),
                            log.get("hash"),
                            log.get("prev_hash"),
                            log.get("created_at"),
                        ))
                        logs_restored += 1
                    except Exception as e:
                        logger.warning(f"Failed to restore log: {e}")
            
            await conn.execute("""
                INSERT INTO audit_archive_restores
                (id, archive_id, restored_by, log_count, status)
                VALUES (?, ?, ?, ?, ?)
            """, (restore_id, archive_id, restored_by, logs_restored, "completed"))
            
            await conn.commit()
            
            logger.info(f"Restored {logs_restored} logs from archive {archive_id}")
            
            return {
                "status": "completed",
                "restore_id": restore_id,
                "logs_restored": logs_restored,
            }
            
        except Exception as e:
            logger.error(f"Restore failed: {e}")
            return {"status": "failed", "error": str(e)}
        finally:
            await conn.close()
    
    async def verify_archive(self, archive_id: str) -> Dict[str, Any]:
        conn = await get_db_connection()
        try:
            cursor = await conn.execute(
                "SELECT * FROM audit_archives WHERE id = ?",
                (archive_id,)
            )
            archive = await cursor.fetchone()
            
            if not archive:
                return {"valid": False, "error": "归档文件不存在"}
            
            archive_dict = dict(archive)
            file_path = archive_dict["file_path"]
            
            if not os.path.exists(file_path):
                return {"valid": False, "error": "归档文件已丢失"}
            
            hasher = hashlib.sha256()
            log_count = 0
            first_hash = None
            last_hash = None
            prev_hash = "0" * 64
            
            chain_valid = True
            chain_errors = []
            
            with gzip.open(file_path, 'rt', encoding='utf-8') as f:
                for i, line in enumerate(f):
                    try:
                        log = json.loads(line.strip())
                        log_count += 1
                        
                        hasher.update(line.encode('utf-8'))
                        
                        if i == 0:
                            first_hash = log.get("hash")
                        
                        last_hash = log.get("hash")
                        
                        if log.get("prev_hash") != prev_hash:
                            chain_valid = False
                            chain_errors.append({
                                "index": i,
                                "expected": prev_hash[:16],
                                "actual": log.get("prev_hash", "")[:16] if log.get("prev_hash") else None,
                            })
                        
                        prev_hash = log.get("hash", "")
                        
                    except Exception as e:
                        logger.warning(f"Failed to verify log at index {i}: {e}")
            
            computed_checksum = hasher.hexdigest()
            checksum_valid = computed_checksum == archive_dict["checksum"]
            
            return {
                "valid": checksum_valid and chain_valid,
                "log_count": log_count,
                "expected_count": archive_dict["log_count"],
                "checksum_valid": checksum_valid,
                "chain_valid": chain_valid,
                "chain_errors": chain_errors[:10],
                "first_hash": first_hash,
                "last_hash": last_hash,
            }
            
        except Exception as e:
            logger.error(f"Verify failed: {e}")
            return {"valid": False, "error": str(e)}
        finally:
            await conn.close()


audit_archiver = AuditArchiver()


async def run_archive_task():
    return await audit_archiver.run_archive()


class ArchiveScheduler:
    def __init__(self):
        self._running = False
        self._task: Optional[asyncio.Task] = None
    
    async def start(self):
        if self._running:
            return
        
        self._running = True
        self._task = asyncio.create_task(self._run_loop())
        logger.info("Audit archive scheduler started")
    
    async def stop(self):
        self._running = False
        if self._task:
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass
        logger.info("Audit archive scheduler stopped")
    
    async def _run_loop(self):
        while self._running:
            try:
                config = await AuditArchiveConfig.load()
                
                if config.enabled:
                    result = await run_archive_task()
                    logger.info(f"Archive task completed: {result}")
                
            except Exception as e:
                logger.error(f"Archive task failed: {e}")
            
            await asyncio.sleep(7 * 24 * 60 * 60)


archive_scheduler = ArchiveScheduler()


async def setup_archive_scheduler():
    await archive_scheduler.start()


async def shutdown_archive_scheduler():
    await archive_scheduler.stop()
