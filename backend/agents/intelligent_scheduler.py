"""
智能体调度系统
实现任务复杂度评估、智能体组合匹配、负载检查和任务分配
"""

import asyncio
import time
import logging
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass, field
from enum import Enum

logger = logging.getLogger(__name__)


class TaskComplexity(Enum):
    """任务复杂度级别"""
    SIMPLE = 0.1
    MEDIUM = 0.5
    COMPLEX = 0.9


class AgentType(Enum):
    """智能体类型"""
    HUBU = "户部"
    LIBU = "礼部"
    BINGBU = "兵部"
    XINGBU = "刑部"
    LIBU_OFFICIAL = "吏部"
    GONGBU = "工部"


@dataclass
class Agent:
    """智能体"""
    id: str
    type: AgentType
    capabilities: List[str]
    load: float = 0.0  # 0.0-1.0
    status: str = "idle"
    completed_tasks: int = 0


@dataclass
class AgentCombination:
    """智能体组合"""
    agents: List[AgentType]
    complexity_range: Tuple[float, float]
    description: str


@dataclass
class TaskRecord:
    """任务记录"""
    query: str
    complexity: float
    agent_combination: List[AgentType]
    execution_time: float
    cost: float
    timestamp: float = field(default_factory=time.time)


class IntelligentScheduler:
    """智能调度器"""
    
    def __init__(self):
        self.agents: Dict[str, Agent] = {}
        self.agent_combinations: List[AgentCombination] = self._build_agent_combinations()
        self.task_records: List[TaskRecord] = []
        self.complexity_thresholds = {
            "simple": 0.3,
            "medium": 0.7
        }
    
    def _build_agent_combinations(self) -> List[AgentCombination]:
        """构建智能体组合映射库"""
        return [
            AgentCombination(
                agents=[AgentType.HUBU, AgentType.LIBU],
                complexity_range=(0.0, 0.3),
                description="数据采集与简单对话"
            ),
            AgentCombination(
                agents=[AgentType.HUBU, AgentType.LIBU, AgentType.BINGBU],
                complexity_range=(0.3, 0.7),
                description="数据采集、对话与分析"
            ),
            AgentCombination(
                agents=[AgentType.HUBU, AgentType.LIBU, AgentType.BINGBU, AgentType.GONGBU],
                complexity_range=(0.7, 1.0),
                description="数据采集、对话、分析与报告"
            )
        ]
    
    def register_agent(self, agent_id: str, agent_type: AgentType, capabilities: List[str]):
        """注册智能体"""
        agent = Agent(
            id=agent_id,
            type=agent_type,
            capabilities=capabilities
        )
        self.agents[agent_id] = agent
        logger.info(f"Registered agent: {agent_id} ({agent_type.value})")
    
    def calculate_complexity(self, query: str) -> float:
        """评估任务复杂度
        
        模拟BERT模型评估，实际项目中应使用真实的预训练模型
        """
        # 简单模拟复杂度计算
        # 基于查询长度和关键词
        query_length = len(query)
        keywords = ["房价", "估值", "分析", "报告", "对比", "详细", "全面"]
        keyword_count = sum(1 for keyword in keywords if keyword in query)
        
        # 计算复杂度分数 (0.0-1.0)
        length_factor = min(query_length / 50, 1.0) * 0.3
        keyword_factor = min(keyword_count / len(keywords), 1.0) * 0.7
        complexity = length_factor + keyword_factor
        
        # 归一化到0.0-1.0范围
        complexity = max(0.0, min(1.0, complexity))
        
        logger.info(f"Calculated complexity for query '{query}': {complexity:.2f}")
        return complexity
    
    def match_agent_combination(self, complexity: float) -> AgentCombination:
        """根据复杂度匹配智能体组合"""
        for combination in self.agent_combinations:
            min_complexity, max_complexity = combination.complexity_range
            if min_complexity <= complexity < max_complexity:
                logger.info(f"Matched agent combination: {[a.value for a in combination.agents]} for complexity {complexity:.2f}")
                return combination
        
        # 默认返回最简单的组合
        default_combination = self.agent_combinations[0]
        logger.info(f"Defaulting to agent combination: {[a.value for a in default_combination.agents]}")
        return default_combination
    
    def check_agent_load(self, agent_type: AgentType) -> float:
        """检查指定类型智能体的平均负载"""
        agents_of_type = [agent for agent in self.agents.values() if agent.type == agent_type]
        if not agents_of_type:
            return 0.5  # 默认负载
        
        avg_load = sum(agent.load for agent in agents_of_type) / len(agents_of_type)
        logger.info(f"Average load for {agent_type.value}: {avg_load:.2f}")
        return avg_load
    
    def assign_task(self, combination: AgentCombination) -> Dict[AgentType, str]:
        """分配任务给智能体"""
        assignment = {}
        
        for agent_type in combination.agents:
            # 选择该类型中负载最低的智能体
            agents_of_type = [agent for agent in self.agents.values() if agent.type == agent_type]
            if agents_of_type:
                # 按负载排序
                agents_of_type.sort(key=lambda a: a.load)
                selected_agent = agents_of_type[0]
                assignment[agent_type] = selected_agent.id
                
                # 更新负载
                selected_agent.load += 0.1  # 假设任务增加0.1负载
                selected_agent.status = "busy"
                
                logger.info(f"Assigned task to {selected_agent.id} ({agent_type.value}), new load: {selected_agent.load:.2f}")
        
        return assignment
    
    async def execute_task(self, query: str) -> Dict[str, Any]:
        """执行任务"""
        start_time = time.time()
        
        # 步骤S1: 评估复杂度
        complexity = self.calculate_complexity(query)
        
        # 步骤S2: 匹配智能体组合
        combination = self.match_agent_combination(complexity)
        
        # 步骤S3: 检查负载并分配任务
        for agent_type in combination.agents:
            load = self.check_agent_load(agent_type)
            logger.info(f"{agent_type.value} current load: {load:.2f}")
        
        assignment = self.assign_task(combination)
        
        # 步骤S4: 并行执行任务
        results = await self._execute_agent_tasks(assignment, query)
        
        # 聚合结果
        aggregated_result = self._aggregate_results(results, query)
        
        # 步骤S5: 记录任务信息
        execution_time = time.time() - start_time
        cost = execution_time * 0.0125  # 假设每0.8秒成本0.01元
        
        task_record = TaskRecord(
            query=query,
            complexity=complexity,
            agent_combination=combination.agents,
            execution_time=execution_time,
            cost=cost
        )
        self.task_records.append(task_record)
        
        # 重置智能体状态
        for agent_id in assignment.values():
            if agent_id in self.agents:
                agent = self.agents[agent_id]
                agent.load = max(0.0, agent.load - 0.1)
                agent.status = "idle"
                agent.completed_tasks += 1
        
        logger.info(f"Task executed in {execution_time:.2f}s, cost: ¥{cost:.3f}")
        
        return {
            "query": query,
            "complexity": complexity,
            "agent_combination": [a.value for a in combination.agents],
            "results": aggregated_result,
            "execution_time": execution_time,
            "cost": cost
        }
    
    async def _execute_agent_tasks(self, assignment: Dict[AgentType, str], query: str) -> Dict[AgentType, Any]:
        """并行执行智能体任务"""
        async def execute_agent(agent_type: AgentType, agent_id: str) -> Tuple[AgentType, Any]:
            if agent_type == AgentType.HUBU:
                # 户部：采集房价数据
                await asyncio.sleep(0.5)  # 模拟数据采集时间
                return agent_type, {"average_price": 9.8, "unit": "万/㎡", "region": "南山区"}
            elif agent_type == AgentType.LIBU:
                # 礼部：生成回复
                await asyncio.sleep(0.3)  # 模拟回复生成时间
                return agent_type, {"response": "南山区二手房均价约9.8万/㎡"}
            elif agent_type == AgentType.BINGBU:
                # 兵部：分析数据
                await asyncio.sleep(0.4)
                return agent_type, {"analysis": "市场稳定，略有上涨"}
            elif agent_type == AgentType.GONGBU:
                # 工部：生成报告
                await asyncio.sleep(0.6)
                return agent_type, {"report": "详细报告已生成"}
            else:
                await asyncio.sleep(0.2)
                return agent_type, {"result": "任务完成"}
        
        tasks = []
        for agent_type, agent_id in assignment.items():
            tasks.append(execute_agent(agent_type, agent_id))
        
        results = await asyncio.gather(*tasks)
        return dict(results)
    
    def _aggregate_results(self, results: Dict[AgentType, Any], query: str) -> str:
        """聚合智能体结果"""
        if AgentType.LIBU in results:
            return results[AgentType.LIBU].get("response", "任务完成")
        elif AgentType.HUBU in results:
            price = results[AgentType.HUBU].get("average_price")
            unit = results[AgentType.HUBU].get("unit")
            return f"南山区房价均价约{price}{unit}"
        else:
            return "任务完成"
    
    def get_task_records(self) -> List[TaskRecord]:
        """获取任务记录"""
        return self.task_records
    
    def optimize_agent_combinations(self):
        """优化智能体组合映射库"""
        # 基于历史任务记录优化映射库
        if len(self.task_records) < 10:
            return
        
        # 这里可以实现更复杂的优化逻辑
        # 例如：基于任务执行时间、成本和成功率调整复杂度范围
        logger.info("Optimizing agent combinations based on task records")


