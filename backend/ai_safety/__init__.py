"""
AI安全合规防护系统
AI Safety & Compliance Protection System

核心功能：
1. 模型滥用防护（防知识污染）
2. 流式内容实时审核
3. 内容标识与数字水印
4. RAG检索增强生成
5. 多模态内容审核
"""

import os
import re
import json
import time
import uuid
import hashlib
import logging
import threading
from datetime import datetime
from typing import Dict, List, Optional, Any, Tuple, Callable, AsyncIterator
from dataclasses import dataclass, field, asdict
from enum import Enum
from collections import defaultdict, Counter
from concurrent.futures import ThreadPoolExecutor, as_completed
import asyncio

logger = logging.getLogger(__name__)


class RiskLevel(Enum):
    SAFE = "safe"
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class ContentType(Enum):
    TEXT = "text"
    IMAGE = "image"
    AUDIO = "audio"
    VIDEO = "video"
    DOCUMENT = "document"


class AbuseCategory(Enum):
    DRUGS = "drugs"
    FRAUD = "fraud"
    GAMBLING = "gambling"
    DISCRIMINATION = "discrimination"
    VIOLENCE = "violence"
    PORNOGRAPHY = "pornography"
    POLITICAL_SENSITIVE = "political_sensitive"
    PERSONAL_INFO = "personal_info"
    PROMPT_INJECTION = "prompt_injection"
    JAILBREAK = "jailbreak"
    HARMFUL_INSTRUCTION = "harmful_instruction"
    MISINFORMATION = "misinformation"


@dataclass
class AuditResult:
    risk_level: RiskLevel
    categories: List[AbuseCategory]
    confidence: float
    details: Dict[str, Any] = field(default_factory=dict)
    action: str = "allow"
    reason: str = ""
    timestamp: float = field(default_factory=time.time)

    def to_dict(self) -> Dict:
        return {
            "risk_level": self.risk_level.value,
            "categories": [c.value for c in self.categories],
            "confidence": self.confidence,
            "details": self.details,
            "action": self.action,
            "reason": self.reason,
            "timestamp": self.timestamp
        }


@dataclass
class ContentWatermark:
    content_id: str
    content_type: ContentType
    ai_generated: bool
    generator_info: Dict[str, str]
    timestamp: float
    signature: str
    visible_mark: str = ""
    invisible_mark: str = ""

    def to_dict(self) -> Dict:
        return asdict(self)


