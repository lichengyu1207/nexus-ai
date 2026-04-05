"""
巡捕智能体 PatrolAgent
负责实时流量监控、特征提取和异常检测

功能：
- 实时监控进入系统的流量
- 提取多维特征，形成特征向量
- 将异常特征发送给判官智能体
"""

import json
import time
import uuid
import asyncio
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, field
from enum import Enum
from collections import deque
import threading


class ThreatLevel(Enum):
    """威胁等级"""
    SAFE = "safe"
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class AttackType(Enum):
    """攻击类型"""
    NORMAL = "normal"
    DDOS = "ddos"
    CC = "cc"
    SQL_INJECTION = "sql_injection"
    XSS = "xss"
    BRUTE_FORCE = "brute_force"
    CRAWLER = "crawler"
    UNKNOWN = "unknown"


@dataclass
class TrafficFeatures:
    """流量特征"""
    timestamp: float = field(default_factory=time.time)
    
    ip_request_rate: float = 0.0
    unique_ips: int = 0
    unique_urls: int = 0
    unique_uas: int = 0
    
    get_ratio: float = 0.5
    post_ratio: float = 0.5
    
    status_2xx_ratio: float = 0.9
    status_4xx_ratio: float = 0.05
    status_5xx_ratio: float = 0.05
    
    avg_packet_size: float = 0.0
    max_packet_size: float = 0.0
    
    tcp_connections: int = 0
    
    geo_diversity: float = 0.0
    
    session_duration_avg: float = 0.0
    
    request_interval_avg: float = 0.0
    request_interval_std: float = 0.0
    
    url_entropy: float = 0.0
    ua_entropy: float = 0.0
    
    error_rate: float = 0.0
    retry_rate: float = 0.0
    
    def to_vector(self) -> np.ndarray:
        """转换为特征向量"""
        return np.array([
            self.ip_request_rate / 1000.0,
            self.unique_ips / 10000.0,
            self.unique_urls / 1000.0,
            self.unique_uas / 100.0,
            self.get_ratio,
            self.post_ratio,
            self.status_2xx_ratio,
            self.status_4xx_ratio,
            self.status_5xx_ratio,
            self.avg_packet_size / 10000.0,
            self.max_packet_size / 100000.0,
            self.tcp_connections / 10000.0,
            self.geo_diversity,
            self.session_duration_avg / 3600.0,
            self.request_interval_avg / 10.0,
            self.request_interval_std / 10.0,
            self.url_entropy / 10.0,
            self.ua_entropy / 10.0,
            self.error_rate,
            self.retry_rate
        ], dtype=np.float32)
    
    def to_dict(self) -> Dict:
        return {
            "timestamp": self.timestamp,
            "ip_request_rate": self.ip_request_rate,
            "unique_ips": self.unique_ips,
            "unique_urls": self.unique_urls,
            "unique_uas": self.unique_uas,
            "get_ratio": self.get_ratio,
            "post_ratio": self.post_ratio,
            "status_2xx_ratio": self.status_2xx_ratio,
            "status_4xx_ratio": self.status_4xx_ratio,
            "status_5xx_ratio": self.status_5xx_ratio,
            "avg_packet_size": self.avg_packet_size,
            "max_packet_size": self.max_packet_size,
            "tcp_connections": self.tcp_connections,
            "geo_diversity": self.geo_diversity,
            "session_duration_avg": self.session_duration_avg,
            "request_interval_avg": self.request_interval_avg,
            "request_interval_std": self.request_interval_std,
            "url_entropy": self.url_entropy,
            "ua_entropy": self.ua_entropy,
            "error_rate": self.error_rate,
            "retry_rate": self.retry_rate
        }
    
    @classmethod
    def from_dict(cls, data: Dict) -> "TrafficFeatures":
        return cls(
            timestamp=data.get("timestamp", time.time()),
            ip_request_rate=data.get("ip_request_rate", 0.0),
            unique_ips=data.get("unique_ips", 0),
            unique_urls=data.get("unique_urls", 0),
            unique_uas=data.get("unique_uas", 0),
            get_ratio=data.get("get_ratio", 0.5),
            post_ratio=data.get("post_ratio", 0.5),
            status_2xx_ratio=data.get("status_2xx_ratio", 0.9),
            status_4xx_ratio=data.get("status_4xx_ratio", 0.05),
            status_5xx_ratio=data.get("status_5xx_ratio", 0.05),
            avg_packet_size=data.get("avg_packet_size", 0.0),
            max_packet_size=data.get("max_packet_size", 0.0),
            tcp_connections=data.get("tcp_connections", 0),
            geo_diversity=data.get("geo_diversity", 0.0),
            session_duration_avg=data.get("session_duration_avg", 0.0),
            request_interval_avg=data.get("request_interval_avg", 0.0),
            request_interval_std=data.get("request_interval_std", 0.0),
            url_entropy=data.get("url_entropy", 0.0),
            ua_entropy=data.get("ua_entropy", 0.0),
            error_rate=data.get("error_rate", 0.0),
            retry_rate=data.get("retry_rate", 0.0)
        )


