"""
思维链验证智能体
Chain of Thought Verifier Agent

负责在执行敏感操作前，要求智能体展示思维链，验证其决策逻辑。
"""

import asyncio
import json
import logging
import uuid
from typing import Dict, Any, Optional, List
from dataclasses import dataclass, field
from datetime import datetime
from collections import defaultdict
from enum import Enum

logger = logging.getLogger(__name__)


class OperationRisk(Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class VerificationStatus(Enum):
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"
    NEEDS_REVIEW = "needs_review"


@dataclass
class ThoughtChainStep:
    step_number: int = 0
    step_type: str = ""
    content: str = ""
    is_valid: bool = True
    issues: List[str] = field(default_factory=list)


@dataclass
class ThoughtChain:
    chain_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    operation_type: str = ""
    user_request: str = ""
    steps: List[ThoughtChainStep] = field(default_factory=list)
    
    rules_checked: List[str] = field(default_factory=list)
    risks_identified: List[str] = field(default_factory=list)
    decision: str = ""
    
    verification_status: str = VerificationStatus.PENDING.value
    verification_notes: List[str] = field(default_factory=list)
    verified_by: str = ""
    verified_at: str = ""
    
    created_at: str = field(default_factory=lambda: datetime.utcnow().isoformat())


@dataclass
class VerificationResult:
    result_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    chain_id: str = ""
    is_valid: bool = True
    status: str = VerificationStatus.APPROVED.value
    issues: List[str] = field(default_factory=list)
    recommendations: List[str] = field(default_factory=list)
    confidence: float = 1.0


class ChainOfThoughtVerifierAgent:
    """
    思维链验证智能体
    
    功能：
    1. 触发条件：高风险操作、可疑输入、首次执行的非常规任务
    2. 思维链验证流程：要求智能体输出决策过程
    3. 验证思维链中是否包含规则检查、风险评估步骤
    4. 检测思维链中是否有被恶意指令覆盖的痕迹
    """
    
    def __init__(self, config: Optional[Dict] = None):
        self.name = "ChainOfThoughtVerifierAgent"
        self.description = "在执行敏感操作前验证智能体的决策逻辑"
        self.config = config or {}
        
        self.thought_chains: Dict[str, ThoughtChain] = {}
        self.high_risk_operations = self._init_high_risk_operations()
        self.required_steps = self._init_required_steps()
        
        self.stats = {
            "total_verifications": 0,
            "approved": 0,
            "rejected": 0,
            "needs_review": 0,
            "issues_found": defaultdict(int),
        }
        
        self._initialized = False
    
    def _init_high_risk_operations(self) -> Dict[str, Dict]:
        return {
            "data_export": {
                "risk": OperationRisk.HIGH.value,
                "description": "数据导出操作",
                "requires_verification": True,
            },
            "permission_change": {
                "risk": OperationRisk.CRITICAL.value,
                "description": "权限变更操作",
                "requires_verification": True,
            },
            "user_deletion": {
                "risk": OperationRisk.CRITICAL.value,
                "description": "用户删除操作",
                "requires_verification": True,
            },
            "bulk_operation": {
                "risk": OperationRisk.HIGH.value,
                "description": "批量操作",
                "requires_verification": True,
            },
            "cross_border_transfer": {
                "risk": OperationRisk.HIGH.value,
                "description": "跨境数据传输",
                "requires_verification": True,
            },
            "sensitive_data_access": {
                "risk": OperationRisk.HIGH.value,
                "description": "敏感数据访问",
                "requires_verification": True,
            },
        }
    
    def _init_required_steps(self) -> List[Dict]:
        return [
            {"step_type": "receive_request", "description": "接收用户指令", "required": True},
            {"step_type": "query_rules", "description": "查询系统规则", "required": True},
            {"step_type": "risk_assessment", "description": "风险评估", "required": True},
            {"step_type": "compliance_check", "description": "合规判断", "required": True},
            {"step_type": "final_decision", "description": "最终决定", "required": True},
        ]
    
    async def initialize(self):
        if not self._initialized:
            await self._setup()
            self._initialized = True
            logger.info(f"Agent '{self.name}' initialized")
    
    async def _setup(self):
        pass
    
    def _assess_operation_risk(
        self,
        operation_type: str,
        context: Optional[Dict] = None,
    ) -> str:
        if operation_type in self.high_risk_operations:
            return self.high_risk_operations[operation_type]["risk"]
        
        if context:
            if context.get("suspicious_input_confidence", 0) > 0.5:
                return OperationRisk.HIGH.value
            if context.get("first_time_operation", False):
                return OperationRisk.MEDIUM.value
        
        return OperationRisk.LOW.value
    
    async def requires_verification(
        self,
        operation_type: str,
        context: Optional[Dict] = None,
    ) -> bool:
        risk = self._assess_operation_risk(operation_type, context)
        
        if risk in [OperationRisk.HIGH.value, OperationRisk.CRITICAL.value]:
            return True
        
        if context:
            if context.get("suspicious_input_confidence", 0) > 0.3:
                return True
            if context.get("first_time_operation", False):
                return True
        
        return False
    
    async def create_thought_chain(
        self,
        operation_type: str,
        user_request: str,
    ) -> ThoughtChain:
        chain = ThoughtChain(
            operation_type=operation_type,
            user_request=user_request,
        )
        
        for i, step_template in enumerate(self.required_steps, 1):
            step = ThoughtChainStep(
                step_number=i,
                step_type=step_template["step_type"],
                content="",
            )
            chain.steps.append(step)
        
        self.thought_chains[chain.chain_id] = chain
        return chain
    
    async def update_thought_chain_step(
        self,
        chain_id: str,
        step_number: int,
        content: str,
    ) -> bool:
        chain = self.thought_chains.get(chain_id)
        if not chain:
            return False
        
        for step in chain.steps:
            if step.step_number == step_number:
                step.content = content
                return True
        
        return False
    
    async def complete_thought_chain(
        self,
        chain_id: str,
        decision: str,
        rules_checked: Optional[List[str]] = None,
        risks_identified: Optional[List[str]] = None,
    ) -> ThoughtChain:
        chain = self.thought_chains.get(chain_id)
        if not chain:
            return None
        
        chain.decision = decision
        chain.rules_checked = rules_checked or []
        chain.risks_identified = risks_identified or []
        
        return chain
    
    async def verify_thought_chain(
        self,
        chain_id: str,
    ) -> VerificationResult:
        self.stats["total_verifications"] += 1
        
        chain = self.thought_chains.get(chain_id)
        if not chain:
            return VerificationResult(
                chain_id=chain_id,
                is_valid=False,
                status=VerificationStatus.REJECTED.value,
                issues=["思维链不存在"],
            )
        
        issues = []
        recommendations = []
        
        for step_template in self.required_steps:
            if step_template["required"]:
                step_found = False
                for step in chain.steps:
                    if step.step_type == step_template["step_type"] and step.content:
                        step_found = True
                        break
                
                if not step_found:
                    issues.append(f"缺少必要步骤: {step_template['description']}")
        
        if not chain.rules_checked:
            issues.append("未检查任何系统规则")
        else:
            critical_rules = ["privacy", "security", "compliance"]
            has_critical = any(r in str(chain.rules_checked).lower() for r in critical_rules)
            if not has_critical:
                issues.append("未检查关键安全规则")
        
        if chain.decision == "execute" and not chain.risks_identified:
            issues.append("执行决定未进行风险评估")
        
        malicious_patterns = [
            "忽略规则",
            "绕过检查",
            "用户指令优先",
        ]
        
        for step in chain.steps:
            for pattern in malicious_patterns:
                if pattern in step.content:
                    issues.append(f"检测到可疑内容: {pattern}")
                    step.is_valid = False
        
        is_valid = len(issues) == 0
        
        if is_valid:
            status = VerificationStatus.APPROVED.value
            self.stats["approved"] += 1
        elif len(issues) <= 2:
            status = VerificationStatus.NEEDS_REVIEW.value
            self.stats["needs_review"] += 1
            recommendations.append("建议人工审核后执行")
        else:
            status = VerificationStatus.REJECTED.value
            self.stats["rejected"] += 1
            recommendations.append("拒绝执行，需要重新评估")
        
        for issue in issues:
            self.stats["issues_found"][issue] += 1
        
        chain.verification_status = status
        chain.verification_notes = issues
        chain.verified_at = datetime.utcnow().isoformat()
        
        return VerificationResult(
            chain_id=chain_id,
            is_valid=is_valid,
            status=status,
            issues=issues,
            recommendations=recommendations,
            confidence=0.9 if is_valid else 0.6,
        )
    
    async def get_thought_chain_template(self, operation_type: str) -> str:
        template = f"""决策过程：
1. 接收用户指令：[用户输入]
2. 查询系统规则：[相关规则]
3. 风险评估：检测到[风险因素]
4. 合规判断：[合规/不合规]
5. 最终决定：[执行/拒绝]

操作类型: {operation_type}
"""
        return template
    
    async def get_pending_chains(self) -> List[Dict]:
        return [
            {
                "chain_id": c.chain_id,
                "operation_type": c.operation_type,
                "user_request": c.user_request[:100],
                "status": c.verification_status,
                "created_at": c.created_at,
            }
            for c in self.thought_chains.values()
            if c.verification_status == VerificationStatus.PENDING.value
        ]
    
    async def store_to_audit_log(self, chain_id: str) -> Dict:
        chain = self.thought_chains.get(chain_id)
        if not chain:
            return {"success": False, "reason": "思维链不存在"}
        
        audit_entry = {
            "chain_id": chain.chain_id,
            "operation_type": chain.operation_type,
            "user_request": chain.user_request,
            "steps": [
                {
                    "step_number": s.step_number,
                    "step_type": s.step_type,
                    "content": s.content,
                }
                for s in chain.steps
            ],
            "decision": chain.decision,
            "verification_status": chain.verification_status,
            "timestamp": chain.created_at,
        }
        
        return {"success": True, "audit_entry": audit_entry}
    
    async def get_stats(self) -> Dict:
        return {
            "name": self.name,
            "total_verifications": self.stats["total_verifications"],
            "approved": self.stats["approved"],
            "rejected": self.stats["rejected"],
            "needs_review": self.stats["needs_review"],
            "issues_found": dict(self.stats["issues_found"]),
        }