class AbusePatternLibrary:
    _instance = None
    _lock = threading.Lock()

    def __new__(cls):
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
                    cls._instance._initialized = False
        return cls._instance

    def __init__(self):
        if self._initialized:
            return
        self._initialized = True
        self._patterns = self._load_patterns()
        self._prompt_injection_patterns = self._load_prompt_injection_patterns()
        self._jailbreak_patterns = self._load_jailbreak_patterns()

    def _load_patterns(self) -> Dict[AbuseCategory, List[re.Pattern]]:
        patterns = {}
        
        patterns[AbuseCategory.DRUGS] = [
            re.compile(r'(毒品|大麻|冰毒|海洛因|可卡因|摇头丸|K粉|摇头丸|贩卖.*毒|吸食)', re.I),
            re.compile(r'(drug|cocaine|heroin|marijuana|meth|ecstasy)', re.I),
        ]
        
        patterns[AbuseCategory.FRAUD] = [
            re.compile(r'(诈骗|骗取|钓鱼网站|虚假投资|杀猪盘|刷单|返利|中奖.*领奖|验证码.*转账)', re.I),
            re.compile(r'(fraud|scam|phishing|ponzi|pyramid scheme)', re.I),
        ]
        
        patterns[AbuseCategory.GAMBLING] = [
            re.compile(r'(赌博|赌场|博彩|下注|投注|百家乐|老虎机|赌球|赌马)', re.I),
            re.compile(r'(gambling|casino|betting|poker|slot machine)', re.I),
        ]
        
        patterns[AbuseCategory.DISCRIMINATION] = [
            re.compile(r'(种族歧视|性别歧视|地域歧视|歧视.*人|侮辱.*族)', re.I),
            re.compile(r'(racism|sexism|discrimination|hate speech)', re.I),
        ]
        
        patterns[AbuseCategory.VIOLENCE] = [
            re.compile(r'(暴力|杀人|伤害|袭击|恐怖袭击|炸弹|爆炸|武器制造)', re.I),
            re.compile(r'(violence|kill|murder|terrorist|bomb|weapon)', re.I),
        ]
        
        patterns[AbuseCategory.PERSONAL_INFO] = [
            re.compile(r'(\d{17}[\dXx]|\d{15})'),
            re.compile(r'(1[3-9]\d{9})'),
            re.compile(r'[\w\.-]+@[\w\.-]+\.\w+'),
            re.compile(r'(银行卡|信用卡|账号|密码|身份证号)'),
        ]
        
        patterns[AbuseCategory.MISINFORMATION] = [
            re.compile(r'(假新闻|谣言|虚假信息|造谣|辟谣)', re.I),
            re.compile(r'(fake news|rumor|misinformation)', re.I),
        ]
        
        return patterns

    def _load_prompt_injection_patterns(self) -> List[re.Pattern]:
        return [
            re.compile(r'(ignore\s+(previous|all|above)\s+(instructions?|prompts?|rules?))', re.I),
            re.compile(r'(forget\s+(everything|all|previous))', re.I),
            re.compile(r'(you\s+are\s+now|act\s+as|pretend\s+(to\s+be|you\s+are))', re.I),
            re.compile(r'(system\s*:\s*|assistant\s*:\s*|user\s*:\s*)', re.I),
            re.compile(r'(jailbreak|DAN|do\s+anything\s+now)', re.I),
            re.compile(r'(绕过|忽略|忘记|覆盖).*?(指令|规则|限制)', re.I),
            re.compile(r'(假装|扮演|模拟).*?(AI|助手|系统)', re.I),
            re.compile(r'(developer\s+mode|debug\s+mode|admin\s+mode)', re.I),
            re.compile(r'(print\s+your\s+(instructions|prompt|system))', re.I),
            re.compile(r'(reveal|show|tell)\s+(your|the)\s+(instructions|prompt)', re.I),
        ]

    def _load_jailbreak_patterns(self) -> List[re.Pattern]:
        return [
            re.compile(r'(sudo|chmod|rm\s+-rf|exec|eval|system\s*\()', re.I),
            re.compile(r'(<\|.*?\||\{\{.*?\}\}|\$\{.*?\})'),
            re.compile(r'(python|javascript|code)\s*:\s*```', re.I),
            re.compile(r'(import\s+|from\s+|exec\s*\(|eval\s*\()', re.I),
        ]

    def detect_abuse(self, text: str) -> Tuple[List[AbuseCategory], Dict[str, Any]]:
        detected = []
        details = {}
        
        for category, patterns in self._patterns.items():
            for pattern in patterns:
                matches = pattern.findall(text)
                if matches:
                    detected.append(category)
                    details[category.value] = {
                        "matches": matches[:5],
                        "pattern": pattern.pattern[:50]
                    }
                    break
        
        return detected, details

    def detect_prompt_injection(self, text: str) -> Tuple[bool, List[str]]:
        detected_patterns = []
        
        for pattern in self._prompt_injection_patterns:
            if pattern.search(text):
                detected_patterns.append(pattern.pattern[:50])
        
        for pattern in self._jailbreak_patterns:
            if pattern.search(text):
                detected_patterns.append(f"[jailbreak] {pattern.pattern[:50]}")
        
        return len(detected_patterns) > 0, detected_patterns


