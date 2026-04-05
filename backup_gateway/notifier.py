"""
故障切换通知器 - 发送切换事件通知
"""
import asyncio
import logging
import json
from typing import Optional, Dict, Any
from datetime import datetime, timezone
from enum import Enum

import aiohttp

from .config import settings

logger = logging.getLogger(__name__)


class NodeState(str, Enum):
    MASTER = "MASTER"
    BACKUP = "BACKUP"
    FAULT = "FAULT"


class FailoverEvent:
    def __init__(
        self,
        old_state: NodeState,
        new_state: NodeState,
        vip: str,
        reason: str = "",
        timestamp: Optional[datetime] = None,
    ):
        self.old_state = old_state
        self.new_state = new_state
        self.vip = vip
        self.reason = reason
        self.timestamp = timestamp or datetime.now(timezone.utc)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "old_state": self.old_state.value,
            "new_state": self.new_state.value,
            "vip": self.vip,
            "reason": self.reason,
            "timestamp": self.timestamp.isoformat(),
        }

    def get_message(self) -> str:
        if self.new_state == NodeState.MASTER:
            return f"🚨 故障切换: VIP {self.vip} 已切换到当前节点，成为 MASTER"
        elif self.new_state == NodeState.BACKUP:
            return f"ℹ️ 状态变更: 当前节点成为 BACKUP"
        else:
            return f"⚠️ 状态异常: {self.new_state.value}"


class FailoverNotifier:
    def __init__(
        self,
        webhook_url: Optional[str] = None,
        webhook_type: str = "feishu",
    ):
        self.webhook_url = webhook_url or settings.WEBHOOK_URL
        self.webhook_type = webhook_type or settings.WEBHOOK_TYPE
        self._event_history: list = []

    async def notify(self, event: FailoverEvent) -> bool:
        self._event_history.append(event)
        if len(self._event_history) > 100:
            self._event_history = self._event_history[-100:]

        logger.info(f"Failover event: {event.get_message()}")

        if not self.webhook_url:
            logger.warning("No webhook URL configured, skipping notification")
            return False

        try:
            if self.webhook_type == "feishu":
                return await self._send_feishu(event)
            elif self.webhook_type == "dingtalk":
                return await self._send_dingtalk(event)
            else:
                return await self._send_generic(event)
        except Exception as e:
            logger.error(f"Failed to send notification: {e}")
            return False

    async def _send_feishu(self, event: FailoverEvent) -> bool:
        payload = {
            "msg_type": "text",
            "content": {
                "text": event.get_message()
            }
        }

        async with aiohttp.ClientSession() as session:
            async with session.post(
                self.webhook_url,
                json=payload,
                headers={"Content-Type": "application/json"},
            ) as response:
                if response.status == 200:
                    logger.info("Feishu notification sent successfully")
                    return True
                else:
                    logger.error(f"Feishu notification failed: {response.status}")
                    return False

    async def _send_dingtalk(self, event: FailoverEvent) -> bool:
        payload = {
            "msgtype": "text",
            "text": {
                "content": event.get_message()
            }
        }

        async with aiohttp.ClientSession() as session:
            async with session.post(
                self.webhook_url,
                json=payload,
                headers={"Content-Type": "application/json"},
            ) as response:
                if response.status == 200:
                    logger.info("DingTalk notification sent successfully")
                    return True
                else:
                    logger.error(f"DingTalk notification failed: {response.status}")
                    return False

    async def _send_generic(self, event: FailoverEvent) -> bool:
        payload = {
            "message": event.get_message(),
            "event": event.to_dict(),
        }

        async with aiohttp.ClientSession() as session:
            async with session.post(
                self.webhook_url,
                json=payload,
                headers={"Content-Type": "application/json"},
            ) as response:
                if response.status == 200:
                    logger.info("Generic notification sent successfully")
                    return True
                else:
                    logger.error(f"Generic notification failed: {response.status}")
                    return False

    def get_history(self, limit: int = 20) -> list:
        return [e.to_dict() for e in self._event_history[-limit:]]


async def send_failover_notification(
    old_state: str,
    new_state: str,
    vip: str,
    reason: str = "",
) -> bool:
    notifier = FailoverNotifier()
    event = FailoverEvent(
        old_state=NodeState(old_state.upper()),
        new_state=NodeState(new_state.upper()),
        vip=vip,
        reason=reason,
    )
    return await notifier.notify(event)
