"""
牢头智能体 PrisonAgent
负责执行处置动作和网关交互

功能：
- 接收判官的决策，执行具体处置
- 与网关（Nginx/OpenResty）交互，动态修改配置
- 记录处置日志
"""

import json
import time
import uuid
import asyncio
import redis
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Set
from dataclasses import dataclass, field
from enum import Enum

from .judge_agent import SecurityAction, SecurityDecision


class BanDuration(Enum):
    """封禁时长"""
    SHORT = 300      # 5分钟
    MEDIUM = 3600    # 1小时
    LONG = 86400     # 24小时
    PERMANENT = 0    # 永久


@dataclass
class ExecutionRecord:
    """执行记录"""
    record_id: str
    timestamp: float
    action: SecurityAction
    target: str
    duration: int = 0
    success: bool = False
    error: str = ""
    metadata: Dict = field(default_factory=dict)
    
    def to_dict(self) -> Dict:
        return {
            "record_id": self.record_id,
            "timestamp": self.timestamp,
            "action": self.action.name,
            "target": self.target,
            "duration": self.duration,
            "success": self.success,
            "error": self.error,
            "metadata": self.metadata
        }


@dataclass
class IPBanRecord:
    """IP封禁记录"""
    ip: str
    ban_time: float
    duration: int
    reason: str
    attack_type: str = ""
    unban_time: Optional[float] = None
    
    def to_dict(self) -> Dict:
        return {
            "ip": self.ip,
            "ban_time": self.ban_time,
            "duration": self.duration,
            "reason": self.reason,
            "attack_type": self.attack_type,
            "unban_time": self.unban_time
        }


class GatewayInterface:
    """网关接口"""
    
    def __init__(self, redis_host: str = "localhost", redis_port: int = 6379):
        self.redis_client = redis.Redis(
            host=redis_host,
            port=redis_port,
            decode_responses=True
        )
        
        self.key_prefix = "security:"
    
    async def block_ip(self, ip: str, duration: int = 3600, reason: str = ""):
        """封禁IP"""
        key = f"{self.key_prefix}block:{ip}"
        
        await asyncio.to_thread(
            self.redis_client.setex,
            key,
            duration if duration > 0 else 86400 * 365,
            json.dumps({
                "reason": reason,
                "ban_time": time.time(),
                "duration": duration
            })
        )
        
        await asyncio.to_thread(
            self.redis_client.publish,
            "security:actions",
            json.dumps({
                "action": "block_ip",
                "ip": ip,
                "duration": duration
            })
        )
    
    async def unblock_ip(self, ip: str):
        """解封IP"""
        key = f"{self.key_prefix}block:{ip}"
        
        await asyncio.to_thread(self.redis_client.delete, key)
        
        await asyncio.to_thread(
            self.redis_client.publish,
            "security:actions",
            json.dumps({
                "action": "unblock_ip",
                "ip": ip
            })
        )
    
    async def rate_limit_ip(self, ip: str, rate: int, duration: int = 3600):
        """限速IP"""
        key = f"{self.key_prefix}rate:{ip}"
        
        await asyncio.to_thread(
            self.redis_client.setex,
            key,
            duration,
            str(rate)
        )
        
        await asyncio.to_thread(
            self.redis_client.publish,
            "security:actions",
            json.dumps({
                "action": "rate_limit",
                "ip": ip,
                "rate": rate
            })
        )
    
    async def require_captcha(self, ip: str, duration: int = 300):
        """要求验证码"""
        key = f"{self.key_prefix}captcha:{ip}"
        
        await asyncio.to_thread(
            self.redis_client.setex,
            key,
            duration,
            json.dumps({
                "required": True,
                "attempts": 0
            })
        )
    
    async def block_device(self, device_fingerprint: str, duration: int = 86400):
        """封禁设备"""
        key = f"{self.key_prefix}device:{device_fingerprint}"
        
        await asyncio.to_thread(
            self.redis_client.setex,
            key,
            duration,
            json.dumps({
                "ban_time": time.time(),
                "duration": duration
            })
        )
    
    async def escalate_to_high_defense(self, reason: str = ""):
        """升级到高防节点"""
        await asyncio.to_thread(
            self.redis_client.publish,
            "security:actions",
            json.dumps({
                "action": "escalate",
                "reason": reason,
                "timestamp": time.time()
            })
        )
    
    async def get_blocked_ips(self) -> List[str]:
        """获取被封禁的IP列表"""
        pattern = f"{self.key_prefix}block:*"
        keys = await asyncio.to_thread(self.redis_client.keys, pattern)
        return [key.replace(f"{self.key_prefix}block:", "") for key in keys]
    
    async def get_rate_limited_ips(self) -> Dict[str, int]:
        """获取被限速的IP列表"""
        pattern = f"{self.key_prefix}rate:*"
        keys = await asyncio.to_thread(self.redis_client.keys, pattern)
        
        result = {}
        for key in keys:
            rate = await asyncio.to_thread(self.redis_client.get, key)
            if rate:
                ip = key.replace(f"{self.key_prefix}rate:", "")
                result[ip] = int(rate)
        
        return result


