"""
道法自然 - 智能体动态组队与自组织协作系统
房都督平台发展纲领第一章：顺势而为的智能体进化

核心思想（道家）：
- 道法自然：智能体应像水一样，随任务难度而变，随容器形状而调
- 动态组队（MaAS）：简单问题1-2个智能体，复杂问题才调动全员
- 自组织协作（Agent Swarm）：六部自行协商竞标，无需中书省集中调度
- 健康监控：实时感知每个智能体的负载与状态

包含模块：
1.1 TaskComplexityAnalyzer - 任务复杂度评估器
1.2 MaASDynamicTeamScheduler - MaAS动态组队调度器
1.3 AgentSwarmCollaborator - Agent Swarm自组织协作机制
1.4 AgentHealthMonitor - 智能体健康监控与负载均衡
"""
import asyncio
import json
import logging
import time
import math
import re
import uuid
import threading
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Dict, Any, Optional, List, Callable, Awaitable, Set, Tuple
from collections import deque
from concurrent.futures import ThreadPoolExecutor

logger = logging.getLogger(__name__)


# ==================== 1.1 任务复杂度评估器 ====================


class ComplexityLevel(str, Enum):
    """任务复杂度等级"""
    TRIVIAL = "trivial"
    SIMPLE = "simple"
    MODERATE = "moderate"
    COMPLEX = "complex"
    CRITICAL = "critical"


@dataclass
class ComplexityAnalysisResult:
    """复杂度分析结果"""
    score: float
    level: ComplexityLevel
    features: Dict[str, float]
    reasoning: List[str]
    estimated_agent_count: int
    estimated_duration_seconds: float
    suggested_cooperation_mode: str
    confidence: float


