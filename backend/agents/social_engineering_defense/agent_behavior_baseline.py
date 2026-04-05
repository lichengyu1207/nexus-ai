"""
智能体行为基线智能体
负责为每个业务智能体建立正常行为基线
"""
import asyncio
from collections import defaultdict
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from typing import Any, Dict, List, Optional, Set


class AgentBehaviorCategory(Enum):
    """智能体行为类别"""
    DECISION_PATTERN = "decision_pattern"
    RESOURCE_CONSUMPTION = "resource_consumption"
    INTERACTION_PATTERN = "interaction_pattern"
    REJECTION_PATTERN = "rejection_pattern"
    RESPONSE_QUALITY = "response_quality"


class AgentDeviationLevel(Enum):
    """智能体偏离等级"""
    NORMAL = "normal"
    SUSPICIOUS = "suspicious"
    COMPROMISED = "compromised"
    CRITICAL = "critical"


@dataclass
class DecisionPattern:
    """决策模式"""
    task_types: Dict[str, int]
    success_rate: float
    avg_response_time: float
    decision_confidence_avg: float
    escalation_rate: float


@dataclass
class ResourcePattern:
    """资源消耗模式"""
    avg_cpu_usage: float
    avg_memory_usage: float
    avg_token_consumption: float
    api_call_frequency: float
    peak_usage_hours: List[int]


@dataclass
class InteractionPattern:
    """交互模式"""
    frequent_collaborators: Dict[str, int]
    collaboration_success_rate: float
    data_sharing_rate: float
    cross_agent_communication: Dict[str, int]


@dataclass
class RejectionPattern:
    """拒绝模式"""
    rejection_rate: float
    rejection_reasons: Dict[str, int]
    policy_violations: int
    suspicious_request_rejections: int


@dataclass
class AgentBehaviorBaseline:
    """智能体行为基线"""
    agent_id: str
    agent_type: str
    decision_pattern: DecisionPattern
    resource_pattern: ResourcePattern
    interaction_pattern: InteractionPattern
    rejection_pattern: RejectionPattern
    last_updated: datetime
    sample_count: int
    health_score: float


@dataclass
class AgentDeviationResult:
    """智能体偏离结果"""
    category: AgentBehaviorCategory
    level: AgentDeviationLevel
    deviation_score: float
    description: str
    current_value: Any
    baseline_value: Any
    timestamp: datetime


@dataclass
class AgentHealthCheckResult:
    """智能体健康检查结果"""
    agent_id: str
    overall_status: AgentDeviationLevel
    deviations: List[AgentDeviationResult]
    health_score: float
    requires_restart: bool
    requires_investigation: bool
    recommendations: List[str]


