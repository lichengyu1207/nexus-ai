"""
仵作智能体 CoronerAgent
负责攻击事后分析和特征存储

功能：
- 攻击结束后分析日志，提取攻击特征
- 生成攻击报告，存入海马体
- 更新判官智能体的经验池
"""

import json
import time
import uuid
import asyncio
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, field
from enum import Enum

from .patrol_agent import AttackType, TrafficFeatures
from .judge_agent import SecurityAction, SecurityDecision, SecurityExperience


@dataclass
class AttackReport:
    """攻击报告"""
    report_id: str
    timestamp: float
    
    attack_type: AttackType
    start_time: float
    end_time: float
    duration: float
    
    source_ips: List[str]
    target_urls: List[str]
    
    feature_vector: np.ndarray
    feature_summary: Dict
    
    actions_taken: List[Dict]
    effectiveness_score: float
    
    damage_assessment: Dict
    recommendations: List[str]
    
    def to_dict(self) -> Dict:
        return {
            "report_id": self.report_id,
            "timestamp": self.timestamp,
            "attack_type": self.attack_type.value,
            "start_time": self.start_time,
            "end_time": self.end_time,
            "duration": self.duration,
            "source_ips": self.source_ips,
            "target_urls": self.target_urls,
            "feature_summary": self.feature_summary,
            "actions_taken": self.actions_taken,
            "effectiveness_score": self.effectiveness_score,
            "damage_assessment": self.damage_assessment,
            "recommendations": self.recommendations
        }


@dataclass
class AttackPattern:
    """攻击模式"""
    pattern_id: str
    attack_type: AttackType
    feature_signature: np.ndarray
    common_ips: List[str]
    common_urls: List[str]
    typical_duration: float
    severity_range: Tuple[float, float]
    occurrence_count: int
    last_seen: float
    
    def to_dict(self) -> Dict:
        return {
            "pattern_id": self.pattern_id,
            "attack_type": self.attack_type.value,
            "feature_signature": self.feature_signature.tolist(),
            "common_ips": self.common_ips,
            "common_urls": self.common_urls,
            "typical_duration": self.typical_duration,
            "severity_range": self.severity_range,
            "occurrence_count": self.occurrence_count,
            "last_seen": self.last_seen
        }