class TaskComplexityAnalyzer:
    """
    任务复杂度评估器（提示词 1.1）
    
    基于多维度特征实时判断用户请求的复杂程度：
    - 文本长度、关键词密度、数值参数量
    - 历史对话上下文深度
    - 语义结构复杂度
    
    输出0~1分数 + 等级分类，为动态组队提供决策依据。
    """

    COMPLEXITY_KEYWORDS = {
        "critical": [
            "紧急", "危机", "风险", "违规", "安全漏洞", "攻击",
            "深度推理", "数学证明", "多步推导", "综合方案设计",
        ],
        "complex": [
            "综合分析", "多维度", "跨部门", "复杂计算", "模型训练",
            "批量处理", "策略制定", "对比报告", "代码生成", "方案设计",
            "详细评估", "全面分析", "系统性", "架构设计",
        ],
        "moderate": [
            "分析", "评估", "查询", "报告", "对比", "推荐",
            "建议", "预测", "判断", "解释", "说明", "比较",
        ],
        "simple": [
            "价格", "面积", "位置", "基本信息", "快速查询",
            "是什么", "多少", "列表", "简单", "简短",
        ],
    }

    DOMAIN_KEYWORDS = {
        "real_estate": ["房产", "房价", "楼盘", "户型", "地段", "租金", "买卖"],
        "fortune_telling": ["命盘", "八字", "运势", "风水", "紫微", "星座"],
        "emotion": ["感情", "心情", "压力", "烦恼", "开心", "难过"],
        "decision": ["选择", "决定", "建议", "方案", "策略", "规划"],
    }

    STRUCTURAL_PATTERNS = {
        "multi_question": re.compile(r'[？?。！!]', re.MULTILINE),
        "has_numbers": re.compile(r'\d+\.?\d*'),
        "has_json_like": re.compile(r'[\{\}\[\]]'),
        "conditional": re.compile(r'(如果|假如|若|当.*时|是否)'),
        "comparative": re.compile(r'(比较|对比|哪个|更好|更优|vs|或者)'),
        "causal": re.compile(r'(因为|所以|由于|导致|原因|为什么|如何)'),
    }

    def __init__(self):
        self._analysis_history: deque = deque(maxlen=500)
        self._domain_stats: Dict[str, int] = {}

    def analyze(self, request_text: str, context: Dict[str, Any] = None) -> ComplexityAnalysisResult:
        """
        分析任务复杂度
        
        Args:
            request_text: 用户请求文本
            context: 可选上下文（历史对话、用户画像等）
            
        Returns:
            ComplexityAnalysisResult 完整分析结果
        """
        start_time = time.time()
        context = context or {}
        features = self._extract_features(request_text, context)
        score = self._compute_score(features)
        level = self._classify_level(score)
        reasoning = self._generate_reasoning(features, level)

        agent_count = self._estimate_agent_count(level)
        duration = self._estimate_duration(score, len(request_text))
        mode = self._suggest_mode(level, score)

        result = ComplexityAnalysisResult(
            score=round(score, 4),
            level=level,
            features=features,
            reasoning=reasoning,
            estimated_agent_count=agent_count,
            estimated_duration_seconds=round(duration, 1),
            suggested_cooperation_mode=mode,
            confidence=self._compute_confidence(features),
        )

        self._analysis_history.append({
            "timestamp": time.time(),
            "request_length": len(request_text),
            "score": score,
            "level": level.value,
            "latency_ms": (time.time() - start_time) * 1000,
        })

        logger.info(f"复杂度分析完成: score={score:.3f}, level={level.value}, agents={agent_count}, mode={mode}")
        return result

    def _extract_features(self, text: str, context: Dict) -> Dict[str, float]:
        """提取多维特征"""
        text_len = len(text)
        features = {
            "text_length_norm": min(1.0, text_len / 2000),
            "keyword_density": 0.0,
            "structural_complexity": 0.0,
            "numerical_density": 0.0,
            "domain_breadth": 0.0,
            "context_depth": 0.0,
            "uncertainty_score": 0.0,
            "urgency_score": 0.0,
        }

        keyword_matches = {level: [] for level in self.COMPLEXITY_KEYWORDS}
        for level, keywords in self.COMPLEXITY_KEYWORDS.items():
            for kw in keywords:
                if kw in text:
                    keyword_matches[level].append(kw)

        total_keywords = sum(len(v) for v in keyword_matches.values())
        if total_keywords > 0:
            weights = {"critical": 0.35, "complex": 0.25, "moderate": 0.15, "simple": 0.05}
            weighted_sum = sum(len(keyword_matches[l]) * weights.get(l, 0.1) for l in keyword_matches)
            features["keyword_density"] = min(1.0, weighted_sum / max(total_keywords * 0.5, 1))

        structural_score = 0.0
        questions = len(self.STRUCTURAL_PATTERNS["multi_question"].findall(text))
        structural_score += min(0.25, questions * 0.05)
        if self.STRUCTURAL_PATTERNS["has_json_like"].search(text):
            structural_score += 0.15
        if self.STRUCTURAL_PATTERNS["conditional"].search(text):
            structural_score += 0.15
        if self.STRUCTURAL_PATTERNS["comparative"].search(text):
            structural_score += 0.12
        if self.STRUCTURAL_PATTERNS["causal"].search(text):
            structural_score += 0.13
        features["structural_complexity"] = min(1.0, structural_score)

        numbers = self.STRUCTURAL_PATTERNS["has_numbers"].findall(text)
        features["numerical_density"] = min(1.0, len(numbers) / 10)

        matched_domains = set()
        for domain, keywords in self.DOMAIN_KEYWORDS.items():
            if any(kw in text for kw in keywords):
                matched_domains.add(domain)
        features["domain_breadth"] = len(matched_domains) / max(len(self.DOMAIN_KEYWORDS), 1)

        history_len = context.get("history_length", 0)
        turn_count = context.get("turn_count", 0)
        features["context_depth"] = min(1.0, (history_len / 5000 + turn_count / 20) / 2)

        uncertainty_words = ["可能", "也许", "大概", "不确定", "不清楚", "不知道"]
        features["uncertainty_score"] = min(1.0, sum(1 for w in uncertainty_words if w in text) / 3)

        urgency_words = ["紧急", "马上", "尽快", "立即", "现在", "急"]
        features["urgency_score"] = min(1.0, sum(1 for w in urgency_words if w in text) / 2)

        return features

    def _compute_score(self, features: Dict[str, float]) -> float:
        """加权计算综合复杂度分数"""
        weights = {
            "text_length_norm": 0.10,
            "keyword_density": 0.30,
            "structural_complexity": 0.20,
            "numerical_density": 0.08,
            "domain_breadth": 0.12,
            "context_depth": 0.10,
            "uncertainty_score": 0.03,
            "urgency_score": 0.07,
        }
        score = sum(features.get(k, 0) * w for k, w in weights.items())
        return min(1.0, max(0.0, score))

    def _classify_level(self, score: float) -> ComplexityLevel:
        """根据分数分级"""
        if score >= 0.80:
            return ComplexityLevel.CRITICAL
        elif score >= 0.55:
            return ComplexityLevel.COMPLEX
        elif score >= 0.30:
            return ComplexityLevel.MODERATE
        elif score >= 0.12:
            return ComplexityLevel.SIMPLE
        else:
            return ComplexityLevel.TRIVIAL

    def _estimate_agent_count(self, level: ComplexityLevel) -> int:
        """估计所需智能体数量"""
        mapping = {
            ComplexityLevel.TRIVIAL: 1,
            ComplexityLevel.SIMPLE: 1,
            ComplexityLevel.MODERATE: 2,
            ComplexityLevel.COMPLEX: 4,
            ComplexityLevel.CRITICAL: 6,
        }
        return mapping.get(level, 2)

    def _estimate_duration(self, score: float, text_len: int) -> float:
        """估算执行时长（秒）"""
        base = 2.0
        length_factor = text_len / 200
        complexity_factor = score * 8
        return base + length_factor + complexity_factor

    def _suggest_mode(self, level: ComplexityLevel, score: float) -> str:
        """建议协作模式"""
        if level in [ComplexityLevel.TRIVIAL, ComplexityLevel.SIMPLE]:
            return "direct"
        elif level == ComplexityLevel.MODERATE:
            return "lightweight_pipeline"
        elif level == ComplexityLevel.COMPLEX:
            return "full_pipeline"
        else:
            return "emergency_full"

    def _compute_confidence(self, features: Dict[str, float]) -> float:
        """计算分析置信度"""
        signal_strength = sum(1 for v in features.values() if v > 0.1)
        total_signals = len(features)
        return signal_strength / max(total_signals, 1)

    def _generate_reasoning(self, features: Dict, level: ComplexityLevel) -> List[str]:
        """生成可解释的分析理由"""
        reasons = []
        if features["text_length_norm"] > 0.5:
            reasons.append(f"文本较长({features['text_length_norm']:.0%}饱和)")
        if features["keyword_density"] > 0.3:
            reasons.append(f"含高复杂度关键词(密度{features['keyword_density']:.2f})")
        if features["structural_complexity"] > 0.4:
            reasons.append(f"语义结构复杂(条件/因果/比较等)")
        if features["domain_breadth"] > 0.3:
            reasons.append(f"跨{int(features['domain_breadth']*len(self.DOMAIN_KEYWORDS))}个领域")
        if features["urgency_score"] > 0.3:
            reasons.append("检测到紧急性信号")
        if not reasons:
            reasons.append("基础特征分析")
        return reasons

    def get_stats(self) -> Dict[str, Any]:
        """获取分析统计"""
        if not self._analysis_history:
            return {"total_analyses": 0}
        scores = [h["score"] for h in self._analysis_history]
        level_counts = {}
        for h in self._analysis_history:
            lv = h["level"]
            level_counts[lv] = level_counts.get(lv, 0) + 1
        return {
            "total_analyses": len(self._analysis_history),
            "avg_score": round(sum(scores) / len(scores), 3),
            "level_distribution": level_counts,
            "avg_latency_ms": round(sum(h["latency_ms"] for h in self._analysis_history) / len(scores), 1),
        }


