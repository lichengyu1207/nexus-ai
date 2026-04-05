"""
法律法规动态追踪智能体
Law Tracking Agent

负责自动追踪与业务相关的法律法规更新，并通知相关智能体。
"""

import asyncio
import json
import logging
import hashlib
import uuid
import re
from typing import Dict, Any, Optional, List
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from collections import defaultdict
from enum import Enum

logger = logging.getLogger(__name__)


class LawCategory(Enum):
    PERSONAL_INFO = "personal_info"
    DATA_SECURITY = "data_security"
    CONSUMER_PROTECTION = "consumer_protection"
    INDUSTRY_SPECIFIC = "industry_specific"
    NETWORK_SECURITY = "network_security"


class ImpactLevel(Enum):
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


@dataclass
class LawUpdate:
    update_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    timestamp: str = field(default_factory=lambda: datetime.utcnow().isoformat())
    law_name: str = ""
    category: str = ""
    source: str = ""
    publish_date: str = ""
    effective_date: str = ""
    summary: str = ""
    key_requirements: List[str] = field(default_factory=list)
    impact_level: str = ImpactLevel.MEDIUM.value
    affected_business_processes: List[str] = field(default_factory=list)
    affected_policies: List[str] = field(default_factory=list)
    notification_sent: bool = False


@dataclass
class LawSource:
    name: str
    url: str
    source_type: str
    check_frequency: int
    last_check: str = ""
    api_key: str = ""


