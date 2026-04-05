"""
日志查询API
提供日志检索和分析功能
"""
import os
import json
import re
from datetime import datetime, timedelta
from typing import Optional, List
from pathlib import Path
from fastapi import APIRouter, Depends, Query, HTTPException
from pydantic import BaseModel

from ...auth import require_admin
from ...logger import get_logger

logger = get_logger("logs_api")

router = APIRouter(prefix="/api/admin/logs", tags=["logs"])


class LogEntry(BaseModel):
    timestamp: str
    level: str
    logger: str
    message: str
    module: Optional[str] = None
    function: Optional[str] = None
    line: Optional[int] = None
    request_id: Optional[str] = None
    user_id: Optional[str] = None
    exception: Optional[str] = None


class LogStats(BaseModel):
    total: int
    by_level: dict
    by_logger: dict
    error_rate: float


class LogLevelUpdate(BaseModel):
    logger: str
    level: str


LOG_DIR = os.getenv("LOG_DIR", "./logs")


def parse_log_line(line: str) -> Optional[LogEntry]:
    """解析日志行"""
    try:
        if line.strip().startswith("{"):
            data = json.loads(line)
            return LogEntry(
                timestamp=data.get("timestamp", ""),
                level=data.get("level", "INFO"),
                logger=data.get("logger", ""),
                message=data.get("message", ""),
                module=data.get("module"),
                function=data.get("function"),
                line=data.get("line"),
                request_id=data.get("request_id"),
                user_id=data.get("user_id"),
                exception=data.get("exception"),
            )
        else:
            match = re.match(
                r"(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}) \| (\w+)\s*\| (\S+) \| (.+)",
                line
            )
            if match:
                return LogEntry(
                    timestamp=match.group(1),
                    level=match.group(2),
                    logger=match.group(3),
                    message=match.group(4),
                )
    except Exception:
        pass
    return None


@router.get("/search")
async def search_logs(
    query: Optional[str] = Query(None, description="搜索关键词"),
    level: Optional[str] = Query(None, description="日志级别"),
    logger_name: Optional[str] = Query(None, description="日志器名称"),
    start_time: Optional[datetime] = Query(None, description="开始时间"),
    end_time: Optional[datetime] = Query(None, description="结束时间"),
    limit: int = Query(100, ge=1, le=1000),
    offset: int = Query(0, ge=0),
    current_user = Depends(require_admin),
):
    """搜索日志"""
    logs = []
    log_path = Path(LOG_DIR)
    
    if not log_path.exists():
        return {"logs": [], "total": 0}
    
    log_files = ["app.log", "error.log", "access.log"]
    
    for log_file in log_files:
        file_path = log_path / log_file
        if not file_path.exists():
            continue
        
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                for line in f:
                    entry = parse_log_line(line)
                    if not entry:
                        continue
                    
                    if level and entry.level != level:
                        continue
                    
                    if logger_name and logger_name not in entry.logger:
                        continue
                    
                    if query and query.lower() not in entry.message.lower():
                        continue
                    
                    if start_time:
                        try:
                            entry_time = datetime.fromisoformat(entry.timestamp.replace("Z", "+00:00"))
                            if entry_time < start_time:
                                continue
                        except Exception:
                            pass
                    
                    if end_time:
                        try:
                            entry_time = datetime.fromisoformat(entry.timestamp.replace("Z", "+00:00"))
                            if entry_time > end_time:
                                continue
                        except Exception:
                            pass
                    
                    logs.append(entry)
        
        except Exception as e:
            logger.error(f"Error reading log file {log_file}: {e}")
    
    logs.sort(key=lambda x: x.timestamp, reverse=True)
    
    total = len(logs)
    logs = logs[offset:offset + limit]
    
    return {
        "logs": [log.model_dump() for log in logs],
        "total": total,
        "limit": limit,
        "offset": offset,
    }