# ==================== 1.2 MaAS动态组队调度器 ====================


@dataclass
class AgentCapability:
    """智能体能力标签"""
    agent_name: str
    department: str
    tags: Set[str]
    efficiency: float = 1.0
    current_load: float = 0.0
    is_available: bool = True


@dataclass
class TeamComposition:
    """团队组成方案"""
    team_id: str
    agents: List[AgentCapability]
    total_efficiency: float
    estimated_cost: int
    cooperation_strategy: str
    rationale: str


class MaASDynamicTeamScheduler:
    """
    MaAS动态组队调度器（提示词 1.2）
    
    基于MaAS（Multi-Agent-as-a-Service）思想：
    - 根据任务复杂度和领域自动组建最小可用团队
    - 简单任务：1-2个智能体直路处理
    - 复杂任务：动态组合最优智能体集合
    - 支持规则+反馈混合优化
    """

    AGENT_CAPABILITIES = {
        "zhongshu": AgentCapability(
            agent_name="中书省_诸葛亮", department="中书省",
            tags={"规划", "拆解", "策略", "全局视野", "协调"},
            efficiency=0.95,
        ),
        "menxia": AgentCapability(
            agent_name="门下省_魏征", department="门下省",
            tags={"审核", "风控", "合规", "质疑", "质量把关"},
            efficiency=0.90,
        ),
        "gongbu": AgentCapability(
            agent_name="工部_鲁班", department="工部",
            tags={"估值", "分析", "报告", "房产数据", "工程"},
            efficiency=0.92,
        ),
        "bingbu": AgentCapability(
            agent_name="兵部_韩信", department="兵部",
            tags={"数据采集", "爬虫", "情报", "搜索", "API调用"},
            efficiency=0.88,
        ),
        "libu": AgentCapability(
            agent_name="礼部_苏轼", department="礼部",
            tags={"咨询", "客服", "沟通", "文案", "人格化交互"},
            efficiency=0.93,
        ),
        "hubu": AgentCapability(
            agent_name="户部_桑弘羊", department="户部",
            tags={"积分", "财务", "账单", "经济分析", "成本核算"},
            efficiency=0.85,
        ),
        "xingbu": AgentCapability(
            agent_name="刑部_包拯", department="刑部",
            tags={"安全", "风控", "合规", "审计", "违规检测"},
            efficiency=0.87,
        ),
        "libu_li": AgentCapability(
            agent_name="吏部_萧何", department="吏部",
            tags={"智能体管理", "招募", "考核", "人才市场", "晋升"},
            efficiency=0.86,
        ),
        "shangshu": AgentCapability(
            agent_name="尚书省_房玄龄", department="尚书省",
            tags={"执行协调", "资源分配", "进度管控", "部门调度"},
            efficiency=0.94,
        ),
    }

    TEAM_TEMPLATES = {
        "trivial": ["libu"],
        "simple": ["gongbu", "libu"],
        "moderate": ["gongbu", "bingbu", "libu"],
        "complex": ["zhongshu", "menxia", "gongbu", "bingbu", "libu"],
        "critical": ["zhongshu", "menxia", "shangshu", "gongbu", "bingbu", "hubu", "xingbu", "libu_li"],
    }

    def __init__(self, analyzer: TaskComplexityAnalyzer = None):
        self.analyzer = analyzer or TaskComplexityAnalyzer()
        self._agent_states: Dict[str, AgentCapability] = {
            k: AgentCapability(v.agent_name, v.department, set(v.tags), v.efficiency)
            for k, v in self.AGENT_CAPABILITIES.items()
        }
        self._team_history: List[TeamComposition] = []
        self._feedback_buffer: List[Dict] = []

    def form_team(self, request_text: str, context: Dict[str, Any] = None) -> TeamComposition:
        """
        根据请求动态组建团队
        
        Args:
            request_text: 用户请求
            context: 上下文信息
            
        Returns:
            团队组成方案
        """
        analysis = self.analyzer.analyze(request_text, context)
        level = analysis.level.value

        template_agents = self.TEAM_TEMPLATES.get(level, self.TEAM_TEMPLATES["moderate"])
        selected_agents = []

        for agent_key in template_agents:
            agent = self._agent_states.get(agent_key)
            if agent and agent.is_available and agent.current_load < 0.85:
                selected_agents.append(agent)
            else:
                alternatives = self._find_alternative(agent_key)
                if alternatives:
                    selected_agents.append(alternatives[0])

        if len(selected_agents) < analysis.estimated_agent_count and level == "critical":
            for key, agent in self._agent_states.items():
                if agent.is_available and agent not in selected_agents:
                    selected_agents.append(agent)
                    if len(selected_agents) >= analysis.estimated_agent_count:
                        break

        total_eff = sum(a.efficiency for a in selected_agents) / max(len(selected_agents), 1)
        est_cost = sum(int(a.efficiency * 50) for a in selected_agents)

        strategy_map = {
            "trivial": "direct_single",
            "simple": "sequential_pair",
            "moderate": "parallel_with_coordination",
            "complex": "full_pipeline_parallel",
            "critical": "emergency_all_hands",
        }

        team = TeamComposition(
            team_id=f"team_{uuid.uuid4().hex[:8]}",
            agents=selected_agents,
            total_efficiency=round(total_eff, 3),
            estimated_cost=est_cost,
            cooperation_strategy=strategy_map.get(level, "default"),
            rationale=f"复杂度={analysis.score:.2f}(级={level}), 选{len(selected_agents)}智能体, 模式={strategy_map.get(level,'?')}",
        )

        self._team_history.append(team)
        logger.info(f"MaAS组队完成: {team.team_id}, 智能体={[a.agent_name for a in team.agents]}, 策略={team.cooperation_strategy}")
        return team

    def _find_alternative(self, unavailable_key: str) -> List[AgentCapability]:
        """寻找替代智能体"""
        unavailable = self.AGENT_CAPABILITIES.get(unavailable_key)
        if not unavailable:
            return []
        target_tags = unavailable.tags
        candidates = []
        for key, agent in self._agent_states.items():
            if key != unavailable_key and agent.is_available:
                overlap = len(target_tags & agent.tags)
                if overlap > 0:
                    candidates.append((agent, overlap))
        candidates.sort(key=lambda x: x[1], reverse=True)
        return [c[0] for c in candidates[:3]]

    def update_agent_load(self, agent_name: str, load_delta: float):
        """更新智能体负载"""
        for agent in self._agent_states.values():
            if agent.agent_name == agent_name:
                agent.current_load = max(0.0, min(1.0, agent.current_load + load_delta))
                break

    def set_agent_availability(self, agent_name: str, available: bool):
        """设置智能体可用状态"""
        for agent in self._agent_states.values():
            if agent.agent_name == agent_name:
                agent.is_available = available
                break

    def record_feedback(self, team_id: str, success: bool, actual_cost: int, duration_sec: float):
        """记录组队反馈（用于后续优化）"""
        self._feedback_buffer.append({
            "team_id": team_id,
            "success": success,
            "actual_cost": actual_cost,
            "duration_sec": duration_sec,
            "timestamp": time.time(),
        })
        if len(self._feedback_buffer) > 200:
            self._feedback_buffer = self._feedback_buffer[-200:]

    def get_team_stats(self) -> Dict[str, Any]:
        """获取组队统计"""
        recent_teams = self._team_history[-20:] if self._team_history else []
        avg_size = sum(len(t.agents) for t in recent_teams) / max(len(recent_teams), 1)
        success_rate = 0.0
        if self._feedback_buffer:
            success_rate = sum(1 for f in self._feedback_buffer if f["success"]) / len(self._feedback_buffer)
        return {
            "total_teams_formed": len(self._team_history),
            "avg_team_size": round(avg_size, 1),
            "feedback_success_rate": round(success_rate, 3),
            "agent_statuses": {
                name: {"load": round(a.current_load, 2), "available": a.is_available}
                for name, a in list(self._agent_states.items())[:6]
            },
        }


