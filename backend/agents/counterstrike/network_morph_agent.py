"""
动态网络变换智能体
Network Morph Agent

动态调整网络结构（IP变换、端口变换、路由重定向）
使攻击者无法稳定攻击，配合蜜罐诱捕
"""

import asyncio
import time
import hashlib
import random
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from typing import Any, Dict, List, Optional, Set, Tuple
from collections import defaultdict, deque
import structlog

logger = structlog.get_logger()


class TransformType(Enum):
    IP_SHIFT = "ip_shift"
    PORT_HOPPING = "port_hopping"
    ROUTE_REDIRECT = "route_redirect"
    SERVICE_MIGRATION = "service_migration"
    TOPOLOGY_CHANGE = "topology_change"
    DECOY_INJECTION = "decoy_injection"


class TransformTrigger(Enum):
    ATTACK_DETECTED = "attack_detected"
    SCHEDULED = "scheduled"
    THRESHOLD_REACHED = "threshold_reached"
    MANUAL = "manual"
    ADAPTIVE = "adaptive"


@dataclass
class NetworkTransform:
    transform_id: str
    transform_type: TransformType
    trigger: TransformTrigger
    timestamp: datetime
    source_config: Dict[str, Any]
    target_config: Dict[str, Any]
    affected_services: List[str]
    duration_seconds: float
    success: bool = True
    rollback_data: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict:
        return {
            "transform_id": self.transform_id,
            "transform_type": self.transform_type.value,
            "trigger": self.trigger.value,
            "timestamp": self.timestamp.isoformat(),
            "source_config": self.source_config,
            "target_config": self.target_config,
            "affected_services": self.affected_services,
            "duration_seconds": self.duration_seconds,
            "success": self.success,
            "rollback_data": self.rollback_data
        }


class IPPool:
    def __init__(self, base_network: str = "10.100.0.0/16"):
        self.base_network = base_network
        self.available_ips: Set[str] = set()
        self.used_ips: Dict[str, str] = {}
        self.ip_history: Dict[str, List[Dict]] = defaultdict(list)
        
        self._initialize_pool()
        
    def _initialize_pool(self):
        parts = self.base_network.split("/")
        base = parts[0]
        prefix = int(parts[1]) if len(parts) > 1 else 16
        
        base_parts = base.split(".")
        if len(base_parts) == 4:
            for i in range(1, 255):
                for j in range(1, 255):
                    ip = f"{base_parts[0]}.{base_parts[1]}.{i}.{j}"
                    self.available_ips.add(ip)
                    
    def allocate(self, service_id: str) -> Optional[str]:
        if not self.available_ips:
            return None
            
        ip = self.available_ips.pop()
        self.used_ips[ip] = service_id
        
        self.ip_history[service_id].append({
            "ip": ip,
            "allocated_at": datetime.now().isoformat(),
            "action": "allocate"
        })
        
        return ip
        
    def release(self, ip: str) -> bool:
        if ip not in self.used_ips:
            return False
            
        service_id = self.used_ips.pop(ip)
        self.available_ips.add(ip)
        
        self.ip_history[service_id].append({
            "ip": ip,
            "released_at": datetime.now().isoformat(),
            "action": "release"
        })
        
        return True
        
    def shift_ip(self, current_ip: str, service_id: str) -> Optional[str]:
        new_ip = self.allocate(service_id)
        if new_ip:
            self.release(current_ip)
        return new_ip
        
    def get_service_ip(self, service_id: str) -> Optional[str]:
        for ip, sid in self.used_ips.items():
            if sid == service_id:
                return ip
        return None


