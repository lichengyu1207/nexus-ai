"""
服务发现模块 - Consul/etcd动态节点管理
实现智能体节点的自动注册、发现、健康检查
"""

from enum import Enum
from typing import Dict, List, Optional, Any, Callable
from dataclasses import dataclass, field
from datetime import datetime
import asyncio
import logging
import json
import random

logger = logging.getLogger(__name__)


class ServiceStatus(Enum):
    HEALTHY = "healthy"
    UNHEALTHY = "unhealthy"
    MAINTENANCE = "maintenance"
    UNKNOWN = "unknown"


class LoadBalanceStrategy(Enum):
    ROUND_ROBIN = "round_robin"
    RANDOM = "random"
    LEAST_CONNECTIONS = "least_connections"
    WEIGHTED = "weighted"
    CONSISTENT_HASH = "consistent_hash"


@dataclass
class ServiceNode:
    node_id: str
    service_name: str
    address: str
    port: int
    tags: List[str]
    metadata: Dict[str, Any]
    weight: int = 1
    status: ServiceStatus = ServiceStatus.UNKNOWN
    last_heartbeat: datetime = None
    connections: int = 0
    cpu_usage: float = 0.0
    memory_usage: float = 0.0
    
    @property
    def endpoint(self) -> str:
        return f"{self.address}:{self.port}"
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "node_id": self.node_id,
            "service_name": self.service_name,
            "address": self.address,
            "port": self.port,
            "tags": self.tags,
            "metadata": self.metadata,
            "weight": self.weight,
            "status": self.status.value,
            "last_heartbeat": self.last_heartbeat.isoformat() if self.last_heartbeat else None,
            "connections": self.connections,
            "cpu_usage": self.cpu_usage,
            "memory_usage": self.memory_usage
        }


@dataclass
class HealthCheck:
    check_id: str
    node_id: str
    check_type: str
    interval_seconds: int
    timeout_seconds: int
    endpoint: str
    last_status: ServiceStatus = ServiceStatus.UNKNOWN
    last_check: datetime = None
    consecutive_failures: int = 0


class ServiceRegistry:
    def __init__(self):
        self._nodes: Dict[str, ServiceNode] = {}
        self._service_index: Dict[str, List[str]] = {}
        self._tag_index: Dict[str, List[str]] = {}
        self._health_checks: Dict[str, HealthCheck] = {}
        self._heartbeat_timeout = 30
        
    def register(self, node: ServiceNode) -> bool:
        self._nodes[node.node_id] = node
        node.last_heartbeat = datetime.now()
        node.status = ServiceStatus.HEALTHY
        
        if node.service_name not in self._service_index:
            self._service_index[node.service_name] = []
        if node.node_id not in self._service_index[node.service_name]:
            self._service_index[node.service_name].append(node.node_id)
            
        for tag in node.tags:
            if tag not in self._tag_index:
                self._tag_index[tag] = []
            if node.node_id not in self._tag_index[tag]:
                self._tag_index[tag].append(node.node_id)
                
        logger.info(f"Registered service node: {node.node_id} ({node.service_name})")
        return True
        
    def deregister(self, node_id: str) -> bool:
        if node_id not in self._nodes:
            return False
            
        node = self._nodes[node_id]
        
        if node.service_name in self._service_index:
            if node_id in self._service_index[node.service_name]:
                self._service_index[node.service_name].remove(node_id)
                
        for tag in node.tags:
            if tag in self._tag_index:
                if node_id in self._tag_index[tag]:
                    self._tag_index[tag].remove(node_id)
                    
        del self._nodes[node_id]
        
        if node_id in self._health_checks:
            del self._health_checks[node_id]
            
        logger.info(f"Deregistered service node: {node_id}")
        return True
        
    def get_node(self, node_id: str) -> Optional[ServiceNode]:
        return self._nodes.get(node_id)
        
    def get_service_nodes(
        self, 
        service_name: str,
        healthy_only: bool = True
    ) -> List[ServiceNode]:
        node_ids = self._service_index.get(service_name, [])
        nodes = [self._nodes[nid] for nid in node_ids if nid in self._nodes]
        
        if healthy_only:
            nodes = [n for n in nodes if n.status == ServiceStatus.HEALTHY]
            
        return nodes
        
    def get_nodes_by_tag(self, tag: str) -> List[ServiceNode]:
        node_ids = self._tag_index.get(tag, [])
        return [self._nodes[nid] for nid in node_ids if nid in self._nodes]
        
    def update_heartbeat(
        self, 
        node_id: str,
        cpu_usage: float = 0.0,
        memory_usage: float = 0.0
    ) -> bool:
        node = self._nodes.get(node_id)
        if not node:
            return False
            
        node.last_heartbeat = datetime.now()
        node.cpu_usage = cpu_usage
        node.memory_usage = memory_usage
        node.status = ServiceStatus.HEALTHY
        
        return True
        
    def check_health(self) -> List[str]:
        import time
        current_time = datetime.now()
        unhealthy_nodes = []
        
        for node_id, node in self._nodes.items():
            if node.last_heartbeat:
                elapsed = (current_time - node.last_heartbeat).total_seconds()
                if elapsed > self._heartbeat_timeout:
                    node.status = ServiceStatus.UNHEALTHY
                    unhealthy_nodes.append(node_id)
                    
        return unhealthy_nodes
        
    def add_health_check(self, check: HealthCheck):
        self._health_checks[check.node_id] = check
        
    def get_all_services(self) -> Dict[str, List[ServiceNode]]:
        return {
            service: self.get_service_nodes(service, healthy_only=False)
            for service in self._service_index
        }