class HubuAgent:
    """户部智能体 - 数据采集"""
    
    def __init__(self):
        self.name = "户部"
        self.role = "数据采集"
    
    async def collect_data(self, query: str) -> Dict[str, Any]:
        """采集数据"""
        # 模拟数据采集
        await asyncio.sleep(0.5)
        
        # 基于查询返回相应数据
        if "房价" in query and "南山区" in query:
            return {
                "average_price": 9.8,
                "unit": "万/㎡",
                "region": "南山区",
                "data_source": "贝壳、房天下",
                "update_time": time.time()
            }
        else:
            return {
                "error": "无法识别的查询"
            }


class LibuAgent:
    """礼部智能体 - 对话生成"""
    
    def __init__(self):
        self.name = "礼部"
        self.role = "对话生成"
    
    async def generate_response(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """生成回复"""
        # 模拟回复生成
        await asyncio.sleep(0.3)
        
        if "average_price" in data:
            price = data["average_price"]
            unit = data.get("unit", "万/㎡")
            region = data.get("region", "该区域")
            return {
                "response": f"{region}二手房均价约{price}{unit}"
            }
        else:
            return {
                "response": "抱歉，无法获取相关信息"
            }


# 全局调度器实例
intelligent_scheduler: Optional[IntelligentScheduler] = None


def get_intelligent_scheduler() -> IntelligentScheduler:
    """获取智能调度器实例"""
    global intelligent_scheduler
    if intelligent_scheduler is None:
        intelligent_scheduler = IntelligentScheduler()
        # 注册默认智能体
        intelligent_scheduler.register_agent("hubu_1", AgentType.HUBU, ["data_collection"])
        intelligent_scheduler.register_agent("libu_1", AgentType.LIBU, ["dialogue"])
        intelligent_scheduler.register_agent("bingbu_1", AgentType.BINGBU, ["analysis"])
        intelligent_scheduler.register_agent("gongbu_1", AgentType.GONGBU, ["report"])
    return intelligent_scheduler


async def process_query(query: str) -> Dict[str, Any]:
    """处理查询"""
    scheduler = get_intelligent_scheduler()
    return await scheduler.execute_task(query)
