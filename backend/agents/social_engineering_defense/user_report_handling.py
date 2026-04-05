"""
用户举报处理智能体
负责处理用户举报的可疑交互
"""
import asyncio
from collections import defaultdict
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional


class ReportType(Enum):
    """举报类型"""
    SUSPICIOUS_MESSAGE = "suspicious_message"
    SUSPICIOUS_USER = "suspicious_user"
    SUSPICIOUS_LINK = "suspicious_link"
    FRAUD_ATTEMPT = "fraud_attempt"
    IMPERSONATION = "impersonation"
    HARASSMENT = "harassment"
    OTHER = "other"


class ReportStatus(Enum):
    """举报状态"""
    PENDING = "pending"
    UNDER_REVIEW = "under_review"
    VERIFIED = "verified"
    DISMISSED = "dismissed"
    ESCALATED = "escalated"


class ReportValidity(Enum):
    """举报有效性"""
    VALID = "valid"
    INVALID = "invalid"
    UNCLEAR = "unclear"


@dataclass
class UserReport:
    """用户举报"""
    report_id: str
    report_type: ReportType
    reporter_id: str
    reported_user_id: Optional[str]
    reported_session_id: Optional[str]
    description: str
    context: Dict[str, Any]
    status: ReportStatus
    validity: Optional[ReportValidity]
    scam_category: Optional[str]
    analysis_result: Optional[Dict[str, Any]]
    created_at: datetime
    updated_at: datetime
    reviewed_by: Optional[str] = None
    review_notes: str = ""
    actions_taken: List[str] = field(default_factory=list)


@dataclass
class ReportAnalysis:
    """举报分析"""
    is_valid: bool
    confidence: float
    scam_indicators: List[str]
    scam_category: Optional[str]
    risk_level: str
    recommended_actions: List[str]


