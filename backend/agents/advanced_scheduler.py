"""
高级智能体调度系统
实现任务复杂度评估、智能体组合匹配、负载检查和任务分配
"""

import os
import json
import asyncio
import time
import logging
import queue
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass, field
from enum import Enum

from backend.agents.complexity_evaluator import evaluate_complexity, incremental_learning
from backend.memory.hippocampus import Hippocampus

logger = logging.getLogger(__name__)


class TaskPriority(Enum):
    """任务优先级"""
    LOW = 0
    MEDIUM = 1
    HIGH = 2
    VIP = 3


class AgentType(Enum):
    """智能体类型"""
    ZHONGSHU = "zhongshu"
    HUBU = "hu_bu"
    LIBU = "li_bu"
    BINGBU = "bing_bu"
    XINGBU = "xing_bu"
    LIBU_OFFICIAL = "li_bu_official"
    GONGBU = "gong_bu"
    MENSHANG = "menshang"
    SHANGSHU = "shangshu"


@dataclass
class Agent:
    """智能体"""
    id: str
    type: AgentType
    capabilities: List[str]
    load: float = 0.0  # 0.0-1.0
    status: str = "idle"
    queue_length: int = 0
    completed_tasks: int = 0


@dataclass
class Task:
    """任务"""
    id: str
    query: str
    priority: TaskPriority
    complexity: float
    agent_combination: List[AgentType]
    status: str = "pending"
    result: Optional[Dict[str, Any]] = None
    execution_time: Optional[float] = None
    cost: Optional[float] = None
    created_at: float = field(default_factory=time.time)
    completed_at: Optional[float] = None


@dataclass
class AgentCombination:
    """智能体组合"""
    agents: List[AgentType]
    complexity_range: Tuple[float, float]
    description: str
    usage_count: int = 0
    success_rate: float = 1.0
    avg_execution_time: float = 0.0
    avg_cost: float = 0.0


