"""
Keepalived 管理器 - 管理 Keepalived 配置和状态
"""
import asyncio
import logging
import os
import subprocess
from typing import Optional, Dict, Any
from datetime import datetime, timezone
from pathlib import Path
from enum import Enum

from .config import settings
from .notifier import FailoverNotifier, FailoverEvent, NodeState

logger = logging.getLogger(__name__)


class KeepalivedState(str, Enum):
    MASTER = "MASTER"
    BACKUP = "BACKUP"
    FAULT = "FAULT"
    INIT = "INIT"
    UNKNOWN = "UNKNOWN"


class KeepalivedManager:
    KEEPALIVED_CONF_PATH = "/etc/keepalived/keepalived.conf"
    KEEPALIVED_PID_FILE = "/var/run/keepalived.pid"

    def __init__(
        self,
        interface: Optional[str] = None,
        vip: Optional[str] = None,
        priority: Optional[int] = None,
        state: Optional[str] = None,
    ):
        self.interface = interface or settings.INTERFACE
        self.vip = vip or settings.VIP
        self.priority = priority or settings.PRIORITY
        self.state = state or settings.STATE
        self.virtual_router_id = settings.VIRTUAL_ROUTER_ID
        self.auth_password = settings.AUTH_PASSWORD
        self._notifier = FailoverNotifier()
        self._current_state: KeepalivedState = KeepalivedState.UNKNOWN
        self._last_check: Optional[datetime] = None

    def generate_config(self, role: str = "backup") -> str:
        state = "MASTER" if role.lower() == "master" else "BACKUP"
        priority = 100 if role.lower() == "master" else 50
        router_id = f"LVS_{state}"

        config = f"""global_defs {{
    router_id {router_id}
    notification_email {{
        admin@example.com
    }}
    notification_email_from keepalived@example.com
    smtp_server localhost
    smtp_connect_timeout 30
}}

vrrp_script check_gateway {{
    script "/usr/local/bin/check_gateway.sh"
    interval {settings.CHECK_INTERVAL}
    weight -20
}}

vrrp_instance VI_1 {{
    state {state}
    interface {self.interface}
    virtual_router_id {self.virtual_router_id}
    priority {priority}
    advert_int 1
    authentication {{
        auth_type PASS
        auth_pass {self.auth_password}
    }}
    virtual_ipaddress {{
        {self.vip}/24 dev {self.interface} label {self.interface}:1
    }}
    track_script {{
        check_gateway
    }}
    notify "/usr/local/bin/notify.sh"
}}
"""
        return config

    def write_config(self, role: str = "backup") -> bool:
        config = self.generate_config(role)
        try:
            config_path = Path(self.KEEPALIVED_CONF_PATH)
            config_path.parent.mkdir(parents=True, exist_ok=True)
            config_path.write_text(config)
            logger.info(f"Keepalived config written to {self.KEEPALIVED_CONF_PATH}")
            return True
        except Exception as e:
            logger.error(f"Failed to write keepalived config: {e}")
            return False

    async def start(self) -> bool:
        try:
            result = subprocess.run(
                ["systemctl", "start", "keepalived"],
                capture_output=True,
                text=True,
            )
            if result.returncode == 0:
                logger.info("Keepalived started successfully")
                return True
            else:
                logger.error(f"Failed to start keepalived: {result.stderr}")
                return False
        except Exception as e:
            logger.error(f"Error starting keepalived: {e}")
            return False

    async def stop(self) -> bool:
        try:
            result = subprocess.run(
                ["systemctl", "stop", "keepalived"],
                capture_output=True,
                text=True,
            )
            if result.returncode == 0:
                logger.info("Keepalived stopped successfully")
                return True
            else:
                logger.error(f"Failed to stop keepalived: {result.stderr}")
                return False
        except Exception as e:
            logger.error(f"Error stopping keepalived: {e}")
            return False

    async def restart(self) -> bool:
        try:
            result = subprocess.run(
                ["systemctl", "restart", "keepalived"],
                capture_output=True,
                text=True,
            )
            if result.returncode == 0:
                logger.info("Keepalived restarted successfully")
                return True
            else:
                logger.error(f"Failed to restart keepalived: {result.stderr}")
                return False
        except Exception as e:
            logger.error(f"Error restarting keepalived: {e}")
            return False

    def is_running(self) -> bool:
        try:
            result = subprocess.run(
                ["systemctl", "is-active", "keepalived"],
                capture_output=True,
                text=True,
            )
            return result.returncode == 0
        except Exception:
            return False

    def get_state(self) -> KeepalivedState:
        try:
            result = subprocess.run(
                ["journalctl", "-u", "keepalived", "-n", "50", "--no-pager"],
                capture_output=True,
                text=True,
            )
            output = result.stdout.lower()

            if "entering master state" in output:
                return KeepalivedState.MASTER
            elif "entering backup state" in output:
                return KeepalivedState.BACKUP
            elif "entering fault state" in output:
                return KeepalivedState.FAULT
            else:
                return KeepalivedState.UNKNOWN
        except Exception as e:
            logger.error(f"Error getting keepalived state: {e}")
            return KeepalivedState.UNKNOWN

    def has_vip(self) -> bool:
        try:
            result = subprocess.run(
                ["ip", "addr", "show", self.interface],
                capture_output=True,
                text=True,
            )
            return self.vip in result.stdout
        except Exception as e:
            logger.error(f"Error checking VIP: {e}")
            return False

    async def check_and_notify(self) -> Optional[FailoverEvent]:
        new_state = self.get_state()
        has_vip = self.has_vip()

        old_state = self._current_state
        self._current_state = new_state
        self._last_check = datetime.now(timezone.utc)

        if old_state != KeepalivedState.UNKNOWN and old_state != new_state:
            event = FailoverEvent(
                old_state=NodeState(old_state.value),
                new_state=NodeState(new_state.value),
                vip=self.vip,
                reason=f"VIP present: {has_vip}",
            )
            await self._notifier.notify(event)
            return event

        return None

    def get_stats(self) -> Dict[str, Any]:
        return {
            "running": self.is_running(),
            "state": self._current_state.value,
            "has_vip": self.has_vip(),
            "vip": self.vip,
            "interface": self.interface,
            "priority": self.priority,
            "last_check": self._last_check.isoformat() if self._last_check else None,
        }


def generate_health_check_script(script_type: str = "gateway") -> str:
    if script_type == "nginx":
        return """#!/bin/bash
if pgrep -x nginx > /dev/null; then
    exit 0
else
    exit 1
fi
"""
    elif script_type == "gateway":
        return """#!/bin/bash
if systemctl is-active --quiet backup-gateway; then
    exit 0
else
    exit 1
fi
"""
    else:
        return """#!/bin/bash
exit 0
"""


def generate_notify_script(webhook_url: str = "") -> str:
    return f"""#!/bin/bash
STATE=$2
VIP=$3
if [ "$STATE" == "MASTER" ]; then
    MESSAGE="VIP $VIP 已切换到当前节点，成为 MASTER"
elif [ "$STATE" == "BACKUP" ]; then
    MESSAGE="当前节点成为 BACKUP"
else
    MESSAGE="状态异常: $STATE"
fi

WEBHOOK_URL="{webhook_url}"
if [ -n "$WEBHOOK_URL" ]; then
    curl -X POST -H "Content-Type: application/json" -d "{{\\"msg_type\\":\\"text\\",\\"content\\":{{\\"text\\":\\"$MESSAGE\\"}}}}" $WEBHOOK_URL
fi

logger -t keepalived-notify "$MESSAGE"
"""
