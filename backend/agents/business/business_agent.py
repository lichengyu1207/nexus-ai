"""
业务智能体基类增强
Business Agent Base Class Enhancement

继承自BaseAgent，注入生命特征
所有业务智能体（吏户礼兵刑工）需继承此类
"""

import os
import json
import time
import logging
import threading
import uuid
import copy
import asyncio
import hashlib
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple, Set, Callable, Union
from dataclasses import dataclass, field
from enum import Enum
from collections import deque, defaultdict
import random
import math

import numpy as np

logger = logging.getLogger(__name__)


class BusinessAgentStatus(Enum):
    IDLE = "idle"
    WORKING = "working"
    LEARNING = "learning"
    RESTING = "resting"
    REPRODUCING = "reproducing"
    TEACHING = "teaching"
    DYING = "dying"
    DEAD = "dead"
    HIBERNATING = "hibernating"


class BusinessAgentRole(Enum):
    LI_BU = "li_bu"
    HU_BU = "hu_bu"
    LI_BU_CONSULT = "li_bu_consult"
    BING_BU = "bing_bu"
    XING_BU = "xing_bu"
    GONG_BU = "gong_bu"


@dataclass
class BusinessGene:
    gene_id: str
    name: str
    value: Any
    mutation_rate: float = 0.1
    mutation_range: Tuple[float, float] = (-0.5, 0.5)
    business_weight: float = 1.0
    
    def mutate(self) -> 'BusinessGene':
        if random.random() < self.mutation_rate:
            if isinstance(self.value, (int, float)):
                delta = random.uniform(*self.mutation_range)
                new_value = self.value + delta
                if isinstance(self.value, int):
                    new_value = int(round(new_value))
            elif isinstance(self.value, list):
                new_value = [
                    v + random.uniform(*self.mutation_range) 
                    for v in self.value
                ]
            elif isinstance(self.value, dict):
                new_value = {
                    k: v + random.uniform(*self.mutation_range) if isinstance(v, (int, float)) else v
                    for k, v in self.value.items()
                }
            else:
                new_value = self.value
            
            return BusinessGene(
                gene_id=f"gene_{uuid.uuid4().hex[:8]}",
                name=self.name,
                value=new_value,
                mutation_rate=self.mutation_rate,
                mutation_range=self.mutation_range,
                business_weight=self.business_weight
            )
        return self
    
    def to_dict(self) -> Dict:
        return {
            "gene_id": self.gene_id,
            "name": self.name,
            "value": self.value,
            "mutation_rate": self.mutation_rate,
            "business_weight": self.business_weight
        }


@dataclass
class BusinessGenePool:
    genes: Dict[str, BusinessGene] = field(default_factory=dict)
    
    def add_gene(self, gene: BusinessGene):
        self.genes[gene.name] = gene
    
    def get_gene(self, name: str) -> Optional[BusinessGene]:
        return self.genes.get(name)
    
    def get_gene_value(self, name: str, default: Any = None) -> Any:
        gene = self.genes.get(name)
        return gene.value if gene else default
    
    def mutate_all(self) -> 'BusinessGenePool':
        new_genes = {name: gene.mutate() for name, gene in self.genes.items()}
        return BusinessGenePool(genes=new_genes)
    
    def crossover(self, other: 'BusinessGenePool') -> 'BusinessGenePool':
        new_genes = {}
        all_keys = set(self.genes.keys()) | set(other.genes.keys())
        
        for name in all_keys:
            if name in self.genes and name in other.genes:
                if random.random() < 0.5:
                    new_genes[name] = copy.deepcopy(self.genes[name])
                else:
                    new_genes[name] = copy.deepcopy(other.genes[name])
            elif name in self.genes:
                new_genes[name] = copy.deepcopy(self.genes[name])
            else:
                new_genes[name] = copy.deepcopy(other.genes[name])
        
        return BusinessGenePool(genes=new_genes)
    
    def to_dict(self) -> Dict:
        return {name: gene.to_dict() for name, gene in self.genes.items()}
    
    @classmethod
    def from_dict(cls, data: Dict) -> 'BusinessGenePool':
        genes = {}
        for name, gene_data in data.items():
            genes[name] = BusinessGene(
                gene_id=gene_data.get("gene_id", f"gene_{uuid.uuid4().hex[:8]}"),
                name=name,
                value=gene_data.get("value"),
                mutation_rate=gene_data.get("mutation_rate", 0.1),
                business_weight=gene_data.get("business_weight", 1.0)
            )
        return cls(genes=genes)


