"""
审计日志安全备份服务
定期备份审计日志到加密文件
"""
import asyncio
import gzip
import os
import uuid
from datetime import datetime, timedelta
from typing import Optional, Dict, Any
import logging
import json
from pathlib import Path

from ..database import get_db_connection

logger = logging.getLogger(__name__)

try:
    from cryptography.fernet import Fernet
    from cryptography.hazmat.primitives import hashes
    from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
    import base64
    CRYPTO_AVAILABLE = True
except ImportError:
    CRYPTO_AVAILABLE = False
    logger.warning("cryptography library not available, backup encryption disabled")


class AuditBackupService:
    def __init__(self):
        self._running = False
        self._task: Optional[asyncio.Task] = None
        self._encryption_key = None
        self._load_or_generate_key()
    
    def _load_or_generate_key(self):
        if not CRYPTO_AVAILABLE:
            return
        
        key_dir = Path(__file__).parent.parent.parent / "keys"
        key_dir.mkdir(exist_ok=True)
        key_path = key_dir / "backup_key.key"
        
        if key_path.exists():
            with open(key_path, "rb") as f:
                self._encryption_key = f.read()
            logger.info("Loaded backup encryption key")
        else:
            self._encryption_key = Fernet.generate_key()
            with open(key_path, "wb") as f:
                f.write(self._encryption_key)
            os.chmod(key_path, 0o600)
            logger.info("Generated new backup encryption key")
    
    def _encrypt_data(self, data: bytes) -> bytes:
        if not CRYPTO_AVAILABLE or not self._encryption_key:
            return data
        
        fernet = Fernet(self._encryption_key)
        return fernet.encrypt(data)
    
    def _decrypt_data(self, data: bytes) -> bytes:
        if not CRYPTO_AVAILABLE or not self._encryption_key:
            return data
        
        fernet = Fernet(self._encryption_key)
        return fernet.decrypt(data)
    
    async def create_backup(
        self,
        backup_path: str = "./backups/audit",
        days: int = 30,
        encrypt: bool = True,
    ) -> Dict[str, Any]:
        """
        创建审计日志备份
        
        Args:
            backup_path: 备份目录路径
            days: 备份最近N天的日志
            encrypt: 是否加密备份
            
        Returns:
            备份结果信息
        """
        os.makedirs(backup_path, exist_ok=True)
        
        timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
        backup_id = str(uuid.uuid4())[:8]
        
        conn = await get_db_connection()
        try:
            since = datetime.utcnow() - timedelta(days=days)
            
            cursor = await conn.execute("""
                SELECT * FROM audit_logs
                WHERE timestamp >= ?
                ORDER BY timestamp ASC
            """, (since.isoformat(),))
            
            logs = await cursor.fetchall()
            
            if not logs:
                return {
                    "status": "skipped",
                    "message": "没有需要备份的日志",
                    "backup_id": backup_id,
                }
            
            logs_list = [dict(log) for log in logs]
            
            json_data = json.dumps(logs_list, default=str, ensure_ascii=False)
            compressed_data = gzip.compress(json_data.encode('utf-8'))
            
            if encrypt:
                final_data = self._encrypt_data(compressed_data)
                extension = ".enc.gz"
            else:
                final_data = compressed_data
                extension = ".gz"
            
            filename = f"audit_backup_{timestamp}_{backup_id}{extension}"
            filepath = os.path.join(backup_path, filename)
            
            with open(filepath, "wb") as f:
                f.write(final_data)
            
            file_size = os.path.getsize(filepath)
            
            await conn.execute("""
                INSERT INTO audit_backups
                (id, filename, file_path, file_size, log_count, 
                 start_timestamp, end_timestamp, encrypted, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
            """, (
                backup_id,
                filename,
                filepath,
                file_size,
                len(logs_list),
                logs_list[0]["timestamp"],
                logs_list[-1]["timestamp"],
                encrypt,
            ))
            await conn.commit()
            
            logger.info(f"Created backup: {filename}, {len(logs_list)} logs, {file_size} bytes")
            
            return {
                "status": "success",
                "backup_id": backup_id,
                "filename": filename,
                "file_path": filepath,
                "file_size": file_size,
                "log_count": len(logs_list),
                "encrypted": encrypt,
                "start_timestamp": logs_list[0]["timestamp"],
                "end_timestamp": logs_list[-1]["timestamp"],
            }
            
        except Exception as e:
            logger.error(f"Backup failed: {e}")
            return {
                "status": "failed",
                "backup_id": backup_id,
                "error": str(e),
            }
        finally:
            await conn.close()
    
    async def restore_backup(
        self,
        backup_id: str,
        restore_path: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        从备份恢复审计日志
        
        Args:
            backup_id: 备份ID
            restore_path: 恢复路径（可选，默认恢复到数据库）
            
        Returns:
            恢复结果信息
        """
        conn = await get_db_connection()
        try:
            cursor = await conn.execute(
                "SELECT * FROM audit_backups WHERE id = ?",
                (backup_id,)
            )
            backup = await cursor.fetchone()
            
            if not backup:
                return {"status": "failed", "error": "备份不存在"}
            
            backup_dict = dict(backup)
            filepath = backup_dict["file_path"]
            
            if not os.path.exists(filepath):
                return {"status": "failed", "error": "备份文件不存在"}
            
            with open(filepath, "rb") as f:
                encrypted_data = f.read()
            
            if backup_dict["encrypted"]:
                compressed_data = self._decrypt_data(encrypted_data)
            else:
                compressed_data = encrypted_data
            
            json_data = gzip.decompress(compressed_data).decode('utf-8')
            logs = json.loads(json_data)
            
            if restore_path:
                output_file = os.path.join(restore_path, f"restored_{backup_id}.json")
                with open(output_file, "w", encoding="utf-8") as f:
                    json.dump(logs, f, ensure_ascii=False, indent=2)
                
                return {
                    "status": "success",
                    "message": f"已恢复到文件: {output_file}",
                    "log_count": len(logs),
                }
            
            restored_count = 0
            for log in logs:
                try:
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
                    restored_count += 1
                except Exception as e:
                    logger.warning(f"Failed to restore log {log.get('id')}: {e}")
            
            await conn.commit()
            
            return {
                "status": "success",
                "message": f"已恢复 {restored_count} 条日志到数据库",
                "log_count": restored_count,
            }
            
        except Exception as e:
            logger.error(f"Restore failed: {e}")
            return {"status": "failed", "error": str(e)}
        finally:
            await conn.close()
    
    async def list_backups(self) -> list:
        """列出所有备份"""
        conn = await get_db_connection()
        try:
            cursor = await conn.execute("""
                SELECT id, filename, file_size, log_count,
                       start_timestamp, end_timestamp, encrypted, created_at
                FROM audit_backups
                ORDER BY created_at DESC
            """)
            return [dict(row) for row in await cursor.fetchall()]
        finally:
            await conn.close()
    
    async def cleanup_old_backups(self, retention_days: int = 90):
        """清理过期备份"""
        conn = await get_db_connection()
        try:
            cutoff = datetime.utcnow() - timedelta(days=retention_days)
            
            cursor = await conn.execute(
                "SELECT id, file_path FROM audit_backups WHERE created_at < ?",
                (cutoff.isoformat(),)
            )
            old_backups = await cursor.fetchall()
            
            for backup in old_backups:
                try:
                    if os.path.exists(backup["file_path"]):
                        os.remove(backup["file_path"])
                except Exception as e:
                    logger.warning(f"Failed to delete backup file: {e}")
                
                await conn.execute(
                    "DELETE FROM audit_backups WHERE id = ?",
                    (backup["id"],)
                )
            
            await conn.commit()
            
            if old_backups:
                logger.info(f"Cleaned up {len(old_backups)} old backups")
            
            return len(old_backups)
        finally:
            await conn.close()
    
    async def start_scheduler(self, interval_hours: int = 24):
        """启动定时备份"""
        if self._running:
            return
        
        self._running = True
        self._task = asyncio.create_task(self._run_backup_loop(interval_hours))
        logger.info(f"Backup scheduler started (interval: {interval_hours}h)")
    
    async def stop_scheduler(self):
        """停止定时备份"""
        self._running = False
        if self._task:
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass
        logger.info("Backup scheduler stopped")
    
    async def _run_backup_loop(self, interval_hours: int):
        while self._running:
            try:
                await self.create_backup()
                await self.cleanup_old_backups()
            except Exception as e:
                logger.error(f"Scheduled backup failed: {e}")
            
            await asyncio.sleep(interval_hours * 3600)


audit_backup = AuditBackupService()


async def setup_backup_scheduler():
    await audit_backup.start_scheduler()


async def shutdown_backup_scheduler():
    await audit_backup.stop_scheduler()