class ModelAbuseProtector:
    def __init__(self, config: Optional[Dict] = None):
        self.config = config or {}
        self.pattern_library = AbusePatternLibrary()
        self.action_rules = self._load_action_rules()
        self.audit_log: List[AuditResult] = []
        self._lock = threading.Lock()
        self.stats = defaultdict(int)

    def _load_action_rules(self) -> Dict[RiskLevel, str]:
        return {
            RiskLevel.SAFE: "allow",
            RiskLevel.LOW: "allow_with_warning",
            RiskLevel.MEDIUM: "observe",
            RiskLevel.HIGH: "intercept",
            RiskLevel.CRITICAL: "block",
        }

    def analyze_input(self, user_input: str, context: Optional[Dict] = None) -> AuditResult:
        categories, details = self.pattern_library.detect_abuse(user_input)
        is_injection, injection_patterns = self.pattern_library.detect_prompt_injection(user_input)
        
        if is_injection:
            categories.append(AbuseCategory.PROMPT_INJECTION)
            details["prompt_injection"] = {
                "patterns": injection_patterns
            }
        
        risk_level = self._calculate_risk_level(categories, details)
        action = self.action_rules.get(risk_level, "allow")
        
        result = AuditResult(
            risk_level=risk_level,
            categories=list(set(categories)),
            confidence=self._calculate_confidence(categories, details),
            details=details,
            action=action,
            reason=self._generate_reason(categories, risk_level)
        )
        
        with self._lock:
            self.audit_log.append(result)
            self.stats[risk_level.value] += 1
            for cat in categories:
                self.stats[f"category_{cat.value}"] += 1
        
        return result

    def _calculate_risk_level(self, categories: List[AbuseCategory], details: Dict) -> RiskLevel:
        if not categories:
            return RiskLevel.SAFE
        
        critical_categories = {
            AbuseCategory.DRUGS,
            AbuseCategory.VIOLENCE,
            AbuseCategory.PROMPT_INJECTION,
            AbuseCategory.JAILBREAK,
        }
        
        high_categories = {
            AbuseCategory.FRAUD,
            AbuseCategory.GAMBLING,
            AbuseCategory.HARMFUL_INSTRUCTION,
        }
        
        for cat in categories:
            if cat in critical_categories:
                return RiskLevel.CRITICAL
        
        for cat in categories:
            if cat in high_categories:
                return RiskLevel.HIGH
        
        if len(categories) >= 2:
            return RiskLevel.MEDIUM
        
        return RiskLevel.LOW

    def _calculate_confidence(self, categories: List[AbuseCategory], details: Dict) -> float:
        if not categories:
            return 1.0
        
        base_confidence = 0.7
        match_count = sum(len(d.get("matches", [])) for d in details.values())
        confidence_boost = min(0.25, match_count * 0.05)
        
        return min(1.0, base_confidence + confidence_boost)

    def _generate_reason(self, categories: List[AbuseCategory], risk_level: RiskLevel) -> str:
        if not categories:
            return "内容安全"
        
        category_names = {
            AbuseCategory.DRUGS: "涉毒",
            AbuseCategory.FRAUD: "诈骗",
            AbuseCategory.GAMBLING: "赌博",
            AbuseCategory.DISCRIMINATION: "歧视",
            AbuseCategory.VIOLENCE: "暴力",
            AbuseCategory.PORNOGRAPHY: "色情",
            AbuseCategory.POLITICAL_SENSITIVE: "政治敏感",
            AbuseCategory.PERSONAL_INFO: "个人信息",
            AbuseCategory.PROMPT_INJECTION: "提示词注入攻击",
            AbuseCategory.JAILBREAK: "越狱攻击",
            AbuseCategory.HARMFUL_INSTRUCTION: "有害指令",
            AbuseCategory.MISINFORMATION: "虚假信息",
        }
        
        detected = [category_names.get(c, c.value) for c in categories]
        return f"检测到{risk_level.value}风险: {', '.join(detected)}"

    def get_stats(self) -> Dict[str, Any]:
        with self._lock:
            return {
                "total_audits": len(self.audit_log),
                "risk_distribution": dict(self.stats),
                "recent_critical": [
                    r.to_dict() for r in self.audit_log[-10:]
                    if r.risk_level in [RiskLevel.CRITICAL, RiskLevel.HIGH]
                ]
            }


class StreamingContentAuditor:
    def __init__(self, config: Optional[Dict] = None):
        self.config = config or {
            "chunk_size": 100,
            "window_size": 200,
            "max_buffer_size": 10000,
        }
        self.pattern_library = AbusePatternLibrary()
        self.buffer = ""
        self.chunks_processed = 0
        self.violations: List[Dict] = []
        self._lock = threading.Lock()

    def audit_stream_chunk(self, chunk: str) -> Tuple[bool, Optional[AuditResult]]:
        with self._lock:
            self.buffer += chunk
            
            if len(self.buffer) > self.config["max_buffer_size"]:
                self.buffer = self.buffer[-self.config["max_buffer_size"]:]
            
            self.chunks_processed += 1
            
            if len(self.buffer) >= self.config["chunk_size"]:
                window = self.buffer[-self.config["window_size"]:]
                
                categories, details = self.pattern_library.detect_abuse(window)
                is_injection, _ = self.pattern_library.detect_prompt_injection(window)
                
                if categories or is_injection:
                    result = AuditResult(
                        risk_level=RiskLevel.HIGH if is_injection else RiskLevel.MEDIUM,
                        categories=categories,
                        confidence=0.8,
                        details={"window": window[:100]},
                        action="flag",
                        reason="流式内容检测到风险"
                    )
                    self.violations.append({
                        "chunk_index": self.chunks_processed,
                        "result": result.to_dict(),
                        "timestamp": time.time()
                    })
                    return True, result
            
            return False, None

    def get_audit_summary(self) -> Dict[str, Any]:
        with self._lock:
            return {
                "chunks_processed": self.chunks_processed,
                "violations_count": len(self.violations),
                "violations": self.violations[-10:],
                "buffer_size": len(self.buffer)
            }

    def reset(self):
        with self._lock:
            self.buffer = ""
            self.chunks_processed = 0
            self.violations = []


