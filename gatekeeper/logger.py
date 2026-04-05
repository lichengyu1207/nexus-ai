"""
审计日志记录器 - 记录所有重启事件
"""
import json
import logging
from datetime import datetime
from typing import Optional
from .config import settings
from .models import RestartEvent, TriggerType, RestartResult

logger = logging.getLogger(__name__)

try:
    import aiofiles
    HAS_AIOFILES = True
except ImportError:
    HAS_AIOFILES = False

try:
    import asyncpg
    HAS_ASYNCPG = True
except ImportError:
    HAS_ASYNCPG = False


async def log_restart_event(
    agent_id: str,
    trigger: str,
    operator: Optional[str],
    last_heartbeat: Optional[float],
    success: bool,
    error: str = "",
):
    if settings.audit_log_type == "file":
        await _log_to_file(agent_id, trigger, operator, last_heartbeat, success, error)
    elif settings.audit_log_type == "postgres":
        await _log_to_postgres(
            agent_id, trigger, operator, last_heartbeat, success, error
        )
    else:
        logger.warning(f"Unknown audit log type: {settings.audit_log_type}")


async def _log_to_file(
    agent_id: str,
    trigger: str,
    operator: Optional[str],
    last_heartbeat: Optional[float],
    success: bool,
    error: str = "",
):
    entry = RestartEvent(
        agent_id=agent_id,
        trigger_type=TriggerType(trigger),
        last_heartbeat=last_heartbeat,
        operator=operator,
        result=RestartResult.SUCCESS if success else RestartResult.FAILURE,
        error_message=error if error else None,
        created_at=datetime.utcnow(),
    )

    try:
        if HAS_AIOFILES:
            async with aiofiles.open(settings.audit_log_path, "a") as f:
                await f.write(entry.model_dump_json() + "\n")
        else:
            with open(settings.audit_log_path, "a", encoding="utf-8") as f:
                f.write(entry.model_dump_json() + "\n")
        logger.debug(f"Logged restart event for {agent_id} to file")
    except Exception as e:
        logger.error(f"Failed to write audit log to file: {e}")


async def _log_to_postgres(
    agent_id: str,
    trigger: str,
    operator: Optional[str],
    last_heartbeat: Optional[float],
    success: bool,
    error: str = "",
):
    if not HAS_ASYNCPG:
        logger.error("asyncpg not installed, falling back to file logging")
        await _log_to_file(agent_id, trigger, operator, last_heartbeat, success, error)
        return

    conn = None
    try:
        conn = await asyncpg.connect(settings.database_url)
        last_heartbeat_dt = None
        if last_heartbeat:
            last_heartbeat_dt = datetime.fromtimestamp(last_heartbeat)

        await conn.execute(
            """
            INSERT INTO agent_restart_logs 
            (agent_id, trigger_type, last_heartbeat, operator, result, error_message, created_at)
            VALUES ($1, $2, $3, $4, $5, $6, $7)
            """,
            agent_id,
            trigger,
            last_heartbeat_dt,
            operator,
            "success" if success else "failure",
            error,
            datetime.utcnow(),
        )
        logger.debug(f"Logged restart event for {agent_id} to postgres")
    except Exception as e:
        logger.error(f"Failed to write audit log to postgres: {e}")
        await _log_to_file(agent_id, trigger, operator, last_heartbeat, success, error)
    finally:
        if conn:
            await conn.close()


async def get_recent_events(limit: int = 100) -> list:
    if settings.audit_log_type == "file":
        return await _read_from_file(limit)
    elif settings.audit_log_type == "postgres":
        return await _read_from_postgres(limit)
    return []


async def _read_from_file(limit: int = 100) -> list:
    events = []
    try:
        if HAS_AIOFILES:
            async with aiofiles.open(settings.audit_log_path, "r") as f:
                lines = await f.readlines()
        else:
            with open(settings.audit_log_path, "r", encoding="utf-8") as f:
                lines = f.readlines()

        for line in reversed(lines[-limit * 2 :]):
            line = line.strip()
            if line:
                try:
                    events.append(json.loads(line))
                    if len(events) >= limit:
                        break
                except json.JSONDecodeError:
                    continue
    except FileNotFoundError:
        pass
    except Exception as e:
        logger.error(f"Failed to read audit log: {e}")
    return events


async def _read_from_postgres(limit: int = 100) -> list:
    if not HAS_ASYNCPG:
        return []

    conn = None
    try:
        conn = await asyncpg.connect(settings.database_url)
        rows = await conn.fetch(
            """
            SELECT * FROM agent_restart_logs 
            ORDER BY created_at DESC 
            LIMIT $1
            """,
            limit,
        )
        return [dict(row) for row in rows]
    except Exception as e:
        logger.error(f"Failed to read audit log from postgres: {e}")
        return []
    finally:
        if conn:
            await conn.close()
