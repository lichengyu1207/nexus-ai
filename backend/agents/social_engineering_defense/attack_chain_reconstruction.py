"""
攻击链重构智能体
负责将多个离散异常事件重构为完整的攻击链
"""
import asyncio
from collections import defaultdict
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from typing import Any, Dict, List, Optional, Set, Tuple


class AttackPhase(Enum):
    """攻击阶段 (参考ATT&CK框架)"""
    RECONNAISSANCE = "reconnaissance"
    TRUST_BUILDING = "trust_building"
    BAIT_DELIVERY = "bait_delivery"
    INFORMATION_HARVESTING = "information_harvesting"
    PRIVILEGE_ESCALATION = "privilege_escalation"
    LATERAL_MOVEMENT = "lateral_movement"
    DATA_EXFILTRATION = "data_exfiltration"
    IMPACT = "impact"


class AttackChainStatus(Enum):
    """攻击链状态"""
    POTENTIAL = "potential"
    IN_PROGRESS = "in_progress"
    ADVANCED = "advanced"
    CRITICAL = "critical"
    COMPLETED = "completed"


class PredictionConfidence(Enum):
    """预测置信度"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


@dataclass
class AttackEvent:
    """攻击事件"""
    event_id: str
    phase: AttackPhase
    timestamp: datetime
    user_id: str
    session_id: str
    description: str
    severity: str
    indicators: List[str]
    raw_data: Dict[str, Any]


@dataclass
class AttackChainLink:
    """攻击链环节"""
    phase: AttackPhase
    events: List[AttackEvent]
    start_time: datetime
    end_time: datetime
    confidence: float
    next_phase_prediction: Optional[AttackPhase]
    prediction_confidence: PredictionConfidence


@dataclass
class AttackChain:
    """攻击链"""
    chain_id: str
    user_id: str
    status: AttackChainStatus
    phases: List[AttackChainLink]
    current_phase: AttackPhase
    total_duration: float
    risk_score: float
    attack_type: str
    predicted_next_actions: List[str]
    defense_recommendations: List[str]
    created_at: datetime
    updated_at: datetime


@dataclass
class ChainReconstructionResult:
    """攻击链重构结果"""
    chain_id: str
    is_attack_chain: bool
    chain: Optional[AttackChain]
    matched_patterns: List[str]
    prediction: Dict[str, Any]
    immediate_actions: List[str]


class AttackChainReconstructionAgent:
    """攻击链重构智能体"""
    
    def __init__(self, config: Optional[Dict] = None):
        self.name = "AttackChainReconstructionAgent"
        self.config = config or {}
        self.phase_mapping = self._init_phase_mapping()
        self.attack_patterns = self._init_attack_patterns()
        self.phase_transitions = self._init_phase_transitions()
        self.active_chains: Dict[str, AttackChain] = {}
        self.event_buffer: Dict[str, List[AttackEvent]] = defaultdict(list)
        self.stats = {
            "total_events_processed": 0,
            "chains_created": 0,
            "chains_advanced": 0,
            "attacks_detected": 0,
            "predictions_made": 0,
            "successful_predictions": 0,
        }
    
    def _init_phase_mapping(self) -> Dict[str, AttackPhase]:
        """初始化阶段映射"""
        return {
            "prompt_injection": AttackPhase.BAIT_DELIVERY,
            "identity_verification": AttackPhase.INFORMATION_HARVESTING,
            "emotion_manipulation": AttackPhase.TRUST_BUILDING,
            "urgency_creation": AttackPhase.BAIT_DELIVERY,
            "fear_induction": AttackPhase.TRUST_BUILDING,
            "context_pollution": AttackPhase.RECONNAISSANCE,
            "behavior_anomaly": AttackPhase.LATERAL_MOVEMENT,
            "data_request": AttackPhase.INFORMATION_HARVESTING,
            "permission_request": AttackPhase.PRIVILEGE_ESCALATION,
            "export_request": AttackPhase.DATA_EXFILTRATION,
            "deletion_request": AttackPhase.IMPACT,
        }
    
    def _init_attack_patterns(self) -> List[Dict]:
        """初始化攻击模式"""
        return [
            {
                "name": "social_engineering_phishing",
                "description": "社会工程钓鱼攻击",
                "phases": [
                    AttackPhase.RECONNAISSANCE,
                    AttackPhase.TRUST_BUILDING,
                    AttackPhase.BAIT_DELIVERY,
                    AttackPhase.INFORMATION_HARVESTING
                ],
                "time_threshold": 7200,
                "risk_multiplier": 1.5
            },
            {
                "name": "account_takeover",
                "description": "账户接管攻击",
                "phases": [
                    AttackPhase.RECONNAISSANCE,
                    AttackPhase.INFORMATION_HARVESTING,
                    AttackPhase.PRIVILEGE_ESCALATION,
                    AttackPhase.LATERAL_MOVEMENT
                ],
                "time_threshold": 3600,
                "risk_multiplier": 2.0
            },
            {
                "name": "data_breach",
                "description": "数据泄露攻击",
                "phases": [
                    AttackPhase.RECONNAISSANCE,
                    AttackPhase.TRUST_BUILDING,
                    AttackPhase.PRIVILEGE_ESCALATION,
                    AttackPhase.DATA_EXFILTRATION
                ],
                "time_threshold": 10800,
                "risk_multiplier": 2.5
            },
            {
                "name": "insider_threat",
                "description": "内部威胁",
                "phases": [
                    AttackPhase.RECONNAISSANCE,
                    AttackPhase.LATERAL_MOVEMENT,
                    AttackPhase.DATA_EXFILTRATION,
                    AttackPhase.IMPACT
                ],
                "time_threshold": 86400,
                "risk_multiplier": 3.0
            },
        ]
    
    def _init_phase_transitions(self) -> Dict[AttackPhase, List[AttackPhase]]:
        """初始化阶段转换"""
        return {
            AttackPhase.RECONNAISSANCE: [
                AttackPhase.TRUST_BUILDING,
                AttackPhase.INFORMATION_HARVESTING
            ],
            AttackPhase.TRUST_BUILDING: [
                AttackPhase.BAIT_DELIVERY,
                AttackPhase.INFORMATION_HARVESTING
            ],
            AttackPhase.BAIT_DELIVERY: [
                AttackPhase.INFORMATION_HARVESTING,
                AttackPhase.PRIVILEGE_ESCALATION
            ],
            AttackPhase.INFORMATION_HARVESTING: [
                AttackPhase.PRIVILEGE_ESCALATION,
                AttackPhase.DATA_EXFILTRATION
            ],
            AttackPhase.PRIVILEGE_ESCALATION: [
                AttackPhase.LATERAL_MOVEMENT,
                AttackPhase.DATA_EXFILTRATION
            ],
            AttackPhase.LATERAL_MOVEMENT: [
                AttackPhase.DATA_EXFILTRATION,
                AttackPhase.IMPACT
            ],
            AttackPhase.DATA_EXFILTRATION: [
                AttackPhase.IMPACT
            ],
            AttackPhase.IMPACT: [],
        }
    
    async def initialize(self) -> bool:
        """初始化智能体"""
        await asyncio.sleep(0.1)
        return True
    
    def process_event(
        self,
        event_type: str,
        user_id: str,
        session_id: str,
        description: str,
        severity: str,
        indicators: List[str],
        raw_data: Dict[str, Any]
    ) -> str:
        """处理事件"""
        phase = self.phase_mapping.get(event_type, AttackPhase.RECONNAISSANCE)
        
        event = AttackEvent(
            event_id=f"evt_{datetime.now().strftime('%Y%m%d%H%M%S')}_{len(self.event_buffer[user_id])}",
            phase=phase,
            timestamp=datetime.now(),
            user_id=user_id,
            session_id=session_id,
            description=description,
            severity=severity,
            indicators=indicators,
            raw_data=raw_data
        )
        
        self.event_buffer[user_id].append(event)
        self.stats["total_events_processed"] += 1
        
        return event.event_id
    
    def reconstruct_chain(self, user_id: str) -> ChainReconstructionResult:
        """重构攻击链"""
        events = self.event_buffer.get(user_id, [])
        
        if len(events) < 2:
            return self._create_empty_result(user_id)
        
        events = sorted(events, key=lambda x: x.timestamp)
        
        phase_events = self._group_events_by_phase(events)
        
        chain_links = self._build_chain_links(phase_events, events)
        
        if not chain_links:
            return self._create_empty_result(user_id)
        
        current_phase = chain_links[-1].phase
        status = self._determine_chain_status(chain_links)
        
        matched_patterns = self._match_attack_patterns(chain_links)
        
        attack_type = matched_patterns[0] if matched_patterns else "unknown"
        
        risk_score = self._calculate_chain_risk(chain_links, matched_patterns)
        
        prediction = self._predict_next_phase(chain_links)
        
        predicted_actions = self._predict_next_actions(current_phase, prediction)
        
        defense_recommendations = self._generate_defense_recommendations(
            current_phase, prediction, matched_patterns
        )
        
        total_duration = (events[-1].timestamp - events[0].timestamp).total_seconds()
        
        chain = AttackChain(
            chain_id=f"chain_{user_id}_{datetime.now().strftime('%Y%m%d%H%M%S')}",
            user_id=user_id,
            status=status,
            phases=chain_links,
            current_phase=current_phase,
            total_duration=total_duration,
            risk_score=risk_score,
            attack_type=attack_type,
            predicted_next_actions=predicted_actions,
            defense_recommendations=defense_recommendations,
            created_at=datetime.now(),
            updated_at=datetime.now()
        )
        
        self.active_chains[user_id] = chain
        self.stats["chains_created"] += 1
        
        if status in [AttackChainStatus.ADVANCED, AttackChainStatus.CRITICAL]:
            self.stats["attacks_detected"] += 1
        
        immediate_actions = self._get_immediate_actions(status, current_phase)
        
        return ChainReconstructionResult(
            chain_id=chain.chain_id,
            is_attack_chain=True,
            chain=chain,
            matched_patterns=matched_patterns,
            prediction=prediction,
            immediate_actions=immediate_actions
        )
    
    def _group_events_by_phase(
        self, 
        events: List[AttackEvent]
    ) -> Dict[AttackPhase, List[AttackEvent]]:
        """按阶段分组事件"""
        grouped: Dict[AttackPhase, List[AttackEvent]] = defaultdict(list)
        for event in events:
            grouped[event.phase].append(event)
        return grouped
    
    def _build_chain_links(
        self,
        phase_events: Dict[AttackPhase, List[AttackEvent]],
        all_events: List[AttackEvent]
    ) -> List[AttackChainLink]:
        """构建攻击链环节"""
        links = []
        sorted_phases = sorted(phase_events.keys(), key=lambda p: min(e.timestamp for e in phase_events[p]))
        
        for i, phase in enumerate(sorted_phases):
            events = phase_events[phase]
            start_time = min(e.timestamp for e in events)
            end_time = max(e.timestamp for e in events)
            
            confidence = sum(1 for e in events if e.severity in ["high", "critical"]) / len(events)
            
            next_phase = None
            prediction_confidence = PredictionConfidence.LOW
            
            if i < len(sorted_phases) - 1:
                next_phase = sorted_phases[i + 1]
                prediction_confidence = PredictionConfidence.HIGH
            else:
                valid_transitions = self.phase_transitions.get(phase, [])
                if valid_transitions:
                    next_phase = valid_transitions[0]
                    prediction_confidence = PredictionConfidence.MEDIUM
            
            link = AttackChainLink(
                phase=phase,
                events=events,
                start_time=start_time,
                end_time=end_time,
                confidence=confidence,
                next_phase_prediction=next_phase,
                prediction_confidence=prediction_confidence
            )
            links.append(link)
        
        return links
    
    def _determine_chain_status(self, links: List[AttackChainLink]) -> AttackChainStatus:
        """确定攻击链状态"""
        if len(links) >= 5:
            return AttackChainStatus.COMPLETED
        elif len(links) >= 4:
            return AttackChainStatus.CRITICAL
        elif len(links) >= 3:
            return AttackChainStatus.ADVANCED
        elif len(links) >= 2:
            return AttackChainStatus.IN_PROGRESS
        else:
            return AttackChainStatus.POTENTIAL
    
    def _match_attack_patterns(self, links: List[AttackChainLink]) -> List[str]:
        """匹配攻击模式"""
        matched = []
        chain_phases = [link.phase for link in links]
        
        for pattern in self.attack_patterns:
            pattern_phases = pattern["phases"]
            
            for i in range(len(chain_phases) - len(pattern_phases) + 1):
                if chain_phases[i:i + len(pattern_phases)] == pattern_phases:
                    matched.append(pattern["name"])
                    break
        
        return matched
    
    def _calculate_chain_risk(
        self,
        links: List[AttackChainLink],
        matched_patterns: List[str]
    ) -> float:
        """计算攻击链风险"""
        base_score = len(links) * 0.15
        
        for link in links:
            high_severity = sum(1 for e in link.events if e.severity in ["high", "critical"])
            base_score += high_severity * 0.1
        
        for pattern in self.attack_patterns:
            if pattern["name"] in matched_patterns:
                base_score *= pattern.get("risk_multiplier", 1.0)
        
        return min(1.0, base_score)
    
    def _predict_next_phase(
        self, 
        links: List[AttackChainLink]
    ) -> Dict[str, Any]:
        """预测下一阶段"""
        if not links:
            return {"next_phase": None, "confidence": PredictionConfidence.LOW}
        
        last_link = links[-1]
        
        self.stats["predictions_made"] += 1
        
        return {
            "next_phase": last_link.next_phase_prediction.value if last_link.next_phase_prediction else None,
            "confidence": last_link.prediction_confidence.value,
            "current_phase": last_link.phase.value,
            "time_estimate": 300
        }
    
    def _predict_next_actions(
        self,
        current_phase: AttackPhase,
        prediction: Dict[str, Any]
    ) -> List[str]:
        """预测下一步行动"""
        action_predictions = {
            AttackPhase.RECONNAISSANCE: [
                "尝试建立信任关系",
                "收集更多用户信息",
                "探测系统漏洞"
            ],
            AttackPhase.TRUST_BUILDING: [
                "发送钓鱼链接或文件",
                "请求敏感信息",
                "制造紧迫感"
            ],
            AttackPhase.BAIT_DELIVERY: [
                "请求账户凭证",
                "诱导下载恶意文件",
                "引导访问钓鱼网站"
            ],
            AttackPhase.INFORMATION_HARVESTING: [
                "请求更多敏感数据",
                "尝试权限提升",
                "收集系统信息"
            ],
            AttackPhase.PRIVILEGE_ESCALATION: [
                "尝试访问其他账户",
                "请求管理员权限",
                "修改安全设置"
            ],
            AttackPhase.LATERAL_MOVEMENT: [
                "访问其他系统",
                "收集更多数据",
                "准备数据外传"
            ],
            AttackPhase.DATA_EXFILTRATION: [
                "批量导出数据",
                "删除痕迹",
                "造成破坏"
            ],
            AttackPhase.IMPACT: [
                "勒索行为",
                "数据破坏",
                "服务中断"
            ],
        }
        
        return action_predictions.get(current_phase, ["未知行动"])
    
    def _generate_defense_recommendations(
        self,
        current_phase: AttackPhase,
        prediction: Dict[str, Any],
        matched_patterns: List[str]
    ) -> List[str]:
        """生成防御建议"""
        recommendations = []
        
        phase_defenses = {
            AttackPhase.RECONNAISSANCE: [
                "限制信息泄露",
                "监控异常查询",
                "加强访问控制"
            ],
            AttackPhase.TRUST_BUILDING: [
                "验证身份真实性",
                "提醒用户警惕",
                "延迟敏感操作"
            ],
            AttackPhase.BAIT_DELIVERY: [
                "拦截可疑链接",
                "扫描附件文件",
                "警告用户风险"
            ],
            AttackPhase.INFORMATION_HARVESTING: [
                "阻止敏感信息输出",
                "要求额外验证",
                "记录详细信息"
            ],
            AttackPhase.PRIVILEGE_ESCALATION: [
                "冻结权限变更",
                "要求管理员审批",
                "隔离账户"
            ],
            AttackPhase.LATERAL_MOVEMENT: [
                "限制跨系统访问",
                "加强监控",
                "准备隔离措施"
            ],
            AttackPhase.DATA_EXFILTRATION: [
                "阻止数据导出",
                "立即隔离账户",
                "通知安全团队"
            ],
            AttackPhase.IMPACT: [
                "紧急响应",
                "系统隔离",
                "启动应急预案"
            ],
        }
        
        recommendations.extend(phase_defenses.get(current_phase, []))
        
        if matched_patterns:
            recommendations.append(f"检测到{matched_patterns[0]}攻击模式")
        
        return recommendations
    
    def _get_immediate_actions(
        self,
        status: AttackChainStatus,
        current_phase: AttackPhase
    ) -> List[str]:
        """获取立即行动"""
        actions = []
        
        if status == AttackChainStatus.CRITICAL:
            actions.append("立即中断当前会话")
            actions.append("冻结相关账户")
            actions.append("通知安全团队")
        elif status == AttackChainStatus.ADVANCED:
            actions.append("加强身份验证")
            actions.append("限制敏感操作")
            actions.append("准备隔离措施")
        elif status == AttackChainStatus.IN_PROGRESS:
            actions.append("持续监控")
            actions.append("记录详细日志")
        
        if current_phase in [AttackPhase.DATA_EXFILTRATION, AttackPhase.IMPACT]:
            actions.append("紧急响应: 阻止数据泄露")
        
        return actions
    
    def _create_empty_result(self, user_id: str) -> ChainReconstructionResult:
        """创建空结果"""
        return ChainReconstructionResult(
            chain_id=f"chain_empty_{user_id}",
            is_attack_chain=False,
            chain=None,
            matched_patterns=[],
            prediction={"next_phase": None, "confidence": "low"},
            immediate_actions=["继续监控"]
        )
    
    def get_active_chain(self, user_id: str) -> Optional[AttackChain]:
        """获取活跃攻击链"""
        return self.active_chains.get(user_id)
    
    def clear_chain(self, user_id: str):
        """清除攻击链"""
        if user_id in self.active_chains:
            del self.active_chains[user_id]
        if user_id in self.event_buffer:
            del self.event_buffer[user_id]
    
    def get_stats(self) -> Dict[str, Any]:
        """获取统计信息"""
        return {
            **self.stats,
            "active_chains": len(self.active_chains),
            "buffered_users": len(self.event_buffer),
        }