@dataclass
class AnomalyReport:
    """异常报告"""
    report_id: str
    timestamp: float
    features: TrafficFeatures
    threat_level: ThreatLevel
    suspected_attack: AttackType
    confidence: float
    source_ip: Optional[str] = None
    source_ips: List[str] = field(default_factory=list)
    details: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict:
        return {
            "report_id": self.report_id,
            "timestamp": self.timestamp,
            "features": self.features.to_dict(),
            "threat_level": self.threat_level.value,
            "suspected_attack": self.suspected_attack.value,
            "confidence": self.confidence,
            "source_ip": self.source_ip,
            "source_ips": self.source_ips,
            "details": self.details
        }


class BaselineProfile:
    """基线配置文件"""
    
    def __init__(self):
        self.ip_request_rate_baseline = 10.0
        self.ip_request_rate_std = 5.0
        
        self.error_rate_baseline = 0.01
        self.error_rate_std = 0.02
        
        self.unique_ips_baseline = 100
        self.unique_ips_std = 50
        
        self.request_interval_baseline = 1.0
        self.request_interval_std = 0.5
        
        self._load_baselines()
    
    def _load_baselines(self):
        """从数据库加载基线"""
        pass
    
    def is_anomaly(self, features: TrafficFeatures) -> Tuple[bool, float, str]:
        """检测是否异常"""
        anomaly_score = 0.0
        reasons = []
        
        if features.ip_request_rate > self.ip_request_rate_baseline + 3 * self.ip_request_rate_std:
            anomaly_score += 0.3
            reasons.append(f"IP请求频率异常: {features.ip_request_rate:.1f}/s")
        
        if features.error_rate > self.error_rate_baseline + 3 * self.error_rate_std:
            anomaly_score += 0.2
            reasons.append(f"错误率异常: {features.error_rate:.2%}")
        
        if features.status_4xx_ratio > 0.3:
            anomaly_score += 0.2
            reasons.append(f"4xx错误比例异常: {features.status_4xx_ratio:.2%}")
        
        if features.status_5xx_ratio > 0.1:
            anomaly_score += 0.3
            reasons.append(f"5xx错误比例异常: {features.status_5xx_ratio:.2%}")
        
        if features.request_interval_std < 0.1 and features.ip_request_rate > 50:
            anomaly_score += 0.2
            reasons.append("请求间隔过于规律，疑似机器行为")
        
        if features.url_entropy > 8.0:
            anomaly_score += 0.15
            reasons.append(f"URL熵值异常: {features.url_entropy:.2f}")
        
        if features.ua_entropy < 0.5 and features.unique_ips > 100:
            anomaly_score += 0.1
            reasons.append("User-Agent过于单一")
        
        is_anomaly = anomaly_score > 0.3
        reason = "; ".join(reasons) if reasons else "正常"
        
        return is_anomaly, min(anomaly_score, 1.0), reason