class TaskAgentMapping:
    """任务-智能体映射库"""
    
    def __init__(self, mapping_file: str = None):
        self.mapping_file = mapping_file or os.path.join(
            os.path.dirname(__file__), "..", "data", "task_agent_mapping.json"
        )
        self.mappings = self._load_mappings()
        self.agent_combinations = self._build_agent_combinations()
    
    def _load_mappings(self) -> Dict[str, List[str]]:
        """加载映射关系"""
        try:
            if os.path.exists(self.mapping_file):
                with open(self.mapping_file, "r", encoding="utf-8") as f:
                    return json.load(f)
            else:
                # 创建默认映射
                default_mappings = {
                    "complexity_low": ["li_bu", "hu_bu"],
                    "complexity_medium": ["zhongshu", "hu_bu", "gong_bu", "menshang", "shangshu"],
                    "complexity_high": ["zhongshu", "hu_bu", "bing_bu", "gong_bu", "xing_bu", "li_bu", "menshang", "shangshu"]
                }
                self._save_mappings(default_mappings)
                return default_mappings
        except Exception as e:
            logger.error(f"加载映射关系失败: {e}")
            return {
                "complexity_low": ["li_bu", "hu_bu"],
                "complexity_medium": ["zhongshu", "hu_bu", "gong_bu", "menshang", "shangshu"],
                "complexity_high": ["zhongshu", "hu_bu", "bing_bu", "gong_bu", "xing_bu", "li_bu", "menshang", "shangshu"]
            }
    
    def _save_mappings(self, mappings: Dict[str, List[str]]):
        """保存映射关系"""
        os.makedirs(os.path.dirname(self.mapping_file), exist_ok=True)
        with open(self.mapping_file, "w", encoding="utf-8") as f:
            json.dump(mappings, f, ensure_ascii=False, indent=2)
    
    def _build_agent_combinations(self) -> List[AgentCombination]:
        """构建智能体组合"""
        combinations = []
        
        # 低复杂度组合
        low_agents = [AgentType.LIBU, AgentType.HUBU]
        combinations.append(AgentCombination(
            agents=low_agents,
            complexity_range=(0.0, 0.3),
            description="低复杂度任务组合"
        ))
        
        # 中等复杂度组合
        medium_agents = [AgentType.ZHONGSHU, AgentType.HUBU, AgentType.GONGBU, AgentType.MENSHANG, AgentType.SHANGSHU]
        combinations.append(AgentCombination(
            agents=medium_agents,
            complexity_range=(0.3, 0.7),
            description="中等复杂度任务组合"
        ))
        
        # 高复杂度组合
        high_agents = [AgentType.ZHONGSHU, AgentType.HUBU, AgentType.BINGBU, AgentType.GONGBU, AgentType.XINGBU, AgentType.LIBU, AgentType.MENSHANG, AgentType.SHANGSHU]
        combinations.append(AgentCombination(
            agents=high_agents,
            complexity_range=(0.7, 1.0),
            description="高复杂度任务组合"
        ))
        
        return combinations
    
    def get_agent_combination(self, complexity: float) -> AgentCombination:
        """根据复杂度获取智能体组合"""
        for combination in self.agent_combinations:
            min_complexity, max_complexity = combination.complexity_range
            if min_complexity <= complexity < max_complexity:
                return combination
        # 默认返回低复杂度组合
        return self.agent_combinations[0]
    
    def optimize_mappings(self, task_records: List[Dict[str, Any]]):
        """根据任务执行效果优化映射关系"""
        if len(task_records) < 100:
            return
        
        logger.info("开始优化任务-智能体映射关系")
        
        # 统计各组合的执行效果
        combination_stats = {}
        for record in task_records:
            combination_key = "-" .join(sorted(record["agent_combination"]))
            if combination_key not in combination_stats:
                combination_stats[combination_key] = {
                    "count": 0,
                    "total_time": 0,
                    "total_cost": 0,
                    "success_count": 0
                }
            
            stats = combination_stats[combination_key]
            stats["count"] += 1
            stats["total_time"] += record.get("execution_time", 0)
            stats["total_cost"] += record.get("cost", 0)
            if record.get("success", True):
                stats["success_count"] += 1
        
        # 计算各组合的性能指标
        for combination_key, stats in combination_stats.items():
            success_rate = stats["success_count"] / stats["count"]
            avg_time = stats["total_time"] / stats["count"]
            avg_cost = stats["total_cost"] / stats["count"]
            
            # 更新组合的性能指标
            for combination in self.agent_combinations:
                combo_key = "-" .join(sorted([agent.value for agent in combination.agents]))
                if combo_key == combination_key:
                    combination.success_rate = success_rate
                    combination.avg_execution_time = avg_time
                    combination.avg_cost = avg_cost
                    break
        
        # 根据性能指标排序组合
        self.agent_combinations.sort(key=lambda x: (x.success_rate, -x.avg_execution_time, -x.avg_cost), reverse=True)
        
        logger.info("任务-智能体映射关系优化完成")


