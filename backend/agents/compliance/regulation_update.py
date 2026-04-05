"""
法规更新推送智能体
监测法规变更并推送影响分析
"""
import asyncio
import json
import logging
from datetime import datetime, timedelta
from enum import Enum
from typing import Any, Dict, List, Optional, Set
from uuid import uuid4

from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)


class UpdateType(str, Enum):
    NEW_REGULATION = "new_regulation"
    AMENDMENT = "amendment"
    REPEAL = "repeal"
    INTERPRETATION = "interpretation"
    IMPLEMENTATION_RULE = "implementation_rule"


class ImpactLevel(str, Enum):
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


class RegulationUpdate(BaseModel):
    update_id: str = Field(default_factory=lambda: str(uuid4()))
    update_type: UpdateType
    document_id: str
    document_title: str
    old_version: Optional[Dict[str, Any]] = None
    new_version: Dict[str, Any]
    changes: List[Dict[str, Any]] = Field(default_factory=list)
    detected_at: datetime = Field(default_factory=datetime.now)
    source: str = ""


class ImpactAnalysis(BaseModel):
    analysis_id: str = Field(default_factory=lambda: str(uuid4()))
    update_id: str
    impact_level: ImpactLevel
    affected_areas: List[str] = Field(default_factory=list)
    affected_processes: List[str] = Field(default_factory=list)
    required_actions: List[str] = Field(default_factory=list)
    compliance_deadline: Optional[datetime] = None
    risk_assessment: Dict[str, Any] = Field(default_factory=dict)
    recommendations: List[str] = Field(default_factory=list)
    analyzed_at: datetime = Field(default_factory=datetime.now)


class UpdateSubscription(BaseModel):
    subscription_id: str = Field(default_factory=lambda: str(uuid4()))
    subscriber_id: str
    areas: List[str]
    impact_threshold: ImpactLevel = ImpactLevel.MEDIUM
    notification_channels: List[str] = Field(default_factory=list)
    active: bool = True


class ChangeDetector:
    def __init__(self):
        self.change_patterns = [
            ("增加", "addition"),
            ("修改", "modification"),
            ("删除", "deletion"),
            ("调整", "adjustment"),
            ("废止", "repeal"),
        ]
    
    def detect_changes(
        self,
        old_content: Optional[str],
        new_content: str
    ) -> List[Dict[str, Any]]:
        changes = []
        
        if not old_content:
            changes.append({
                "type": "new_document",
                "description": "新发布法规",
                "significance": "high"
            })
            return changes
        
        old_lines = set(old_content.split('\n'))
        new_lines = set(new_content.split('\n'))
        
        added = new_lines - old_lines
        removed = old_lines - new_lines
        
        for line in added:
            for pattern, change_type in self.change_patterns:
                if pattern in line:
                    changes.append({
                        "type": change_type,
                        "content": line[:200],
                        "significance": "medium"
                    })
                    break
        
        for line in removed:
            if line.strip():
                changes.append({
                    "type": "deletion",
                    "content": line[:200],
                    "significance": "medium"
                })
        
        return changes


