"""
替代智能体调度系统实现
使用不同的方法和依赖
"""

import os
import json
import asyncio
import time
import logging
import random
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass, field
from enum import Enum

# 替代依赖
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LinearRegression

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
            os.path.dirname(__file__), "..", "data", "alternative_task_agent_mapping.json"
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
                    "complexity_medium": ["zhongshu", "hu_bu", "gong_bu"],
                    "complexity_high": ["zhongshu", "hu_bu", "bing_bu", "gong_bu", "xing_bu", "li_bu"]
                }
                self._save_mappings(default_mappings)
                return default_mappings
        except Exception as e:
            logger.error(f"加载映射关系失败: {e}")
            return {
                "complexity_low": ["li_bu", "hu_bu"],
                "complexity_medium": ["zhongshu", "hu_bu", "gong_bu"],
                "complexity_high": ["zhongshu", "hu_bu", "bing_bu", "gong_bu", "xing_bu", "li_bu"]
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
        medium_agents = [AgentType.ZHONGSHU, AgentType.HUBU, AgentType.GONGBU]
        combinations.append(AgentCombination(
            agents=medium_agents,
            complexity_range=(0.3, 0.7),
            description="中等复杂度任务组合"
        ))
        
        # 高复杂度组合
        high_agents = [AgentType.ZHONGSHU, AgentType.HUBU, AgentType.BINGBU, AgentType.GONGBU, AgentType.XINGBU, AgentType.LIBU]
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
        if len(task_records) < 50:
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


class ComplexityEvaluator:
    """任务复杂度评估器（使用scikit-learn）"""
    
    def __init__(self):
        self.vectorizer = TfidfVectorizer(analyzer='char', ngram_range=(1, 2))
        self.model = LinearRegression()
        self.dataset_path = os.path.join(
            os.path.dirname(__file__), "..", "data", "complexity_dataset.json"
        )
        self.dataset = self._load_dataset()
        self._train_model()
    
    def _load_dataset(self) -> List[Dict[str, Any]]:
        """加载复杂度标注数据集"""
        try:
            if os.path.exists(self.dataset_path):
                with open(self.dataset_path, "r", encoding="utf-8") as f:
                    return json.load(f)
            else:
                # 创建默认数据集
                default_dataset = [
                    {"text": "深圳南山区房价多少", "complexity": 0.15},
                    {"text": "深圳福田区房价分析", "complexity": 0.25},
                    {"text": "广州天河区房价详细报告", "complexity": 0.37},
                    {"text": "北京朝阳区房价对比", "complexity": 0.25},
                    {"text": "上海浦东新区房价走势预测", "complexity": 0.45},
                    {"text": "杭州西湖区学区房推荐", "complexity": 0.30},
                    {"text": "成都锦江区投资价值分析", "complexity": 0.40},
                    {"text": "武汉武昌区二手房交易流程", "complexity": 0.50},
                    {"text": "西安雁塔区新房开盘信息", "complexity": 0.20},
                    {"text": "南京玄武区房产政策解读", "complexity": 0.35}
                ]
                self._save_dataset(default_dataset)
                return default_dataset
        except Exception as e:
            logger.error(f"加载数据集失败: {e}")
            return []
    
    def _save_dataset(self, dataset: List[Dict[str, Any]]):
        """保存数据集"""
        os.makedirs(os.path.dirname(self.dataset_path), exist_ok=True)
        with open(self.dataset_path, "w", encoding="utf-8") as f:
            json.dump(dataset, f, ensure_ascii=False, indent=2)
    
    def _train_model(self):
        """训练复杂度评估模型"""
        if not self.dataset:
            logger.warning("数据集为空，使用随机复杂度评估")
            return
        
        texts = [item["text"] for item in self.dataset]
        complexities = [item["complexity"] for item in self.dataset]
        
        try:
            X = self.vectorizer.fit_transform(texts)
            self.model.fit(X, complexities)
            logger.info("复杂度评估模型训练完成")
        except Exception as e:
            logger.error(f"训练模型失败: {e}")
    
    def evaluate(self, text: str) -> float:
        """评估任务复杂度"""
        try:
            if hasattr(self, 'model') and hasattr(self, 'vectorizer'):
                X = self.vectorizer.transform([text])
                complexity = float(self.model.predict(X)[0])
                # 归一化到0-1范围
                return max(0.0, min(1.0, complexity))
            else:
                # 基于规则的回退方法
                return self._rule_based_evaluation(text)
        except Exception as e:
            logger.error(f"评估复杂度失败: {e}")
            return self._rule_based_evaluation(text)
    
    def _rule_based_evaluation(self, text: str) -> float:
        """基于规则的复杂度评估"""
        # 基于查询长度和关键词
        query_length = len(text)
        keywords = ["房价", "估值", "分析", "报告", "对比", "详细", "全面", "预测", "推荐", "流程", "政策", "解读"]
        keyword_count = sum(1 for keyword in keywords if keyword in text)
        
        # 计算复杂度分数 (0.0-1.0)
        length_factor = min(query_length / 50, 1.0) * 0.3
        keyword_factor = min(keyword_count / len(keywords), 1.0) * 0.7
        complexity = length_factor + keyword_factor
        
        # 归一化到0.0-1.0范围
        complexity = max(0.0, min(1.0, complexity))
        
        return complexity
    
    def incremental_learning(self, text: str, complexity: float):
        """增量学习"""
        # 添加到数据集
        self.dataset.append({"text": text, "complexity": complexity})
        # 保存数据集
        self._save_dataset(self.dataset)
        # 重新训练模型
        self._train_model()
        logger.info(f"增量学习：添加样本 '{text}'，复杂度 {complexity}")


class AlternativeScheduler:
    """替代智能调度器"""
    
    def __init__(self):
        self.agents: Dict[str, Agent] = {}
        self.task_queue = []  # 简单的任务队列
        self.task_counter = 0
        self.task_records: List[Dict[str, Any]] = []
        self.mapping = TaskAgentMapping()
        self.hippocampus = Hippocampus()
        self.complexity_evaluator = ComplexityEvaluator()
        self.max_queue_length = 8  # 调整队列长度阈值
    
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
        complexity = self.complexity_evaluator.evaluate(query)
        
        # 获取智能体组合
        combination = self.mapping.get_agent_combination(complexity)
        
        # 创建任务
        task_id = f"alt_task_{self.task_counter}"
        self.task_counter += 1
        
        task = Task(
            id=task_id,
            query=query,
            priority=priority,
            complexity=complexity,
            agent_combination=combination.agents
        )
        
        # 添加到任务队列（按优先级排序）
        self.task_queue.append((-priority.value, time.time(), task))
        self.task_queue.sort(key=lambda x: (x[0], x[1]))  # 按优先级和时间排序
        
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
            if self.task_queue:
                # 获取优先级最高的任务
                _, _, task = self.task_queue.pop(0)
                
                # 分配任务
                await self._assign_task(task)
                
                # 检查是否需要优化映射
                if len(self.task_records) % 50 == 0 and len(self.task_records) > 0:
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
            # 模拟智能体执行时间
            execution_time = random.uniform(0.2, 0.8)
            await asyncio.sleep(execution_time)
            
            if agent_type == AgentType.HUBU:
                # 户部：采集房价数据
                return agent_type, {"average_price": 9.8, "unit": "万/㎡", "region": "南山区"}
            elif agent_type == AgentType.LIBU:
                # 礼部：生成回复
                return agent_type, {"response": "南山区二手房均价约9.8万/㎡"}
            elif agent_type == AgentType.ZHONGSHU:
                # 中书省：任务拆解
                return agent_type, {"decomposition": "任务拆解完成"}
            elif agent_type == AgentType.BINGBU:
                # 兵部：分析数据
                return agent_type, {"analysis": "市场稳定，略有上涨"}
            elif agent_type == AgentType.GONGBU:
                # 工部：生成报告
                return agent_type, {"report": "详细报告已生成"}
            elif agent_type == AgentType.XINGBU:
                # 刑部：安全检查
                return agent_type, {"security": "安全检查通过"}
            elif agent_type == AgentType.MENSHANG:
                # 门下省：审核
                return agent_type, {"review": "审核通过"}
            elif agent_type == AgentType.SHANGSHU:
                # 尚书省：执行协调
                return agent_type, {"coordination": "执行协调完成"}
            else:
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
        self.complexity_evaluator.incremental_learning(task.query, task.complexity)
    
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
alternative_scheduler: Optional[AlternativeScheduler] = None


def get_alternative_scheduler() -> AlternativeScheduler:
    """获取替代调度器实例"""
    global alternative_scheduler
    if alternative_scheduler is None:
        alternative_scheduler = AlternativeScheduler()
        # 注册默认智能体
        alternative_scheduler.register_agent("zhongshu_1", AgentType.ZHONGSHU, ["task_decomposition"])
        alternative_scheduler.register_agent("hubu_1", AgentType.HUBU, ["data_collection"])
        alternative_scheduler.register_agent("libu_1", AgentType.LIBU, ["dialogue"])
        alternative_scheduler.register_agent("bingbu_1", AgentType.BINGBU, ["analysis"])
        alternative_scheduler.register_agent("xingbu_1", AgentType.XINGBU, ["security"])
        alternative_scheduler.register_agent("gongbu_1", AgentType.GONGBU, ["report"])
        alternative_scheduler.register_agent("menshang_1", AgentType.MENSHANG, ["review"])
        alternative_scheduler.register_agent("shangshu_1", AgentType.SHANGSHU, ["coordination"])
        # 启动任务处理线程
        asyncio.create_task(alternative_scheduler.process_tasks())
    return alternative_scheduler


async def process_query_alternative(query: str, priority: TaskPriority = TaskPriority.MEDIUM) -> Dict[str, Any]:
    """处理查询（替代实现）"""
    scheduler = get_alternative_scheduler()
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