# ==================== 1.3 Agent Swarm自组织协作 ====================


@dataclass
class SwarmTask:
    """蜂群任务"""
    task_id: str
    title: str
    description: str
    required_tags: Set[str]
    priority: int
    reward_points: int
    publisher: str
    status: str = "open"
    assigned_to: Optional[str] = None
    bids: List[Dict] = field(default_factory=list)
    created_at: float = field(default_factory=time.time)
    deadline: Optional[float] = None


@dataclass
class SwarmBid:
    """竞标报价"""
    bid_id: str
    task_id: str
    bidder: str
    bid_score: float
    estimated_duration: float
    confidence: float
    current_load: float
    capability_match: float
    timestamp: float = field(default_factory=time.time)


@dataclass
class HeartbeatMessage:
    """心跳消息"""
    agent_name: str
    status: str
    load: float
    capabilities: Set[str]
    active_tasks: int
    timestamp: float = field(default_factory=time.time)


class AgentSwarmCollaborator:
    """
    Agent Swarm自组织协作机制（提示词 1.3）
    
    核心特性：
    - 任务公告板：基于内存的任务发布/订阅机制
    - 自主竞标：智能体根据自身能力和负载计算投标分
    - 心跳检测：定期广播健康状态，故障自动接管
    - 邻居感知：智能体间互相感知健康状态
    """

    BID_WEIGHTS = {
        "capability_match": 0.40,
        "load_factor": 0.25,
        "confidence": 0.15,
        "speed_bonus": 0.10,
        "reliability": 0.10,
    }

    HEARTBEAT_INTERVAL_SEC = 10
    FAILURE_THRESHOLD = 3
    TASK_TAKEOVER_TIMEOUT_SEC = 30

    def __init__(self):
        self._task_board: Dict[str, SwarmTask] = {}
        self._bids: Dict[str, List[SwarmBid]] = {}
        self._heartbeats: Dict[str, deque] = {}
        self._agent_capabilities: Dict[str, Set[str]] = {}
        self._neighbor_graph: Dict[str, Set[str]] = {}
        self._takeover_log: List[Dict] = []
        self._lock = threading.Lock()
        self._running = False
        self._monitor_thread: Optional[threading.Thread] = None

    def register_agent(self, agent_name: str, capabilities: Set[str]):
        """注册智能体及其能力"""
        with self._lock:
            self._agent_capabilities[agent_name] = capabilities
            self._heartbeats[agent_name] = deque(maxlen=self.FAILURE_THRESHOLD + 5)
            self._neighbor_graph[agent_name] = set()
            logger.info(f"AgentSwarm注册智能体: {agent_name}, 能力={capabilities}")

    def publish_task(
        self,
        title: str,
        description: str,
        required_tags: Set[str],
        publisher: str,
        priority: int = 5,
        reward_points: int = 10,
        deadline_sec: Optional[float] = None,
    ) -> SwarmTask:
        """
        发布任务到公告板
        
        Args:
            title: 任务标题
            description: 任务描述
            required_tags: 所需能力标签
            publisher: 发布者名称
            priority: 优先级(1-10)
            reward_points: 奖励积分
            deadline_sec: 截止时间（秒后）
            
        Returns:
            发布的任务对象
        """
        task = SwarmTask(
            task_id=f"swarm_{uuid.uuid4().hex[:8]}",
            title=title,
            description=description,
            required_tags=required_tags,
            priority=priority,
            reward_points=reward_points,
            publisher=publisher,
            deadline=time.time() + deadline_sec if deadline_sec else None,
        )
        with self._lock:
            self._task_board[task.task_id] = task
            self._bids[task.task_id] = []
        logger.info(f"AgentSwarm任务发布: {task.task_id} [{title}], 所需标签={required_tags}, 发布者={publisher}")
        return task

    def submit_bid(self, task_id: str, bidder: str, estimated_duration: float = 5.0, confidence: float = 0.9) -> Optional[SwarmBid]:
        """
        智能体提交竞标
        
        自动计算投标分（基于能力匹配、负载、置信度等）
        """
        with self._lock:
            task = self._task_board.get(task_id)
            if not task or task.status != "open":
                return None

            caps = self._agent_capabilities.get(bidder, set())
            match = len(task.required_tags & caps) / max(len(task.required_tags), 1)

            heartbeat_q = self._heartbeats.get(bidder, deque())
            latest_hb = heartbeat_q[-1] if heartbeat_q else None
            current_load = latest_hb.load if latest_hb else 0.5
            reliability = min(1.0, len(heartbeat_q) / (self.FAILURE_THRESHOLD + 1))

            load_score = 1.0 - current_load
            speed_score = max(0.2, 1.0 / max(estimated_duration, 1))

            bid_score = (
                match * self.BID_WEIGHTS["capability_match"] +
                load_score * self.BID_WEIGHTS["load_factor"] +
                confidence * self.BID_WEIGHTS["confidence"] +
                speed_score * self.BID_WEIGHTS["speed_bonus"] +
                reliability * self.BID_WEIGHTS["reliability"]
            )

            bid = SwarmBid(
                bid_id=f"bid_{uuid.uuid4().hex[:6]}",
                task_id=task_id,
                bidder=bidder,
                bid_score=round(bid_score, 4),
                estimated_duration=estimated_duration,
                confidence=confidence,
                current_load=current_load,
                capability_match=round(match, 3),
            )

            self._bids[task_id].append(bid)
            task.bids.append({
                "bidder": bidder,
                "score": bid.bid_score,
                "match": bid.capability_match,
            })

            logger.debug(f"AgentSwarm竞标: {bidder} -> {task_id}, 分数={bid_score:.3f}, 匹配={match:.2f}")
            return bid

    def award_task(self, task_id: str, strategy: str = "best_score") -> Optional[SwarmTask]:
        """
        授予任务给最优竞标者
        
        strategy: best_score(最高分) | lowest_load(最低负载) | fastest(最快)
        """
        with self._lock:
            task = self._task_board.get(task_id)
            if not task or task.status != "open":
                return None

            bids = self._bids.get(task_id, [])
            if not bids:
                return None

            if strategy == "best_score":
                winner = max(bids, key=lambda b: b.bid_score)
            elif strategy == "lowest_load":
                winner = min(bids, key=lambda b: b.current_load)
            elif strategy == "fastest":
                winner = min(bids, key=lambda b: b.estimated_duration)
            else:
                winner = max(bids, key=lambda b: b.bid_score)

            task.status = "assigned"
            task.assigned_to = winner.bidder
            logger.info(f"AgentSwarm任务授予: {task_id} -> {winner.bidder} (分数={winner.bid_score:.3f})")
            return task

    def send_heartbeat(self, agent_name: str, status: str = "active", load: float = 0.0):
        """发送心跳"""
        with self._lock:
            hb = HeartbeatMessage(
                agent_name=agent_name,
                status=status,
                load=load,
                capabilities=self._agent_capabilities.get(agent_name, set()),
                active_tasks=sum(1 for t in self._task_board.values() if t.assigned_to == agent_name),
            )
            self._heartbeats.setdefault(agent_name, deque(maxlen=self.FAILURE_THRESHOLD + 5)).append(hb)
            self._update_neighbors(agent_name)

    def _update_neighbors(self, agent_name: str):
        """更新邻居关系（最近活跃的智能体互为邻居）"""
        recent_agents = set()
        for name, hbs in self._heartbeats.items():
            if hbs and (time.time() - hbs[-1].timestamp) < 60:
                recent_agents.add(name)
        self._neighbor_graph[agent_name] = recent_agents - {agent_name}

    def check_and_takeover_failed_tasks(self) -> List[Dict]:
        """
        检查并接管失败任务
        
        当被分配任务的智能体连续多次未发送心跳时，
        自动将任务重新开放或分配给邻居
        """
        takeovers = []
        now = time.time()

        with self._lock:
            for task_id, task in list(self._task_board.items()):
                if task.status != "assigned" or not task.assigned_to:
                    continue

                assignee_hbs = self._heartbeats.get(task.assigned_to, deque())
                if not assignee_hbs:
                    continue

                last_hb_time = assignee_hbs[-1].timestamp if assignee_hbs else 0
                time_since_hb = now - last_hb_time

                if time_since_hb > self.TASK_TAKEOVER_TIMEOUT_SEC:
                    neighbors = self._neighbor_graph.get(task.assigned_to, set())
                    available_neighbor = None
                    for neighbor in neighbors:
                        n_hbs = self._heartbeats.get(neighbor, deque())
                        if n_hbs and (now - n_hbs[-1].timestamp) < 30:
                            n_caps = self._agent_capabilities.get(neighbor, set())
                            if task.required_tags & n_caps:
                                available_neighbor = neighbor
                                break

                    old_assignee = task.assigned_to
                    if available_neighbor:
                        task.assigned_to = available_neighbor
                        takeover_type = "neighbor_takeover"
                    else:
                        task.status = "open"
                        task.assigned_to = None
                        takeover_type = "reopened"

                    takeover_record = {
                        "task_id": task_id,
                        "old_assignee": old_assignee,
                        "new_assignee": getattr(task, 'assigned_to', None),
                        "type": takeover_type,
                        "timestamp": now,
                    }
                    takeovers.append(takeover_record)
                    self._takeover_log.append(takeover_record)
                    logger.warning(f"AgentSwarm任务接管: {task_id}, 原={old_assignee}, 类型={takeover_type}")

        return takeovers

    def start_monitoring(self):
        """启动后台监控线程"""
        if self._running:
            return
        self._running = True
        self._monitor_thread = threading.Thread(target=self._monitor_loop, daemon=True)
        self._monitor_thread.start()
        logger.info("AgentSwarm监控已启动")

    def stop_monitoring(self):
        """停止后台监控"""
        self._running = False
        if self._monitor_thread:
            self._monitor_thread.join(timeout=5)
        logger.info("AgentSwarm监控已停止")

    def _monitor_loop(self):
        """监控循环"""
        while self._running:
            try:
                takeovers = self.check_and_takeover_failed_tasks()
                if takeovers:
                    logger.info(f"AgentSwarm本轮接管: {len(takeovers)}个任务")
            except Exception as e:
                logger.error(f"AgentSwarm监控异常: {e}")
            time.sleep(self.HEARTBEAT_INTERVAL_SEC)

    def get_swarm_status(self) -> Dict[str, Any]:
        """获取蜂群整体状态"""
        with self._lock:
            open_tasks = sum(1 for t in self._task_board.values() if t.status == "open")
            assigned_tasks = sum(1 for t in self._task_board.values() if t.status == "assigned")
            completed_tasks = sum(1 for t in self._task_board.values() if t.status == "completed")
            healthy_agents = sum(
                1 for name, hbs in self._heartbeat_buffers() if hbs and (time.time() - hbs[-1].timestamp) < 30
            ) if hasattr(self, '_heartbeat_buffers') else 0

            healthy_agents = sum(
                1 for name, hbs in self._heartbeats.items()
                if hbs and (time.time() - hbs[-1].timestamp) < 30
            )

            return {
                "total_tasks": len(self._task_board),
                "open_tasks": open_tasks,
                "assigned_tasks": assigned_tasks,
                "completed_tasks": completed_tasks,
                "registered_agents": len(self._agent_capabilities),
                "healthy_agents": healthy_agents,
                "total_takeovers": len(self._takeover_log),
                "recent_takeovers": self._takeover_log[-5:],
            }