class PatrolAgent:
    """巡捕智能体"""
    
    def __init__(
        self,
        agent_id: str = "patrol_001",
        sampling_interval: float = 5.0,
        window_size: int = 60,
        anomaly_threshold: float = 0.3
    ):
        self.agent_id = agent_id
        self.sampling_interval = sampling_interval
        self.window_size = window_size
        self.anomaly_threshold = anomaly_threshold
        
        self.baseline = BaselineProfile()
        
        self._request_buffer: deque = deque(maxlen=10000)
        self._ip_counter: Dict[str, deque] = {}
        self._url_counter: Dict[str, int] = {}
        self._ua_counter: Dict[str, int] = {}
        self._status_counter: Dict[int, int] = {}
        
        self._current_features: Optional[TrafficFeatures] = None
        self._feature_history: deque = deque(maxlen=1000)
        
        self._running = False
        self._task: Optional[asyncio.Task] = None
        
        self._message_handlers: List[callable] = []
        
        self._attack_signatures = self._load_attack_signatures()
    
    def _load_attack_signatures(self) -> Dict[str, List[str]]:
        """加载攻击特征签名"""
        return {
            "sql_injection": [
                "'", "\"", "--", ";", "/*", "*/", "xp_", "sp_", "exec(", "execute(",
                "union select", "or 1=1", "and 1=1", "drop table", "insert into",
                "delete from", "update set", "having ", "group by", "order by",
                "information_schema", "sysobjects", "syscolumns"
            ],
            "xss": [
                "<script", "javascript:", "onerror=", "onload=", "onclick=",
                "onmouseover=", "onfocus=", "onblur=", "<iframe", "<object",
                "<embed", "eval(", "document.cookie", "document.write"
            ],
            "path_traversal": [
                "../", "..\\", "/etc/passwd", "/etc/shadow", "c:\\windows",
                "boot.ini", "win.ini", "web.config", ".htaccess"
            ],
            "command_injection": [
                "|", "&&", "||", ";", "$(", "`", "cmd.exe", "/bin/bash",
                "/bin/sh", "wget ", "curl ", "nc -", "netcat"
            ]
        }
    
    def register_message_handler(self, handler: callable):
        """注册消息处理器"""
        self._message_handlers.append(handler)
    
    async def _send_message(self, message: Dict):
        """发送消息给判官智能体"""
        for handler in self._message_handlers:
            try:
                await handler(message)
            except Exception as e:
                print(f"消息处理器错误: {e}")
    
    def record_request(
        self,
        ip: str,
        url: str,
        method: str,
        status_code: int,
        user_agent: str,
        packet_size: int,
        response_time: float = 0.0,
        geo_location: str = ""
    ):
        """记录请求"""
        timestamp = time.time()
        
        self._request_buffer.append({
            "timestamp": timestamp,
            "ip": ip,
            "url": url,
            "method": method,
            "status_code": status_code,
            "user_agent": user_agent,
            "packet_size": packet_size,
            "response_time": response_time,
            "geo_location": geo_location
        })
        
        if ip not in self._ip_counter:
            self._ip_counter[ip] = deque(maxlen=1000)
        self._ip_counter[ip].append(timestamp)
        
        self._url_counter[url] = self._url_counter.get(url, 0) + 1
        self._ua_counter[user_agent] = self._ua_counter.get(user_agent, 0) + 1
        self._status_counter[status_code] = self._status_counter.get(status_code, 0) + 1
    
    def _calculate_entropy(self, counter: Dict) -> float:
        """计算熵值"""
        if not counter:
            return 0.0
        
        total = sum(counter.values())
        if total == 0:
            return 0.0
        
        probabilities = [count / total for count in counter.values()]
        entropy = -sum(p * np.log2(p + 1e-10) for p in probabilities if p > 0)
        
        return entropy
    
    def _extract_features(self) -> TrafficFeatures:
        """提取特征"""
        current_time = time.time()
        window_start = current_time - self.window_size
        
        recent_requests = [
            req for req in self._request_buffer
            if req["timestamp"] >= window_start
        ]
        
        if not recent_requests:
            return TrafficFeatures()
        
        ip_requests: Dict[str, List[float]] = {}
        for req in recent_requests:
            ip = req["ip"]
            if ip not in ip_requests:
                ip_requests[ip] = []
            ip_requests[ip].append(req["timestamp"])
        
        ip_rates = []
        for ip, timestamps in ip_requests.items():
            if len(timestamps) > 1:
                rate = len(timestamps) / self.window_size
                ip_rates.append(rate)
        
        avg_ip_rate = np.mean(ip_rates) if ip_rates else 0.0
        
        methods = {"GET": 0, "POST": 0, "OTHER": 0}
        for req in recent_requests:
            method = req["method"].upper()
            if method in methods:
                methods[method] += 1
            else:
                methods["OTHER"] += 1
        
        total_requests = len(recent_requests)
        get_ratio = methods["GET"] / total_requests if total_requests > 0 else 0.5
        post_ratio = methods["POST"] / total_requests if total_requests > 0 else 0.5
        
        status_counts = {2: 0, 4: 0, 5: 0}
        for req in recent_requests:
            status = req["status_code"]
            if 200 <= status < 300:
                status_counts[2] += 1
            elif 400 <= status < 500:
                status_counts[4] += 1
            elif 500 <= status < 600:
                status_counts[5] += 1
        
        status_2xx_ratio = status_counts[2] / total_requests if total_requests > 0 else 0.9
        status_4xx_ratio = status_counts[4] / total_requests if total_requests > 0 else 0.05
        status_5xx_ratio = status_counts[5] / total_requests if total_requests > 0 else 0.05
        
        packet_sizes = [req["packet_size"] for req in recent_requests]
        avg_packet_size = np.mean(packet_sizes) if packet_sizes else 0.0
        max_packet_size = max(packet_sizes) if packet_sizes else 0.0
        
        geo_locations = set()
        for req in recent_requests:
            if req.get("geo_location"):
                geo_locations.add(req["geo_location"])
        geo_diversity = len(geo_locations) / 50.0
        
        intervals = []
        sorted_requests = sorted(recent_requests, key=lambda x: x["timestamp"])
        for i in range(1, len(sorted_requests)):
            interval = sorted_requests[i]["timestamp"] - sorted_requests[i-1]["timestamp"]
            intervals.append(interval)
        
        request_interval_avg = np.mean(intervals) if intervals else 0.0
        request_interval_std = np.std(intervals) if intervals else 0.0
        
        url_entropy = self._calculate_entropy(self._url_counter)
        ua_entropy = self._calculate_entropy(self._ua_counter)
        
        error_rate = (status_counts[4] + status_counts[5]) / total_requests if total_requests > 0 else 0.0
        
        features = TrafficFeatures(
            timestamp=current_time,
            ip_request_rate=avg_ip_rate,
            unique_ips=len(ip_requests),
            unique_urls=len(self._url_counter),
            unique_uas=len(self._ua_counter),
            get_ratio=get_ratio,
            post_ratio=post_ratio,
            status_2xx_ratio=status_2xx_ratio,
            status_4xx_ratio=status_4xx_ratio,
            status_5xx_ratio=status_5xx_ratio,
            avg_packet_size=avg_packet_size,
            max_packet_size=max_packet_size,
            tcp_connections=len(ip_requests),
            geo_diversity=min(geo_diversity, 1.0),
            request_interval_avg=request_interval_avg,
            request_interval_std=request_interval_std,
            url_entropy=url_entropy,
            ua_entropy=ua_entropy,
            error_rate=error_rate,
            retry_rate=status_4xx_ratio * 0.5
        )
        
        return features
    
    def _detect_attack_type(self, features: TrafficFeatures) -> Tuple[AttackType, float]:
        """检测攻击类型"""
        scores = {
            AttackType.NORMAL: 0.0,
            AttackType.DDOS: 0.0,
            AttackType.CC: 0.0,
            AttackType.SQL_INJECTION: 0.0,
            AttackType.XSS: 0.0,
            AttackType.BRUTE_FORCE: 0.0,
            AttackType.CRAWLER: 0.0
        }
        
        if features.ip_request_rate > 100:
            scores[AttackType.DDOS] += 0.4
        if features.unique_ips > 1000:
            scores[AttackType.DDOS] += 0.3
        if features.tcp_connections > 5000:
            scores[AttackType.DDOS] += 0.3
        
        if features.request_interval_std < 0.1 and features.ip_request_rate > 20:
            scores[AttackType.CC] += 0.5
        if features.status_5xx_ratio > 0.3:
            scores[AttackType.CC] += 0.3
        if features.session_duration_avg < 1.0 and features.ip_request_rate > 30:
            scores[AttackType.CC] += 0.2
        
        if features.status_4xx_ratio > 0.5:
            scores[AttackType.BRUTE_FORCE] += 0.4
        if features.post_ratio > 0.8:
            scores[AttackType.BRUTE_FORCE] += 0.3
        
        if features.url_entropy > 7.0:
            scores[AttackType.CRAWLER] += 0.3
        if features.ua_entropy < 1.0 and features.unique_ips > 100:
            scores[AttackType.CRAWLER] += 0.4
        if features.get_ratio > 0.95:
            scores[AttackType.CRAWLER] += 0.2
        
        if features.error_rate > 0.3:
            scores[AttackType.SQL_INJECTION] += 0.3
            scores[AttackType.XSS] += 0.2
        
        max_attack = max(scores, key=scores.get)
        max_score = scores[max_attack]
        
        if max_score < 0.2:
            return AttackType.NORMAL, 1.0 - max_score
        
        return max_attack, max_score
    
    def _determine_threat_level(self, features: TrafficFeatures, attack_type: AttackType, confidence: float) -> ThreatLevel:
        """确定威胁等级"""
        if attack_type == AttackType.NORMAL:
            return ThreatLevel.SAFE
        
        if confidence > 0.8:
            if features.ip_request_rate > 500 or features.error_rate > 0.5:
                return ThreatLevel.CRITICAL
            return ThreatLevel.HIGH
        
        if confidence > 0.6:
            return ThreatLevel.MEDIUM
        
        if confidence > 0.3:
            return ThreatLevel.LOW
        
        return ThreatLevel.SAFE
    
    async def detect_anomaly(self) -> Optional[AnomalyReport]:
        """检测异常"""
        features = self._extract_features()
        self._current_features = features
        self._feature_history.append(features)
        
        is_anomaly, anomaly_score, reason = self.baseline.is_anomaly(features)
        
        if not is_anomaly:
            return None
        
        attack_type, confidence = self._detect_attack_type(features)
        threat_level = self._determine_threat_level(features, attack_type, confidence)
        
        top_ips = []
        current_time = time.time()
        window_start = current_time - self.window_size
        
        ip_rates = {}
        for ip, timestamps in self._ip_counter.items():
            recent = [t for t in timestamps if t >= window_start]
            if recent:
                rate = len(recent) / self.window_size
                ip_rates[ip] = rate
        
        sorted_ips = sorted(ip_rates.items(), key=lambda x: x[1], reverse=True)[:10]
        top_ips = [ip for ip, rate in sorted_ips if rate > 10]
        
        report = AnomalyReport(
            report_id=str(uuid.uuid4()),
            timestamp=current_time,
            features=features,
            threat_level=threat_level,
            suspected_attack=attack_type,
            confidence=confidence,
            source_ips=top_ips,
            details={
                "anomaly_score": anomaly_score,
                "reason": reason,
                "ip_rates": dict(sorted_ips[:5])
            }
        )
        
        return report
    
    async def run(self):
        """主运行循环"""
        self._running = True
        
        while self._running:
            try:
                report = await self.detect_anomaly()
                
                if report and report.threat_level != ThreatLevel.SAFE:
                    await self._send_message({
                        "type": "anomaly_detected",
                        "agent_id": self.agent_id,
                        "report": report.to_dict()
                    })
                
                await asyncio.sleep(self.sampling_interval)
                
            except Exception as e:
                print(f"巡捕智能体运行错误: {e}")
                await asyncio.sleep(1)
    
    def start(self):
        """启动智能体"""
        if not self._running:
            self._task = asyncio.create_task(self.run())
    
    def stop(self):
        """停止智能体"""
        self._running = False
        if self._task:
            self._task.cancel()
    
    def get_status(self) -> Dict:
        """获取状态"""
        return {
            "agent_id": self.agent_id,
            "running": self._running,
            "current_features": self._current_features.to_dict() if self._current_features else None,
            "buffer_size": len(self._request_buffer),
            "unique_ips_tracked": len(self._ip_counter),
            "feature_history_size": len(self._feature_history)
        }


patrol_agent = PatrolAgent()