class AdvancedScheduler:
    """高级智能调度器"""
    
    def __init__(self):
        self.agents: Dict[str, Agent] = {}
        self.task_queue = queue.PriorityQueue()
        self.task_counter = 0
        self.task_records: List[Dict[str, Any]] = []
        self.mapping = TaskAgentMapping()
        self.hippocampus = Hippocampus()
        self.max_queue_length = 10
    
    def register_agent(self, agent_id: str, agent_type: AgentType, capabilities: List[str]):
        """注册智能体"""
        agent = Agent(
            id=agent_id,
            type=agent_type,
            capabilities=capabilities
        )
        self.agents[agent_id] = agent
        logger.info(f"Registered agent: {agent_id} ({agent_type.value})")
    
    def create_task(self, query: str, priority: TaskPriority = TaskPriority.MEDIUM) -> Task:
        """创建任务"""
        # 评估复杂度
        complexity = evaluate_complexity(query)
        
        # 获取智能体组合
        combination = self.mapping.get_agent_combination(complexity)
        
        # 创建任务
        task_id = f"task_{self.task_counter}"
        self.task_counter += 1
        
        task = Task(
            id=task_id,
            query=query,
            priority=priority,
            complexity=complexity,
            agent_combination=combination.agents
        )
        
        # 添加到任务队列
        self.task_queue.put((-priority.value, time.time(), task))
        
        return task
    
    def check_agent_load(self, agent_type: AgentType) -> List[Agent]:
        """检查指定类型智能体的负载"""
        agents_of_type = [agent for agent in self.agents.values() if agent.type == agent_type]
        # 按负载和队列长度排序
        agents_of_type.sort(key=lambda a: (a.load, a.queue_length))
        return agents_of_type
    
    async def process_tasks(self):
        """处理任务队列"""
        while True:
            if not self.task_queue.empty():
                # 获取优先级最高的任务
                priority_value, _, task = self.task_queue.get()
                
                # 分配任务
                await self._assign_task(task)
                
                # 检查是否需要优化映射
                if len(self.task_records) % 100 == 0 and len(self.task_records) > 0:
                    self.mapping.optimize_mappings(self.task_records)
            
            await asyncio.sleep(0.1)
    
    async def _assign_task(self, task: Task):
        """分配任务给智能体"""
        task.status = "assigning"
        
        # 为每个智能体类型选择负载最低的实例
        assignment = {}
        for agent_type in task.agent_combination:
            agents_of_type = self.check_agent_load(agent_type)
            if agents_of_type:
                # 选择负载最低的智能体
                selected_agent = None
                for agent in agents_of_type:
                    if agent.queue_length < self.max_queue_length:
                        selected_agent = agent
                        break
                
                if selected_agent:
                    assignment[agent_type] = selected_agent
                    selected_agent.queue_length += 1
                    selected_agent.status = "busy"
                    logger.info(f"Assigned task {task.id} to {selected_agent.id} ({agent_type.value})")
                else:
                    logger.warning(f"No available agent for type {agent_type.value}")
                    task.status = "failed"
                    return
        
        # 并行执行任务
        task.status = "executing"
        start_time = time.time()
        
        results = await self._execute_agent_tasks(assignment, task)
        
        # 聚合结果
        task.result = self._aggregate_results(results, task)
        task.execution_time = time.time() - start_time
        task.cost = task.execution_time * 0.0125  # 假设每0.8秒成本0.01元
        task.status = "completed"
        task.completed_at = time.time()
        
        # 记录任务
        self._record_task(task, results)
        
        # 重置智能体状态
        for agent in assignment.values():
            agent.queue_length -= 1
            agent.load = max(0.0, agent.load - 0.1)
            agent.status = "idle" if agent.queue_length == 0 else "busy"
            agent.completed_tasks += 1
        
        logger.info(f"Task {task.id} completed in {task.execution_time:.2f}s, cost: ¥{task.cost:.3f}")
    
    async def _execute_agent_tasks(self, assignment: Dict[AgentType, Agent], task: Task) -> Dict[AgentType, Any]:
        """并行执行智能体任务"""
        async def execute_agent(agent_type: AgentType, agent: Agent) -> Tuple[AgentType, Any]:
            if agent_type == AgentType.HUBU:
                # 户部：采集房价数据
                await asyncio.sleep(0.5)
                return agent_type, {"average_price": 9.8, "unit": "万/㎡", "region": "南山区"}
            elif agent_type == AgentType.LIBU:
                # 礼部：生成回复
                await asyncio.sleep(0.3)
                return agent_type, {"response": "南山区二手房均价约9.8万/㎡"}
            elif agent_type == AgentType.ZHONGSHU:
                # 中书省：任务拆解
                await asyncio.sleep(0.2)
                return agent_type, {"decomposition": "任务拆解完成"}
            elif agent_type == AgentType.BINGBU:
                # 兵部：分析数据
                await asyncio.sleep(0.4)
                return agent_type, {"analysis": "市场稳定，略有上涨"}
            elif agent_type == AgentType.GONGBU:
                # 工部：生成报告
                await asyncio.sleep(0.6)
                return agent_type, {"report": "详细报告已生成"}
            elif agent_type == AgentType.XINGBU:
                # 刑部：安全检查
                await asyncio.sleep(0.1)
                return agent_type, {"security": "安全检查通过"}
            elif agent_type == AgentType.MENSHANG:
                # 门下省：审核
                await asyncio.sleep(0.2)
                return agent_type, {"review": "审核通过"}
            elif agent_type == AgentType.SHANGSHU:
                # 尚书省：执行协调
                await asyncio.sleep(0.3)
                return agent_type, {"coordination": "执行协调完成"}
            else:
                await asyncio.sleep(0.2)
                return agent_type, {"result": "任务完成"}
        
        tasks = []
        for agent_type, agent in assignment.items():
            tasks.append(execute_agent(agent_type, agent))
        
        results = await asyncio.gather(*tasks)
        return dict(results)
    
    def _aggregate_results(self, results: Dict[AgentType, Any], task: Task) -> Dict[str, Any]:
        """聚合智能体结果"""
        if AgentType.LIBU in results:
            return {"response": results[AgentType.LIBU].get("response", "任务完成")}
        elif AgentType.HUBU in results:
            price = results[AgentType.HUBU].get("average_price")
            unit = results[AgentType.HUBU].get("unit")
            region = results[AgentType.HUBU].get("region")
            return {"response": f"{region}房价均价约{price}{unit}"}
        else:
            return {"response": "任务完成"}
    
    def _record_task(self, task: Task, results: Dict[AgentType, Any]):
        """记录任务"""
        # 记录到内存
        task_record = {
            "task_id": task.id,
            "query": task.query,
            "complexity": task.complexity,
            "agent_combination": [agent.value for agent in task.agent_combination],
            "execution_time": task.execution_time,
            "cost": task.cost,
            "success": task.status == "completed",
            "timestamp": time.time()
        }
        self.task_records.append(task_record)
        
        # 存储到海马体记忆系统
        intermediate_data = {
            "complexity": task.complexity,
            "agent_combination": [agent.value for agent in task.agent_combination],
            "agent_results": results
        }
        
        self.hippocampus.create_memory(
            user_id="system",
            request={"query": task.query, "priority": task.priority.name},
            intermediate_data=intermediate_data,
            result=task.result
        )
        
        # 增量学习
        incremental_learning(task.query, task.complexity)
    
    def get_task_records(self) -> List[Dict[str, Any]]:
        """获取任务记录"""
        return self.task_records
    
    def get_agent_status(self) -> Dict[str, Any]:
        """获取智能体状态"""
        status = {}
        for agent_id, agent in self.agents.items():
            status[agent_id] = {
                "type": agent.type.value,
                "status": agent.status,
                "load": agent.load,
                "queue_length": agent.queue_length,
                "completed_tasks": agent.completed_tasks
            }
        return status