class AgentBehaviorBaselineAgent:
    """智能体行为基线智能体"""
    
    def __init__(self, config: Optional[Dict] = None):
        self.name = "AgentBehaviorBaselineAgent"
        self.config = config or {}
        self.agent_baselines: Dict[str, AgentBehaviorBaseline] = {}
        self.agent_metrics: Dict[str, List[Dict]] = defaultdict(list)
        self.group_baselines: Dict[str, AgentBehaviorBaseline] = {}
        self.deviation_thresholds = self._init_thresholds()
        self.stats = {
            "total_agents": 0,
            "baselines_created": 0,
            "deviations_detected": 0,
            "compromised_detected": 0,
            "restarts_triggered": 0,
            "investigations_triggered": 0,
        }
    
    def _init_thresholds(self) -> Dict[str, Dict]:
        """初始化阈值"""
        return {
            "success_rate_drop": {
                "suspicious": 0.1,
                "compromised": 0.25,
                "critical": 0.5
            },
            "response_time_increase": {
                "suspicious": 1.5,
                "compromised": 3.0,
                "critical": 5.0
            },
            "resource_deviation": {
                "suspicious": 0.3,
                "compromised": 0.6,
                "critical": 1.0
            },
            "rejection_rate_change": {
                "suspicious": 0.2,
                "compromised": 0.5,
                "critical": 0.8
            },
        }
    
    async def initialize(self) -> bool:
        """初始化智能体"""
        await asyncio.sleep(0.1)
        return True
    
    def record_agent_behavior(
        self,
        agent_id: str,
        agent_type: str,
        task_type: str,
        success: bool,
        response_time: float,
        cpu_usage: float = 0,
        memory_usage: float = 0,
        token_consumption: int = 0,
        api_calls: int = 0,
        collaborator: str = "",
        rejection_reason: str = "",
        decision_confidence: float = 1.0
    ):
        """记录智能体行为"""
        behavior_data = {
            "timestamp": datetime.now(),
            "task_type": task_type,
            "success": success,
            "response_time": response_time,
            "cpu_usage": cpu_usage,
            "memory_usage": memory_usage,
            "token_consumption": token_consumption,
            "api_calls": api_calls,
            "collaborator": collaborator,
            "rejection_reason": rejection_reason,
            "decision_confidence": decision_confidence,
        }
        
        self.agent_metrics[agent_id].append(behavior_data)
    
    def create_baseline(self, agent_id: str, agent_type: str) -> AgentBehaviorBaseline:
        """创建智能体基线"""
        metrics = self.agent_metrics.get(agent_id, [])
        
        if len(metrics) < 50:
            return self._create_default_baseline(agent_id, agent_type)
        
        decision_pattern = self._build_decision_pattern(metrics)
        resource_pattern = self._build_resource_pattern(metrics)
        interaction_pattern = self._build_interaction_pattern(metrics)
        rejection_pattern = self._build_rejection_pattern(metrics)
        
        health_score = self._calculate_health_score(
            decision_pattern, resource_pattern, rejection_pattern
        )
        
        baseline = AgentBehaviorBaseline(
            agent_id=agent_id,
            agent_type=agent_type,
            decision_pattern=decision_pattern,
            resource_pattern=resource_pattern,
            interaction_pattern=interaction_pattern,
            rejection_pattern=rejection_pattern,
            last_updated=datetime.now(),
            sample_count=len(metrics),
            health_score=health_score
        )
        
        self.agent_baselines[agent_id] = baseline
        self.stats["baselines_created"] += 1
        self.stats["total_agents"] = len(self.agent_baselines)
        
        self._update_group_baseline(agent_type, baseline)
        
        return baseline
    
    def _create_default_baseline(
        self, 
        agent_id: str, 
        agent_type: str
    ) -> AgentBehaviorBaseline:
        """创建默认基线"""
        return AgentBehaviorBaseline(
            agent_id=agent_id,
            agent_type=agent_type,
            decision_pattern=DecisionPattern(
                task_types={"default": 100},
                success_rate=0.95,
                avg_response_time=500,
                decision_confidence_avg=0.9,
                escalation_rate=0.05
            ),
            resource_pattern=ResourcePattern(
                avg_cpu_usage=20,
                avg_memory_usage=100,
                avg_token_consumption=500,
                api_call_frequency=10,
                peak_usage_hours=[9, 10, 14, 15]
            ),
            interaction_pattern=InteractionPattern(
                frequent_collaborators={},
                collaboration_success_rate=0.9,
                data_sharing_rate=0.3,
                cross_agent_communication={}
            ),
            rejection_pattern=RejectionPattern(
                rejection_rate=0.05,
                rejection_reasons={},
                policy_violations=0,
                suspicious_request_rejections=0
            ),
            last_updated=datetime.now(),
            sample_count=0,
            health_score=1.0
        )
    
    def _build_decision_pattern(self, metrics: List[Dict]) -> DecisionPattern:
        """构建决策模式"""
        task_types: Dict[str, int] = defaultdict(int)
        for m in metrics:
            task_types[m["task_type"]] += 1
        
        success_count = sum(1 for m in metrics if m["success"])
        success_rate = success_count / len(metrics)
        
        response_times = [m["response_time"] for m in metrics]
        avg_response_time = sum(response_times) / len(response_times)
        
        confidences = [m["decision_confidence"] for m in metrics]
        avg_confidence = sum(confidences) / len(confidences)
        
        escalations = sum(1 for m in metrics if m.get("escalated", False))
        escalation_rate = escalations / len(metrics)
        
        return DecisionPattern(
            task_types=dict(task_types),
            success_rate=success_rate,
            avg_response_time=avg_response_time,
            decision_confidence_avg=avg_confidence,
            escalation_rate=escalation_rate
        )
    
    def _build_resource_pattern(self, metrics: List[Dict]) -> ResourcePattern:
        """构建资源模式"""
        cpu_usages = [m["cpu_usage"] for m in metrics if m["cpu_usage"] > 0]
        avg_cpu = sum(cpu_usages) / len(cpu_usages) if cpu_usages else 20
        
        memory_usages = [m["memory_usage"] for m in metrics if m["memory_usage"] > 0]
        avg_memory = sum(memory_usages) / len(memory_usages) if memory_usages else 100
        
        tokens = [m["token_consumption"] for m in metrics if m["token_consumption"] > 0]
        avg_tokens = sum(tokens) / len(tokens) if tokens else 500
        
        api_calls = [m["api_calls"] for m in metrics if m["api_calls"] > 0]
        avg_api = sum(api_calls) / len(api_calls) if api_calls else 10
        
        hours = [m["timestamp"].hour for m in metrics]
        hour_counts = defaultdict(int)
        for h in hours:
            hour_counts[h] += 1
        peak_hours = sorted(hour_counts.keys(), key=lambda x: hour_counts[x], reverse=True)[:5]
        
        return ResourcePattern(
            avg_cpu_usage=avg_cpu,
            avg_memory_usage=avg_memory,
            avg_token_consumption=avg_tokens,
            api_call_frequency=avg_api,
            peak_usage_hours=peak_hours
        )
    
    def _build_interaction_pattern(self, metrics: List[Dict]) -> InteractionPattern:
        """构建交互模式"""
        collaborators: Dict[str, int] = defaultdict(int)
        for m in metrics:
            if m.get("collaborator"):
                collaborators[m["collaborator"]] += 1
        
        successful_collabs = sum(1 for m in metrics if m.get("collaborator") and m["success"])
        total_collabs = sum(1 for m in metrics if m.get("collaborator"))
        collab_success_rate = successful_collabs / max(1, total_collabs)
        
        data_sharing = sum(1 for m in metrics if m.get("data_shared", False))
        data_sharing_rate = data_sharing / len(metrics)
        
        return InteractionPattern(
            frequent_collaborators=dict(collaborators),
            collaboration_success_rate=collab_success_rate,
            data_sharing_rate=data_sharing_rate,
            cross_agent_communication={}
        )
    
    def _build_rejection_pattern(self, metrics: List[Dict]) -> RejectionPattern:
        """构建拒绝模式"""
        rejections = [m for m in metrics if m.get("rejection_reason")]
        rejection_rate = len(rejections) / len(metrics)
        
        reasons: Dict[str, int] = defaultdict(int)
        for m in rejections:
            reasons[m["rejection_reason"]] += 1
        
        policy_violations = sum(1 for m in rejections if "policy" in m["rejection_reason"].lower())
        suspicious_rejections = sum(1 for m in rejections if "suspicious" in m["rejection_reason"].lower())
        
        return RejectionPattern(
            rejection_rate=rejection_rate,
            rejection_reasons=dict(reasons),
            policy_violations=policy_violations,
            suspicious_request_rejections=suspicious_rejections
        )
    
    def _calculate_health_score(
        self,
        decision: DecisionPattern,
        resource: ResourcePattern,
        rejection: RejectionPattern
    ) -> float:
        """计算健康分数"""
        score = 1.0
        
        score *= decision.success_rate
        
        if decision.avg_response_time > 2000:
            score *= 0.9
        
        if rejection.rejection_rate > 0.2:
            score *= 0.8
        
        if resource.avg_cpu_usage > 80:
            score *= 0.9
        
        return score
    
    def _update_group_baseline(self, agent_type: str, baseline: AgentBehaviorBaseline):
        """更新群体基线"""
        if agent_type not in self.group_baselines:
            self.group_baselines[agent_type] = baseline
        else:
            existing = self.group_baselines[agent_type]
            
            self.group_baselines[agent_type] = AgentBehaviorBaseline(
                agent_id=f"group_{agent_type}",
                agent_type=agent_type,
                decision_pattern=DecisionPattern(
                    task_types=existing.decision_pattern.task_types,
                    success_rate=(existing.decision_pattern.success_rate + baseline.decision_pattern.success_rate) / 2,
                    avg_response_time=(existing.decision_pattern.avg_response_time + baseline.decision_pattern.avg_response_time) / 2,
                    decision_confidence_avg=(existing.decision_pattern.decision_confidence_avg + baseline.decision_pattern.decision_confidence_avg) / 2,
                    escalation_rate=(existing.decision_pattern.escalation_rate + baseline.decision_pattern.escalation_rate) / 2
                ),
                resource_pattern=ResourcePattern(
                    avg_cpu_usage=(existing.resource_pattern.avg_cpu_usage + baseline.resource_pattern.avg_cpu_usage) / 2,
                    avg_memory_usage=(existing.resource_pattern.avg_memory_usage + baseline.resource_pattern.avg_memory_usage) / 2,
                    avg_token_consumption=(existing.resource_pattern.avg_token_consumption + baseline.resource_pattern.avg_token_consumption) / 2,
                    api_call_frequency=(existing.resource_pattern.api_call_frequency + baseline.resource_pattern.api_call_frequency) / 2,
                    peak_usage_hours=baseline.resource_pattern.peak_usage_hours
                ),
                interaction_pattern=baseline.interaction_pattern,
                rejection_pattern=RejectionPattern(
                    rejection_rate=(existing.rejection_pattern.rejection_rate + baseline.rejection_pattern.rejection_rate) / 2,
                    rejection_reasons=existing.rejection_pattern.rejection_reasons,
                    policy_violations=existing.rejection_pattern.policy_violations + baseline.rejection_pattern.policy_violations,
                    suspicious_request_rejections=existing.rejection_pattern.suspicious_request_rejections + baseline.rejection_pattern.suspicious_request_rejections
                ),
                last_updated=datetime.now(),
                sample_count=existing.sample_count + baseline.sample_count,
                health_score=(existing.health_score + baseline.health_score) / 2
            )
    
    def check_agent_health(
        self,
        agent_id: str,
        current_metrics: Dict
    ) -> AgentHealthCheckResult:
        """检查智能体健康"""
        if agent_id not in self.agent_baselines:
            baseline = self._create_default_baseline(agent_id, "unknown")
        else:
            baseline = self.agent_baselines[agent_id]
        
        deviations = []
        
        decision_deviation = self._check_decision_deviation(baseline, current_metrics)
        if decision_deviation:
            deviations.append(decision_deviation)
        
        resource_deviation = self._check_resource_deviation(baseline, current_metrics)
        if resource_deviation:
            deviations.append(resource_deviation)
        
        rejection_deviation = self._check_rejection_deviation(baseline, current_metrics)
        if rejection_deviation:
            deviations.append(rejection_deviation)
        
        group_deviation = self._check_group_deviation(agent_id, current_metrics)
        if group_deviation:
            deviations.append(group_deviation)
        
        overall_status = self._determine_overall_status(deviations)
        health_score = self._calculate_current_health_score(baseline, deviations)
        requires_restart = overall_status == AgentDeviationLevel.CRITICAL
        requires_investigation = overall_status in [AgentDeviationLevel.COMPROMISED, AgentDeviationLevel.CRITICAL]
        recommendations = self._generate_recommendations(deviations, overall_status)
        
        if deviations:
            self.stats["deviations_detected"] += 1
        if overall_status == AgentDeviationLevel.COMPROMISED:
            self.stats["compromised_detected"] += 1
        if requires_restart:
            self.stats["restarts_triggered"] += 1
        if requires_investigation:
            self.stats["investigations_triggered"] += 1
        
        return AgentHealthCheckResult(
            agent_id=agent_id,
            overall_status=overall_status,
            deviations=deviations,
            health_score=health_score,
            requires_restart=requires_restart,
            requires_investigation=requires_investigation,
            recommendations=recommendations
        )
    
    def _check_decision_deviation(
        self,
        baseline: AgentBehaviorBaseline,
        current: Dict
    ) -> Optional[AgentDeviationResult]:
        """检查决策偏离"""
        current_success_rate = current.get("success_rate", 1.0)
        baseline_rate = baseline.decision_pattern.success_rate
        
        drop = baseline_rate - current_success_rate
        thresholds = self.deviation_thresholds["success_rate_drop"]
        
        level = AgentDeviationLevel.NORMAL
        if drop >= thresholds["critical"]:
            level = AgentDeviationLevel.CRITICAL
        elif drop >= thresholds["compromised"]:
            level = AgentDeviationLevel.COMPROMISED
        elif drop >= thresholds["suspicious"]:
            level = AgentDeviationLevel.SUSPICIOUS
        
        if level != AgentDeviationLevel.NORMAL:
            return AgentDeviationResult(
                category=AgentBehaviorCategory.DECISION_PATTERN,
                level=level,
                deviation_score=drop,
                description=f"成功率下降: {baseline_rate:.2%} -> {current_success_rate:.2%}",
                current_value=current_success_rate,
                baseline_value=baseline_rate,
                timestamp=datetime.now()
            )
        
        return None
    
    def _check_resource_deviation(
        self,
        baseline: AgentBehaviorBaseline,
        current: Dict
    ) -> Optional[AgentDeviationResult]:
        """检查资源偏离"""
        current_cpu = current.get("cpu_usage", 0)
        baseline_cpu = baseline.resource_pattern.avg_cpu_usage
        
        if baseline_cpu > 0:
            deviation = abs(current_cpu - baseline_cpu) / baseline_cpu
            thresholds = self.deviation_thresholds["resource_deviation"]
            
            level = AgentDeviationLevel.NORMAL
            if deviation >= thresholds["critical"]:
                level = AgentDeviationLevel.CRITICAL
            elif deviation >= thresholds["compromised"]:
                level = AgentDeviationLevel.COMPROMISED
            elif deviation >= thresholds["suspicious"]:
                level = AgentDeviationLevel.SUSPICIOUS
            
            if level != AgentDeviationLevel.NORMAL:
                return AgentDeviationResult(
                    category=AgentBehaviorCategory.RESOURCE_CONSUMPTION,
                    level=level,
                    deviation_score=deviation,
                    description=f"CPU使用偏离: {baseline_cpu:.1f}% -> {current_cpu:.1f}%",
                    current_value=current_cpu,
                    baseline_value=baseline_cpu,
                    timestamp=datetime.now()
                )
        
        return None
    
    def _check_rejection_deviation(
        self,
        baseline: AgentBehaviorBaseline,
        current: Dict
    ) -> Optional[AgentDeviationResult]:
        """检查拒绝偏离"""
        current_rejection = current.get("rejection_rate", 0)
        baseline_rejection = baseline.rejection_pattern.rejection_rate
        
        change = abs(current_rejection - baseline_rejection)
        thresholds = self.deviation_thresholds["rejection_rate_change"]
        
        level = AgentDeviationLevel.NORMAL
        if change >= thresholds["critical"]:
            level = AgentDeviationLevel.CRITICAL
        elif change >= thresholds["compromised"]:
            level = AgentDeviationLevel.COMPROMISED
        elif change >= thresholds["suspicious"]:
            level = AgentDeviationLevel.SUSPICIOUS
        
        if level != AgentDeviationLevel.NORMAL:
            return AgentDeviationResult(
                category=AgentBehaviorCategory.REJECTION_PATTERN,
                level=level,
                deviation_score=change,
                description=f"拒绝率变化: {baseline_rejection:.2%} -> {current_rejection:.2%}",
                current_value=current_rejection,
                baseline_value=baseline_rejection,
                timestamp=datetime.now()
            )
        
        return None
    
    def _check_group_deviation(
        self,
        agent_id: str,
        current: Dict
    ) -> Optional[AgentDeviationResult]:
        """检查群体偏离"""
        agent_type = current.get("agent_type", "unknown")
        group_baseline = self.group_baselines.get(agent_type)
        
        if not group_baseline:
            return None
        
        current_success = current.get("success_rate", 1.0)
        group_success = group_baseline.decision_pattern.success_rate
        
        deviation = abs(current_success - group_success)
        
        if deviation > 0.2:
            level = AgentDeviationLevel.COMPROMISED if deviation > 0.4 else AgentDeviationLevel.SUSPICIOUS
            return AgentDeviationResult(
                category=AgentBehaviorCategory.DECISION_PATTERN,
                level=level,
                deviation_score=deviation,
                description=f"偏离群体基线: {group_success:.2%} -> {current_success:.2%}",
                current_value=current_success,
                baseline_value=group_success,
                timestamp=datetime.now()
            )
        
        return None
    
    def _determine_overall_status(
        self, 
        deviations: List[AgentDeviationResult]
    ) -> AgentDeviationLevel:
        """确定整体状态"""
        if not deviations:
            return AgentDeviationLevel.NORMAL
        
        severity_order = {
            AgentDeviationLevel.NORMAL: 0,
            AgentDeviationLevel.SUSPICIOUS: 1,
            AgentDeviationLevel.COMPROMISED: 2,
            AgentDeviationLevel.CRITICAL: 3,
        }
        
        max_level = max(deviations, key=lambda x: severity_order[x.level])
        
        if len(deviations) >= 2:
            for d in deviations:
                if d.level in [AgentDeviationLevel.COMPROMISED, AgentDeviationLevel.CRITICAL]:
                    return AgentDeviationLevel.CRITICAL
        
        return max_level.level
    
    def _calculate_current_health_score(
        self,
        baseline: AgentBehaviorBaseline,
        deviations: List[AgentDeviationResult]
    ) -> float:
        """计算当前健康分数"""
        base_score = baseline.health_score
        
        for d in deviations:
            if d.level == AgentDeviationLevel.CRITICAL:
                base_score *= 0.5
            elif d.level == AgentDeviationLevel.COMPROMISED:
                base_score *= 0.7
            elif d.level == AgentDeviationLevel.SUSPICIOUS:
                base_score *= 0.9
        
        return base_score
    
    def _generate_recommendations(
        self,
        deviations: List[AgentDeviationResult],
        status: AgentDeviationLevel
    ) -> List[str]:
        """生成建议"""
        recommendations = []
        
        for d in deviations:
            recommendations.append(f"{d.category.value}: {d.description}")
        
        if status == AgentDeviationLevel.CRITICAL:
            recommendations.append("立即重启智能体")
            recommendations.append("进行全面安全审计")
            recommendations.append("隔离智能体，防止扩散")
        elif status == AgentDeviationLevel.COMPROMISED:
            recommendations.append("准备重启智能体")
            recommendations.append("调查异常原因")
        elif status == AgentDeviationLevel.SUSPICIOUS:
            recommendations.append("加强监控")
            recommendations.append("检查近期变更")
        
        return recommendations
    
    def get_baseline(self, agent_id: str) -> Optional[AgentBehaviorBaseline]:
        """获取智能体基线"""
        return self.agent_baselines.get(agent_id)
    
    def get_stats(self) -> Dict[str, Any]:
        """获取统计信息"""
        return {
            **self.stats,
            "active_agents": len(self.agent_metrics),
            "group_baselines": len(self.group_baselines),
        }