class PortHoppingEngine:
    def __init__(self, port_range: Tuple[int, int] = (10000, 65535)):
        self.port_range = port_range
        self.service_ports: Dict[str, int] = {}
        self.port_history: Dict[str, List[Dict]] = defaultdict(list)
        self.hopping_sequences: Dict[str, List[int]] = {}
        self.sequence_index: Dict[str, int] = {}
        
    def allocate_port(self, service_id: str, preferred_port: Optional[int] = None) -> int:
        if preferred_port and self._is_port_available(preferred_port):
            port = preferred_port
        else:
            port = self._find_available_port()
            
        self.service_ports[service_id] = port
        self._record_port_change(service_id, port, "allocate")
        
        return port
        
    def hop_port(self, service_id: str) -> int:
        current_port = self.service_ports.get(service_id)
        
        if service_id in self.hopping_sequences:
            seq = self.hopping_sequences[service_id]
            idx = self.sequence_index.get(service_id, 0)
            new_port = seq[idx % len(seq)]
            self.sequence_index[service_id] = idx + 1
        else:
            new_port = self._find_available_port()
            
        if current_port:
            self._record_port_change(service_id, current_port, "release")
            
        self.service_ports[service_id] = new_port
        self._record_port_change(service_id, new_port, "allocate")
        
        return new_port
        
    def generate_hopping_sequence(self, service_id: str, length: int = 100, seed: Optional[int] = None) -> List[int]:
        if seed:
            random.seed(seed)
            
        sequence = []
        used = set(self.service_ports.values())
        
        while len(sequence) < length:
            port = random.randint(self.port_range[0], self.port_range[1])
            if port not in used and port not in sequence:
                sequence.append(port)
                
        self.hopping_sequences[service_id] = sequence
        self.sequence_index[service_id] = 0
        
        return sequence
        
    def _find_available_port(self) -> int:
        used = set(self.service_ports.values())
        
        for port in range(self.port_range[0], self.port_range[1]):
            if port not in used:
                return port
                
        raise RuntimeError("No available ports")
        
    def _is_port_available(self, port: int) -> bool:
        return port not in self.service_ports.values()
        
    def _record_port_change(self, service_id: str, port: int, action: str):
        self.port_history[service_id].append({
            "port": port,
            "action": action,
            "timestamp": datetime.now().isoformat()
        })


class RouteManager:
    def __init__(self):
        self.routes: Dict[str, Dict] = {}
        self.redirect_rules: Dict[str, Dict] = {}
        self.route_history: List[Dict] = []
        
    def add_route(
        self,
        route_id: str,
        source: str,
        destination: str,
        gateway: Optional[str] = None,
        priority: int = 100
    ) -> Dict:
        route = {
            "route_id": route_id,
            "source": source,
            "destination": destination,
            "gateway": gateway,
            "priority": priority,
            "created_at": datetime.now().isoformat(),
            "active": True
        }
        
        self.routes[route_id] = route
        self._record_route_change(route, "add")
        
        return route
        
    def create_redirect(
        self,
        redirect_id: str,
        original_target: str,
        new_target: str,
        attacker_ips: List[str],
        duration_seconds: int = 3600
    ) -> Dict:
        redirect = {
            "redirect_id": redirect_id,
            "original_target": original_target,
            "new_target": new_target,
            "attacker_ips": attacker_ips,
            "duration_seconds": duration_seconds,
            "created_at": datetime.now().isoformat(),
            "expires_at": (datetime.now() + timedelta(seconds=duration_seconds)).isoformat(),
            "active": True
        }
        
        self.redirect_rules[redirect_id] = redirect
        self._record_route_change(redirect, "redirect")
        
        return redirect
        
    def remove_redirect(self, redirect_id: str) -> bool:
        if redirect_id not in self.redirect_rules:
            return False
            
        redirect = self.redirect_rules.pop(redirect_id)
        redirect["active"] = False
        self._record_route_change(redirect, "remove_redirect")
        
        return True
        
    def get_redirect_for_ip(self, ip: str) -> Optional[Dict]:
        for redirect in self.redirect_rules.values():
            if redirect["active"] and ip in redirect["attacker_ips"]:
                expires = datetime.fromisoformat(redirect["expires_at"])
                if datetime.now() < expires:
                    return redirect
        return None
        
    def cleanup_expired(self):
        now = datetime.now()
        expired = []
        
        for redirect_id, redirect in self.redirect_rules.items():
            if redirect["active"]:
                expires = datetime.fromisoformat(redirect["expires_at"])
                if now >= expires:
                    expired.append(redirect_id)
                    
        for redirect_id in expired:
            self.remove_redirect(redirect_id)
            
        return len(expired)
        
    def _record_route_change(self, route: Dict, action: str):
        self.route_history.append({
            **route,
            "action": action,
            "recorded_at": datetime.now().isoformat()
        })