class LawTrackingAgent:
    """
    法律法规动态追踪智能体
    
    功能：
    1. 跟踪范围：个保法、数据安全法、消费者权益保护、行业特定法规
    2. 采集来源：国家法律法规数据库、监管机构官方、专业法律数据库API
    3. 解析与更新：调用大模型解析核心要求，与现有规则比对
    4. 影响分析：评估新法规对业务的影响程度
    5. 通知机制：通过合规中台推送法规更新
    """
    
    def __init__(self, config: Optional[Dict] = None):
        self.name = "LawTrackingAgent"
        self.description = "自动追踪与业务相关的法律法规更新"
        self.config = config or {}
        
        self.law_updates: List[LawUpdate] = []
        self.sources: List[LawSource] = []
        self.tracked_laws: Dict[str, Dict] = {}
        
        self._init_sources()
        self._init_tracked_laws()
        
        self.stats = {
            "total_updates": 0,
            "updates_by_category": defaultdict(int),
            "notifications_sent": 0,
            "last_check_time": "",
        }
        
        self._initialized = False
    
    def _init_sources(self):
        self.sources = [
            LawSource(
                name="国家法律法规数据库",
                url="https://flk.npc.gov.cn",
                source_type="official",
                check_frequency=86400,
            ),
            LawSource(
                name="网信办",
                url="http://www.cac.gov.cn",
                source_type="official",
                check_frequency=86400,
            ),
            LawSource(
                name="住建部",
                url="https://www.mohurd.gov.cn",
                source_type="official",
                check_frequency=86400,
            ),
            LawSource(
                name="威科先行",
                url="https://law.wkinfo.com.cn",
                source_type="commercial",
                check_frequency=3600,
            ),
        ]
    
    def _init_tracked_laws(self):
        self.tracked_laws = {
            "个人信息保护法": {
                "category": LawCategory.PERSONAL_INFO.value,
                "effective_date": "2021-11-01",
                "key_requirements": [
                    "处理个人信息应当遵循合法、正当、必要原则",
                    "应当取得个人同意",
                    "应当公开个人信息处理规则",
                    "应当保障个人信息安全",
                ],
            },
            "数据安全法": {
                "category": LawCategory.DATA_SECURITY.value,
                "effective_date": "2021-09-01",
                "key_requirements": [
                    "应当建立健全全流程数据安全管理制度",
                    "应当组织开展数据安全教育培训",
                    "应当采取相应技术措施保障数据安全",
                    "应当加强风险监测和应急处置",
                ],
            },
            "网络安全法": {
                "category": LawCategory.NETWORK_SECURITY.value,
                "effective_date": "2017-06-01",
                "key_requirements": [
                    "网络运营者应当保障网络安全稳定运行",
                    "应当制定网络安全事件应急预案",
                    "应当留存网络日志不少于六个月",
                    "应当对用户信息严格保密",
                ],
            },
            "房地产经纪管理办法": {
                "category": LawCategory.INDUSTRY_SPECIFIC.value,
                "effective_date": "2011-04-01",
                "key_requirements": [
                    "房地产经纪机构应当公示服务项目和服务标准",
                    "不得赚取差价",
                    "不得隐瞒真实信息",
                    "应当建立业务记录制度",
                ],
            },
            "消费者权益保护法": {
                "category": LawCategory.CONSUMER_PROTECTION.value,
                "effective_date": "2014-03-15",
                "key_requirements": [
                    "经营者应当保障消费者知情权",
                    "不得作虚假或者引人误解的宣传",
                    "收集消费者个人信息应当明示目的",
                    "应当保障消费者个人信息安全",
                ],
            },
        }
    
    async def initialize(self):
        if not self._initialized:
            await self._setup()
            self._initialized = True
            logger.info(f"Agent '{self.name}' initialized")
    
    async def _setup(self):
        asyncio.create_task(self._periodic_check())
    
    async def _periodic_check(self):
        while True:
            await asyncio.sleep(3600)
            await self.check_all_sources()
    
    async def check_all_sources(self) -> List[LawUpdate]:
        new_updates = []
        
        for source in self.sources:
            try:
                updates = await self._check_source(source)
                new_updates.extend(updates)
                source.last_check = datetime.utcnow().isoformat()
            except Exception as e:
                logger.error(f"Failed to check source {source.name}: {e}")
        
        self.stats["last_check_time"] = datetime.utcnow().isoformat()
        return new_updates
    
    async def _check_source(self, source: LawSource) -> List[LawUpdate]:
        updates = []
        
        return updates
    
    async def parse_law_update(
        self,
        law_name: str,
        law_content: str,
        source: str,
        publish_date: str,
        effective_date: Optional[str] = None,
    ) -> LawUpdate:
        key_requirements = await self._extract_requirements(law_content)
        
        impact_analysis = await self._analyze_impact(law_name, key_requirements)
        
        update = LawUpdate(
            law_name=law_name,
            category=self._categorize_law(law_name),
            source=source,
            publish_date=publish_date,
            effective_date=effective_date or publish_date,
            summary=law_content[:500],
            key_requirements=key_requirements,
            impact_level=impact_analysis["impact_level"],
            affected_business_processes=impact_analysis["affected_processes"],
            affected_policies=impact_analysis["affected_policies"],
        )
        
        self.law_updates.append(update)
        self.stats["total_updates"] += 1
        self.stats["updates_by_category"][update.category] += 1
        
        return update
    
    async def _extract_requirements(self, content: str) -> List[str]:
        requirements = []
        
        patterns = [
            r"应当([^，。！？]+)",
            r"必须([^，。！？]+)",
            r"不得([^，。！？]+)",
            r"需要([^，。！？]+)",
        ]
        
        for pattern in patterns:
            matches = re.findall(pattern, content)
            requirements.extend(matches[:5])
        
        return requirements[:10]
    
    def _categorize_law(self, law_name: str) -> str:
        if any(kw in law_name for kw in ["个人信息", "隐私", "数据保护"]):
            return LawCategory.PERSONAL_INFO.value
        elif any(kw in law_name for kw in ["数据安全", "网络安全", "信息安全"]):
            return LawCategory.DATA_SECURITY.value
        elif any(kw in law_name for kw in ["消费者", "用户权益"]):
            return LawCategory.CONSUMER_PROTECTION.value
        elif any(kw in law_name for kw in ["房地产", "经纪", "住房"]):
            return LawCategory.INDUSTRY_SPECIFIC.value
        else:
            return LawCategory.NETWORK_SECURITY.value
    
    async def _analyze_impact(
        self,
        law_name: str,
        requirements: List[str],
    ) -> Dict:
        impact_level = ImpactLevel.MEDIUM.value
        affected_processes = []
        affected_policies = []
        
        high_impact_keywords = ["个人信息", "数据出境", "安全评估", "用户同意"]
        for req in requirements:
            if any(kw in req for kw in high_impact_keywords):
                impact_level = ImpactLevel.HIGH.value
                break
        
        if "个人信息" in law_name or "隐私" in law_name:
            affected_processes.extend([
                "用户注册流程",
                "数据采集流程",
                "数据存储流程",
                "数据共享流程",
            ])
            affected_policies.extend([
                "隐私政策",
                "用户协议",
                "数据处理协议",
            ])
        
        if "数据安全" in law_name or "网络安全" in law_name:
            affected_processes.extend([
                "系统访问控制",
                "数据加密存储",
                "日志审计",
                "应急响应",
            ])
            affected_policies.extend([
                "数据安全管理制度",
                "网络安全应急预案",
            ])
        
        return {
            "impact_level": impact_level,
            "affected_processes": list(set(affected_processes)),
            "affected_policies": list(set(affected_policies)),
        }
    
    async def compare_with_existing_rules(
        self,
        update: LawUpdate,
    ) -> Dict:
        existing_law = self.tracked_laws.get(update.law_name)
        
        if not existing_law:
            return {
                "is_new": True,
                "changes": [],
                "recommendation": "新增法规，需要全面评估合规状态",
            }
        
        existing_reqs = set(existing_law.get("key_requirements", []))
        new_reqs = set(update.key_requirements)
        
        added_reqs = new_reqs - existing_reqs
        removed_reqs = existing_reqs - new_reqs
        
        return {
            "is_new": False,
            "changes": {
                "added_requirements": list(added_reqs),
                "removed_requirements": list(removed_reqs),
            },
            "recommendation": f"法规更新，新增{len(added_reqs)}项要求，移除{len(removed_reqs)}项要求",
        }
    
    async def send_notification(
        self,
        update: LawUpdate,
        recipients: List[str],
    ) -> bool:
        notification = {
            "type": "law_update",
            "update_id": update.update_id,
            "law_name": update.law_name,
            "impact_level": update.impact_level,
            "summary": update.summary[:200],
            "affected_processes": update.affected_business_processes,
            "affected_policies": update.affected_policies,
            "recipients": recipients,
            "sent_at": datetime.utcnow().isoformat(),
        }
        
        logger.info(f"Sending law update notification: {notification}")
        
        update.notification_sent = True
        self.stats["notifications_sent"] += 1
        
        return True
    
    async def get_recent_updates(
        self,
        days: int = 30,
        category: Optional[str] = None,
    ) -> List[Dict]:
        cutoff = (datetime.utcnow() - timedelta(days=days)).isoformat()
        
        filtered = [
            u for u in self.law_updates
            if u.timestamp > cutoff
        ]
        
        if category:
            filtered = [u for u in filtered if u.category == category]
        
        return [
            {
                "update_id": u.update_id,
                "law_name": u.law_name,
                "category": u.category,
                "impact_level": u.impact_level,
                "effective_date": u.effective_date,
                "summary": u.summary[:200],
                "notification_sent": u.notification_sent,
            }
            for u in filtered
        ]
    
    async def get_tracked_laws_summary(self) -> List[Dict]:
        return [
            {
                "name": name,
                "category": info["category"],
                "effective_date": info["effective_date"],
                "key_requirements_count": len(info["key_requirements"]),
            }
            for name, info in self.tracked_laws.items()
        ]
    
    async def get_stats(self) -> Dict:
        return {
            "name": self.name,
            "total_updates": self.stats["total_updates"],
            "updates_by_category": dict(self.stats["updates_by_category"]),
            "notifications_sent": self.stats["notifications_sent"],
            "last_check_time": self.stats["last_check_time"],
            "tracked_laws_count": len(self.tracked_laws),
        }