class ImpactAnalyzer:
    BUSINESS_AREAS = {
        "real_estate_valuation": ["房地产估价", "不动产评估", "房产价值"],
        "data_collection": ["数据采集", "信息收集", "个人信息"],
        "ai_service": ["人工智能", "算法", "自动化决策"],
        "user_service": ["用户服务", "客户权益", "消费者保护"],
        "transaction": ["交易", "合同", "签约"],
    }
    
    PROCESS_KEYWORDS = {
        "data_processing": ["数据处理", "信息处理", "数据存储"],
        "consent_management": ["授权", "同意", "用户许可"],
        "disclosure": ["披露", "公开", "告知"],
        "security": ["安全", "加密", "保护措施"],
    }
    
    def analyze(
        self,
        update: RegulationUpdate,
        business_context: Optional[Dict[str, Any]] = None
    ) -> ImpactAnalysis:
        affected_areas = self._identify_affected_areas(update)
        affected_processes = self._identify_affected_processes(update)
        impact_level = self._determine_impact_level(update, affected_areas)
        required_actions = self._generate_required_actions(update, affected_areas)
        deadline = self._extract_deadline(update)
        risk_assessment = self._assess_risk(update, affected_areas)
        recommendations = self._generate_recommendations(update, affected_areas)
        
        return ImpactAnalysis(
            update_id=update.update_id,
            impact_level=impact_level,
            affected_areas=affected_areas,
            affected_processes=affected_processes,
            required_actions=required_actions,
            compliance_deadline=deadline,
            risk_assessment=risk_assessment,
            recommendations=recommendations
        )
    
    def _identify_affected_areas(self, update: RegulationUpdate) -> List[str]:
        affected = []
        content = str(update.new_version.get("content", ""))
        
        for area, keywords in self.BUSINESS_AREAS.items():
            for keyword in keywords:
                if keyword in content:
                    affected.append(area)
                    break
        
        return affected
    
    def _identify_affected_processes(self, update: RegulationUpdate) -> List[str]:
        affected = []
        content = str(update.new_version.get("content", ""))
        
        for process, keywords in self.PROCESS_KEYWORDS.items():
            for keyword in keywords:
                if keyword in content:
                    affected.append(process)
                    break
        
        return affected
    
    def _determine_impact_level(
        self,
        update: RegulationUpdate,
        affected_areas: List[str]
    ) -> ImpactLevel:
        if update.update_type == UpdateType.REPEAL:
            return ImpactLevel.HIGH
        
        if len(affected_areas) >= 3:
            return ImpactLevel.HIGH
        
        high_impact_keywords = ["必须", "禁止", "处罚", "责任"]
        content = str(update.new_version.get("content", ""))
        
        for keyword in high_impact_keywords:
            if keyword in content:
                return ImpactLevel.HIGH
        
        if len(affected_areas) >= 1:
            return ImpactLevel.MEDIUM
        
        return ImpactLevel.LOW
    
    def _generate_required_actions(
        self,
        update: RegulationUpdate,
        affected_areas: List[str]
    ) -> List[str]:
        actions = []
        
        if update.update_type == UpdateType.NEW_REGULATION:
            actions.append("学习新法规内容")
            actions.append("评估对现有业务的影响")
            actions.append("制定合规实施方案")
        
        elif update.update_type == UpdateType.AMENDMENT:
            actions.append("对比新旧版本差异")
            actions.append("更新内部合规流程")
            actions.append("培训相关人员")
        
        elif update.update_type == UpdateType.REPEAL:
            actions.append("停止执行相关条款")
            actions.append("清理相关内部规定")
        
        for area in affected_areas:
            actions.append(f"检查{area}相关流程的合规性")
        
        return list(set(actions))
    
    def _extract_deadline(self, update: RegulationUpdate) -> Optional[datetime]:
        new_version = update.new_version
        
        if "effective_date" in new_version:
            return new_version["effective_date"]
        
        return None
    
    def _assess_risk(
        self,
        update: RegulationUpdate,
        affected_areas: List[str]
    ) -> Dict[str, Any]:
        risk_score = 0.0
        risk_factors = []
        
        content = str(update.new_version.get("content", ""))
        
        if "处罚" in content or "罚款" in content:
            risk_score += 0.3
            risk_factors.append("包含处罚条款")
        
        if "刑事责任" in content:
            risk_score += 0.4
            risk_factors.append("涉及刑事责任")
        
        if len(affected_areas) >= 3:
            risk_score += 0.2
            risk_factors.append("影响多个业务领域")
        
        return {
            "score": min(1.0, risk_score),
            "factors": risk_factors,
            "mitigation_priority": "high" if risk_score > 0.5 else "medium" if risk_score > 0.2 else "low"
        }
    
    def _generate_recommendations(
        self,
        update: RegulationUpdate,
        affected_areas: List[str]
    ) -> List[str]:
        recommendations = []
        
        if update.update_type in [UpdateType.NEW_REGULATION, UpdateType.AMENDMENT]:
            recommendations.append("建议组织法规培训")
            recommendations.append("建议进行合规差距分析")
        
        if "data_processing" in update.new_version.get("affected_processes", []):
            recommendations.append("建议审查数据处理流程")
        
        if "个人信息" in str(update.new_version.get("content", "")):
            recommendations.append("建议更新隐私政策")
        
        return recommendations


