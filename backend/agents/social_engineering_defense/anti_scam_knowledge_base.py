"""
防骗知识库智能体
负责构建和维护防骗知识库
"""
import asyncio
from collections import defaultdict
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional


class ScamCategory(Enum):
    """诈骗类型"""
    IMPERSONATION = "impersonation"
    INVESTMENT_FRAUD = "investment_fraud"
    ROMANCE_SCAM = "romance_scam"
    PHISHING = "phishing"
    TECH_SUPPORT = "tech_support"
    LOTTERY_SCAM = "lottery_scam"
    EMERGENCY_SCAM = "emergency_scam"
    JOB_SCAM = "job_scam"
    REAL_ESTATE_FRAUD = "real_estate_fraud"
    OTHER = "other"


class VictimGroup(Enum):
    """受害者群体"""
    ELDERLY = "elderly"
    STUDENTS = "students"
    INVESTORS = "investors"
    JOB_SEEKERS = "job_seekers"
    PROPERTY_OWNERS = "property_owners"
    GENERAL = "general"


class AttackChannel(Enum):
    """攻击渠道"""
    PHONE = "phone"
    SMS = "sms"
    EMAIL = "email"
    SOCIAL_MEDIA = "social_media"
    MESSAGING_APP = "messaging_app"
    WEBSITE = "website"
    IN_PERSON = "in_person"


@dataclass
class ScamCase:
    """诈骗案例"""
    case_id: str
    title: str
    category: ScamCategory
    description: str
    attack_vectors: List[str]
    warning_signs: List[str]
    prevention_tips: List[str]
    victim_groups: List[VictimGroup]
    channels: List[AttackChannel]
    severity: str
    reported_count: int
    created_at: datetime
    updated_at: datetime
    tags: List[str] = field(default_factory=list)
    related_cases: List[str] = field(default_factory=list)


@dataclass
class KnowledgeEntry:
    """知识条目"""
    entry_id: str
    title: str
    content: str
    category: ScamCategory
    keywords: List[str]
    source: str
    confidence: float
    created_at: datetime


