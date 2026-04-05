# -*- coding: utf-8 -*-
"""
Recall Manager
Handles proactive recall and modification of consultation responses
"""
import logging
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field
from enum import Enum
import json
import time
import uuid

from backend.database_pg import PostgreSQLConnectionPool

logger = logging.getLogger(__name__)


class RecallTrigger(Enum):
    USER_FEEDBACK = "user_feedback"
    SYSTEM_DETECT = "system_detect"
    DATA_UPDATE = "data_update"
    LOGIC_ERROR = "logic_error"
    POLICY_CHANGE = "policy_change"
    NEW_INFORMATION = "new_information"


class RecallSeverity(Enum):
    MINOR = "minor"
    MODERATE = "moderate"
    MAJOR = "major"


@dataclass
class RecallRequest:
    session_id: str
    report_id: str
    trigger_type: str
    trigger_reason: str
    severity: str
    affected_sections: List[str]
    original_content: Dict
    proposed_fix: Dict


@dataclass
class RecallResult:
    recall_id: str
    success: bool
    new_report_id: Optional[str]
    recall_message: str
    changes_made: List[Dict]
    user_notification: str


class RecallManager:
    def __init__(self, db: PostgreSQLConnectionPool = None):
        self.db = db
        self._recall_rules = self._load_recall_rules()
        self._notification_templates = self._load_notification_templates()
    
    def _load_recall_rules(self) -> Dict:
        return {
            RecallTrigger.USER_FEEDBACK: {
                "auto_recall": False,
                "requires_confirmation": True,
                "min_severity": RecallSeverity.MINOR.value
            },
            RecallTrigger.SYSTEM_DETECT: {
                "auto_recall": True,
                "requires_confirmation": False,
                "min_severity": RecallSeverity.MODERATE.value
            },
            RecallTrigger.DATA_UPDATE: {
                "auto_recall": True,
                "requires_confirmation": False,
                "min_severity": RecallSeverity.MODERATE.value
            },
            RecallTrigger.LOGIC_ERROR: {
                "auto_recall": True,
                "requires_confirmation": False,
                "min_severity": RecallSeverity.MINOR.value
            },
            RecallTrigger.POLICY_CHANGE: {
                "auto_recall": True,
                "requires_confirmation": True,
                "min_severity": RecallSeverity.MAJOR.value
            }
        }
    
    def _load_notification_templates(self) -> Dict:
        return {
            "zhouyu": {
                RecallTrigger.USER_FEEDBACK: "阁下，关于刚才的建议，我重新审视后发现可改进之处，特此修正：{changes}",
                RecallTrigger.SYSTEM_DETECT: "阁下，我发现先前分析有疏漏，现更正如下：{changes}",
                RecallTrigger.DATA_UPDATE: "阁下，市场数据有变，我已更新分析：{changes}",
                RecallTrigger.LOGIC_ERROR: "阁下，先前计算有误，现修正如下：{changes}",
                RecallTrigger.POLICY_CHANGE: "阁下，政策有变，我已调整建议：{changes}"
            },
            "luxun": {
                RecallTrigger.USER_FEEDBACK: "您好，我重新审视了刚才的建议，发现有一些可以改进的地方，现在为您更新：{changes}",
                RecallTrigger.SYSTEM_DETECT: "您好，我发现之前的分析有一些疏漏，现在为您更正：{changes}",
                RecallTrigger.DATA_UPDATE: "您好，市场数据有更新，我已经调整了分析结果：{changes}",
                RecallTrigger.LOGIC_ERROR: "您好，之前的计算有误，现在为您修正：{changes}",
                RecallTrigger.POLICY_CHANGE: "您好，政策有变化，我已经更新了建议：{changes}"
            }
        }
    
    async def check_recall_needed(
        self,
        session_id: str,
        report_id: str,
        context: Dict
    ) -> Optional[RecallRequest]:
        if not self.db:
            return None
        
        async with self.db.get_connection() as conn:
            report = await conn.fetchrow(
                "SELECT * FROM consultation_reports WHERE id = $1 AND is_latest = true",
                report_id
            )
            
            if not report:
                return None
            
            content = report["content"]
            
            issues = await self._detect_issues(conn, session_id, content, context)
            
            if issues:
                severity = self._calculate_severity(issues)
                return RecallRequest(
                    session_id=session_id,
                    report_id=report_id,
                    trigger_type=RecallTrigger.SYSTEM_DETECT.value,
                    trigger_reason="; ".join([i["reason"] for i in issues]),
                    severity=severity,
                    affected_sections=[i["section"] for i in issues],
                    original_content=content,
                    proposed_fix=self._generate_fix(content, issues)
                )
        
        return None
    
    async def _detect_issues(
        self,
        conn,
        session_id: str,
        content: Dict,
        context: Dict
    ) -> List[Dict]:
        issues = []
        
        text_content = json.dumps(content, ensure_ascii=False)
        
        absolute_words = ["一定", "必然", "绝对", "肯定", "百分之百"]
        for word in absolute_words:
            if word in text_content:
                issues.append({
                    "type": "objectivity_violation",
                    "section": "content",
                    "reason": f"发现绝对化语言: {word}",
                    "severity": RecallSeverity.MINOR.value
                })
        
        slots = context.get("slots", {})
        if "学区" in text_content and "education" not in slots.get("purposes", []):
            issues.append({
                "type": "content_mismatch",
                "section": "recommendations",
                "reason": "报告中提及学区但用户未表达学区需求",
                "severity": RecallSeverity.MODERATE.value
            })
        
        return issues
    
    def _calculate_severity(self, issues: List[Dict]) -> str:
        severities = [i.get("severity", RecallSeverity.MINOR.value) for i in issues]
        
        if RecallSeverity.MAJOR.value in severities:
            return RecallSeverity.MAJOR.value
        elif RecallSeverity.MODERATE.value in severities:
            return RecallSeverity.MODERATE.value
        else:
            return RecallSeverity.MINOR.value
    
    def _generate_fix(self, original_content: Dict, issues: List[Dict]) -> Dict:
        fixed_content = json.loads(json.dumps(original_content))
        
        for issue in issues:
            if issue["type"] == "objectivity_violation":
                text = json.dumps(fixed_content, ensure_ascii=False)
                replacements = {
                    "一定": "可能",
                    "必然": "很有可能",
                    "绝对": "比较",
                    "肯定": "应该",
                    "百分之百": "大概率"
                }
                for old, new in replacements.items():
                    text = text.replace(old, new)
                fixed_content = json.loads(text)
        
        return fixed_content
    
    async def execute_recall(
        self,
        request: RecallRequest,
        persona_name: str = "zhouyu",
        auto_confirm: bool = False
    ) -> RecallResult:
        recall_id = str(uuid.uuid4())
        
        rule = self._recall_rules.get(RecallTrigger(request.trigger_type), {})
        
        if rule.get("auto_recall") or auto_confirm:
            new_report_id = await self._create_revised_report(request)
            changes_made = self._summarize_changes(
                request.original_content, 
                request.proposed_fix
            )
            
            notification = self._generate_notification(
                request.trigger_type,
                persona_name,
                changes_made
            )
            
            await self._record_recall(request, recall_id, new_report_id)
            
            return RecallResult(
                recall_id=recall_id,
                success=True,
                new_report_id=new_report_id,
                recall_message="报告已修正",
                changes_made=changes_made,
                user_notification=notification
            )
        else:
            return RecallResult(
                recall_id=recall_id,
                success=False,
                new_report_id=None,
                recall_message="需要用户确认",
                changes_made=[],
                user_notification="检测到需要修正的内容，是否确认修改？"
            )
    
    async def _create_revised_report(self, request: RecallRequest) -> str:
        if not self.db:
            return None
        
        new_report_id = str(uuid.uuid4())
        
        async with self.db.get_connection() as conn:
            await conn.execute("""
                UPDATE consultation_reports 
                SET is_latest = false, revoked_at = CURRENT_TIMESTAMP
                WHERE id = $1
            """, request.report_id)
            
            old_report = await conn.fetchrow(
                "SELECT * FROM consultation_reports WHERE id = $1",
                request.report_id
            )
            
            if old_report:
                await conn.execute("""
                    INSERT INTO consultation_reports 
                    (id, session_id, user_id, title, content, persona, gene_dimensions,
                     data_sources, referenced_cases, version, is_latest, parent_report_id)
                    VALUES ($1, $2, $3, $4, $5::jsonb, $6, $7::jsonb, $8::jsonb, $9, $10, true, $11)
                """, new_report_id, old_report["session_id"], old_report["user_id"],
                    old_report["title"], request.proposed_fix, old_report["persona"],
                    old_report["gene_dimensions"], old_report["data_sources"],
                    old_report["referenced_cases"], old_report["version"] + 1,
                    request.report_id)
        
        return new_report_id
    
    def _summarize_changes(self, original: Dict, revised: Dict) -> List[Dict]:
        changes = []
        
        def compare_dicts(orig, rev, path=""):
            if isinstance(orig, dict) and isinstance(rev, dict):
                for key in set(list(orig.keys()) + list(rev.keys())):
                    new_path = f"{path}.{key}" if path else key
                    if key not in orig:
                        changes.append({
                            "type": "added",
                            "path": new_path,
                            "value": rev[key]
                        })
                    elif key not in rev:
                        changes.append({
                            "type": "removed",
                            "path": new_path,
                            "old_value": orig[key]
                        })
                    elif orig[key] != rev[key]:
                        if isinstance(orig[key], (dict, list)):
                            compare_dicts(orig[key], rev[key], new_path)
                        else:
                            changes.append({
                                "type": "modified",
                                "path": new_path,
                                "old_value": orig[key],
                                "new_value": rev[key]
                            })
            elif isinstance(orig, list) and isinstance(rev, list):
                if len(orig) != len(rev):
                    changes.append({
                        "type": "list_length_changed",
                        "path": path,
                        "old_length": len(orig),
                        "new_length": len(rev)
                    })
        
        compare_dicts(original, revised)
        return changes
    
    def _generate_notification(
        self,
        trigger_type: str,
        persona_name: str,
        changes: List[Dict]
    ) -> str:
        templates = self._notification_templates.get(
            persona_name, 
            self._notification_templates["zhouyu"]
        )
        
        template = templates.get(
            RecallTrigger(trigger_type),
            templates[RecallTrigger.SYSTEM_DETECT]
        )
        
        change_summary = "、".join([c["path"] for c in changes[:3]])
        if len(changes) > 3:
            change_summary += f"等{len(changes)}处"
        
        return template.format(changes=change_summary)
    
    async def _record_recall(
        self,
        request: RecallRequest,
        recall_id: str,
        new_report_id: str
    ):
        if not self.db:
            return
        
        async with self.db.get_connection() as conn:
            await conn.execute("""
                INSERT INTO recall_records 
                (id, session_id, report_id, trigger_type, trigger_reason,
                 original_content, revised_content, new_report_id, user_notified)
                VALUES ($1, $2, $3, $4, $5, $6::jsonb, $7::jsonb, $8, true)
            """, recall_id, request.session_id, request.report_id,
                request.trigger_type, request.trigger_reason,
                request.original_content, request.proposed_fix, new_report_id)
    
    async def get_recall_history(self, session_id: str) -> List[Dict]:
        if not self.db:
            return []
        
        async with self.db.get_connection() as conn:
            rows = await conn.fetch("""
                SELECT * FROM recall_records 
                WHERE session_id = $1 
                ORDER BY created_at DESC
            """, session_id)
            
            return [dict(row) for row in rows]


recall_manager: Optional[RecallManager] = None


async def get_recall_manager(db: PostgreSQLConnectionPool = None) -> RecallManager:
    global recall_manager
    if recall_manager is None:
        recall_manager = RecallManager(db)
    return recall_manager