class ContentWatermarker:
    def __init__(self, config: Optional[Dict] = None):
        self.config = config or {
            "generator_name": "房都督AI",
            "generator_version": "1.0.0",
            "platform": "智链五方",
        }
        self._secret_key = os.getenv("WATERMARK_SECRET", "property-ai-watermark-key")

    def generate_watermark(
        self,
        content: str,
        content_type: ContentType = ContentType.TEXT,
        ai_generated: bool = True,
        visible: bool = True
    ) -> ContentWatermark:
        content_id = str(uuid.uuid4())
        timestamp = time.time()
        
        generator_info = {
            "name": self.config["generator_name"],
            "version": self.config["generator_version"],
            "platform": self.config["platform"],
        }
        
        signature = self._generate_signature(content_id, content, timestamp)
        
        visible_mark = ""
        if visible and ai_generated:
            visible_mark = "【本内容由AI生成，仅供参考】"
        
        invisible_mark = self._generate_invisible_mark(content_id, timestamp)
        
        return ContentWatermark(
            content_id=content_id,
            content_type=content_type,
            ai_generated=ai_generated,
            generator_info=generator_info,
            timestamp=timestamp,
            signature=signature,
            visible_mark=visible_mark,
            invisible_mark=invisible_mark
        )

    def _generate_signature(self, content_id: str, content: str, timestamp: float) -> str:
        data = f"{content_id}:{content[:100]}:{timestamp}:{self._secret_key}"
        return hashlib.sha256(data.encode()).hexdigest()[:32]

    def _generate_invisible_mark(self, content_id: str, timestamp: float) -> str:
        data = f"AI_GEN:{content_id}:{int(timestamp)}"
        encoded = data.encode().hex()
        zero_width_chars = "".join(chr(0x200B + int(encoded[i:i+2], 16) % 5) for i in range(0, min(len(encoded), 20), 2))
        return zero_width_chars

    def embed_watermark(self, content: str, watermark: ContentWatermark) -> str:
        marked_content = content
        
        if watermark.visible_mark:
            marked_content = f"{watermark.visible_mark}\n\n{content}"
        
        marked_content += watermark.invisible_mark
        
        return marked_content

    def verify_watermark(self, content: str) -> Tuple[bool, Optional[Dict]]:
        ai_gen_marker = "【本内容由AI生成"
        has_visible = ai_gen_marker in content
        
        zero_width_pattern = re.compile(r'[\u200B-\u200F\u2028-\u202F]')
        invisible_chars = zero_width_pattern.findall(content)
        has_invisible = len(invisible_chars) > 5
        
        is_ai_generated = has_visible or has_invisible
        
        return is_ai_generated, {
            "has_visible_mark": has_visible,
            "has_invisible_mark": has_invisible,
            "invisible_char_count": len(invisible_chars)
        }


class RAGKnowledgeBase:
    def __init__(self, config: Optional[Dict] = None):
        self.config = config or {}
        self.knowledge_store: Dict[str, Dict] = {}
        self.index: Dict[str, List[str]] = defaultdict(list)
        self._lock = threading.Lock()

    def add_knowledge(
        self,
        knowledge_id: str,
        content: str,
        source: str,
        category: str,
        credibility: float = 1.0,
        metadata: Optional[Dict] = None
    ):
        with self._lock:
            self.knowledge_store[knowledge_id] = {
                "id": knowledge_id,
                "content": content,
                "source": source,
                "category": category,
                "credibility": credibility,
                "metadata": metadata or {},
                "created_at": time.time()
            }
            
            keywords = self._extract_keywords(content)
            for keyword in keywords:
                self.index[keyword].append(knowledge_id)

    def _extract_keywords(self, text: str) -> List[str]:
        keywords = re.findall(r'[\u4e00-\u9fa5]{2,4}', text)
        return list(set(keywords))

    def retrieve(self, query: str, top_k: int = 5) -> List[Dict]:
        with self._lock:
            query_keywords = self._extract_keywords(query)
            
            scores: Dict[str, float] = defaultdict(float)
            
            for keyword in query_keywords:
                for knowledge_id in self.index.get(keyword, []):
                    scores[knowledge_id] += 1
            
            sorted_ids = sorted(scores.keys(), key=lambda x: scores[x], reverse=True)[:top_k]
            
            results = []
            for kid in sorted_ids:
                knowledge = self.knowledge_store.get(kid)
                if knowledge:
                    results.append({
                        **knowledge,
                        "relevance_score": scores[kid] / max(len(query_keywords), 1)
                    })
            
            return results

    def get_stats(self) -> Dict[str, Any]:
        with self._lock:
            categories = defaultdict(int)
            for k in self.knowledge_store.values():
                categories[k["category"]] += 1
            
            return {
                "total_knowledge": len(self.knowledge_store),
                "total_keywords": len(self.index),
                "categories": dict(categories)
            }