class UserReportHandlingAgent:
    """用户举报处理智能体"""
    
    def __init__(self, config: Optional[Dict] = None):
        self.name = "UserReportHandlingAgent"
        self.config = config or {}
        self.reports: Dict[str, UserReport] = {}
        self.blacklist: Dict[str, Dict[str, Any]] = {}
        self.report_patterns = self._init_report_patterns()
        self.report_counter = 0
        self.stats = {
            "total_reports": 0,
            "reports_by_type": defaultdict(int),
            "valid_reports": 0,
            "invalid_reports": 0,
            "escalated_reports": 0,
            "users_blacklisted": 0,
        }
    
    def _init_report_patterns(self) -> Dict[str, Dict]:
        """初始化举报模式"""
        return {
            "fraud_indicators": [
                "转账", "汇款", "银行卡", "密码", "验证码",
                "中奖", "返利", "投资", "理财", "贷款",
                "公检法", "安全账户", "涉案", "洗钱"
            ],
            "impersonation_indicators": [
                "客服", "管理员", "官方", "工作人员",
                "领导", "老板", "朋友", "亲戚"
            ],
            "urgency_indicators": [
                "紧急", "立即", "马上", "限时", "最后",
                "错过", "失效", "过期"
            ],
            "threat_indicators": [
                "冻结", "封号", "起诉", "报警", "拘留",
                "法律责任", "后果自负"
            ]
        }
    
    async def initialize(self) -> bool:
        """初始化智能体"""
        await asyncio.sleep(0.1)
        return True
    
    def submit_report(
        self,
        report_type: ReportType,
        reporter_id: str,
        description: str,
        reported_user_id: str = None,
        reported_session_id: str = None,
        context: Dict[str, Any] = None
    ) -> UserReport:
        """提交举报"""
        self.report_counter += 1
        report_id = f"report_{datetime.now().strftime('%Y%m%d%H%M%S')}_{self.report_counter}"
        
        report = UserReport(
            report_id=report_id,
            report_type=report_type,
            reporter_id=reporter_id,
            reported_user_id=reported_user_id,
            reported_session_id=reported_session_id,
            description=description,
            context=context or {},
            status=ReportStatus.PENDING,
            validity=None,
            scam_category=None,
            analysis_result=None,
            created_at=datetime.now(),
            updated_at=datetime.now()
        )
        
        self.reports[report_id] = report
        self.stats["total_reports"] += 1
        self.stats["reports_by_type"][report_type.value] += 1
        
        analysis = self._analyze_report(report)
        report.analysis_result = {
            "is_valid": analysis.is_valid,
            "confidence": analysis.confidence,
            "scam_indicators": analysis.scam_indicators,
            "scam_category": analysis.scam_category,
            "risk_level": analysis.risk_level,
            "recommended_actions": analysis.recommended_actions
        }
        
        if analysis.is_valid:
            report.validity = ReportValidity.VALID
            report.scam_category = analysis.scam_category
            self.stats["valid_reports"] += 1
        elif analysis.confidence > 0.3:
            report.validity = ReportValidity.UNCLEAR
        else:
            report.validity = ReportValidity.INVALID
            self.stats["invalid_reports"] += 1
        
        report.updated_at = datetime.now()
        
        return report
    
    def _analyze_report(self, report: UserReport) -> ReportAnalysis:
        """分析举报"""
        text = f"{report.description} {report.context.get('message_history', '')}".lower()
        
        scam_indicators = []
        indicator_scores = {}
        
        for indicator_type, indicators in self.report_patterns.items():
            matches = [ind for ind in indicators if ind in text]
            if matches:
                scam_indicators.extend(matches)
                indicator_scores[indicator_type] = len(matches) / len(indicators)
        
        fraud_score = indicator_scores.get("fraud_indicators", 0)
        impersonation_score = indicator_scores.get("impersonation_indicators", 0)
        urgency_score = indicator_scores.get("urgency_indicators", 0)
        threat_score = indicator_scores.get("threat_indicators", 0)
        
        confidence = (fraud_score * 0.4 + impersonation_score * 0.3 + 
                     urgency_score * 0.15 + threat_score * 0.15)
        
        confidence = min(1.0, confidence * 3)
        
        is_valid = confidence > 0.5 or len(scam_indicators) >= 3
        
        scam_category = None
        if impersonation_score > 0.1:
            scam_category = "impersonation"
        elif fraud_score > 0.1:
            scam_category = "fraud"
        elif threat_score > 0.1:
            scam_category = "threat"
        
        risk_level = "low"
        if confidence > 0.7:
            risk_level = "high"
        elif confidence > 0.4:
            risk_level = "medium"
        
        recommended_actions = self._generate_recommendations(
            is_valid, risk_level, scam_category
        )
        
        return ReportAnalysis(
            is_valid=is_valid,
            confidence=confidence,
            scam_indicators=list(set(scam_indicators)),
            scam_category=scam_category,
            risk_level=risk_level,
            recommended_actions=recommended_actions
        )
    
    def _generate_recommendations(
        self,
        is_valid: bool,
        risk_level: str,
        scam_category: Optional[str]
    ) -> List[str]:
        """生成建议"""
        recommendations = []
        
        if is_valid:
            if risk_level == "high":
                recommendations.append("立即加入黑名单")
                recommendations.append("通知相关用户")
                recommendations.append("升级安全团队审核")
            elif risk_level == "medium":
                recommendations.append("标记为可疑")
                recommendations.append("加强监控")
            else:
                recommendations.append("记录观察")
            
            if scam_category == "impersonation":
                recommendations.append("验证身份真实性")
            elif scam_category == "fraud":
                recommendations.append("检查资金流向")
        else:
            recommendations.append("标记为无效举报")
            recommendations.append("向举报者反馈")
        
        return recommendations
    
    def review_report(
        self,
        report_id: str,
        reviewer_id: str,
        validity: ReportValidity,
        notes: str = "",
        actions: List[str] = None
    ) -> bool:
        """审核举报"""
        report = self.reports.get(report_id)
        if not report:
            return False
        
        report.status = ReportStatus.UNDER_REVIEW
        report.reviewed_by = reviewer_id
        report.validity = validity
        report.review_notes = notes
        report.updated_at = datetime.now()
        
        if actions:
            report.actions_taken.extend(actions)
        
        if validity == ReportValidity.VALID:
            report.status = ReportStatus.VERIFIED
            self._take_action(report)
        else:
            report.status = ReportStatus.DISMISSED
        
        return True
    
    def _take_action(self, report: UserReport):
        """采取行动"""
        if report.reported_user_id:
            if report.reported_user_id not in self.blacklist:
                self.blacklist[report.reported_user_id] = {
                    "added_at": datetime.now(),
                    "reason": report.scam_category or "user_report",
                    "report_id": report.report_id
                }
                self.stats["users_blacklisted"] += 1
        
        report.actions_taken.append("processed")
    
    def escalate_report(
        self,
        report_id: str,
        reason: str
    ) -> bool:
        """升级举报"""
        report = self.reports.get(report_id)
        if not report:
            return False
        
        report.status = ReportStatus.ESCALATED
        report.review_notes += f"\n升级原因: {reason}"
        report.updated_at = datetime.now()
        self.stats["escalated_reports"] += 1
        
        return True
    
    def get_report(self, report_id: str) -> Optional[UserReport]:
        """获取举报"""
        return self.reports.get(report_id)
    
    def get_reports_by_status(self, status: ReportStatus) -> List[UserReport]:
        """按状态获取举报"""
        return [r for r in self.reports.values() if r.status == status]
    
    def get_reports_by_reporter(self, reporter_id: str) -> List[UserReport]:
        """按举报者获取举报"""
        return [r for r in self.reports.values() if r.reporter_id == reporter_id]
    
    def get_pending_reports(self, limit: int = 50) -> List[UserReport]:
        """获取待处理举报"""
        pending = [r for r in self.reports.values() if r.status == ReportStatus.PENDING]
        return sorted(pending, key=lambda x: x.created_at, reverse=True)[:limit]
    
    def is_blacklisted(self, user_id: str) -> bool:
        """检查是否在黑名单"""
        return user_id in self.blacklist
    
    def get_blacklist_info(self, user_id: str) -> Optional[Dict[str, Any]]:
        """获取黑名单信息"""
        return self.blacklist.get(user_id)
    
    def remove_from_blacklist(self, user_id: str) -> bool:
        """移出黑名单"""
        if user_id in self.blacklist:
            del self.blacklist[user_id]
            return True
        return False
    
    def generate_report_summary(self, days: int = 7) -> Dict[str, Any]:
        """生成举报摘要"""
        cutoff = datetime.now() - __import__('datetime').timedelta(days=days)
        
        recent_reports = [
            r for r in self.reports.values()
            if r.created_at > cutoff
        ]
        
        type_distribution = defaultdict(int)
        for report in recent_reports:
            type_distribution[report.report_type.value] += 1
        
        status_distribution = defaultdict(int)
        for report in recent_reports:
            status_distribution[report.status.value] += 1
        
        return {
            "period_days": days,
            "total_reports": len(recent_reports),
            "by_type": dict(type_distribution),
            "by_status": dict(status_distribution),
            "valid_rate": sum(1 for r in recent_reports if r.validity == ReportValidity.VALID) / max(1, len(recent_reports)),
            "avg_processing_time": "N/A",
        }
    
    def get_stats(self) -> Dict[str, Any]:
        """获取统计信息"""
        return {
            **self.stats,
            "reports_by_type": dict(self.stats["reports_by_type"]),
            "blacklist_size": len(self.blacklist),
        }