class LoadBalancer:
    def __init__(
        self, 
        registry: ServiceRegistry,
        strategy: LoadBalanceStrategy = LoadBalanceStrategy.ROUND_ROBIN
    ):
        self.registry = registry
        self.strategy = strategy
        self._round_robin_index: Dict[str, int] = {}
        self._consistent_hash_ring: Dict[str, List[tuple]] = {}
        
    def select_node(
        self, 
        service_name: str,
        key: Optional[str] = None
    ) -> Optional[ServiceNode]:
        nodes = self.registry.get_service_nodes(service_name)
        
        if not nodes:
            return None
            
        if self.strategy == LoadBalanceStrategy.ROUND_ROBIN:
            return self._round_robin_select(service_name, nodes)
        elif self.strategy == LoadBalanceStrategy.RANDOM:
            return random.choice(nodes)
        elif self.strategy == LoadBalanceStrategy.LEAST_CONNECTIONS:
            return self._least_connections_select(nodes)
        elif self.strategy == LoadBalanceStrategy.WEIGHTED:
            return self._weighted_select(nodes)
        elif self.strategy == LoadBalanceStrategy.CONSISTENT_HASH:
            return self._consistent_hash_select(service_name, nodes, key)
            
        return nodes[0]
        
    def _round_robin_select(
        self, 
        service_name: str, 
        nodes: List[ServiceNode]
    ) -> ServiceNode:
        if service_name not in self._round_robin_index:
            self._round_robin_index[service_name] = 0
            
        index = self._round_robin_index[service_name] % len(nodes)
        self._round_robin_index[service_name] += 1
        
        return nodes[index]
        
    def _least_connections_select(self, nodes: List[ServiceNode]) -> ServiceNode:
        return min(nodes, key=lambda n: n.connections)
        
    def _weighted_select(self, nodes: List[ServiceNode]) -> ServiceNode:
        total_weight = sum(n.weight for n in nodes)
        r = random.randint(1, total_weight)
        
        current = 0
        for node in nodes:
            current += node.weight
            if r <= current:
                return node
                
        return nodes[0]
        
    def _consistent_hash_select(
        self,
        service_name: str,
        nodes: List[ServiceNode],
        key: Optional[str]
    ) -> ServiceNode:
        if not key:
            return nodes[0]
            
        if service_name not in self._consistent_hash_ring:
            self._build_hash_ring(service_name, nodes)
            
        ring = self._consistent_hash_ring.get(service_name, [])
        if not ring:
            return nodes[0]
            
        key_hash = hash(key)
        
        for hash_val, node in ring:
            if key_hash <= hash_val:
                return node
                
        return ring[0][1]
        
    def _build_hash_ring(self, service_name: str, nodes: List[ServiceNode]):
        ring = []
        virtual_nodes = 150
        
        for node in nodes:
            for i in range(virtual_nodes):
                hash_val = hash(f"{node.node_id}:{i}")
                ring.append((hash_val, node))
                
        ring.sort(key=lambda x: x[0])
        self._consistent_hash_ring[service_name] = ring