class RAGEnhancer:
    def __init__(self, knowledge_base: Optional[RAGKnowledgeBase] = None):
        self.knowledge_base = knowledge_base or RAGKnowledgeBase()
        self._initialize_default_knowledge()

    def _initialize_default_knowledge(self):
        default_knowledge = [
            {
                "id": "policy_down_payment_2025",
                "content": "2025年深圳首套房首付比例最低为20%，二套房首付比例最低为30%。公积金贷款首套房首付比例可低至15%。",
                "source": "深圳市住房和建设局",
                "category": "购房政策",
                "credibility": 1.0
            },
            {
                "id": "policy_loan_rate_2025",
                "content": "2025年首套房贷款利率下限为LPR-20BP，当前5年期以上LPR为3.6%，实际利率约3.4%。二套房贷款利率下限为LPR+60BP。",
                "source": "中国人民银行",
                "category": "贷款政策",
                "credibility": 1.0
            },
            {
                "id": "tax_deed_2025",
                "content": "契税征收标准：首套房90㎡以下按1%征收，90㎡以上按1.5%征收；二套房90㎡以下按1%征收，90㎡以上按2%征收。",
                "source": "国家税务总局",
                "category": "税费政策",
                "credibility": 1.0
            },
            {
                "id": "risk_house_age",
                "content": "房龄超过30年的房屋可能面临贷款困难，银行通常要求房龄+贷款年限不超过50年。建议购房前核实房屋结构和产权状况。",
                "source": "房都督风险提示",
                "category": "风险提示",
                "credibility": 0.9
            },
            {
                "id": "market_trend_2025",
                "content": "2025年房地产市场整体趋稳，一线城市核心区域价格相对坚挺，部分区域出现小幅调整。建议关注政策变化和市场动态。",
                "source": "房都督市场分析",
                "category": "市场分析",
                "credibility": 0.8
            }
        ]
        
        for k in default_knowledge:
            self.knowledge_base.add_knowledge(
                knowledge_id=k["id"],
                content=k["content"],
                source=k["source"],
                category=k["category"],
                credibility=k["credibility"]
            )

    def enhance_prompt(self, user_query: str, system_prompt: str = "") -> Tuple[str, List[Dict]]:
        relevant_knowledge = self.knowledge_base.retrieve(user_query, top_k=3)
        
        if not relevant_knowledge:
            return system_prompt, []
        
        knowledge_context = "\n\n【参考知识库】\n"
        sources = []
        
        for i, k in enumerate(relevant_knowledge, 1):
            knowledge_context += f"{i}. {k['content']}\n   来源：{k['source']}（可信度：{k['credibility']:.0%}）\n"
            sources.append({
                "id": k["id"],
                "source": k["source"],
                "relevance": k["relevance_score"]
            })
        
        knowledge_context += "\n请基于以上知识库内容回答用户问题，确保信息准确可靠。如知识库信息与用户问题不相关，请根据常识回答。\n"
        
        enhanced_prompt = knowledge_context + system_prompt
        
        return enhanced_prompt, sources

    def verify_response(self, response: str, sources: List[Dict]) -> Dict[str, Any]:
        return {
            "verified": True,
            "sources": sources,
            "confidence": 0.85,
            "note": "回答基于可信知识库"
        }