# ==================== 1.4 智能体健康监控 ====================


@dataclass
class AgentHealthMetrics:
    """智能体健康指标"""
    agent_name: str
    timestamp: float
    cpu_usage: float = 0.0
    memory_usage: float = 0.0
    queue_length: int = 0
    load_percentage: float = 0.0
    requests_per_minute: float = 0.0
    avg_response_time_ms: float = 0.0
    error_rate: float = 0.0
    status: str = "healthy"
    consecutive_failures: int = 0


@dataclass
class LoadBalancingDecision:
    """负载均衡决策"""
    agent_name: str
    weight: float
    reason: str
    effective_at: float = field(default_factory=time.time)


class AgentHealthMonitor:
    """
    智能体健康监控与负载均衡（提示词 1.4）
    
    功能：
    - 每个智能体暴露/metrics接口
    - 定期拉取指标，更新权重
    - 负载>80%时降权，连续3次心跳失败标记不可用
    - 提供Prometheus格式指标输出
    """

    HEALTH_THRESHOLDS = {
        "healthy_max_load": 0.70,
        "warning_max_load": 0.85,
        "critical_max_load": 0.95,
        "max_consecutive_failures": 3,
        "weight_reduction_factor": 0.5,
        "recovery_boost_factor": 1.2,
    }

    def __init__(self, poll_interval_sec: float = 5.0):
        self.poll_interval = poll_interval_sec
        self._metrics_history: Dict[str, deque] = {}
        self._weights: Dict[str, float] = {}
        self._availability: Dict[str, bool] = {}
        self._failure_counts: Dict[str, int] = {}
        self._alerts: List[Dict] = []
        self._callbacks: Dict[str, List[Callable]] = {
            "on_degradation": [],
            "on_recovery": [],
            "on_failure": [],
        }
        self._running = False
        self._poll_thread: Optional[threading.Thread] = None

    def register_agent(self, agent_name: str, initial_weight: float = 1.0):
        """注册需要监控的智能体"""
        self._metrics_history[agent_name] = deque(maxlen=60)
        self._weights[agent_name] = initial_weight
        self._availability[agent_name] = True
        self._failure_counts[agent_name] = 0

    def report_metrics(self, metrics: AgentHealthMetrics):
        """上报智能体指标（由智能体或探针调用）"""
        name = metrics.agent_name
        if name not in self._metrics_history:
            self.register_agent(name)

        self._metrics_history[name].append(metrics)
        self._update_health_status(name, metrics)
        self._adjust_weight(name, metrics)

    def _update_health_status(self, name: str, m: AgentHealthMetrics):
        """更新健康状态"""
        prev_avail = self._availability.get(name, True)

        if m.error_rate > 0.1 or m.consecutive_failures >= self.HEALTH_THRESHOLDS["max_consecutive_failures"]:
            self._failure_counts[name] = self._failure_counts.get(name, 0) + 1
            if self._failure_counts[name] >= self.HEALTH_THRESHOLDS["max_consecutive_failures"]:
                self._availability[name] = False
                m.status = "unhealthy"
                if prev_avail:
                    self._fire_alert("on_failure", name, f"连续{self._failure_counts[name]}次失败，标记不可用")
        elif m.load_percentage <= self.HEALTH_THRESHOLDS["healthy_max_load"]:
            self._failure_counts[name] = 0
            if not self._availability[name]:
                self._availability[name] = True
                self._fire_alert("on_recovery", name, "已恢复可用")
            m.status = "healthy"
        elif m.load_percentage <= self.HEALTH_THRESHOLDS["warning_max_load"]:
            m.status = "warning"
            if prev_avail and m.status != "healthy":
                self._fire_alert("on_degradation", name, f"负载升高至{m.load_percentage:.0%}")
        else:
            m.status = "critical"
            self._fire_alert("on_degradation", name, f"负载过高: {m.load_percentage:.0%}")

    def _adjust_weight(self, name: str, m: AgentHealthMetrics):
        """调整负载均衡权重"""
        current_weight = self._weights.get(name, 1.0)

        if m.load_percentage > self.HEALTH_THRESHOLDS["warning_max_load"]:
            new_weight = current_weight * self.HEALTH_THRESHOLDS["weight_reduction_factor"]
        elif m.status == "unhealthy":
            new_weight = 0.0
        elif m.load_percentage < self.HEALTH_THRESHOLDS["healthy_max_load"] * 0.5:
            new_weight = min(2.0, current_weight * self.HEALTH_THRESHOLDS["recovery_boost_factor"])
        else:
            new_weight = current_weight

        self._weights[name] = max(0.0, min(2.0, new_weight))

    def _fire_alert(self, alert_type: str, agent_name: str, message: str):
        """触发告警回调"""
        alert = {
            "type": alert_type,
            "agent": agent_name,
            "message": message,
            "timestamp": time.time(),
        }
        self._alerts.append(alert)
        for cb in self._callbacks.get(alert_type, []):
            try:
                cb(alert)
            except Exception as e:
                logger.error(f"告警回调错误: {e}")

    def on_alert(self, alert_type: str, callback: Callable):
        """注册告警回调"""
        self._callbacks.setdefault(alert_type, []).append(callback)

    def get_optimal_agent(self, candidates: List[str], required_capability: str = None) -> Optional[str]:
        """
        获取当前最优智能体（考虑权重和可用性）
        
        用于调度器在多个候选中选择执行者
        """
        available = [
            name for name in candidates
            if self._availability.get(name, True) and self._weights.get(name, 0) > 0
        ]
        if not available:
            return None

        weighted = [(name, self._weights.get(name, 1.0)) for name in available]
        weighted.sort(key=lambda x: x[1], reverse=True)
        return weighted[0][0]

    def get_prometheus_metrics(self) -> str:
        """输出Prometheus格式指标"""
        lines = []
        for name, weight in self._weights.items():
            lines.append(f'fangdudu_agent_weight{{agent="{name}"}} {weight}')
            avail = 1.0 if self._availability.get(name, True) else 0.0
            lines.append(f'fangdudu_agent_up{{agent="{name}"}} {avail}')

        latest_metrics: Dict[str, AgentHealthMetrics] = {}
        for name, history in self._metrics_history.items():
            if history:
                latest_metrics[name] = history[-1]

        for name, m in latest_metrics.items():
            lines.append(f'fangdudu_agent_load{{agent="{name}"}} {m.load_percentage}')
            lines.append(f'fangdudu_agent_queue{{agent="{name}"}} {m.queue_length}')
            lines.append(f'fangdudu_agent_rpm{{agent="{name}"}} {m.requests_per_minute}')
            lines.append(f'fangdudu_agent_error_rate{{agent="{name}"}} {m.error_rate}')
            lines.append(f'fangdudu_agent_resp_time_ms{{agent="{name}"}} {m.avg_response_time_ms}')

        return "\n".join(lines)

    def get_health_report(self) -> Dict[str, Any]:
        """获取完整健康报告"""
        agents_info = {}
        for name in self._metrics_history:
            history = self._metrics_history[name]
            latest = history[-1] if history else None
            agents_info[name] = {
                "status": latest.status if latest else "unknown",
                "weight": round(self._weights.get(name, 0), 3),
                "available": self._availability.get(name, False),
                "load": round(latest.load_percentage, 2) if latest else None,
                "queue": latest.queue_length if latest else 0,
                "rpm": round(latest.requests_per_minute, 1) if latest else 0,
                "error_rate": round(latest.error_rate, 3) if latest else 0,
                "consecutive_failures": self._failure_counts.get(name, 0),
            }

        return {
            "monitored_agents": len(self._metrics_history),
            "healthy_count": sum(1 for v in self._availability.values() if v),
            "agents": agents_info,
            "recent_alerts": self._alerts[-10:],
            "generated_at": datetime.utcnow().isoformat(),
        }

    def start_polling(self):
        """启动定时轮询"""
        if self._running:
            return
        self._running = True
        self._poll_thread = threading.Thread(target=self._poll_loop, daemon=True)
        self._poll_thread.start()
        logger.info(f"健康监控轮询启动, 间隔={self.poll_interval}s")

    def stop_polling(self):
        """停止轮询"""
        self._running = False
        if self._poll_thread:
            self._poll_thread.join(timeout=5)

    def _poll_loop(self):
        """轮询循环（模拟拉取各智能体/metrics端点）"""
        while self._running:
            for name in list(self._metrics_history.keys()):
                if not self._availability.get(name, True):
                    simulated = AgentHealthMetrics(
                        agent_name=name,
                        timestamp=time.time(),
                        status="unhealthy",
                        load_percentage=0.0,
                        error_rate=1.0,
                        consecutive_failures=self._failure_counts.get(name, 0),
                    )
                else:
                    import random
                    simulated = AgentHealthMetrics(
                        agent_name=name,
                        timestamp=time.time(),
                        cpu_usage=random.uniform(0.1, 0.7),
                        memory_usage=random.uniform(0.2, 0.65),
                        queue_length=random.randint(0, 8),
                        load_percentage=random.uniform(0.1, 0.75),
                        requests_per_minute=random.uniform(2, 25),
                        avg_response_time_ms=random.uniform(50, 800),
                        error_rate=random.choice([0.0, 0.0, 0.0, 0.01, 0.02]),
                        status="healthy",
                    )
                self.report_metrics(simulated)
            time.sleep(self.poll_interval)


# ==================== 全局实例 ====================

complexity_analyzer = TaskComplexityAnalyzer()
maas_scheduler = MaASDynamicTeamScheduler(complexity_analyzer)
agent_swarm = AgentSwarmCollaborator()
health_monitor = AgentHealthMonitor()
