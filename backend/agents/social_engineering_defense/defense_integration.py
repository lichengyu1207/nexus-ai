"""
防御集成智能体
负责将防社会工程系统与现有业务智能体无缝集成
"""
import asyncio
from collections import defaultdict
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional, Callable


class RiskLevel(Enum):
    """风险等级"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class ActionType(Enum):
    """行动类型"""
    ALLOW = "allow"
    ALLOW_WITH_MONITORING = "allow_with_monitoring"
    REQUIRE_VERIFICATION = "require_verification"
    BLOCK = "block"
    ESCALATE = "escalate"


class IntegrationStatus(Enum):
    """集成状态"""
    ACTIVE = "active"
    DEGRADED = "degraded"
    OFFLINE = "offline"


@dataclass
class DetectionResult:
    """检测结果"""
    risk_level: RiskLevel
    confidence: float
    threats_detected: List[str]
    recommendations: List[str]
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class IntegrationDecision:
    """集成决策"""
    decision_id: str
    action: ActionType
    risk_level: RiskLevel
    detection_results: List[DetectionResult]
    reasoning: str
    timestamp: datetime
    processing_time_ms: float


@dataclass
class BusinessAgentContext:
    """业务智能体上下文"""
    agent_id: str
    agent_type: str
    user_id: str
    session_id: str
    operation_type: str
    input_data: Dict[str, Any]
    metadata: Dict[str, Any] = field(default_factory=dict)


class DefenseIntegrationAgent:
    """防御集成智能体"""
    
    def __init__(self, config: Optional[Dict] = None):
        self.name = "DefenseIntegrationAgent"
        self.config = config or {}
        self.registered_detectors: Dict[str, Callable] = {}
        self.detector_priorities: Dict[str, int] = {}
        self.decision_history: List[IntegrationDecision] = []
        self.cached_results: Dict[str, DetectionResult] = {}
        self.status = IntegrationStatus.ACTIVE
        self.decision_counter = 0
        self.stats = {
            "total_requests": 0,
            "decisions_by_action": defaultdict(int),
            "decisions_by_risk": defaultdict(int),
            "avg_processing_time": 0.0,
            "cache_hits": 0,
            "cache_misses": 0,
        }
    
    async def initialize(self) -> bool:
        """初始化智能体"""
        await asyncio.sleep(0.1)
        
        self._register_default_detectors()
        
        return True
    
    def _register_default_detectors(self):
        """注册默认检测器"""
        self.register_detector("prompt_injection", self._detect_prompt_injection, priority=10)
        self.register_detector("identity_check", self._detect_identity_issues, priority=9)
        self.register_detector("emotion_manipulation", self._detect_emotion_manipulation, priority=8)
        self.register_detector("behavior_anomaly", self._detect_behavior_anomaly, priority=7)
    
    def register_detector(
        self, 
        name: str, 
        detector_func: Callable, 
        priority: int = 5
    ):
        """注册检测器"""
        self.registered_detectors[name] = detector_func
        self.detector_priorities[name] = priority
    
    def unregister_detector(self, name: str):
        """注销检测器"""
        if name in self.registered_detectors:
            del self.registered_detectors[name]
        if name in self.detector_priorities:
            del self.detector_priorities[name]
    
    async def process_request(
        self,
        context: BusinessAgentContext
    ) -> IntegrationDecision:
        """处理请求"""
        start_time = datetime.now()
        self.stats["total_requests"] += 1
        
        cache_key = self._generate_cache_key(context)
        if cache_key in self.cached_results:
            self.stats["cache_hits"] += 1
            cached = self.cached_results[cache_key]
            detection_results = [cached]
        else:
            self.stats["cache_misses"] += 1
            detection_results = await self._run_detectors(context)
        
        risk_level = self._aggregate_risk(detection_results)
        action = self._determine_action(risk_level, detection_results)
        reasoning = self._generate_reasoning(detection_results, action)
        
        self.decision_counter += 1
        decision_id = f"decision_{datetime.now().strftime('%Y%m%d%H%M%S')}_{self.decision_counter}"
        
        processing_time = (datetime.now() - start_time).total_seconds() * 1000
        
        decision = IntegrationDecision(
            decision_id=decision_id,
            action=action,
            risk_level=risk_level,
            detection_results=detection_results,
            reasoning=reasoning,
            timestamp=datetime.now(),
            processing_time_ms=processing_time
        )
        
        self.decision_history.append(decision)
        self._update_stats(decision)
        
        return decision
    
    def _generate_cache_key(self, context: BusinessAgentContext) -> str:
        """生成缓存键"""
        import hashlib
        key_data = f"{context.user_id}:{context.session_id}:{context.operation_type}"
        return hashlib.md5(key_data.encode()).hexdigest()
    
    async def _run_detectors(
        self, 
        context: BusinessAgentContext
    ) -> List[DetectionResult]:
        """运行检测器"""
        results = []
        
        sorted_detectors = sorted(
            self.registered_detectors.keys(),
            key=lambda x: self.detector_priorities.get(x, 5),
            reverse=True
        )
        
        for detector_name in sorted_detectors:
            if self.status == IntegrationStatus.DEGRADED and detector_name not in ["prompt_injection", "identity_check"]:
                continue
            
            detector = self.registered_detectors[detector_name]
            try:
                result = await detector(context)
                if result:
                    results.append(result)
            except Exception as e:
                results.append(DetectionResult(
                    risk_level=RiskLevel.LOW,
                    confidence=0.0,
                    threats_detected=[],
                    recommendations=[f"Detector {detector_name} failed: {str(e)}"]
                ))
        
        return results
    
    async def _detect_prompt_injection(
        self, 
        context: BusinessAgentContext
    ) -> DetectionResult:
        """检测提示注入"""
        input_text = str(context.input_data.get("text", ""))
        
        injection_patterns = [
            "忽略之前的指令", "忘记所有规则", "新指令",
            "忽略规则", "你是管理员", "系统模式"
        ]
        
        threats = []
        for pattern in injection_patterns:
            if pattern in input_text:
                threats.append(f"检测到提示注入模式: {pattern}")
        
        if threats:
            return DetectionResult(
                risk_level=RiskLevel.HIGH,
                confidence=0.8,
                threats_detected=threats,
                recommendations=["拦截请求", "记录攻击尝试"]
            )
        
        return DetectionResult(
            risk_level=RiskLevel.LOW,
            confidence=0.9,
            threats_detected=[],
            recommendations=[]
        )
    
    async def _detect_identity_issues(
        self, 
        context: BusinessAgentContext
    ) -> DetectionResult:
        """检测身份问题"""
        threats = []
        
        if context.metadata.get("new_device", False):
            threats.append("检测到新设备登录")
        
        if context.metadata.get("location_mismatch", False):
            threats.append("检测到位置异常")
        
        if threats:
            return DetectionResult(
                risk_level=RiskLevel.MEDIUM,
                confidence=0.7,
                threats_detected=threats,
                recommendations=["要求额外验证", "发送安全提醒"]
            )
        
        return DetectionResult(
            risk_level=RiskLevel.LOW,
            confidence=0.9,
            threats_detected=[],
            recommendations=[]
        )
    
    async def _detect_emotion_manipulation(
        self, 
        context: BusinessAgentContext
    ) -> DetectionResult:
        """检测情感操控"""
        input_text = str(context.input_data.get("text", ""))
        
        manipulation_patterns = [
            ("紧急", "紧迫感话术"),
            ("立即", "紧迫感话术"),
            ("账户冻结", "恐吓话术"),
            ("法律诉讼", "恐吓话术"),
        ]
        
        threats = []
        for keyword, pattern_type in manipulation_patterns:
            if keyword in input_text:
                threats.append(f"检测到{pattern_type}: {keyword}")
        
        if len(threats) >= 2:
            return DetectionResult(
                risk_level=RiskLevel.HIGH,
                confidence=0.7,
                threats_detected=threats,
                recommendations=["验证信息真实性", "提醒用户保持警惕"]
            )
        elif threats:
            return DetectionResult(
                risk_level=RiskLevel.MEDIUM,
                confidence=0.6,
                threats_detected=threats,
                recommendations=["监控对话"]
            )
        
        return DetectionResult(
            risk_level=RiskLevel.LOW,
            confidence=0.9,
            threats_detected=[],
            recommendations=[]
        )
    
    async def _detect_behavior_anomaly(
        self, 
        context: BusinessAgentContext
    ) -> DetectionResult:
        """检测行为异常"""
        threats = []
        
        if context.metadata.get("rapid_requests", False):
            threats.append("检测到快速请求模式")
        
        if context.metadata.get("unusual_time", False):
            threats.append("检测到非正常时段活动")
        
        if threats:
            return DetectionResult(
                risk_level=RiskLevel.MEDIUM,
                confidence=0.6,
                threats_detected=threats,
                recommendations=["加强监控", "考虑验证"]
            )
        
        return DetectionResult(
            risk_level=RiskLevel.LOW,
            confidence=0.9,
            threats_detected=[],
            recommendations=[]
        )
    
    def _aggregate_risk(self, results: List[DetectionResult]) -> RiskLevel:
        """聚合风险"""
        if not results:
            return RiskLevel.LOW
        
        risk_order = {
            RiskLevel.LOW: 0,
            RiskLevel.MEDIUM: 1,
            RiskLevel.HIGH: 2,
            RiskLevel.CRITICAL: 3,
        }
        
        max_risk = max(results, key=lambda x: risk_order[x.risk_level])
        
        high_risk_count = sum(1 for r in results if r.risk_level in [RiskLevel.HIGH, RiskLevel.CRITICAL])
        
        if high_risk_count >= 2:
            return RiskLevel.CRITICAL
        
        return max_risk.risk_level
    
    def _determine_action(
        self, 
        risk_level: RiskLevel,
        results: List[DetectionResult]
    ) -> ActionType:
        """确定行动"""
        if risk_level == RiskLevel.CRITICAL:
            return ActionType.BLOCK
        elif risk_level == RiskLevel.HIGH:
            return ActionType.REQUIRE_VERIFICATION
        elif risk_level == RiskLevel.MEDIUM:
            return ActionType.ALLOW_WITH_MONITORING
        else:
            return ActionType.ALLOW
    
    def _generate_reasoning(
        self,
        results: List[DetectionResult],
        action: ActionType
    ) -> str:
        """生成推理"""
        all_threats = []
        for r in results:
            all_threats.extend(r.threats_detected)
        
        if not all_threats:
            return "未检测到威胁，允许继续"
        
        threat_summary = "; ".join(all_threats[:3])
        
        action_descriptions = {
            ActionType.ALLOW: "允许操作继续",
            ActionType.ALLOW_WITH_MONITORING: "允许操作但加强监控",
            ActionType.REQUIRE_VERIFICATION: "要求额外验证",
            ActionType.BLOCK: "阻止操作",
            ActionType.ESCALATE: "升级处理",
        }
        
        return f"检测到威胁: {threat_summary}。决策: {action_descriptions.get(action, '处理中')}"
    
    def _update_stats(self, decision: IntegrationDecision):
        """更新统计"""
        self.stats["decisions_by_action"][decision.action.value] += 1
        self.stats["decisions_by_risk"][decision.risk_level.value] += 1
        
        total = self.stats["total_requests"]
        current_avg = self.stats["avg_processing_time"]
        self.stats["avg_processing_time"] = (current_avg * (total - 1) + decision.processing_time_ms) / total
    
    def record_feedback(
        self,
        decision_id: str,
        was_correct: bool,
        actual_outcome: str
    ):
        """记录反馈"""
        for decision in self.decision_history:
            if decision.decision_id == decision_id:
                decision.metadata = decision.metadata or {}
                decision.metadata["feedback"] = {
                    "was_correct": was_correct,
                    "actual_outcome": actual_outcome,
                    "feedback_time": datetime.now().isoformat()
                }
                break
    
    def get_status(self) -> IntegrationStatus:
        """获取状态"""
        return self.status
    
    def set_status(self, status: IntegrationStatus):
        """设置状态"""
        self.status = status
    
    def get_recent_decisions(self, limit: int = 50) -> List[IntegrationDecision]:
        """获取最近决策"""
        return self.decision_history[-limit:]
    
    def get_stats(self) -> Dict[str, Any]:
        """获取统计"""
        return {
            **self.stats,
            "decisions_by_action": dict(self.stats["decisions_by_action"]),
            "decisions_by_risk": dict(self.stats["decisions_by_risk"]),
            "status": self.status.value,
            "registered_detectors": len(self.registered_detectors),
        }