class CoronerAgent:
    """仵作智能体"""
    
    def __init__(self, agent_id: str = "coroner_001"):
        self.agent_id = agent_id
        
        self._attack_reports: List[AttackReport] = []
        self._attack_patterns: Dict[str, AttackPattern] = {}
        
        self._pending_analyses: Dict[str, Dict] = {}
        
        self._running = False
        self._analysis_task: Optional[asyncio.Task] = None
    
    async def analyze_attack(
        self,
        attack_id: str,
        start_time: float,
        end_time: float,
        features: List[TrafficFeatures],
        decisions: List[SecurityDecision],
        execution_records: List[Dict]
    ) -> AttackReport:
        """分析攻击"""
        if not features:
            raise ValueError("没有特征数据")
        
        avg_features = self._average_features(features)
        
        attack_type = self._classify_attack(avg_features)
        
        source_ips = set()
        target_urls = set()
        for feature in features:
            pass
        
        for decision in decisions:
            source_ips.update(decision.target_ips)
        
        effectiveness = self._calculate_effectiveness(decisions, execution_records)
        
        damage = self._assess_damage(features, decisions)
        
        recommendations = self._generate_recommendations(attack_type, effectiveness, damage)
        
        report = AttackReport(
            report_id=str(uuid.uuid4()),
            timestamp=time.time(),
            attack_type=attack_type,
            start_time=start_time,
            end_time=end_time,
            duration=end_time - start_time,
            source_ips=list(source_ips)[:100],
            target_urls=list(target_urls)[:50],
            feature_vector=avg_features.to_vector(),
            feature_summary=avg_features.to_dict(),
            actions_taken=[{
                "action": d.action.name,
                "confidence": d.confidence,
                "targets": d.target_ips[:5]
            } for d in decisions],
            effectiveness_score=effectiveness,
            damage_assessment=damage,
            recommendations=recommendations
        )
        
        self._attack_reports.append(report)
        
        await self._store_attack_pattern(report)
        
        await self._update_experience_pool(report, decisions)
        
        return report
    
    def _average_features(self, features: List[TrafficFeatures]) -> TrafficFeatures:
        """计算平均特征"""
        if not features:
            return TrafficFeatures()
        
        avg = TrafficFeatures()
        
        fields = [
            'ip_request_rate', 'unique_ips', 'unique_urls', 'unique_uas',
            'get_ratio', 'post_ratio', 'status_2xx_ratio', 'status_4xx_ratio',
            'status_5xx_ratio', 'avg_packet_size', 'max_packet_size',
            'tcp_connections', 'geo_diversity', 'session_duration_avg',
            'request_interval_avg', 'request_interval_std', 'url_entropy',
            'ua_entropy', 'error_rate', 'retry_rate'
        ]
        
        for field in fields:
            values = [getattr(f, field) for f in features]
            setattr(avg, field, np.mean(values))
        
        return avg
    
    def _classify_attack(self, features: TrafficFeatures) -> AttackType:
        """分类攻击类型"""
        if features.ip_request_rate > 1000:
            return AttackType.DDOS
        elif features.ip_request_rate > 100 and features.request_interval_std < 0.1:
            return AttackType.CC
        elif features.error_rate > 0.3:
            return AttackType.SQL_INJECTION
        elif features.status_4xx_ratio > 0.5:
            return AttackType.BRUTE_FORCE
        elif features.url_entropy > 7.0:
            return AttackType.CRAWLER
        else:
            return AttackType.UNKNOWN
    
    def _calculate_effectiveness(
        self,
        decisions: List[SecurityDecision],
        execution_records: List[Dict]
    ) -> float:
        """计算防御效果评分"""
        if not decisions:
            return 0.0
        
        score = 0.0
        
        blocked_count = sum(1 for r in execution_records if r.get("action") == "BLOCK_IP" and r.get("success"))
        score += min(blocked_count * 5, 50)
        
        for decision in decisions:
            if decision.action == SecurityAction.BLOCK_IP:
                score += 10 * decision.confidence
            elif decision.action == SecurityAction.RATE_LIMIT:
                score += 5 * decision.confidence
            elif decision.action == SecurityAction.CAPTCHA:
                score += 3 * decision.confidence
        
        success_rate = sum(1 for r in execution_records if r.get("success")) / len(execution_records) if execution_records else 0
        score *= success_rate
        
        return min(score, 100)
    
    def _assess_damage(
        self,
        features: List[TrafficFeatures],
        decisions: List[SecurityDecision]
    ) -> Dict:
        """评估损害"""
        if not features:
            return {"level": "unknown", "details": {}}
        
        avg_features = self._average_features(features)
        
        damage = {
            "level": "low",
            "details": {
                "peak_request_rate": max(f.ip_request_rate for f in features),
                "avg_error_rate": avg_features.error_rate,
                "affected_ips": avg_features.unique_ips,
                "duration": features[-1].timestamp - features[0].timestamp if len(features) > 1 else 0
            }
        }
        
        if avg_features.ip_request_rate > 1000 or avg_features.error_rate > 0.5:
            damage["level"] = "critical"
        elif avg_features.ip_request_rate > 500 or avg_features.error_rate > 0.3:
            damage["level"] = "high"
        elif avg_features.ip_request_rate > 100 or avg_features.error_rate > 0.1:
            damage["level"] = "medium"
        
        return damage
    
    def _generate_recommendations(
        self,
        attack_type: AttackType,
        effectiveness: float,
        damage: Dict
    ) -> List[str]:
        """生成建议"""
        recommendations = []
        
        if effectiveness < 50:
            recommendations.append("建议优化防御策略，提高响应速度")
        
        if attack_type == AttackType.DDOS:
            recommendations.append("建议启用高防服务")
            recommendations.append("建议配置更严格的限速规则")
        elif attack_type == AttackType.CC:
            recommendations.append("建议增加验证码验证")
            recommendations.append("建议启用JS挑战")
        elif attack_type == AttackType.SQL_INJECTION:
            recommendations.append("建议加强输入过滤")
            recommendations.append("建议启用WAF规则")
        elif attack_type == AttackType.BRUTE_FORCE:
            recommendations.append("建议增加登录失败锁定时间")
            recommendations.append("建议启用双因素认证")
        
        if damage["level"] in ["high", "critical"]:
            recommendations.append("建议进行安全审计")
            recommendations.append("建议检查系统漏洞")
        
        return recommendations
    
    async def _store_attack_pattern(self, report: AttackReport):
        """存储攻击模式到海马体"""
        try:
            from ..hippocampus import hippocampus_service
            
            await hippocampus_service.store_memory(
                content=json.dumps(report.to_dict()),
                memory_type="attack_pattern",
                embedding=report.feature_vector.tolist(),
                metadata={
                    "attack_type": report.attack_type.value,
                    "effectiveness": report.effectiveness_score,
                    "duration": report.duration,
                    "source_ips_count": len(report.source_ips)
                }
            )
        except Exception as e:
            print(f"存储攻击模式失败: {e}")
    
    async def _update_experience_pool(
        self,
        report: AttackReport,
        decisions: List[SecurityDecision]
    ):
        """更新判官智能体的经验池"""
        try:
            from .judge_agent import judge_agent
            
            for i, decision in enumerate(decisions):
                reward = self._calculate_reward(report, decision)
                
                experience = SecurityExperience(
                    state=report.feature_vector,
                    action=decision.action.value,
                    reward=reward,
                    next_state=np.zeros_like(report.feature_vector),
                    done=True,
                    info={
                        "report_id": report.report_id,
                        "attack_type": report.attack_type.value
                    }
                )
                
                judge_agent.rl_agent.buffer.push(experience)
            
        except Exception as e:
            print(f"更新经验池失败: {e}")
    
    def _calculate_reward(self, report: AttackReport, decision: SecurityDecision) -> float:
        """计算奖励"""
        reward = 0.0
        
        if report.effectiveness_score > 80:
            reward += 10.0
        elif report.effectiveness_score > 50:
            reward += 5.0
        else:
            reward -= 5.0
        
        if report.damage_assessment["level"] == "critical":
            reward -= 20.0
        elif report.damage_assessment["level"] == "high":
            reward -= 10.0
        
        if decision.confidence > 0.8:
            reward += 5.0
        
        return reward
    
    async def run_periodic_analysis(self):
        """定期分析任务"""
        while self._running:
            try:
                for attack_id, data in list(self._pending_analyses.items()):
                    if time.time() - data.get("last_activity", 0) > 300:
                        report = await self.analyze_attack(
                            attack_id=attack_id,
                            start_time=data["start_time"],
                            end_time=time.time(),
                            features=data.get("features", []),
                            decisions=data.get("decisions", []),
                            execution_records=data.get("executions", [])
                        )
                        
                        del self._pending_analyses[attack_id]
                
                await asyncio.sleep(60)
            except Exception as e:
                print(f"定期分析错误: {e}")
                await asyncio.sleep(10)
    
    def start_analysis(self, attack_id: str, initial_data: Dict = None):
        """开始分析"""
        self._pending_analyses[attack_id] = {
            "start_time": time.time(),
            "last_activity": time.time(),
            "features": [],
            "decisions": [],
            "executions": [],
            **(initial_data or {})
        }
    
    def update_analysis(self, attack_id: str, data: Dict):
        """更新分析数据"""
        if attack_id in self._pending_analyses:
            self._pending_analyses[attack_id].update(data)
            self._pending_analyses[attack_id]["last_activity"] = time.time()
    
    def start(self):
        """启动"""
        self._running = True
        self._analysis_task = asyncio.create_task(self.run_periodic_analysis())
    
    def stop(self):
        """停止"""
        self._running = False
        if self._analysis_task:
            self._analysis_task.cancel()
    
    def get_status(self) -> Dict:
        """获取状态"""
        return {
            "agent_id": self.agent_id,
            "running": self._running,
            "reports_count": len(self._attack_reports),
            "patterns_count": len(self._attack_patterns),
            "pending_analyses": len(self._pending_analyses)
        }
    
    def get_recent_reports(self, limit: int = 20) -> List[Dict]:
        """获取最近报告"""
        return [r.to_dict() for r in self._attack_reports[-limit:]]


coroner_agent = CoronerAgent()