class RegulationUpdateAgent:
    def __init__(
        self,
        agent_id: str,
        name: str = "RegulationUpdate",
        regulation_collector: Optional[Any] = None,
        notification_service: Optional[Any] = None
    ):
        self.agent_id = agent_id
        self.name = name
        self.regulation_collector = regulation_collector
        self.notification_service = notification_service
        
        self.change_detector = ChangeDetector()
        self.impact_analyzer = ImpactAnalyzer()
        
        self.updates: Dict[str, RegulationUpdate] = {}
        self.impact_analyses: Dict[str, ImpactAnalysis] = {}
        self.subscriptions: Dict[str, UpdateSubscription] = {}
        
        self.check_interval = timedelta(hours=6)
        self._running = False
        
        self.logger = logging.getLogger(f"{__name__}.{agent_id}")
    
    async def initialize(self):
        self.logger.info(f"RegulationUpdateAgent {self.agent_id} initialized")
    
    async def process_update(
        self,
        old_document: Optional[Dict[str, Any]],
        new_document: Dict[str, Any]
    ) -> Tuple[RegulationUpdate, ImpactAnalysis]:
        update_type = self._determine_update_type(old_document, new_document)
        
        old_content = old_document.get("content") if old_document else None
        
        changes = self.change_detector.detect_changes(
            old_content,
            new_document.get("content", "")
        )
        
        update = RegulationUpdate(
            update_type=update_type,
            document_id=new_document.get("id", ""),
            document_title=new_document.get("title", ""),
            old_version=old_document,
            new_version=new_document,
            changes=changes,
            source=new_document.get("source", "")
        )
        
        self.updates[update.update_id] = update
        
        analysis = self.impact_analyzer.analyze(update)
        self.impact_analyses[update.update_id] = analysis
        
        await self._notify_subscribers(update, analysis)
        
        return update, analysis
    
    def _determine_update_type(
        self,
        old_document: Optional[Dict[str, Any]],
        new_document: Dict[str, Any]
    ) -> UpdateType:
        if not old_document:
            return UpdateType.NEW_REGULATION
        
        if new_document.get("status") == "repealed":
            return UpdateType.REPEAL
        
        if old_document.get("version", 1) < new_document.get("version", 1):
            return UpdateType.AMENDMENT
        
        return UpdateType.AMENDMENT
    
    async def _notify_subscribers(
        self,
        update: RegulationUpdate,
        analysis: ImpactAnalysis
    ):
        if not self.notification_service:
            return
        
        for subscription in self.subscriptions.values():
            if not subscription.active:
                continue
            
            if analysis.impact_level.value < subscription.impact_threshold.value:
                continue
            
            area_match = False
            for area in subscription.areas:
                if area in analysis.affected_areas:
                    area_match = True
                    break
            
            if not area_match and subscription.areas:
                continue
            
            notification = {
                "subscriber_id": subscription.subscriber_id,
                "update": update.dict(),
                "analysis": analysis.dict(),
                "channels": subscription.notification_channels
            }
            
            await self.notification_service.notify(notification)
    
    def subscribe(
        self,
        subscriber_id: str,
        areas: List[str],
        impact_threshold: ImpactLevel = ImpactLevel.MEDIUM,
        channels: Optional[List[str]] = None
    ) -> str:
        subscription = UpdateSubscription(
            subscriber_id=subscriber_id,
            areas=areas,
            impact_threshold=impact_threshold,
            notification_channels=channels or ["email", "dashboard"]
        )
        
        self.subscriptions[subscription.subscription_id] = subscription
        
        return subscription.subscription_id
    
    def unsubscribe(self, subscription_id: str) -> bool:
        if subscription_id in self.subscriptions:
            del self.subscriptions[subscription_id]
            return True
        return False
    
    async def get_updates(
        self,
        area: Optional[str] = None,
        impact_level: Optional[ImpactLevel] = None,
        limit: int = 20
    ) -> List[Dict[str, Any]]:
        results = []
        
        for update in self.updates.values():
            analysis = self.impact_analyses.get(update.update_id)
            
            if area and analysis:
                if area not in analysis.affected_areas:
                    continue
            
            if impact_level and analysis:
                if analysis.impact_level != impact_level:
                    continue
            
            results.append({
                "update": update.dict(),
                "analysis": analysis.dict() if analysis else None
            })
        
        results.sort(key=lambda x: x["update"]["detected_at"], reverse=True)
        
        return results[:limit]
    
    async def get_impact_analysis(self, update_id: str) -> Optional[ImpactAnalysis]:
        return self.impact_analyses.get(update_id)
    
    async def start_monitoring(self):
        self._running = True
        asyncio.create_task(self._monitoring_loop())
    
    async def stop_monitoring(self):
        self._running = False
    
    async def _monitoring_loop(self):
        while self._running:
            try:
                if self.regulation_collector:
                    updates = await self.regulation_collector.check_updates()
                    
                    for update in updates:
                        self.logger.info(f"Processing regulation update: {update}")
                
                await asyncio.sleep(self.check_interval.total_seconds())
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                self.logger.error(f"Error in monitoring loop: {e}")
                await asyncio.sleep(1800)
    
    def get_statistics(self) -> Dict[str, Any]:
        by_type = {}
        for update in self.updates.values():
            update_type = update.update_type.value
            by_type[update_type] = by_type.get(update_type, 0) + 1
        
        by_impact = {}
        for analysis in self.impact_analyses.values():
            impact = analysis.impact_level.value
            by_impact[impact] = by_impact.get(impact, 0) + 1
        
        return {
            "total_updates": len(self.updates),
            "total_analyses": len(self.impact_analyses),
            "active_subscriptions": len([s for s in self.subscriptions.values() if s.active]),
            "updates_by_type": by_type,
            "updates_by_impact": by_impact
        }
