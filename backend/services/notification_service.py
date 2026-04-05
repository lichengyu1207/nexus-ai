"""
站内信通知服务
支持发送、获取、标记已读等功能
"""
import uuid
import json
import logging
from datetime import datetime
from typing import Dict, Any, Optional, List

from ..database import get_db_connection

logger = logging.getLogger(__name__)


class NotificationService:
    """站内信通知服务"""
    
    NOTIFICATION_TYPES = {
        "refund": "积分退还",
        "task_failed": "任务失败",
        "system": "系统通知",
        "integral_low": "积分不足",
        "complaint_reply": "申诉回复",
        "welcome": "欢迎消息"
    }
    
    async def send_notification(
        self,
        user_id: str,
        type: str,
        content: str,
        title: str = None,
        metadata: Dict[str, Any] = None
    ) -> str:
        """
        发送站内信
        
        Args:
            user_id: 用户ID
            type: 通知类型
            content: 通知内容
            title: 标题（可选）
            metadata: 元数据（可选）
            
        Returns:
            str: 通知ID
        """
        conn = await get_db_connection()
        try:
            notification_id = str(uuid.uuid4())
            
            if not title:
                title = self.NOTIFICATION_TYPES.get(type, "系统通知")
            
            related_id = metadata.get("related_id") if metadata else None
            related_type = metadata.get("related_type") if metadata else None
            
            await conn.execute(
                """
                INSERT INTO notifications (id, user_id, type, title, content, related_id, related_type, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    notification_id,
                    user_id,
                    type,
                    title,
                    content,
                    related_id,
                    related_type,
                    datetime.utcnow().isoformat()
                )
            )
            await conn.commit()
            
            logger.info(f"Notification sent: user={user_id}, type={type}")
            
            return notification_id
        finally:
            await conn.close()
    
    async def send_refund_notification(
        self,
        user_id: str,
        refund_integral: float,
        refund_tokens: int,
        reason: str
    ) -> str:
        """
        发送积分退还通知
        
        Args:
            user_id: 用户ID
            refund_integral: 退还积分
            refund_tokens: 退还Token
            reason: 退还原因
            
        Returns:
            str: 通知ID
        """
        content = f"您的积分已退还：{refund_integral:.2f}积分（{refund_tokens} Token）。\n退还原因：{reason}"
        
        return await self.send_notification(
            user_id=user_id,
            type="refund",
            title="积分退还通知",
            content=content,
            metadata={
                "refund_integral": refund_integral,
                "refund_tokens": refund_tokens,
                "reason": reason
            }
        )
    
    async def send_low_balance_warning(
        self,
        user_id: str,
        current_integral: float,
        required_integral: float
    ) -> str:
        """
        发送积分不足警告
        
        Args:
            user_id: 用户ID
            current_integral: 当前积分
            required_integral: 所需积分
            
        Returns:
            str: 通知ID
        """
        content = f"您的积分余额不足。\n当前余额：{current_integral:.2f}积分\n所需积分：{required_integral:.2f}积分\n请及时充值以继续使用服务。"
        
        return await self.send_notification(
            user_id=user_id,
            type="integral_low",
            title="积分不足提醒",
            content=content,
            metadata={
                "current_integral": current_integral,
                "required_integral": required_integral
            }
        )
    
    async def get_unread_count(self, user_id: str) -> int:
        """
        获取未读通知数量
        
        Args:
            user_id: 用户ID
            
        Returns:
            int: 未读数量
        """
        conn = await get_db_connection()
        try:
            cursor = await conn.execute(
                "SELECT COUNT(*) as count FROM notifications WHERE user_id = ? AND is_read = 0",
                (user_id,)
            )
            row = await cursor.fetchone()
            return row["count"] if row else 0
        finally:
            await conn.close()
    
    async def get_notifications(
        self,
        user_id: str,
        limit: int = 20,
        offset: int = 0,
        unread_only: bool = False
    ) -> Dict[str, Any]:
        """
        获取通知列表
        
        Args:
            user_id: 用户ID
            limit: 每页数量
            offset: 偏移量
            unread_only: 仅未读
            
        Returns:
            Dict: 通知列表和总数
        """
        conn = await get_db_connection()
        try:
            if unread_only:
                where_clause = "user_id = ? AND is_read = 0"
                params = [user_id]
            else:
                where_clause = "user_id = ?"
                params = [user_id]
            
            count_cursor = await conn.execute(
                f"SELECT COUNT(*) as total FROM notifications WHERE {where_clause}",
                params
            )
            total_row = await count_cursor.fetchone()
            total = total_row["total"] if total_row else 0
            
            cursor = await conn.execute(
                f"""
                SELECT id, type, title, content, is_read, metadata, created_at
                FROM notifications
                WHERE {where_clause}
                ORDER BY created_at DESC
                LIMIT ? OFFSET ?
                """,
                params + [limit, offset]
            )
            rows = await cursor.fetchall()
            
            notifications = []
            for row in rows:
                notification = {
                    "id": row["id"],
                    "type": row["type"],
                    "title": row["title"],
                    "content": row["content"],
                    "is_read": bool(row["is_read"]),
                    "created_at": row["created_at"]
                }
                if row["metadata"]:
                    try:
                        notification["metadata"] = json.loads(row["metadata"])
                    except:
                        pass
                notifications.append(notification)
            
            return {
                "notifications": notifications,
                "total": total,
                "unread_count": await self.get_unread_count(user_id)
            }
        finally:
            await conn.close()
    
    async def mark_as_read(self, notification_id: str, user_id: str) -> bool:
        """
        标记为已读
        
        Args:
            notification_id: 通知ID
            user_id: 用户ID
            
        Returns:
            bool: 是否成功
        """
        conn = await get_db_connection()
        try:
            await conn.execute(
                "UPDATE notifications SET is_read = 1 WHERE id = ? AND user_id = ?",
                (notification_id, user_id)
            )
            await conn.commit()
            return True
        except Exception as e:
            logger.error(f"Failed to mark notification as read: {e}")
            return False
        finally:
            await conn.close()
    
    async def mark_all_as_read(self, user_id: str) -> int:
        """
        标记所有为已读
        
        Args:
            user_id: 用户ID
            
        Returns:
            int: 更新的数量
        """
        conn = await get_db_connection()
        try:
            cursor = await conn.execute(
                "UPDATE notifications SET is_read = 1 WHERE user_id = ? AND is_read = 0",
                (user_id,)
            )
            await conn.commit()
            return cursor.rowcount
        finally:
            await conn.close()
    
    async def delete_notification(self, notification_id: str, user_id: str) -> bool:
        """
        删除通知
        
        Args:
            notification_id: 通知ID
            user_id: 用户ID
            
        Returns:
            bool: 是否成功
        """
        conn = await get_db_connection()
        try:
            await conn.execute(
                "DELETE FROM notifications WHERE id = ? AND user_id = ?",
                (notification_id, user_id)
            )
            await conn.commit()
            return True
        except Exception as e:
            logger.error(f"Failed to delete notification: {e}")
            return False
        finally:
            await conn.close()


notification_service = NotificationService()