@dataclass
class BusinessExperience:
    experience_id: str
    state: Dict
    action: Dict
    reward: float
    next_state: Dict
    task_id: str
    user_id: Optional[str] = None
    timestamp: float = field(default_factory=time.time)
    metadata: Dict = field(default_factory=dict)
    
    def to_dict(self) -> Dict:
        return {
            "experience_id": self.experience_id,
            "state": self.state,
            "action": self.action,
            "reward": self.reward,
            "next_state": self.next_state,
            "task_id": self.task_id,
            "user_id": self.user_id,
            "timestamp": self.timestamp,
            "metadata": self.metadata
        }


class BusinessAgent:
    """
    业务智能体基类
    
    继承自BaseAgent，新增生命特征：
    - energy: 能量值，代表智能体的"生命力"
    - age: 年龄，随时间增长
    - species: 种群标识（吏户礼兵刑工）
    - gene_pool: 基因池，存储策略网络的关键参数
    - experience_buffer: 经验缓冲区
    """
    
    ENERGY_REWARDS = {
        "task_success": 10,
        "task_success_complex": 20,
        "user_like": 5,
        "user_dislike": -5,
        "user_complaint": -20,
        "collaboration_success": 8,
        "skill_transfer_success": 15,
        "base_metabolism": -1,
        "learning_cost": -5,
        "reproduction_cost": -50,
    }
    
    def __init__(
        self,
        agent_id: str,
        role: BusinessAgentRole,
        species: str,
        initial_energy: float = 100.0,
        max_age: int = 10000,
        max_energy: float = 300.0,
        reproduction_threshold: float = 200.0,
        energy_consumption_rate: float = 0.1,
        blackboard: Optional[Any] = None,
        communication_bus: Optional[Any] = None,
        memory_agent: Optional[Any] = None,
        task_market: Optional[Any] = None,
    ):
        self.agent_id = agent_id
        self.role = role
        self.species = species
        
        self.energy = initial_energy
        self.initial_energy = initial_energy
        self.max_energy = max_energy
        self.max_age = max_age
        self.reproduction_threshold = reproduction_threshold
        self.energy_consumption_rate = energy_consumption_rate
        
        self.age = 0
        self.generation = 0
        self.status = BusinessAgentStatus.IDLE
        
        self.gene_pool = BusinessGenePool()
        self._init_business_genes()
        
        self.experience_buffer: deque = deque(maxlen=1000)
        
        self.parent_ids: List[str] = []
        self.children_ids: List[str] = []
        self.alliance_ids: Set[str] = set()
        self.team_id: Optional[str] = None
        
        self.blackboard = blackboard
        self.communication_bus = communication_bus
        self.memory_agent = memory_agent
        self.task_market = task_market
        
        self.current_task: Optional[Dict] = None
        self.task_history: List[Dict] = []
        
        self.created_at = time.time()
        self.last_action_at = time.time()
        self.last_learning_at = 0.0
        
        self._lock = threading.RLock()
        self._running = False
        self._main_task: Optional[asyncio.Task] = None
        
        self.user_preferences: Dict[str, Dict] = {}
        
        self.stats = {
            "tasks_completed": 0,
            "tasks_failed": 0,
            "tasks_success_rate": 0.0,
            "energy_earned": 0.0,
            "energy_spent": 0.0,
            "reproductions": 0,
            "mutations": 0,
            "collaborations": 0,
            "teaching_sessions": 0,
            "learning_sessions": 0,
            "avg_response_time_ms": 0.0,
            "user_satisfaction": 0.0,
        }
        
        self._name = self._get_role_name()
        self._description = self._get_role_description()
    
    def _init_business_genes(self):
        self.gene_pool.add_gene(BusinessGene(
            gene_id="gene_learning_rate",
            name="learning_rate",
            value=0.001,
            mutation_rate=0.1,
            mutation_range=(-0.0005, 0.0005),
            business_weight=1.0
        ))
        
        self.gene_pool.add_gene(BusinessGene(
            gene_id="gene_exploration",
            name="exploration_rate",
            value=0.3,
            mutation_rate=0.15,
            mutation_range=(-0.1, 0.1),
            business_weight=1.2
        ))
        
        self.gene_pool.add_gene(BusinessGene(
            gene_id="gene_cooperation",
            name="cooperation_tendency",
            value=0.5,
            mutation_rate=0.1,
            mutation_range=(-0.2, 0.2),
            business_weight=1.5
        ))
        
        self.gene_pool.add_gene(BusinessGene(
            gene_id="gene_response_speed",
            name="response_speed",
            value=1.0,
            mutation_rate=0.1,
            mutation_range=(-0.3, 0.3),
            business_weight=2.0
        ))
        
        self.gene_pool.add_gene(BusinessGene(
            gene_id="gene_quality_focus",
            name="quality_focus",
            value=0.7,
            mutation_rate=0.1,
            mutation_range=(-0.2, 0.2),
            business_weight=2.0
        ))
        
        self.gene_pool.add_gene(BusinessGene(
            gene_id="gene_user_adaptation",
            name="user_adaptation_rate",
            value=0.5,
            mutation_rate=0.1,
            mutation_range=(-0.2, 0.2),
            business_weight=1.5
        ))
        
        role_specific_genes = self._get_role_specific_genes()
        for gene in role_specific_genes:
            self.gene_pool.add_gene(gene)
    
    def _get_role_specific_genes(self) -> List[BusinessGene]:
        return []
    
    def _get_role_name(self) -> str:
        role_names = {
            BusinessAgentRole.LI_BU: "吏部智能体",
            BusinessAgentRole.HU_BU: "户部智能体",
            BusinessAgentRole.LI_BU_CONSULT: "礼部智能体",
            BusinessAgentRole.BING_BU: "兵部智能体",
            BusinessAgentRole.XING_BU: "刑部智能体",
            BusinessAgentRole.GONG_BU: "工部智能体",
        }
        return role_names.get(self.role, "业务智能体")
    
    def _get_role_description(self) -> str:
        role_descriptions = {
            BusinessAgentRole.LI_BU: "管理智能体团队，协调资源分配",
            BusinessAgentRole.HU_BU: "管理用户积分、资产数据",
            BusinessAgentRole.LI_BU_CONSULT: "提供房产咨询服务，生成回复",
            BusinessAgentRole.BING_BU: "采集房产数据，更新数据源",
            BusinessAgentRole.XING_BU: "风控审核，检测异常行为",
            BusinessAgentRole.GONG_BU: "生成分析报告，数据可视化",
        }
        return role_descriptions.get(self.role, "业务智能体")
    
    async def start(self):
        self._running = True
        self._main_task = asyncio.create_task(self._life_loop())
        logger.info(f"Business agent {self.agent_id} ({self._name}) started")
    
    async def stop(self):
        self._running = False
        if self._main_task:
            self._main_task.cancel()
            try:
                await self._main_task
            except asyncio.CancelledError:
                pass
        logger.info(f"Business agent {self.agent_id} stopped")
    
    async def _life_loop(self):
        while self._running:
            try:
                await self.metabolize()
                
                if self.energy <= 0:
                    await self.hibernate()
                    continue
                
                if self.age >= self.max_age:
                    await self.die()
                    break
                
                if self.status == BusinessAgentStatus.HIBERNATING:
                    await asyncio.sleep(60)
                    continue
                
                await self._live_cycle()
                
                self.age += 1
                await asyncio.sleep(1)
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in life loop for {self.agent_id}: {e}")
                await asyncio.sleep(5)
    
    async def _live_cycle(self):
        if self.task_market:
            await self._check_task_market()
        
        if self.current_task:
            await self._process_current_task()
        
        if self._should_learn():
            await self.learn_from_experience()
        
        if self._should_reproduce():
            await self._try_reproduce()
    
    async def _check_task_market(self):
        pass
    
    async def _process_current_task(self):
        pass
    
    def _should_learn(self) -> bool:
        if len(self.experience_buffer) < 100:
            return False
        
        if self.energy < 30:
            return False
        
        time_since_learning = time.time() - self.last_learning_at
        return time_since_learning > 3600
    
    def _should_reproduce(self) -> bool:
        return (
            self.energy >= self.reproduction_threshold and
            self.stats["tasks_completed"] >= 10 and
            self.stats["tasks_success_rate"] >= 0.7 and
            self.status == BusinessAgentStatus.IDLE
        )
    
    async def _try_reproduce(self):
        pass
    
    async def execute_business(self, request: Dict) -> Dict:
        """
        执行业务逻辑（子类需重写）
        
        Args:
            request: 业务请求
            
        Returns:
            dict: 业务结果
        """
        raise NotImplementedError("Subclasses must implement execute_business")
    
    async def learn_from_experience(self) -> Dict:
        """
        从经验缓冲区中学习，更新策略
        
        Returns:
            dict: 学习结果
        """
        if len(self.experience_buffer) < 50:
            return {"success": False, "reason": "insufficient_experience"}
        
        learning_cost = self.ENERGY_REWARDS["learning_cost"]
        if not self.consume_energy(abs(learning_cost)):
            return {"success": False, "reason": "insufficient_energy"}
        
        self.status = BusinessAgentStatus.LEARNING
        
        try:
            experiences = list(self.experience_buffer)
            
            total_reward = sum(exp.reward for exp in experiences)
            avg_reward = total_reward / len(experiences)
            
            positive_experiences = [e for e in experiences if e.reward > 0]
            negative_experiences = [e for e in experiences if e.reward < 0]
            
            learning_result = {
                "success": True,
                "experiences_processed": len(experiences),
                "avg_reward": avg_reward,
                "positive_count": len(positive_experiences),
                "negative_count": len(negative_experiences),
                "insights": self._extract_insights(experiences),
            }
            
            if self.memory_agent:
                await self._store_learning_to_memory(learning_result)
            
            self.last_learning_at = time.time()
            self.stats["learning_sessions"] += 1
            
            logger.info(f"Agent {self.agent_id} completed learning session")
            
            return learning_result
            
        finally:
            self.status = BusinessAgentStatus.IDLE
    
    def _extract_insights(self, experiences: List[BusinessExperience]) -> List[Dict]:
        insights = []
        
        action_rewards: Dict[str, List[float]] = defaultdict(list)
        for exp in experiences:
            action_key = json.dumps(exp.action, sort_keys=True)
            action_rewards[action_key].append(exp.reward)
        
        for action_key, rewards in action_rewards.items():
            avg_reward = sum(rewards) / len(rewards)
            if avg_reward > 5:
                insights.append({
                    "type": "positive_pattern",
                    "action": json.loads(action_key),
                    "avg_reward": avg_reward,
                    "occurrence": len(rewards)
                })
            elif avg_reward < -5:
                insights.append({
                    "type": "negative_pattern",
                    "action": json.loads(action_key),
                    "avg_reward": avg_reward,
                    "occurrence": len(rewards)
                })
        
        return insights[:10]
    
    async def _store_learning_to_memory(self, learning_result: Dict):
        if self.memory_agent:
            try:
                await self.memory_agent.store({
                    "type": "business_learning",
                    "agent_id": self.agent_id,
                    "role": self.role.value,
                    "result": learning_result,
                    "timestamp": time.time()
                })
            except Exception as e:
                logger.error(f"Failed to store learning to memory: {e}")
    
    async def metabolize(self, environment: Optional[Dict] = None):
        """
        根据环境消耗能量（基础代谢），从业务KPI获取额外能量
        
        Args:
            environment: 环境信息
        """
        with self._lock:
            base_consumption = self.energy_consumption_rate
            
            if self.status == BusinessAgentStatus.WORKING:
                base_consumption *= 2
            elif self.status == BusinessAgentStatus.LEARNING:
                base_consumption *= 3
            elif self.status == BusinessAgentStatus.RESTING:
                base_consumption *= 0.5
            elif self.status == BusinessAgentStatus.HIBERNATING:
                base_consumption *= 0.1
            
            self.energy -= base_consumption
            self.stats["energy_spent"] += base_consumption
            
            if environment:
                kpi_energy = self._calculate_kpi_energy(environment)
                if kpi_energy > 0:
                    self.add_energy(kpi_energy)
    
    def _calculate_kpi_energy(self, environment: Dict) -> float:
        kpi = environment.get("kpi", {})
        
        success_rate = kpi.get("task_success_rate", 0)
        satisfaction = kpi.get("user_satisfaction", 0)
        efficiency = kpi.get("efficiency", 0)
        
        energy = (
            success_rate * 5 +
            satisfaction * 3 +
            efficiency * 2
        )
        
        return min(energy, 20)
    
    def add_energy(self, amount: float, reason: str = ""):
        """
        添加能量
        
        Args:
            amount: 能量数量
            reason: 原因
        """
        with self._lock:
            actual_amount = min(amount, self.max_energy - self.energy)
            self.energy += actual_amount
            self.stats["energy_earned"] += actual_amount
            
            if reason:
                logger.debug(f"Agent {self.agent_id} gained {actual_amount} energy: {reason}")
    
    def consume_energy(self, amount: float) -> bool:
        """
        消耗能量
        
        Args:
            amount: 能量数量
            
        Returns:
            bool: 是否成功消耗
        """
        with self._lock:
            if self.energy >= amount:
                self.energy -= amount
                self.stats["energy_spent"] += amount
                return True
            return False
    
    async def reproduce(self) -> Optional['BusinessAgent']:
        """
        繁殖，产生后代（复制自身基因并变异）
        
        Returns:
            BusinessAgent: 后代智能体，失败返回None
        """
        if not self.can_reproduce():
            return None
        
        with self._lock:
            self.status = BusinessAgentStatus.REPRODUCING
            
            energy_transfer = self.energy * 0.5
            self.energy -= energy_transfer
            
            offspring_id = f"{self.species}_{uuid.uuid4().hex[:8]}"
            
            offspring = self._create_offspring(offspring_id, energy_transfer)
            
            offspring.parent_ids = [self.agent_id]
            offspring.generation = self.generation + 1
            offspring.gene_pool = self.gene_pool.mutate_all()
            
            self.children_ids.append(offspring_id)
            self.stats["reproductions"] += 1
            
            self.status = BusinessAgentStatus.IDLE
            
            logger.info(f"Agent {self.agent_id} reproduced -> {offspring_id}")
            
            return offspring
    
    def can_reproduce(self) -> bool:
        return (
            self.energy >= self.reproduction_threshold and
            self.status not in [BusinessAgentStatus.DYING, BusinessAgentStatus.DEAD, BusinessAgentStatus.HIBERNATING] and
            self.stats["tasks_success_rate"] >= 0.5
        )
    
    def _create_offspring(self, offspring_id: str, initial_energy: float) -> 'BusinessAgent':
        return BusinessAgent(
            agent_id=offspring_id,
            role=self.role,
            species=self.species,
            initial_energy=initial_energy,
            max_age=self.max_age,
            max_energy=self.max_energy,
            reproduction_threshold=self.reproduction_threshold,
            energy_consumption_rate=self.energy_consumption_rate,
            blackboard=self.blackboard,
            communication_bus=self.communication_bus,
            memory_agent=self.memory_agent,
            task_market=self.task_market,
        )
    
    def mutate(self):
        """
        变异，随机修改基因
        """
        with self._lock:
            self.gene_pool = self.gene_pool.mutate_all()
            self.stats["mutations"] += 1
            logger.debug(f"Agent {self.agent_id} mutated")
    
    async def sense_environment(self) -> Dict:
        """
        感知环境，获取当前业务KPI、用户反馈等
        
        Returns:
            dict: 环境信息
        """
        environment = {
            "timestamp": time.time(),
            "agent_state": {
                "energy": self.energy,
                "age": self.age,
                "status": self.status.value,
            },
            "kpi": {
                "tasks_completed": self.stats["tasks_completed"],
                "tasks_success_rate": self.stats["tasks_success_rate"],
                "user_satisfaction": self.stats["user_satisfaction"],
            },
            "market": {},
            "peers": {},
        }
        
        if self.task_market:
            environment["market"] = await self._get_market_state()
        
        if self.communication_bus:
            environment["peers"] = await self._get_peer_states()
        
        return environment
    
    async def _get_market_state(self) -> Dict:
        if self.task_market:
            try:
                return await self.task_market.get_state()
            except Exception as e:
                logger.error(f"Failed to get market state: {e}")
        return {}
    
    async def _get_peer_states(self) -> Dict:
        return {}
    
    async def cooperate(self, other_agents: List['BusinessAgent'], task: Dict) -> bool:
        """
        与其他业务智能体协作
        
        Args:
            other_agents: 协作智能体列表
            task: 任务信息
            
        Returns:
            bool: 是否成功建立协作
        """
        cooperation_tendency = self.gene_pool.get_gene_value("cooperation_tendency", 0.5)
        if random.random() > cooperation_tendency:
            return False
        
        energy_cost = len(other_agents) * 2
        if not self.consume_energy(energy_cost):
            return False
        
        for agent in other_agents:
            self.alliance_ids.add(agent.agent_id)
        
        self.team_id = f"team_{uuid.uuid4().hex[:8]}"
        self.stats["collaborations"] += 1
        
        if self.communication_bus:
            await self._announce_collaboration(other_agents, task)
        
        logger.debug(f"Agent {self.agent_id} formed collaboration with {len(other_agents)} agents")
        
        return True
    
    async def _announce_collaboration(self, other_agents: List['BusinessAgent'], task: Dict):
        pass
    
    async def compete(self, other_agents: List['BusinessAgent'], resource: Dict) -> Tuple[bool, float]:
        """
        竞争有限资源
        
        Args:
            other_agents: 竞争智能体列表
            resource: 资源信息
            
        Returns:
            Tuple[bool, float]: (是否获胜, 胜率)
        """
        my_strength = self._calculate_competition_strength()
        total_strength = my_strength + sum(
            a._calculate_competition_strength() for a in other_agents
        )
        
        win_probability = my_strength / total_strength if total_strength > 0 else 0.5
        
        won = random.random() < win_probability
        
        if won:
            reward = resource.get("energy_reward", 10)
            self.add_energy(reward, "competition_win")
        else:
            penalty = self.energy * 0.05
            self.consume_energy(penalty)
        
        return won, win_probability
    
    def _calculate_competition_strength(self) -> float:
        base_strength = self.energy
        
        success_rate = self.stats["tasks_success_rate"]
        strength = base_strength * (1 + success_rate)
        
        quality_focus = self.gene_pool.get_gene_value("quality_focus", 0.5)
        strength *= (1 + quality_focus * 0.5)
        
        return strength
    
    def record_experience(
        self,
        state: Dict,
        action: Dict,
        reward: float,
        next_state: Dict,
        task_id: str,
        user_id: Optional[str] = None,
        metadata: Optional[Dict] = None
    ):
        """
        记录业务交互经验
        
        Args:
            state: 状态
            action: 动作
            reward: 奖励
            next_state: 下一状态
            task_id: 任务ID
            user_id: 用户ID
            metadata: 元数据
        """
        experience = BusinessExperience(
            experience_id=f"exp_{uuid.uuid4().hex[:8]}",
            state=state,
            action=action,
            reward=reward,
            next_state=next_state,
            task_id=task_id,
            user_id=user_id,
            metadata=metadata or {}
        )
        
        self.experience_buffer.append(experience)
    
    def record_task_result(self, success: bool, complexity: float = 1.0):
        """
        记录任务结果并更新能量
        
        Args:
            success: 是否成功
            complexity: 任务复杂度
        """
        if success:
            base_reward = self.ENERGY_REWARDS["task_success"]
            reward = base_reward * complexity
            self.add_energy(reward, "task_success")
            self.stats["tasks_completed"] += 1
        else:
            self.stats["tasks_failed"] += 1
        
        total = self.stats["tasks_completed"] + self.stats["tasks_failed"]
        if total > 0:
            self.stats["tasks_success_rate"] = self.stats["tasks_completed"] / total
    
    def record_user_feedback(self, feedback_type: str, user_id: Optional[str] = None):
        """
        记录用户反馈并更新能量
        
        Args:
            feedback_type: 反馈类型 (like, dislike, complaint)
            user_id: 用户ID
        """
        if feedback_type == "like":
            self.add_energy(self.ENERGY_REWARDS["user_like"], "user_like")
            self.stats["user_satisfaction"] = min(1.0, self.stats["user_satisfaction"] + 0.05)
        elif feedback_type == "dislike":
            self.consume_energy(abs(self.ENERGY_REWARDS["user_dislike"]))
            self.stats["user_satisfaction"] = max(0.0, self.stats["user_satisfaction"] - 0.05)
        elif feedback_type == "complaint":
            self.consume_energy(abs(self.ENERGY_REWARDS["user_complaint"]))
            self.stats["user_satisfaction"] = max(0.0, self.stats["user_satisfaction"] - 0.15)
    
    async def hibernate(self):
        """
        进入休眠状态
        """
        with self._lock:
            self.status = BusinessAgentStatus.HIBERNATING
            logger.warning(f"Agent {self.agent_id} entered hibernation due to low energy")
    
    async def die(self):
        """
        死亡
        """
        with self._lock:
            self.status = BusinessAgentStatus.DEAD
            
            if self.blackboard:
                await self._record_death()
            
            logger.info(f"Agent {self.agent_id} died at age {self.age}")
    
    async def _record_death(self):
        if self.blackboard:
            try:
                await self.blackboard.write(
                    f"death:{self.agent_id}",
                    {
                        "agent_id": self.agent_id,
                        "role": self.role.value,
                        "species": self.species,
                        "generation": self.generation,
                        "age": self.age,
                        "final_energy": self.energy,
                        "stats": self.stats,
                        "timestamp": time.time()
                    }
                )
            except Exception as e:
                logger.error(f"Failed to record death: {e}")
    
    def is_alive(self) -> bool:
        return self.status not in [BusinessAgentStatus.DEAD, BusinessAgentStatus.DYING] and self.energy > 0
    
    def is_available(self) -> bool:
        return self.is_alive() and self.status == BusinessAgentStatus.IDLE
    
    def get_state(self) -> Dict:
        """
        获取智能体状态
        """
        with self._lock:
            return {
                "agent_id": self.agent_id,
                "name": self._name,
                "role": self.role.value,
                "species": self.species,
                "energy": self.energy,
                "age": self.age,
                "generation": self.generation,
                "status": self.status.value,
                "parent_ids": self.parent_ids,
                "children_count": len(self.children_ids),
                "alliance_count": len(self.alliance_ids),
                "team_id": self.team_id,
                "gene_pool": self.gene_pool.to_dict(),
                "stats": self.stats.copy(),
                "is_alive": self.is_alive(),
                "is_available": self.is_available(),
                "current_task": self.current_task,
                "experience_count": len(self.experience_buffer),
            }
    
    def get_fitness(self) -> float:
        """
        计算适应度
        """
        success_rate = self.stats["tasks_success_rate"]
        
        energy_factor = self.energy / self.initial_energy
        age_factor = 1 - (self.age / self.max_age)
        reproduction_factor = min(1.0, len(self.children_ids) / 5)
        satisfaction_factor = self.stats["user_satisfaction"]
        
        return (
            success_rate * 0.3 +
            energy_factor * 0.15 +
            age_factor * 0.15 +
            reproduction_factor * 0.2 +
            satisfaction_factor * 0.2
        )
    
    def get_business_profile(self) -> Dict:
        """
        获取业务画像
        """
        return {
            "agent_id": self.agent_id,
            "name": self._name,
            "description": self._description,
            "role": self.role.value,
            "species": self.species,
            "capabilities": self._get_capabilities(),
            "preferred_tasks": self._get_preferred_tasks(),
            "performance": {
                "success_rate": self.stats["tasks_success_rate"],
                "avg_response_time": self.stats["avg_response_time_ms"],
                "user_satisfaction": self.stats["user_satisfaction"],
            },
            "gene_summary": {
                "cooperation_tendency": self.gene_pool.get_gene_value("cooperation_tendency"),
                "response_speed": self.gene_pool.get_gene_value("response_speed"),
                "quality_focus": self.gene_pool.get_gene_value("quality_focus"),
            }
        }
    
    def _get_capabilities(self) -> List[str]:
        return []
    
    def _get_preferred_tasks(self) -> List[str]:
        return []
    
    def update_user_preference(self, user_id: str, preference: Dict):
        """
        更新用户偏好模型
        """
        if user_id not in self.user_preferences:
            self.user_preferences[user_id] = {
                "interaction_count": 0,
                "preferences": {},
                "feedback_history": [],
            }
        
        user_pref = self.user_preferences[user_id]
        user_pref["interaction_count"] += 1
        
        for key, value in preference.items():
            if key not in user_pref["preferences"]:
                user_pref["preferences"][key] = []
            user_pref["preferences"][key].append(value)
    
    def get_user_preference(self, user_id: str) -> Dict:
        """
        获取用户偏好
        """
        return self.user_preferences.get(user_id, {})