class ServiceDiscoveryClient:
    def __init__(self, registry: ServiceRegistry):
        self.registry = registry
        self.load_balancer = LoadBalancer(registry)
        self._watchers: Dict[str, List[Callable]] = {}
        
    async def register_service(
        self,
        service_name: str,
        address: str,
        port: int,
        tags: List[str] = None,
        metadata: Dict[str, Any] = None,
        weight: int = 1
    ) -> str:
        import uuid
        node_id = f"{service_name}_{uuid.uuid4().hex[:8]}"
        
        node = ServiceNode(
            node_id=node_id,
            service_name=service_name,
            address=address,
            port=port,
            tags=tags or [],
            metadata=metadata or {},
            weight=weight
        )
        
        self.registry.register(node)
        
        await self._notify_watchers(service_name, "register", node)
        
        return node_id
        
    async def deregister_service(self, node_id: str) -> bool:
        node = self.registry.get_node(node_id)
        if not node:
            return False
            
        service_name = node.service_name
        result = self.registry.deregister(node_id)
        
        if result:
            await self._notify_watchers(service_name, "deregister", node)
            
        return result
        
    async def discover_service(
        self,
        service_name: str,
        tags: List[str] = None,
        load_balance: bool = True
    ) -> Optional[ServiceNode]:
        if tags:
            nodes_by_tag = set()
            for tag in tags:
                tag_nodes = self.registry.get_nodes_by_tag(tag)
                if nodes_by_tag:
                    nodes_by_tag &= set(n.node_id for n in tag_nodes)
                else:
                    nodes_by_tag = set(n.node_id for n in tag_nodes)
                    
            service_nodes = self.registry.get_service_nodes(service_name)
            nodes = [n for n in service_nodes if n.node_id in nodes_by_tag]
        else:
            nodes = self.registry.get_service_nodes(service_name)
            
        if not nodes:
            return None
            
        if load_balance:
            return self.load_balancer.select_node(service_name)
            
        return nodes[0]
        
    async def discover_all_instances(
        self,
        service_name: str
    ) -> List[ServiceNode]:
        return self.registry.get_service_nodes(service_name)
        
    async def send_heartbeat(
        self,
        node_id: str,
        cpu_usage: float = 0.0,
        memory_usage: float = 0.0
    ) -> bool:
        return self.registry.update_heartbeat(node_id, cpu_usage, memory_usage)
        
    def watch_service(
        self,
        service_name: str,
        callback: Callable[[str, ServiceNode], None]
    ):
        if service_name not in self._watchers:
            self._watchers[service_name] = []
        self._watchers[service_name].append(callback)
        
    async def _notify_watchers(
        self,
        service_name: str,
        event_type: str,
        node: ServiceNode
    ):
        watchers = self._watchers.get(service_name, [])
        for callback in watchers:
            try:
                if asyncio.iscoroutinefunction(callback):
                    await callback(event_type, node)
                else:
                    callback(event_type, node)
            except Exception as e:
                logger.error(f"Watcher callback error: {e}")
                
    def get_service_health(self, service_name: str) -> Dict[str, Any]:
        nodes = self.registry.get_service_nodes(service_name, healthy_only=False)
        
        healthy = len([n for n in nodes if n.status == ServiceStatus.HEALTHY])
        unhealthy = len([n for n in nodes if n.status == ServiceStatus.UNHEALTHY])
        
        return {
            "service_name": service_name,
            "total_instances": len(nodes),
            "healthy_instances": healthy,
            "unhealthy_instances": unhealthy,
            "health_ratio": healthy / len(nodes) if nodes else 0,
            "nodes": [n.to_dict() for n in nodes]
        }


class HealthCheckManager:
    def __init__(self, registry: ServiceRegistry):
        self.registry = registry
        self._check_interval = 10
        self._running = False
        
    async def start_health_checks(self):
        self._running = True
        while self._running:
            await self._run_checks()
            await asyncio.sleep(self._check_interval)
            
    async def stop_health_checks(self):
        self._running = False
        
    async def _run_checks(self):
        unhealthy = self.registry.check_health()
        
        for node_id in unhealthy:
            logger.warning(f"Node {node_id} marked as unhealthy")
            
    def configure_check(
        self,
        node_id: str,
        check_type: str,
        interval: int,
        timeout: int,
        endpoint: str
    ):
        check = HealthCheck(
            check_id=f"check_{node_id}",
            node_id=node_id,
            check_type=check_type,
            interval_seconds=interval,
            timeout_seconds=timeout,
            endpoint=endpoint
        )
        self.registry.add_health_check(check)


service_registry = ServiceRegistry()
discovery_client = ServiceDiscoveryClient(service_registry)
health_check_manager = HealthCheckManager(service_registry)


async def register_agent_service(
    agent_id: str,
    agent_type: str,
    address: str,
    port: int,
    capabilities: List[str] = None
) -> str:
    return await discovery_client.register_service(
        service_name=f"agent_{agent_type}",
        address=address,
        port=port,
        tags=capabilities or [],
        metadata={"agent_id": agent_id, "agent_type": agent_type}
    )


async def discover_agent_service(
    agent_type: str,
    required_capabilities: List[str] = None
) -> Optional[ServiceNode]:
    return await discovery_client.discover_service(
        service_name=f"agent_{agent_type}",
        tags=required_capabilities
    )


def get_service_registry() -> ServiceRegistry:
    return service_registry


def get_discovery_client() -> ServiceDiscoveryClient:
    return discovery_client