# 全局调度器实例
advanced_scheduler: Optional[AdvancedScheduler] = None


def get_advanced_scheduler() -> AdvancedScheduler:
    """获取高级调度器实例"""
    global advanced_scheduler
    if advanced_scheduler is None:
        advanced_scheduler = AdvancedScheduler()
        # 注册默认智能体
        advanced_scheduler.register_agent("zhongshu_1", AgentType.ZHONGSHU, ["task_decomposition"])
        advanced_scheduler.register_agent("hubu_1", AgentType.HUBU, ["data_collection"])
        advanced_scheduler.register_agent("libu_1", AgentType.LIBU, ["dialogue"])
        advanced_scheduler.register_agent("bingbu_1", AgentType.BINGBU, ["analysis"])
        advanced_scheduler.register_agent("xingbu_1", AgentType.XINGBU, ["security"])
        advanced_scheduler.register_agent("gongbu_1", AgentType.GONGBU, ["report"])
        advanced_scheduler.register_agent("menshang_1", AgentType.MENSHANG, ["review"])
        advanced_scheduler.register_agent("shangshu_1", AgentType.SHANGSHU, ["coordination"])
        # 启动任务处理线程
        asyncio.create_task(advanced_scheduler.process_tasks())
    return advanced_scheduler


async def process_query(query: str, priority: TaskPriority = TaskPriority.MEDIUM) -> Dict[str, Any]:
    """处理查询"""
    scheduler = get_advanced_scheduler()
    task = scheduler.create_task(query, priority)
    
    # 等待任务完成
    while task.status != "completed" and task.status != "failed":
        await asyncio.sleep(0.1)
    
    return {
        "task_id": task.id,
        "query": task.query,
        "complexity": task.complexity,
        "agent_combination": [agent.value for agent in task.agent_combination],
        "result": task.result,
        "execution_time": task.execution_time,
        "cost": task.cost,
        "status": task.status
    }