class NetworkMorphAgent:
    def __init__(
        self,
        agent_id: str = "network_morph_agent_001",
        memory_client: Optional[Any] = None,
        communication_bus: Optional[Any] = None
    ):
        self.agent_id = agent_id
        self.memory_client = memory_client
        self.communication_bus = communication_bus
        
        self.ip_pool = IPPool()
        self.port_engine = PortHoppingEngine()
        self.route_manager = RouteManager()
        
        self.services: Dict[str, Dict] = {}
        self.transforms: deque = deque(maxlen=500)
        self.active_transforms: Dict[str, NetworkTransform] = {}
        
        self.morph_policies: Dict[str, Dict] = {}
        self.attack_tracking: Dict[str, List[Dict]] = defaultdict(list)
        
        self.stats = {
            "total_transforms": 0,
            "ip_shifts": 0,
            "port_hops": 0,
            "redirects_created": 0,
            "attacks_mitigated": 0,
            "avg_transform_time_ms": 0.0
        }
        
        self._running = False
        self._task: Optional[asyncio.Task] = None
        
    async def start(self):
        self._running = True
        self._task = asyncio.create_task(self._morph_loop())
        logger.info(f"NetworkMorphAgent {self.agent_id} started")
        
    async def stop(self):
        self._running = False
        if self._task:
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass
        logger.info(f"NetworkMorphAgent {self.agent_id} stopped")
        
    async def _morph_loop(self):
        while self._running:
            try:
                await self._cleanup_expired_redirects()
                await self._check_scheduled_transforms()
                await self._analyze_attack_patterns()
                await asyncio.sleep(30)
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in morph loop: {e}")
                await asyncio.sleep(5)
                
    async def _cleanup_expired_redirects(self):
        expired = self.route_manager.cleanup_expired()
        if expired > 0:
            logger.info(f"Cleaned up {expired} expired redirects")
            
    async def _check_scheduled_transforms(self):
        now = datetime.now()
        
        for service_id, policy in self.morph_policies.items():
            if policy.get("type") == "scheduled":
                interval = policy.get("interval_seconds", 3600)
                last_transform = policy.get("last_transform")
                
                if last_transform:
                    last_time = datetime.fromisoformat(last_transform)
                    if (now - last_time).total_seconds() >= interval:
                        await self.execute_transform(
                            service_id,
                            TransformType.IP_SHIFT,
                            TransformTrigger.SCHEDULED
                        )
                        
    async def _analyze_attack_patterns(self):
        for attacker_ip, attacks in list(self.attack_tracking.items()):
            recent_attacks = [
                a for a in attacks
                if datetime.now() - datetime.fromisoformat(a["timestamp"]) < timedelta(minutes=5)
            ]
            
            if len(recent_attacks) >= 10:
                target_service = recent_attacks[0].get("target_service")
                if target_service:
                    await self.execute_transform(
                        target_service,
                        TransformType.IP_SHIFT,
                        TransformTrigger.THRESHOLD_REACHED
                    )
                    self.stats["attacks_mitigated"] += 1
                    
                    del self.attack_tracking[attacker_ip]
                    
    def register_service(
        self,
        service_id: str,
        service_type: str,
        initial_port: Optional[int] = None,
        initial_ip: Optional[str] = None
    ) -> Dict:
        ip = initial_ip or self.ip_pool.allocate(service_id)
        port = self.port_engine.allocate_port(service_id, initial_port)
        
        service = {
            "service_id": service_id,
            "service_type": service_type,
            "ip": ip,
            "port": port,
            "registered_at": datetime.now().isoformat(),
            "transform_count": 0
        }
        
        self.services[service_id] = service
        
        logger.info(f"Registered service {service_id} at {ip}:{port}")
        
        return service
        
    async def execute_transform(
        self,
        service_id: str,
        transform_type: TransformType,
        trigger: TransformTrigger,
        custom_config: Optional[Dict] = None
    ) -> Optional[NetworkTransform]:
        start_time = time.time()
        
        if service_id not in self.services:
            logger.warning(f"Service {service_id} not found")
            return None
            
        service = self.services[service_id]
        source_config = {
            "ip": service["ip"],
            "port": service["port"]
        }
        
        transform_id = self._generate_transform_id()
        
        try:
            if transform_type == TransformType.IP_SHIFT:
                new_ip = self.ip_pool.shift_ip(service["ip"], service_id)
                if new_ip:
                    service["ip"] = new_ip
                    self.stats["ip_shifts"] += 1
                else:
                    raise RuntimeError("No available IP for shift")
                    
            elif transform_type == TransformType.PORT_HOPPING:
                new_port = self.port_engine.hop_port(service_id)
                service["port"] = new_port
                self.stats["port_hops"] += 1
                
            elif transform_type == TransformType.ROUTE_REDIRECT:
                if custom_config:
                    redirect = self.route_manager.create_redirect(
                        redirect_id=f"redirect_{transform_id}",
                        original_target=service["ip"],
                        new_target=custom_config.get("new_target", "10.100.255.1"),
                        attacker_ips=custom_config.get("attacker_ips", []),
                        duration_seconds=custom_config.get("duration", 3600)
                    )
                    self.stats["redirects_created"] += 1
                    
            elif transform_type == TransformType.DECOY_INJECTION:
                decoy_service = await self._create_decoy_service(service_id)
                if decoy_service:
                    custom_config = {"decoy": decoy_service}
                    
            target_config = {
                "ip": service["ip"],
                "port": service["port"]
            }
            
            duration = (time.time() - start_time) * 1000
            
            transform = NetworkTransform(
                transform_id=transform_id,
                transform_type=transform_type,
                trigger=trigger,
                timestamp=datetime.now(),
                source_config=source_config,
                target_config=target_config,
                affected_services=[service_id],
                duration_seconds=duration / 1000,
                success=True,
                rollback_data={"original": source_config}
            )
            
            service["transform_count"] += 1
            self.transforms.append(transform)
            self.stats["total_transforms"] += 1
            self._update_avg_transform_time(duration)
            
            if service_id in self.morph_policies:
                self.morph_policies[service_id]["last_transform"] = datetime.now().isoformat()
                
            if self.communication_bus:
                await self.communication_bus.publish(
                    "network_transform",
                    transform.to_dict()
                )
                
            logger.info(
                f"Executed {transform_type.value} for service {service_id}: "
                f"{source_config} -> {target_config}"
            )
            
            return transform
            
        except Exception as e:
            logger.error(f"Transform failed: {e}")
            
            transform = NetworkTransform(
                transform_id=transform_id,
                transform_type=transform_type,
                trigger=trigger,
                timestamp=datetime.now(),
                source_config=source_config,
                target_config={},
                affected_services=[service_id],
                duration_seconds=0,
                success=False
            )
            
            self.transforms.append(transform)
            return transform
            
    async def _create_decoy_service(self, service_id: str) -> Optional[Dict]:
        decoy_id = f"decoy_{service_id}_{int(time.time())}"
        
        ip = self.ip_pool.allocate(decoy_id)
        port = self.port_engine.allocate_port(decoy_id)
        
        if ip and port:
            decoy = {
                "decoy_id": decoy_id,
                "parent_service": service_id,
                "ip": ip,
                "port": port,
                "created_at": datetime.now().isoformat()
            }
            return decoy
            
        return None
        
    def set_morph_policy(
        self,
        service_id: str,
        policy_type: str,
        **kwargs
    ):
        policy = {
            "type": policy_type,
            "created_at": datetime.now().isoformat(),
            **kwargs
        }
        
        self.morph_policies[service_id] = policy
        logger.info(f"Set morph policy for {service_id}: {policy_type}")
        
    def track_attack(self, attacker_ip: str, target_service: str, attack_type: str):
        self.attack_tracking[attacker_ip].append({
            "target_service": target_service,
            "attack_type": attack_type,
            "timestamp": datetime.now().isoformat()
        })
        
    async def redirect_attacker(
        self,
        attacker_ip: str,
        target_service: str,
        honeypot_ip: str,
        duration_seconds: int = 3600
    ) -> Optional[Dict]:
        service = self.services.get(target_service)
        if not service:
            return None
            
        redirect = self.route_manager.create_redirect(
            redirect_id=f"redirect_{attacker_ip}_{int(time.time())}",
            original_target=service["ip"],
            new_target=honeypot_ip,
            attacker_ips=[attacker_ip],
            duration_seconds=duration_seconds
        )
        
        self.stats["redirects_created"] += 1
        
        if self.communication_bus:
            await self.communication_bus.publish(
                "attacker_redirected",
                {
                    "attacker_ip": attacker_ip,
                    "original_target": service["ip"],
                    "new_target": honeypot_ip,
                    "duration_seconds": duration_seconds
                }
            )
            
        return redirect
        
    async def get_service(self, service_id: str) -> Optional[Dict]:
        return self.services.get(service_id)
        
    async def get_all_services(self) -> List[Dict]:
        return list(self.services.values())
        
    async def get_transform_history(self, limit: int = 50) -> List[Dict]:
        transforms = list(self.transforms)[-limit:]
        return [t.to_dict() for t in transforms]
        
    async def get_active_redirects(self) -> List[Dict]:
        return [
            r for r in self.route_manager.redirect_rules.values()
            if r.get("active", False)
        ]
        
    async def get_ip_pool_status(self) -> Dict:
        return {
            "total_ips": len(self.ip_pool.available_ips) + len(self.ip_pool.used_ips),
            "available_ips": len(self.ip_pool.available_ips),
            "used_ips": len(self.ip_pool.used_ips),
            "services_using_pool": list(self.ip_pool.used_ips.values())
        }
        
    def _generate_transform_id(self) -> str:
        return f"xform_{int(time.time() * 1000)}_{hashlib.md5(str(time.time()).encode()).hexdigest()[:6]}"
        
    def _update_avg_transform_time(self, duration: float):
        current = self.stats["avg_transform_time_ms"]
        count = self.stats["total_transforms"]
        self.stats["avg_transform_time_ms"] = (
            current * (count - 1) + duration
        ) / count
        
    def get_stats(self) -> Dict:
        return {
            **self.stats,
            "registered_services": len(self.services),
            "active_redirects": len([
                r for r in self.route_manager.redirect_rules.values()
                if r.get("active", False)
            ]),
            "tracked_attackers": len(self.attack_tracking)
        }