@router.get("/stats", response_model=LogStats)
async def get_log_stats(
    hours: int = Query(24, ge=1, le=168),
    current_user = Depends(require_admin),
):
    """获取日志统计"""
    log_path = Path(LOG_DIR)
    
    stats = {
        "total": 0,
        "by_level": {},
        "by_logger": {},
        "error_rate": 0.0,
    }
    
    if not log_path.exists():
        return LogStats(**stats)
    
    start_time = datetime.now() - timedelta(hours=hours)
    error_count = 0
    
    log_files = list(log_path.glob("*.log"))
    
    for log_file in log_files:
        try:
            with open(log_file, "r", encoding="utf-8") as f:
                for line in f:
                    entry = parse_log_line(line)
                    if not entry:
                        continue
                    
                    try:
                        entry_time = datetime.fromisoformat(entry.timestamp.replace("Z", "+00:00"))
                        if entry_time < start_time:
                            continue
                    except Exception:
                        pass
                    
                    stats["total"] += 1
                    
                    level = entry.level
                    stats["by_level"][level] = stats["by_level"].get(level, 0) + 1
                    
                    logger_name = entry.logger.split(".")[0] if entry.logger else "unknown"
                    stats["by_logger"][logger_name] = stats["by_logger"].get(logger_name, 0) + 1
                    
                    if level in ["ERROR", "CRITICAL"]:
                        error_count += 1
        
        except Exception as e:
            logger.error(f"Error reading log file {log_file}: {e}")
    
    if stats["total"] > 0:
        stats["error_rate"] = round(error_count / stats["total"], 4)
    
    return LogStats(**stats)


@router.get("/levels")
async def get_log_levels(
    current_user = Depends(require_admin),
):
    """获取当前日志级别配置"""
    import logging
    
    loggers = {}
    
    for name in ["property-ai", "uvicorn", "sqlalchemy", "httpx", "asyncio"]:
        logger_obj = logging.getLogger(name)
        loggers[name] = {
            "level": logging.getLevelName(logger_obj.level),
            "effective_level": logging.getLevelName(logger_obj.getEffectiveLevel()),
        }
    
    return {"loggers": loggers}


@router.post("/levels")
async def set_log_level(
    update: LogLevelUpdate,
    current_user = Depends(require_admin),
):
    """动态设置日志级别"""
    import logging
    
    valid_levels = ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]
    if update.level.upper() not in valid_levels:
        raise HTTPException(status_code=400, detail=f"Invalid log level. Valid levels: {valid_levels}")
    
    logger_obj = logging.getLogger(update.logger)
    if not logger_obj:
        raise HTTPException(status_code=404, detail=f"Logger not found: {update.logger}")
    
    old_level = logging.getLevelName(logger_obj.level)
    logger_obj.setLevel(update.level.upper())
    
    logger.info(f"Log level changed: {update.logger} from {old_level} to {update.level.upper()}")
    
    return {
        "logger": update.logger,
        "old_level": old_level,
        "new_level": update.level.upper(),
    }


@router.get("/files")
async def list_log_files(
    current_user = Depends(require_admin),
):
    """列出日志文件"""
    log_path = Path(LOG_DIR)
    
    if not log_path.exists():
        return {"files": []}
    
    files = []
    for log_file in log_path.glob("*.log*"):
        stat = log_file.stat()
        files.append({
            "name": log_file.name,
            "size": stat.st_size,
            "size_human": f"{stat.st_size / 1024:.1f} KB",
            "modified": datetime.fromtimestamp(stat.st_mtime).isoformat(),
        })
    
    files.sort(key=lambda x: x["modified"], reverse=True)
    
    return {"files": files}


@router.get("/files/{filename}")
async def get_log_file_content(
    filename: str,
    lines: int = Query(100, ge=1, le=1000),
    current_user = Depends(require_admin),
):
    """获取日志文件内容"""
    log_path = Path(LOG_DIR) / filename
    
    if not log_path.exists() or not log_path.is_file():
        raise HTTPException(status_code=404, detail="Log file not found")
    
    if not str(log_path).startswith(LOG_DIR):
        raise HTTPException(status_code=403, detail="Access denied")
    
    try:
        with open(log_path, "r", encoding="utf-8") as f:
            all_lines = f.readlines()
            content = "".join(all_lines[-lines:])
        
        return {
            "filename": filename,
            "lines": len(all_lines),
            "content": content,
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/files/{filename}")
async def delete_log_file(
    filename: str,
    current_user = Depends(require_admin),
):
    """删除日志文件"""
    log_path = Path(LOG_DIR) / filename
    
    if not log_path.exists() or not log_path.is_file():
        raise HTTPException(status_code=404, detail="Log file not found")
    
    if not str(log_path).startswith(LOG_DIR):
        raise HTTPException(status_code=403, detail="Access denied")
    
    if filename in ["app.log", "error.log", "access.log"]:
        raise HTTPException(status_code=400, detail="Cannot delete active log files")
    
    try:
        log_path.unlink()
        logger.info(f"Log file deleted: {filename}")
        return {"status": "deleted", "filename": filename}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