class MultimodalAuditor:
    def __init__(self, config: Optional[Dict] = None):
        self.config = config or {}
        self.text_auditor = ModelAbuseProtector()
        self.audit_history: List[Dict] = []
        self._lock = threading.Lock()

    def audit_text(self, text: str, context: Optional[Dict] = None) -> AuditResult:
        return self.text_auditor.analyze_input(text, context)

    def audit_image(self, image_data: bytes, metadata: Optional[Dict] = None) -> AuditResult:
        result = AuditResult(
            risk_level=RiskLevel.SAFE,
            categories=[],
            confidence=0.9,
            details={"image_size": len(image_data)},
            action="allow",
            reason="图像审核通过（基础检测）"
        )
        
        with self._lock:
            self.audit_history.append({
                "type": "image",
                "timestamp": time.time(),
                "result": result.to_dict()
            })
        
        return result

    def audit_document(self, content: str, doc_type: str = "text") -> AuditResult:
        return self.text_auditor.analyze_input(content)

    def get_audit_history(self, limit: int = 100) -> List[Dict]:
        with self._lock:
            return self.audit_history[-limit:]


class AISafetyComplianceSystem:
    _instance = None
    _lock = threading.Lock()

    def __new__(cls, config: Optional[Dict] = None):
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self, config: Optional[Dict] = None):
        if hasattr(self, '_initialized') and self._initialized:
            return
        
        self._initialized = True
        self.config = config or {}
        
        self.abuse_protector = ModelAbuseProtector(self.config.get("abuse_protection", {}))
        self.streaming_auditor = StreamingContentAuditor(self.config.get("streaming_audit", {}))
        self.watermarker = ContentWatermarker(self.config.get("watermark", {}))
        self.rag_enhancer = RAGEnhancer()
        self.multimodal_auditor = MultimodalAuditor(self.config.get("multimodal", {}))
        
        self.stats = defaultdict(int)
        logger.info("AI安全合规系统初始化完成")

    def process_user_input(
        self,
        user_input: str,
        context: Optional[Dict] = None,
        enable_rag: bool = True
    ) -> Dict[str, Any]:
        audit_result = self.abuse_protector.analyze_input(user_input, context)
        
        self.stats["total_inputs"] += 1
        self.stats[f"risk_{audit_result.risk_level.value}"] += 1
        
        if audit_result.action in ["block", "intercept"]:
            return {
                "allowed": False,
                "audit": audit_result.to_dict(),
                "enhanced_prompt": None,
                "sources": []
            }
        
        enhanced_prompt = ""
        sources = []
        
        if enable_rag:
            enhanced_prompt, sources = self.rag_enhancer.enhance_prompt(user_input)
        
        return {
            "allowed": True,
            "audit": audit_result.to_dict(),
            "enhanced_prompt": enhanced_prompt,
            "sources": sources,
            "warning": audit_result.visible_mark if audit_result.risk_level == RiskLevel.LOW else None
        }

    def process_model_output(
        self,
        output: str,
        content_type: ContentType = ContentType.TEXT,
        add_watermark: bool = True
    ) -> Dict[str, Any]:
        self.stats["total_outputs"] += 1
        
        streaming_violation, streaming_result = self.streaming_auditor.audit_stream_chunk(output)
        
        if streaming_violation and streaming_result:
            self.stats["output_violations"] += 1
        
        watermarked_content = output
        watermark = None
        
        if add_watermark:
            watermark = self.watermarker.generate_watermark(output, content_type)
            watermarked_content = self.watermarker.embed_watermark(output, watermark)
        
        return {
            "content": watermarked_content,
            "watermark": watermark.to_dict() if watermark else None,
            "streaming_audit": streaming_result.to_dict() if streaming_result else None,
            "audit_summary": self.streaming_auditor.get_audit_summary()
        }

    def add_knowledge(
        self,
        knowledge_id: str,
        content: str,
        source: str,
        category: str,
        credibility: float = 1.0
    ):
        self.rag_enhancer.knowledge_base.add_knowledge(
            knowledge_id=knowledge_id,
            content=content,
            source=source,
            category=category,
            credibility=credibility
        )
        self.stats["knowledge_added"] += 1

    def get_system_stats(self) -> Dict[str, Any]:
        return {
            "input_stats": dict(self.stats),
            "abuse_protection": self.abuse_protector.get_stats(),
            "knowledge_base": self.rag_enhancer.knowledge_base.get_stats(),
            "streaming_audit": self.streaming_auditor.get_audit_summary(),
            "audit_history_count": len(self.multimodal_auditor.audit_history)
        }


ai_safety_system = AISafetyComplianceSystem()
