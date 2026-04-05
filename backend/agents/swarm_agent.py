"""
蜂群协同的多智能体自组织系统
"""

import os
import json
import logging
import random
import time
import threading
from typing import Dict, Any, List, Optional, Tuple
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass
class AgentState:
    """智能体状态"""
    id: str  # 智能体ID
    x: float  # x坐标
    y: float  # y坐标
    load: float  # 负载率 (0-1)
    capabilities: List[str]  # 能力列表
    status: str  # 状态 (idle, busy, offline)
    neighbors: List[str]  # 邻居ID列表


@dataclass
class Task:
    """任务"""
    id: str  # 任务ID
    type: str  # 任务类型
    content: str  # 任务内容
    location: Tuple[float, float]  # 任务位置
    priority: int  # 优先级 (1-5)
    status: str  # 状态 (pending, assigned, in_progress, completed, failed)
    assigned_to: Optional[str] = None  # 分配给的智能体
    start_time: Optional[float] = None  # 开始时间
    end_time: Optional[float] = None  # 结束时间


@dataclass
class Pheromone:
    """信息素"""
    location: Tuple[float, float]  # 位置
    concentration: float  # 浓度
    timestamp: float  # 释放时间
    decay_rate: float = 0.02  # 衰减率 (每秒)


class SwarmAgent:
    """蜂群智能体"""
    
    def __init__(self, agent_id: str, x: float, y: float):
        self.agent_id = agent_id
        self.x = x
        self.y = y
        self.load = 0.0
        self.capabilities = []
        self.status = "idle"
        self.neighbors = []
        self.tasks = {}
        self.pheromones = {}
        self.heartbeat_interval = 1.0  # 心跳间隔（秒）
        self.max_neighbor_distance = 10.0  # 最大邻居距离
        self.last_heartbeat = time.time()
        self.heartbeat_thread = None
        self.running = True
    
    def start(self):
        """启动智能体"""
        self.heartbeat_thread = threading.Thread(target=self._heartbeat_loop)
        self.heartbeat_thread.daemon = True
        self.heartbeat_thread.start()
        logger.info(f"智能体 {self.agent_id} 启动成功")
    
    def stop(self):
        """停止智能体"""
        self.running = False
        if self.heartbeat_thread:
            self.heartbeat_thread.join()
        logger.info(f"智能体 {self.agent_id} 已停止")
    
    def _heartbeat_loop(self):
        """心跳循环"""
        while self.running:
            self._send_heartbeat()
            self._check_neighbors()
            self._update_pheromones()
            time.sleep(self.heartbeat_interval)
    
    def _send_heartbeat(self):
        """发送心跳"""
        # 模拟发送心跳包
        self.last_heartbeat = time.time()
    
    def _check_neighbors(self):
        """检查邻居状态"""
        # 模拟检查邻居心跳
        pass
    
    def _update_pheromones(self):
        """更新信息素"""
        # 信息素衰减
        current_time = time.time()
        to_remove = []
        
        for pheromone_id, pheromone in self.pheromones.items():
            elapsed = current_time - pheromone.timestamp
            new_concentration = pheromone.concentration * (1 - pheromone.decay_rate) ** elapsed
            if new_concentration < 0.1:
                to_remove.append(pheromone_id)
            else:
                pheromone.concentration = new_concentration
                pheromone.timestamp = current_time
        
        for pheromone_id in to_remove:
            del self.pheromones[pheromone_id]
    
    def calculate_distance(self, x: float, y: float) -> float:
        """计算距离"""
        return ((self.x - x) ** 2 + (self.y - y) ** 2) ** 0.5
    
    def add_neighbor(self, neighbor_id: str):
        """添加邻居"""
        if neighbor_id not in self.neighbors:
            self.neighbors.append(neighbor_id)
            logger.info(f"智能体 {self.agent_id} 添加邻居 {neighbor_id}")
    
    def remove_neighbor(self, neighbor_id: str):
        """移除邻居"""
        if neighbor_id in self.neighbors:
            self.neighbors.remove(neighbor_id)
            logger.info(f"智能体 {self.agent_id} 移除邻居 {neighbor_id}")
    
    def receive_task_broadcast(self, task: Task, hop_count: int):
        """接收任务广播"""
        if hop_count <= 0:
            return
        
        if task.id not in self.tasks:
            self.tasks[task.id] = task
            logger.info(f"智能体 {self.agent_id} 接收到任务 {task.id}")
            
            # 计算竞标分数
            score = self._calculate_bid_score(task)
            logger.info(f"智能体 {self.agent_id} 竞标分数: {score}")
            
            # 广播给邻居
            if hop_count > 1:
                self.broadcast_task(task, hop_count - 1)
    
    def _calculate_bid_score(self, task: Task) -> float:
        """计算竞标分数"""
        # 权重
        w1 = 0.5  # 能力匹配度权重
        w2 = 0.3  # 负载权重
        w3 = 0.2  # 距离权重
        
        # 能力匹配度
        capability_match = 1.0 if any(cap in self.capabilities for cap in self._get_task_required_capabilities(task)) else 0.0
        
        # 负载率
        load_factor = 1.0 - self.load
        
        # 距离因素
        distance = self.calculate_distance(task.location[0], task.location[1])
        max_distance = self.max_neighbor_distance * 3  # 最大距离
        distance_factor = 1.0 - min(distance / max_distance, 1.0)
        
        # 计算总分
        score = w1 * capability_match + w2 * load_factor + w3 * distance_factor
        return score
    
    def _get_task_required_capabilities(self, task: Task) -> List[str]:
        """获取任务所需能力"""
        if "采集" in task.content:
            return ["data_collection"]
        elif "分析" in task.content:
            return ["analysis"]
        elif "生成" in task.content:
            return ["generation"]
        elif "报告" in task.content:
            return ["report"]
        else:
            return []
    
    def broadcast_task(self, task: Task, hop_count: int):
        """广播任务"""
        # 模拟广播给邻居
        logger.info(f"智能体 {self.agent_id} 广播任务 {task.id}，剩余跳数: {hop_count}")
    
    def assign_task(self, task_id: str, agent_id: str):
        """分配任务"""
        if task_id in self.tasks:
            self.tasks[task_id].assigned_to = agent_id
            self.tasks[task_id].status = "assigned"
            logger.info(f"智能体 {self.agent_id} 将任务 {task_id} 分配给 {agent_id}")
    
    def start_task(self, task_id: str):
        """开始任务"""
        if task_id in self.tasks:
            self.tasks[task_id].status = "in_progress"
            self.tasks[task_id].start_time = time.time()
            self.status = "busy"
            self.load = 0.8  # 模拟负载
            logger.info(f"智能体 {self.agent_id} 开始执行任务 {task_id}")
    
    def complete_task(self, task_id: str):
        """完成任务"""
        if task_id in self.tasks:
            self.tasks[task_id].status = "completed"
            self.tasks[task_id].end_time = time.time()
            self.status = "idle"
            self.load = 0.0
            # 释放信息素
            self.release_pheromone(self.tasks[task_id].location, 100.0)
            logger.info(f"智能体 {self.agent_id} 完成任务 {task_id}")
    
    def release_pheromone(self, location: Tuple[float, float], concentration: float):
        """释放信息素"""
        pheromone_id = f"p{int(time.time() * 1000)}"
        self.pheromones[pheromone_id] = Pheromone(
            location=location,
            concentration=concentration,
            timestamp=time.time()
        )
        logger.info(f"智能体 {self.agent_id} 在位置 {location} 释放信息素，浓度: {concentration}")
    
    def move_towards_pheromone(self):
        """向信息素浓度高的方向移动"""
        if not self.pheromones:
            return
        
        # 找到浓度最高的信息素
        max_concentration = 0
        target_location = None
        
        for pheromone in self.pheromones.values():
            if pheromone.concentration > max_concentration:
                max_concentration = pheromone.concentration
                target_location = pheromone.location
        
        if target_location:
            # 向目标位置移动
            dx = target_location[0] - self.x
            dy = target_location[1] - self.y
            distance = (dx ** 2 + dy ** 2) ** 0.5
            
            if distance > 0:
                step = 0.5  # 移动步长
                self.x += (dx / distance) * step
                self.y += (dy / distance) * step
                logger.info(f"智能体 {self.agent_id} 向信息素位置移动: ({self.x:.2f}, {self.y:.2f})")
    
    def detect_failure(self, agent_id: str):
        """检测智能体故障"""
        logger.info(f"智能体 {self.agent_id} 检测到智能体 {agent_id} 故障")
        # 接管故障智能体的任务
        for task_id, task in self.tasks.items():
            if task.assigned_to == agent_id and task.status in ["assigned", "in_progress"]:
                logger.info(f"智能体 {self.agent_id} 接管任务 {task_id}")
                self.assign_task(task_id, self.agent_id)
                self.start_task(task_id)
    
    def join_network(self):
        """加入网络"""
        logger.info(f"智能体 {self.agent_id} 加入网络")
        # 广播加入消息
    
    def leave_network(self):
        """离开网络"""
        logger.info(f"智能体 {self.agent_id} 离开网络")
        # 广播离开消息