class AntiScamKnowledgeBaseAgent:
    """防骗知识库智能体"""
    
    def __init__(self, config: Optional[Dict] = None):
        self.name = "AntiScamKnowledgeBaseAgent"
        self.config = config or {}
        self.cases: Dict[str, ScamCase] = {}
        self.entries: Dict[str, KnowledgeEntry] = {}
        self.category_index: Dict[ScamCategory, List[str]] = defaultdict(list)
        self.keyword_index: Dict[str, List[str]] = defaultdict(list)
        self.victim_index: Dict[VictimGroup, List[str]] = defaultdict(list)
        self.case_counter = 0
        self.stats = {
            "total_cases": 0,
            "total_entries": 0,
            "queries_processed": 0,
            "cases_by_category": defaultdict(int),
            "most_queried_categories": defaultdict(int),
        }
        
        self._init_default_cases()
    
    def _init_default_cases(self):
        """初始化默认案例"""
        default_cases = [
            {
                "title": "冒充公检法诈骗",
                "category": ScamCategory.IMPERSONATION,
                "description": "诈骗分子冒充公安机关、检察院、法院工作人员，以涉嫌犯罪为由，要求受害人转账到'安全账户'。",
                "attack_vectors": ["电话冒充", "伪造证件", "制造恐慌"],
                "warning_signs": ["要求转账到安全账户", "声称涉嫌犯罪", "禁止与他人联系"],
                "prevention_tips": ["公检法不会电话办案", "不存在安全账户", "遇到可疑情况拨打110"],
                "victim_groups": [VictimGroup.ELDERLY, VictimGroup.GENERAL],
                "channels": [AttackChannel.PHONE],
                "severity": "high",
                "tags": ["公检法", "电话诈骗", "安全账户"]
            },
            {
                "title": "房产投资诈骗",
                "category": ScamCategory.REAL_ESTATE_FRAUD,
                "description": "诈骗分子以高回报房产投资为诱饵，诱导受害人投资不存在的房产项目。",
                "attack_vectors": ["虚假项目", "高额回报承诺", "伪造合同"],
                "warning_signs": ["承诺超高回报", "要求快速决定", "无法实地考察"],
                "prevention_tips": ["核实房产真实性", "查看开发商资质", "不要轻信口头承诺"],
                "victim_groups": [VictimGroup.INVESTORS, VictimGroup.PROPERTY_OWNERS],
                "channels": [AttackChannel.PHONE, AttackChannel.WEBSITE, AttackChannel.SOCIAL_MEDIA],
                "severity": "high",
                "tags": ["房产投资", "高回报", "虚假项目"]
            },
            {
                "title": "情感诈骗（杀猪盘）",
                "category": ScamCategory.ROMANCE_SCAM,
                "description": "诈骗分子通过网络交友建立感情，然后以各种理由诱导受害人转账。",
                "attack_vectors": ["建立感情", "虚构身份", "投资诱导"],
                "warning_signs": ["快速建立亲密关系", "推荐投资平台", "拒绝视频见面"],
                "prevention_tips": ["警惕网络交友", "不要轻易转账", "核实对方身份"],
                "victim_groups": [VictimGroup.GENERAL],
                "channels": [AttackChannel.SOCIAL_MEDIA, AttackChannel.MESSAGING_APP],
                "severity": "high",
                "tags": ["情感诈骗", "杀猪盘", "网络交友"]
            },
            {
                "title": "钓鱼网站诈骗",
                "category": ScamCategory.PHISHING,
                "description": "诈骗分子制作与官方网站相似的钓鱼网站，诱导用户输入账号密码等敏感信息。",
                "attack_vectors": ["伪造网站", "发送钓鱼链接", "窃取信息"],
                "warning_signs": ["网址与官方不同", "要求输入敏感信息", "页面有异常"],
                "prevention_tips": ["检查网址是否正确", "不点击不明链接", "使用官方APP"],
                "victim_groups": [VictimGroup.GENERAL],
                "channels": [AttackChannel.EMAIL, AttackChannel.SMS, AttackChannel.WEBSITE],
                "severity": "medium",
                "tags": ["钓鱼网站", "信息窃取", "账号安全"]
            },
            {
                "title": "技术支持诈骗",
                "category": ScamCategory.TECH_SUPPORT,
                "description": "诈骗分子冒充技术支持人员，声称电脑中毒需要付费修复。",
                "attack_vectors": ["弹窗警告", "冒充客服", "远程控制"],
                "warning_signs": ["电脑弹出警告", "要求付费修复", "要求远程控制"],
                "prevention_tips": ["官方不会主动联系", "不要允许远程控制", "使用正规杀毒软件"],
                "victim_groups": [VictimGroup.ELDERLY, VictimGroup.GENERAL],
                "channels": [AttackChannel.PHONE, AttackChannel.WEBSITE],
                "severity": "medium",
                "tags": ["技术支持", "电脑病毒", "远程控制"]
            },
        ]
        
        for case_data in default_cases:
            self.add_case(**case_data)
    
    async def initialize(self) -> bool:
        """初始化智能体"""
        await asyncio.sleep(0.1)
        return True
    
    def add_case(
        self,
        title: str,
        category: ScamCategory,
        description: str,
        attack_vectors: List[str],
        warning_signs: List[str],
        prevention_tips: List[str],
        victim_groups: List[VictimGroup],
        channels: List[AttackChannel],
        severity: str = "medium",
        tags: List[str] = None,
        source: str = "system"
    ) -> ScamCase:
        """添加案例"""
        self.case_counter += 1
        case_id = f"case_{category.value}_{self.case_counter:04d}"
        
        case = ScamCase(
            case_id=case_id,
            title=title,
            category=category,
            description=description,
            attack_vectors=attack_vectors,
            warning_signs=warning_signs,
            prevention_tips=prevention_tips,
            victim_groups=victim_groups,
            channels=channels,
            severity=severity,
            reported_count=1,
            created_at=datetime.now(),
            updated_at=datetime.now(),
            tags=tags or [],
            related_cases=[]
        )
        
        self.cases[case_id] = case
        self.category_index[category].append(case_id)
        
        for group in victim_groups:
            self.victim_index[group].append(case_id)
        
        for tag in (tags or []):
            self.keyword_index[tag.lower()].append(case_id)
        
        for vector in attack_vectors:
            self.keyword_index[vector.lower()].append(case_id)
        
        self.stats["total_cases"] += 1
        self.stats["cases_by_category"][category.value] += 1
        
        return case
    
    def add_entry(
        self,
        title: str,
        content: str,
        category: ScamCategory,
        keywords: List[str],
        source: str = "manual",
        confidence: float = 1.0
    ) -> KnowledgeEntry:
        """添加知识条目"""
        entry_id = f"entry_{len(self.entries) + 1:04d}"
        
        entry = KnowledgeEntry(
            entry_id=entry_id,
            title=title,
            content=content,
            category=category,
            keywords=keywords,
            source=source,
            confidence=confidence,
            created_at=datetime.now()
        )
        
        self.entries[entry_id] = entry
        self.stats["total_entries"] += 1
        
        for keyword in keywords:
            self.keyword_index[keyword.lower()].append(entry_id)
        
        return entry
    
    def query(
        self,
        query_text: str,
        category: ScamCategory = None,
        victim_group: VictimGroup = None,
        limit: int = 10
    ) -> List[Dict[str, Any]]:
        """查询知识库"""
        self.stats["queries_processed"] += 1
        
        query_lower = query_text.lower()
        query_keywords = query_lower.split()
        
        relevance_scores: Dict[str, float] = defaultdict(float)
        
        for keyword in query_keywords:
            if keyword in self.keyword_index:
                for case_id in self.keyword_index[keyword]:
                    relevance_scores[case_id] += 1
        
        for case_id, score in relevance_scores.items():
            case = self.cases.get(case_id)
            if case:
                title_match = sum(1 for k in query_keywords if k in case.title.lower())
                relevance_scores[case_id] += title_match * 2
        
        candidate_ids = set(relevance_scores.keys())
        
        if category:
            category_ids = set(self.category_index.get(category, []))
            candidate_ids = candidate_ids & category_ids if candidate_ids else category_ids
            self.stats["most_queried_categories"][category.value] += 1
        
        if victim_group:
            victim_ids = set(self.victim_index.get(victim_group, []))
            candidate_ids = candidate_ids & victim_ids if candidate_ids else victim_ids
        
        sorted_ids = sorted(
            candidate_ids,
            key=lambda x: relevance_scores.get(x, 0),
            reverse=True
        )
        
        results = []
        for case_id in sorted_ids[:limit]:
            case = self.cases.get(case_id)
            if case:
                results.append({
                    "case_id": case.case_id,
                    "title": case.title,
                    "category": case.category.value,
                    "description": case.description,
                    "warning_signs": case.warning_signs,
                    "prevention_tips": case.prevention_tips,
                    "relevance_score": relevance_scores.get(case_id, 0),
                })
        
        return results
    
    def get_case(self, case_id: str) -> Optional[ScamCase]:
        """获取案例"""
        return self.cases.get(case_id)
    
    def get_cases_by_category(self, category: ScamCategory) -> List[ScamCase]:
        """按类别获取案例"""
        case_ids = self.category_index.get(category, [])
        return [self.cases[cid] for cid in case_ids if cid in self.cases]
    
    def get_cases_by_victim_group(self, group: VictimGroup) -> List[ScamCase]:
        """按受害者群体获取案例"""
        case_ids = self.victim_index.get(group, [])
        return [self.cases[cid] for cid in case_ids if cid in self.cases]
    
    def update_case(self, case_id: str, updates: Dict[str, Any]) -> bool:
        """更新案例"""
        case = self.cases.get(case_id)
        if not case:
            return False
        
        for key, value in updates.items():
            if hasattr(case, key):
                setattr(case, key, value)
        
        case.updated_at = datetime.now()
        return True
    
    def increment_report_count(self, case_id: str):
        """增加报告次数"""
        case = self.cases.get(case_id)
        if case:
            case.reported_count += 1
    
    def generate_knowledge_card(self, case_id: str) -> Dict[str, Any]:
        """生成知识卡片"""
        case = self.cases.get(case_id)
        if not case:
            return {}
        
        return {
            "title": case.title,
            "category": case.category.value,
            "summary": case.description[:100] + "..." if len(case.description) > 100 else case.description,
            "warning_signs": case.warning_signs[:3],
            "prevention_tips": case.prevention_tips[:3],
            "share_text": f"【防骗提醒】{case.title}：{case.warning_signs[0] if case.warning_signs else '请保持警惕'}",
        }
    
    def get_popular_cases(self, limit: int = 10) -> List[ScamCase]:
        """获取热门案例"""
        sorted_cases = sorted(
            self.cases.values(),
            key=lambda x: x.reported_count,
            reverse=True
        )
        return sorted_cases[:limit]
    
    def get_stats(self) -> Dict[str, Any]:
        """获取统计信息"""
        return {
            **self.stats,
            "cases_by_category": dict(self.stats["cases_by_category"]),
            "most_queried_categories": dict(self.stats["most_queried_categories"]),
        }
