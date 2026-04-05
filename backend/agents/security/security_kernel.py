"""
安全内核 SecurityKernel
协调巡捕、判官、牢头、仵作四大智能体的协同工作

功能：
- 统一管理所有安全智能体
- 提供统一的状态查询接口
- 协调智能体间的通信
"""

import asyncio
import time
import logging
from typing import Dict, List, Optional, Any
from datetime import datetime

from .patrol_agent import patrol_agent, ThreatLevel, AttackType
from .judge_agent import judge_agent, SecurityAction
from .prison_agent import prison_agent
from .coroner_agent import coroner_agent

logger = logging.getLogger(__name__)


class SecurityKernel:
    """安全内核 - 协调所有安全智能体"""
    
    def __init__(self):
        self.patrol = patrol_agent
        self.judge = judge_agent
        self.prison = prison_agent
        self.coroner = coroner_agent
        
        self._running = False
        self._start_time: Optional[float] = None
        self._request_count = 0
        self._blocked_count = 0
    
    async def start(self):
        """启动安全内核"""
        if self._running:
            return
        
        self._running = True
        self._start_time = time.time()
        
        self.patrol.start()
        self.judge.start()
        self.prison.start()
        self.coroner.start()
        
        logger.info("Security kernel started")
    
    async def stop(self):
        """停止安全内核"""
        self._running = False
        
        self.patrol.stop()
        self.judge.stop()
        self.prison.stop()
        self.coroner.stop()
        
        logger.info("Security kernel stopped")
    
    def record_request(
        self,
        ip: str,
        url: str,
        method: str = "GET",
        status_code: int = 200,
        user_agent: str = "",
        packet_size: int = 0,
        response_time: float = 0.0,
        geo_location: str = ""
    ):
        """记录请求"""
        self._request_count += 1
        
        self.patrol.record_request(
            ip=ip,
            url=url,
            method=method,
            status_code=status_code,
            user_agent=user_agent,
            packet_size=packet_size,
            response_time=response_time,
            geo_location=geo_location
        )
    
    def get_status(self) -> Dict[str, Any]:
        """获取安全内核状态"""
        return {
            "running": self._running,
            "uptime": time.time() - self._start_time if self._start_time else 0,
            "request_count": self._request_count,
            "blocked_count": self._blocked_count,
            "components": {
                "patrol": self.patrol.get_status() if hasattr(self.patrol, 'get_status') else {},
                "judge": self.judge.get_status() if hasattr(self.judge, 'get_status') else {},
                "prison": self.prison.get_status() if hasattr(self.prison, 'get_status') else {},
                "coroner": self.coroner.get_status() if hasattr(self.coroner, 'get_status') else {}
            }
        }


security_kernel = SecurityKernel()