class SwarmSystem:
    """蜂群系统"""
    
    def __init__(self, num_agents: int = 10):
        self.agents = {}
        self.num_agents = num_agents
        self.initialize_agents()
    
    def initialize_agents(self):
        """初始化智能体"""
        for i in range(self.num_agents):
            agent_id = f"agent_{i}"
            x = random.uniform(0, 100)
            y = random.uniform(0, 100)
            agent = SwarmAgent(agent_id, x, y)
            
            # 随机分配能力
            capabilities = ["data_collection", "analysis", "generation", "report"]
            agent.capabilities = random.sample(capabilities, random.randint(1, 3))
            
            self.agents[agent_id] = agent
        
        # 建立通信网络
        self.build_communication_network()
    
    def build_communication_network(self):
        """构建通信网络"""
        max_distance = 10.0
        
        for agent_id, agent in self.agents.items():
            for other_id, other_agent in self.agents.items():
                if agent_id != other_id:
                    distance = agent.calculate_distance(other_agent.x, other_agent.y)
                    if distance <= max_distance:
                        agent.add_neighbor(other_id)
        
        logger.info("通信网络构建完成")
    
    def start_all_agents(self):
        """启动所有智能体"""
        for agent in self.agents.values():
            agent.start()
        logger.info("所有智能体已启动")
    
    def stop_all_agents(self):
        """停止所有智能体"""
        for agent in self.agents.values():
            agent.stop()
        logger.info("所有智能体已停止")
    
    def create_task(self, task_type: str, content: str, location: Tuple[float, float]) -> Task:
        """创建任务"""
        task_id = f"task_{int(time.time() * 1000)}"
        task = Task(
            id=task_id,
            type=task_type,
            content=content,
            location=location,
            priority=3,
            status="pending"
        )
        return task
    
    def broadcast_task(self, task: Task, start_agent_id: str, max_hops: int = 3):
        """广播任务"""
        if start_agent_id in self.agents:
            self.agents[start_agent_id].receive_task_broadcast(task, max_hops)
    
    def simulate_task_execution(self, task: Task):
        """模拟任务执行"""
        # 找到最合适的智能体
        best_agent = None
        best_score = 0
        
        for agent_id, agent in self.agents.items():
            score = agent._calculate_bid_score(task)
            if score > best_score:
                best_score = score
                best_agent = agent
        
        if best_agent:
            # 分配任务
            best_agent.assign_task(task.id, best_agent.agent_id)
            best_agent.start_task(task.id)
            
            # 模拟任务执行
            time.sleep(2)
            
            # 完成任务
            best_agent.complete_task(task.id)
            return True
        return False
    
    def simulate_agent_failure(self, agent_id: str):
        """模拟智能体故障"""
        if agent_id in self.agents:
            agent = self.agents[agent_id]
            logger.info(f"模拟智能体 {agent_id} 故障")
            
            # 通知邻居
            for neighbor_id in agent.neighbors:
                if neighbor_id in self.agents:
                    self.agents[neighbor_id].detect_failure(agent_id)
    
    def get_agent_state(self, agent_id: str) -> Optional[AgentState]:
        """获取智能体状态"""
        if agent_id in self.agents:
            agent = self.agents[agent_id]
            return AgentState(
                id=agent.agent_id,
                x=agent.x,
                y=agent.y,
                load=agent.load,
                capabilities=agent.capabilities,
                status=agent.status,
                neighbors=agent.neighbors
            )
        return None
    
    def get_all_agent_states(self) -> List[AgentState]:
        """获取所有智能体状态"""
        return [self.get_agent_state(agent_id) for agent_id in self.agents.keys() if self.get_agent_state(agent_id)]
