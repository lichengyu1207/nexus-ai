"""
实时防御态势感知智能体
负责提供实时防御态势感知
"""
import asyncio
from collections import defaultdict
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from typing import Any, Dict, List, Optional, Tuple


class ThreatLevel(Enum):
    """威胁等级"""
    NORMAL = "normal"
    ELEVATED = "elevated"
    HIGH = "high"
    CRITICAL = "critical"


class AttackIntensity(Enum):
    """攻击强度"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    OVERWHELMING = "overwhelming"


class AlertType(Enum):
    """告警类型"""
    ATTACK_SURGE = "attack_surge"
    NEW_THREAT = "new_threat"
    DEFENSE_DEGRADATION = "defense_degradation"
    ANOMALY_DETECTED = "anomaly_detected"
    SYSTEM_OVERLOAD = "system_overload"


@dataclass
class AttackMetric:
    """攻击指标"""
    attack_type: str
    count: int
    success_rate: float
    avg_severity: float
    trend: str
    affected_users: int


@dataclass
class DefenseMetric:
    """防御指标"""
    agent_id: str
    load: float
    response_time: float
    success_rate: float
    error_rate: float
    status: str


@dataclass
class RiskZone:
    """风险区域"""
    zone_id: str
    zone_type: str
    risk_level: float
    attack_count: int
    affected_entities: List[str]
    description: str


@dataclass
class SituationalAlert:
    """态势告警"""
    alert_id: str
    alert_type: AlertType
    severity: ThreatLevel
    message: str
    timestamp: datetime
    affected_components: List[str]
    recommended_actions: List[str]
    acknowledged: bool = False


@dataclass
class SituationalReport:
    """态势报告"""
    report_id: str
    timestamp: datetime
    threat_level: ThreatLevel
    attack_intensity: AttackIntensity
    attack_metrics: List[AttackMetric]
    defense_metrics: List[DefenseMetric]
    risk_zones: List[RiskZone]
    active_alerts: List[SituationalAlert]
    predictions: Dict[str, Any]
    recommendations: List[str]


class DefenseSituationalAwarenessAgent:
    """实时防御态势感知智能体"""
    
    def __init__(self, config: Optional[Dict] = None):
        self.name = "DefenseSituationalAwarenessAgent"
        self.config = config or {}
        self.attack_history: List[Dict[str, Any]] = []
        self.defense_status: Dict[str, DefenseMetric] = {}
        self.active_alerts: List[SituationalAlert] = []
        self.risk_zones: Dict[str, RiskZone] = {}
        self.baselines = self._init_baselines()
        self.thresholds = self._init_thresholds()
        self.alert_counter = 0
        self.stats = {
            "total_attacks_tracked": 0,
            "total_alerts_generated": 0,
            "threat_level_changes": 0,
            "predictions_made": 0,
        }
    
    def _init_baselines(self) -> Dict[str, Any]:
        """初始化基线"""
        return {
            "attacks_per_minute": 10,
            "defense_success_rate": 0.95,
            "avg_response_time": 100,
            "max_load": 0.8,
        }
    
    def _init_thresholds(self) -> Dict[str, Any]:
        """初始化阈值"""
        return {
            "attack_surge_multiplier": 2.0,
            "high_load_threshold": 0.7,
            "critical_load_threshold": 0.9,
            "response_time_degradation": 2.0,
            "success_rate_drop": 0.1,
        }
    
    async def initialize(self) -> bool:
        """初始化智能体"""
        await asyncio.sleep(0.1)
        return True
    
    def report_attack(
        self,
        attack_type: str,
        severity: str,
        user_id: str,
        session_id: str,
        blocked: bool,
        response_time: float = 0,
        metadata: Dict[str, Any] = None
    ):
        """报告攻击"""
        attack_record = {
            "timestamp": datetime.now(),
            "attack_type": attack_type,
            "severity": severity,
            "user_id": user_id,
            "session_id": session_id,
            "blocked": blocked,
            "response_time": response_time,
            "metadata": metadata or {},
        }
        
        self.attack_history.append(attack_record)
        self.stats["total_attacks_tracked"] += 1
        
        self._cleanup_old_history()
        
        self._check_for_alerts(attack_record)
    
    def _cleanup_old_history(self):
        """清理旧历史"""
        cutoff = datetime.now() - timedelta(hours=24)
        self.attack_history = [a for a in self.attack_history if a["timestamp"] > cutoff]
    
    def report_defense_status(
        self,
        agent_id: str,
        load: float,
        response_time: float,
        success_rate: float,
        error_rate: float,
        status: str = "active"
    ):
        """报告防御状态"""
        metric = DefenseMetric(
            agent_id=agent_id,
            load=load,
            response_time=response_time,
            success_rate=success_rate,
            error_rate=error_rate,
            status=status
        )
        
        self.defense_status[agent_id] = metric
        
        self._check_defense_health(agent_id, metric)
    
    def _check_for_alerts(self, attack_record: Dict[str, Any]):
        """检查告警"""
        recent_attacks = self._get_recent_attacks(minutes=5)
        
        if len(recent_attacks) > self.baselines["attacks_per_minute"] * 5 * self.thresholds["attack_surge_multiplier"]:
            self._generate_alert(
                AlertType.ATTACK_SURGE,
                ThreatLevel.HIGH,
                f"攻击激增: 最近5分钟{len(recent_attacks)}次攻击",
                ["defense_system"],
                ["加强监控", "准备扩容", "通知安全团队"]
            )
        
        attack_types = defaultdict(int)
        for a in recent_attacks:
            attack_types[a["attack_type"]] += 1
        
        for attack_type, count in attack_types.items():
            if count > 20:
                self._generate_alert(
                    AlertType.ANOMALY_DETECTED,
                    ThreatLevel.ELEVATED,
                    f"异常攻击模式: {attack_type}出现{count}次",
                    ["defense_system"],
                    ["分析攻击模式", "更新防御规则"]
                )
    
    def _check_defense_health(self, agent_id: str, metric: DefenseMetric):
        """检查防御健康"""
        if metric.load > self.thresholds["critical_load_threshold"]:
            self._generate_alert(
                AlertType.SYSTEM_OVERLOAD,
                ThreatLevel.CRITICAL,
                f"智能体{agent_id}负载过高: {metric.load:.1%}",
                [agent_id],
                ["扩容", "负载均衡", "降级服务"]
            )
        elif metric.load > self.thresholds["high_load_threshold"]:
            self._generate_alert(
                AlertType.SYSTEM_OVERLOAD,
                ThreatLevel.HIGH,
                f"智能体{agent_id}负载较高: {metric.load:.1%}",
                [agent_id],
                ["监控", "准备扩容"]
            )
        
        if metric.success_rate < self.baselines["defense_success_rate"] - self.thresholds["success_rate_drop"]:
            self._generate_alert(
                AlertType.DEFENSE_DEGRADATION,
                ThreatLevel.HIGH,
                f"智能体{agent_id}成功率下降: {metric.success_rate:.1%}",
                [agent_id],
                ["检查配置", "重启服务", "人工介入"]
            )
        
        if metric.response_time > self.baselines["avg_response_time"] * self.thresholds["response_time_degradation"]:
            self._generate_alert(
                AlertType.DEFENSE_DEGRADATION,
                ThreatLevel.ELEVATED,
                f"智能体{agent_id}响应时间增加: {metric.response_time:.0f}ms",
                [agent_id],
                ["检查资源", "优化性能"]
            )
    
    def _generate_alert(
        self,
        alert_type: AlertType,
        severity: ThreatLevel,
        message: str,
        affected_components: List[str],
        recommended_actions: List[str]
    ) -> SituationalAlert:
        """生成告警"""
        self.alert_counter += 1
        alert_id = f"alert_{datetime.now().strftime('%Y%m%d%H%M%S')}_{self.alert_counter}"
        
        alert = SituationalAlert(
            alert_id=alert_id,
            alert_type=alert_type,
            severity=severity,
            message=message,
            timestamp=datetime.now(),
            affected_components=affected_components,
            recommended_actions=recommended_actions
        )
        
        self.active_alerts.append(alert)
        self.stats["total_alerts_generated"] += 1
        
        return alert
    
    def _get_recent_attacks(self, minutes: int = 60) -> List[Dict[str, Any]]:
        """获取最近攻击"""
        cutoff = datetime.now() - timedelta(minutes=minutes)
        return [a for a in self.attack_history if a["timestamp"] > cutoff]
    
    def calculate_threat_level(self) -> ThreatLevel:
        """计算威胁等级"""
        recent_attacks = self._get_recent_attacks(minutes=15)
        
        if not recent_attacks:
            return ThreatLevel.NORMAL
        
        attack_rate = len(recent_attacks) / 15
        
        if attack_rate > self.baselines["attacks_per_minute"] * 3:
            return ThreatLevel.CRITICAL
        elif attack_rate > self.baselines["attacks_per_minute"] * 2:
            return ThreatLevel.HIGH
        elif attack_rate > self.baselines["attacks_per_minute"]:
            return ThreatLevel.ELEVATED
        
        critical_count = sum(1 for a in recent_attacks if a["severity"] == "critical")
        if critical_count > 5:
            return ThreatLevel.HIGH
        elif critical_count > 2:
            return ThreatLevel.ELEVATED
        
        return ThreatLevel.NORMAL
    
    def calculate_attack_intensity(self) -> AttackIntensity:
        """计算攻击强度"""
        recent_attacks = self._get_recent_attacks(minutes=5)
        
        if not recent_attacks:
            return AttackIntensity.LOW
        
        attack_rate = len(recent_attacks) / 5
        
        if attack_rate > self.baselines["attacks_per_minute"] * 5:
            return AttackIntensity.OVERWHELMING
        elif attack_rate > self.baselines["attacks_per_minute"] * 3:
            return AttackIntensity.HIGH
        elif attack_rate > self.baselines["attacks_per_minute"]:
            return AttackIntensity.MEDIUM
        
        return AttackIntensity.LOW
    
    def get_attack_metrics(self) -> List[AttackMetric]:
        """获取攻击指标"""
        recent_attacks = self._get_recent_attacks(minutes=60)
        
        attack_data: Dict[str, Dict] = defaultdict(lambda: {
            "count": 0, "blocked": 0, "severity_sum": 0, "users": set()
        })
        
        severity_values = {"low": 1, "medium": 2, "high": 3, "critical": 4}
        
        for attack in recent_attacks:
            attack_type = attack["attack_type"]
            attack_data[attack_type]["count"] += 1
            if attack["blocked"]:
                attack_data[attack_type]["blocked"] += 1
            attack_data[attack_type]["severity_sum"] += severity_values.get(attack["severity"], 1)
            attack_data[attack_type]["users"].add(attack["user_id"])
        
        metrics = []
        for attack_type, data in attack_data.items():
            success_rate = data["blocked"] / max(1, data["count"])
            avg_severity = data["severity_sum"] / max(1, data["count"])
            
            trend = "stable"
            older_attacks = [a for a in self.attack_history if 
                           datetime.now() - timedelta(hours=2) < a["timestamp"] < datetime.now() - timedelta(hours=1)]
            older_count = sum(1 for a in older_attacks if a["attack_type"] == attack_type)
            
            if data["count"] > older_count * 1.5:
                trend = "increasing"
            elif data["count"] < older_count * 0.7:
                trend = "decreasing"
            
            metrics.append(AttackMetric(
                attack_type=attack_type,
                count=data["count"],
                success_rate=success_rate,
                avg_severity=avg_severity,
                trend=trend,
                affected_users=len(data["users"])
            ))
        
        return sorted(metrics, key=lambda x: x.count, reverse=True)
    
    def get_defense_metrics(self) -> List[DefenseMetric]:
        """获取防御指标"""
        return list(self.defense_status.values())
    
    def identify_risk_zones(self) -> List[RiskZone]:
        """识别风险区域"""
        zones = []
        
        recent_attacks = self._get_recent_attacks(minutes=30)
        
        user_attacks: Dict[str, int] = defaultdict(int)
        for attack in recent_attacks:
            user_attacks[attack["user_id"]] += 1
        
        high_risk_users = [uid for uid, count in user_attacks.items() if count >= 5]
        if high_risk_users:
            zones.append(RiskZone(
                zone_id="high_risk_users",
                zone_type="user_group",
                risk_level=0.8,
                attack_count=sum(user_attacks[uid] for uid in high_risk_users),
                affected_entities=high_risk_users[:10],
                description=f"{len(high_risk_users)}个用户遭受高频攻击"
            ))
        
        attack_type_zones: Dict[str, List[str]] = defaultdict(list)
        for attack in recent_attacks:
            attack_type_zones[attack["attack_type"]].append(attack["session_id"])
        
        for attack_type, sessions in attack_type_zones.items():
            if len(sessions) >= 10:
                zones.append(RiskZone(
                    zone_id=f"attack_type_{attack_type}",
                    zone_type="attack_vector",
                    risk_level=0.7 if len(sessions) >= 20 else 0.5,
                    attack_count=len(sessions),
                    affected_entities=list(set(sessions))[:10],
                    description=f"{attack_type}攻击集中区域"
                ))
        
        self.risk_zones = {z.zone_id: z for z in zones}
        
        return zones
    
    def predict_trends(self) -> Dict[str, Any]:
        """预测趋势"""
        self.stats["predictions_made"] += 1
        
        hourly_attacks: Dict[int, int] = defaultdict(int)
        for attack in self.attack_history:
            hour = attack["timestamp"].hour
            hourly_attacks[hour] += 1
        
        current_hour = datetime.now().hour
        next_hour = (current_hour + 1) % 24
        
        predicted_attacks = hourly_attacks.get(next_hour, 0)
        
        if len(hourly_attacks) >= 3:
            recent_hours = sorted(hourly_attacks.keys())[-3:]
            trend = "increasing" if all(hourly_attacks[h] <= hourly_attacks.get(h + 1, 0) for h in recent_hours[:-1]) else "stable"
        else:
            trend = "unknown"
        
        return {
            "next_hour_predicted_attacks": predicted_attacks,
            "trend": trend,
            "confidence": 0.6 if len(hourly_attacks) >= 3 else 0.3,
            "recommendations": self._generate_prediction_recommendations(predicted_attacks, trend)
        }
    
    def _generate_prediction_recommendations(
        self, 
        predicted_attacks: int, 
        trend: str
    ) -> List[str]:
        """生成预测建议"""
        recommendations = []
        
        if predicted_attacks > self.baselines["attacks_per_minute"] * 60:
            recommendations.append("预计下一小时攻击量较大，建议提前扩容")
        
        if trend == "increasing":
            recommendations.append("攻击呈上升趋势，加强监控")
        
        return recommendations
    
    def generate_report(self) -> SituationalReport:
        """生成报告"""
        threat_level = self.calculate_threat_level()
        attack_intensity = self.calculate_attack_intensity()
        attack_metrics = self.get_attack_metrics()
        defense_metrics = self.get_defense_metrics()
        risk_zones = self.identify_risk_zones()
        predictions = self.predict_trends()
        
        unacknowledged_alerts = [a for a in self.active_alerts if not a.acknowledged][-10:]
        
        recommendations = self._generate_situational_recommendations(
            threat_level, attack_intensity, risk_zones
        )
        
        return SituationalReport(
            report_id=f"report_{datetime.now().strftime('%Y%m%d%H%M%S')}",
            timestamp=datetime.now(),
            threat_level=threat_level,
            attack_intensity=attack_intensity,
            attack_metrics=attack_metrics,
            defense_metrics=defense_metrics,
            risk_zones=risk_zones,
            active_alerts=unacknowledged_alerts,
            predictions=predictions,
            recommendations=recommendations
        )
    
    def _generate_situational_recommendations(
        self,
        threat_level: ThreatLevel,
        attack_intensity: AttackIntensity,
        risk_zones: List[RiskZone]
    ) -> List[str]:
        """生成态势建议"""
        recommendations = []
        
        if threat_level == ThreatLevel.CRITICAL:
            recommendations.append("威胁等级严重，立即启动应急响应")
            recommendations.append("通知安全团队全员待命")
        elif threat_level == ThreatLevel.HIGH:
            recommendations.append("威胁等级较高，加强防御措施")
        elif threat_level == ThreatLevel.ELEVATED:
            recommendations.append("威胁等级上升，保持警惕")
        
        if attack_intensity == AttackIntensity.OVERWHELMING:
            recommendations.append("攻击强度过大，考虑启用备用系统")
        elif attack_intensity == AttackIntensity.HIGH:
            recommendations.append("攻击强度较高，准备扩容")
        
        for zone in risk_zones[:3]:
            recommendations.append(f"关注风险区域: {zone.description}")
        
        return recommendations
    
    def acknowledge_alert(self, alert_id: str) -> bool:
        """确认告警"""
        for alert in self.active_alerts:
            if alert.alert_id == alert_id:
                alert.acknowledged = True
                return True
        return False
    
    def get_active_alerts(self, severity: Optional[ThreatLevel] = None) -> List[SituationalAlert]:
        """获取活跃告警"""
        alerts = [a for a in self.active_alerts if not a.acknowledged]
        
        if severity:
            alerts = [a for a in alerts if a.severity == severity]
        
        return alerts
    
    def adjust_defense_strategy(self, strategy: Dict[str, Any]) -> Dict[str, Any]:
        """调整防御策略"""
        adjustments = []
        
        if strategy.get("increase_monitoring"):
            self.baselines["attacks_per_minute"] *= 0.8
            adjustments.append("降低攻击检测阈值")
        
        if strategy.get("reduce_sensitivity"):
            self.baselines["attacks_per_minute"] *= 1.2
            adjustments.append("提高攻击检测阈值")
        
        if strategy.get("isolate_zone"):
            zone_id = strategy.get("zone_id")
            if zone_id in self.risk_zones:
                adjustments.append(f"隔离风险区域: {zone_id}")
        
        return {
            "status": "adjusted",
            "adjustments": adjustments
        }
    
    def get_stats(self) -> Dict[str, Any]:
        """获取统计信息"""
        return {
            **self.stats,
            "attack_history_size": len(self.attack_history),
            "active_defense_agents": len(self.defense_status),
            "active_alerts": len([a for a in self.active_alerts if not a.acknowledged]),
            "risk_zones": len(self.risk_zones),
        }