class PrisonAgent:
    """牢头智能体"""
    
    def __init__(
        self,
        agent_id: str = "prison_001",
        redis_host: str = "localhost",
        redis_port: int = 6379
    ):
        self.agent_id = agent_id
        self.gateway = GatewayInterface(redis_host, redis_port)
        
        self._ban_records: Dict[str, IPBanRecord] = {}
        self._execution_history: List[ExecutionRecord] = []
        self._max_history = 10000
        
        self._running = False
        self._cleanup_task: Optional[asyncio.Task] = None
    
    async def execute(self, decision: SecurityDecision) -> List[ExecutionRecord]:
        """执行决策"""
        records = []
        
        if decision.action == SecurityAction.ALLOW:
            return records
        
        if decision.action == SecurityAction.BLOCK_IP:
            for ip in decision.target_ips:
                record = await self._execute_block_ip(ip, decision)
                records.append(record)
        
        elif decision.action == SecurityAction.RATE_LIMIT:
            for ip in decision.target_ips:
                record = await self._execute_rate_limit(ip, decision)
                records.append(record)
        
        elif decision.action == SecurityAction.CAPTCHA:
            for ip in decision.target_ips:
                record = await self._execute_captcha(ip, decision)
                records.append(record)
        
        elif decision.action == SecurityAction.BLOCK_DEVICE:
            for device in decision.target_devices:
                record = await self._execute_block_device(device, decision)
                records.append(record)
        
        elif decision.action == SecurityAction.ESCALATE:
            record = await self._execute_escalate(decision)
            records.append(record)
        
        self._execution_history.extend(records)
        
        if len(self._execution_history) > self._max_history:
            self._execution_history = self._execution_history[-self._max_history:]
        
        await self._save_execution_records(records)
        
        return records
    
    async def _execute_block_ip(self, ip: str, decision: SecurityDecision) -> ExecutionRecord:
        """执行IP封禁"""
        record = ExecutionRecord(
            record_id=str(uuid.uuid4()),
            timestamp=time.time(),
            action=SecurityAction.BLOCK_IP,
            target=ip
        )
        
        try:
            duration = self._calculate_ban_duration(decision.confidence)
            
            await self.gateway.block_ip(ip, duration, decision.reason)
            
            self._ban_records[ip] = IPBanRecord(
                ip=ip,
                ban_time=time.time(),
                duration=duration,
                reason=decision.reason,
                attack_type=decision.similar_attacks[0].get("attack_type", "") if decision.similar_attacks else ""
            )
            
            record.duration = duration
            record.success = True
            record.metadata = {"confidence": decision.confidence}
            
        except Exception as e:
            record.error = str(e)
            record.success = False
        
        return record
    
    async def _execute_rate_limit(self, ip: str, decision: SecurityDecision) -> ExecutionRecord:
        """执行限速"""
        record = ExecutionRecord(
            record_id=str(uuid.uuid4()),
            timestamp=time.time(),
            action=SecurityAction.RATE_LIMIT,
            target=ip
        )
        
        try:
            rate = decision.rate_limit if decision.rate_limit > 0 else 10
            
            await self.gateway.rate_limit_ip(ip, rate, 3600)
            
            record.duration = 3600
            record.success = True
            record.metadata = {"rate": rate}
            
        except Exception as e:
            record.error = str(e)
            record.success = False
        
        return record
    
    async def _execute_captcha(self, ip: str, decision: SecurityDecision) -> ExecutionRecord:
        """执行验证码要求"""
        record = ExecutionRecord(
            record_id=str(uuid.uuid4()),
            timestamp=time.time(),
            action=SecurityAction.CAPTCHA,
            target=ip
        )
        
        try:
            await self.gateway.require_captcha(ip, 300)
            
            record.duration = 300
            record.success = True
            
        except Exception as e:
            record.error = str(e)
            record.success = False
        
        return record
    
    async def _execute_block_device(self, device: str, decision: SecurityDecision) -> ExecutionRecord:
        """执行设备封禁"""
        record = ExecutionRecord(
            record_id=str(uuid.uuid4()),
            timestamp=time.time(),
            action=SecurityAction.BLOCK_DEVICE,
            target=device
        )
        
        try:
            await self.gateway.block_device(device, 86400)
            
            record.duration = 86400
            record.success = True
            
        except Exception as e:
            record.error = str(e)
            record.success = False
        
        return record
    
    async def _execute_escalate(self, decision: SecurityDecision) -> ExecutionRecord:
        """执行升级"""
        record = ExecutionRecord(
            record_id=str(uuid.uuid4()),
            timestamp=time.time(),
            action=SecurityAction.ESCALATE,
            target="system"
        )
        
        try:
            await self.gateway.escalate_to_high_defense(decision.reason)
            
            record.success = True
            record.metadata = {"reason": decision.reason}
            
        except Exception as e:
            record.error = str(e)
            record.success = False
        
        return record
    
    def _calculate_ban_duration(self, confidence: float) -> int:
        """计算封禁时长"""
        if confidence >= 0.9:
            return BanDuration.LONG.value
        elif confidence >= 0.7:
            return BanDuration.MEDIUM.value
        else:
            return BanDuration.SHORT.value
    
    async def unban_ip(self, ip: str, reason: str = "manual") -> bool:
        """解封IP"""
        try:
            await self.gateway.unblock_ip(ip)
            
            if ip in self._ban_records:
                self._ban_records[ip].unban_time = time.time()
            
            return True
        except Exception as e:
            print(f"解封IP失败: {e}")
            return False
    
    async def _save_execution_records(self, records: List[ExecutionRecord]):
        """保存执行记录到数据库"""
        try:
            from ...database import get_db_connection
            
            async for conn in get_db_connection():
                try:
                    for record in records:
                        await conn.execute("""
                            INSERT INTO security_execution_logs 
                            (id, action, target, duration, success, error, metadata, created_at)
                            VALUES ($1, $2, $3, $4, $5, $6, $7, CURRENT_TIMESTAMP)
                        """, (
                            record.record_id,
                            record.action.name,
                            record.target,
                            record.duration,
                            record.success,
                            record.error,
                            json.dumps(record.metadata)
                        ))
                    
                    await conn.commit()
                finally:
                    await conn.close()
        except Exception as e:
            print(f"保存执行记录失败: {e}")
    
    async def _cleanup_expired_bans(self):
        """清理过期封禁"""
        current_time = time.time()
        
        expired_ips = []
        for ip, record in self._ban_records.items():
            if record.duration > 0:
                if current_time - record.ban_time > record.duration:
                    expired_ips.append(ip)
        
        for ip in expired_ips:
            await self.unban_ip(ip, "expired")
            del self._ban_records[ip]
    
    async def run_cleanup(self):
        """后台清理任务"""
        while self._running:
            try:
                await self._cleanup_expired_bans()
                await asyncio.sleep(60)
            except Exception as e:
                print(f"清理任务错误: {e}")
                await asyncio.sleep(10)
    
    def start(self):
        """启动"""
        self._running = True
        self._cleanup_task = asyncio.create_task(self.run_cleanup())
    
    def stop(self):
        """停止"""
        self._running = False
        if self._cleanup_task:
            self._cleanup_task.cancel()
    
    def get_status(self) -> Dict:
        """获取状态"""
        return {
            "agent_id": self.agent_id,
            "running": self._running,
            "active_bans": len(self._ban_records),
            "execution_history_size": len(self._execution_history)
        }
    
    def get_ban_list(self) -> List[Dict]:
        """获取封禁列表"""
        return [record.to_dict() for record in self._ban_records.values()]
    
    def get_recent_executions(self, limit: int = 100) -> List[Dict]:
        """获取最近执行记录"""
        return [record.to_dict() for record in self._execution_history[-limit:]]


prison_agent = PrisonAgent()
