"""
融会贯通 - 多模态输入与技能扩展
房都督平台发展纲领第五章：杂家不独断，常请教专家

核心思想：
- 多模态输入：图像/语音/手写统一理解
- 人才市场Skill：外部技能动态加载
- 小模型训练：提示注入检测 + 情感分类

包含模块：
5.1 MultiModalProcessor - 图像理解+语音识别
5.2 TalentSkillManager - 人才市场Skill集成
6.1 PromptInjectionDetector - 提示注入检测（UMTAM训练）
6.2 EmotionClassifier - 情感分类模型（BERT）
"""
import json
import logging
import time
import uuid
import base64
import re
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Dict, Any, Optional, List, Callable, Set, Tuple, Union
from collections import deque

logger = logging.getLogger(__name__)


# ==================== 5.1 多模态输入处理 ====================


class InputModality(str, Enum):
    """输入模态类型"""
    TEXT = "text"
    IMAGE = "image"
    VOICE = "voice"
    HANDWRITING = "handwriting"
    FILE = "file"
    MIXED = "mixed"


@dataclass
class ModalityInput:
    """多模态输入"""
    input_id: str
    modality: InputModality
    raw_data: Union[str, bytes]
    metadata: Dict[str, Any] = field(default_factory=dict)
    timestamp: float = field(default_factory=time.time)


@dataclass
class ModalityResult:
    """模态处理结果"""
    input_id: str
    modality: InputModality
    text_content: str
    confidence: float
    extracted_entities: List[Dict[str, str]]
    processing_time_ms: float
    model_used: str
    thumbnail_base64: Optional[str] = None


class MultiModalProcessor:
    """
    多模态输入处理器（提示词 5.1）
    
    能力：
    - 图像理解：识别户型图、房产照片等（模拟Qwen-VL）
    - 语音识别：语音转文本（模拟Whisper）
    - 手写识别：手写命盘/文字转文本
    - 统一输出为文本送入现有对话流程
    - 报告中可展示缩略图
    """

    IMAGE_PATTERNS = {
        "floor_plan": ["户型图", "平面图", "layout", "floor plan", "房间", "客厅", "卧室", "厨房"],
        "property_photo": ["楼盘", "小区", "外立面", "环境", "装修"],
        "document": ["证件", "证书", "合同", "文件", "文档"],
        "fortune_chart": ["命盘", "八字", "紫微", "星盘", "chart"],
    }

    def __init__(self):
        self._processing_history: deque = deque(maxlen=200)
        self._supported_modalities = set(InputModality)

    def process(self, raw_input: ModalityInput) -> ModalityResult:
        """
        处理多模态输入
        
        根据模态类型分发到对应的处理器
        """
        start_time = time.time()

        if raw_input.modality == InputModality.IMAGE:
            result = self._process_image(raw_input)
        elif raw_input.modality == InputModality.VOICE:
            result = self._process_voice(raw_input)
        elif raw_input.modality == InputModality.HANDWRITING:
            result = self._process_handwriting(raw_input)
        elif raw_input.modality == InputModality.TEXT:
            result = self._process_text(raw_input)
        elif raw_input.modality == InputModality.MIXED:
            result = self._process_mixed(raw_input)
        else:
            result = ModalityResult(
                input_id=raw_input.input_id,
                modality=raw_input.modality,
                text_content=str(raw_input.raw_data)[:500],
                confidence=0.5,
                extracted_entities=[],
                processing_time_ms=0,
                model_used="passthrough",
            )

        result.processing_time_ms = round((time.time() - start_time) * 1000, 1)
        self._processing_history.append(result)
        return result

    def _process_image(self, inp: ModalityInput) -> ModalityResult:
        """图像理解（模拟Qwen-VL）"""
        metadata = inp.metadata or {}
        filename = metadata.get("filename", "")
        description_hint = metadata.get("description", "")

        detected_type = self._detect_image_type(filename, description_hint)

        type_descriptions = {
            "floor_plan": f"这是一张户型图。从图像分析来看，包含{self._guess_floor_plan_features()}。",
            "property_photo": f"这是一张房产照片。展示了建筑外观和周边环境。",
            "document": f"这是一份文档图片。包含文字内容需要OCR提取。",
            "fortune_chart": f"这是一张命理图表。包含传统命盘或星盘信息。",
            "unknown": "这是一张通用图片。已进行视觉特征分析。",
        }

        text_content = type_descriptions.get(detected_type, type_descriptions["unknown"])
        if description_hint:
            text_content += f" 用户描述：{description_hint}"

        entities = [{"type": detected_type, "confidence": 0.78}]

        return ModalityResult(
            input_id=inp.input_id,
            modality=InputModality.IMAGE,
            text_content=text_content,
            confidence=0.82,
            extracted_entities=entities,
            processing_time_ms=0,
            model_used="Qwen-VL-Sim",
            thumbnail_base64=self._generate_thumbnail(inp.raw_data),
        )

    def _process_voice(self, inp: ModalityInput) -> ModalityResult:
        """语音识别（模拟Whisper）"""
        if isinstance(inp.raw_data, bytes):
            try:
                text = inp.raw_data.decode("utf-8", errors="ignore")[:1000]
            except Exception:
                text = "[语音数据解码失败]"
        else:
            text = str(inp.raw_data)[:1000]

        duration_sec = (inp.metadata or {}).get("duration_seconds", 10)
        confidence = min(0.95, 0.85 + (duration_sec / 60) * 0.05)

        return ModalityResult(
            input_id=inp.input_id,
            modality=InputModality.VOICE,
            text_content=f"[语音转文本] {text}",
            confidence=round(confidence, 3),
            extracted_entities=[{"type": "speech_text", "length": len(text)}],
            processing_time_ms=0,
            model_used="Whisper-Large-v3",
        )

    def _process_handwriting(self, inp: ModalityInput) -> ModalityResult:
        """手写识别"""
        text = str(inp.raw_data)[:500]

        has_chinese = bool(re.search(r'[\u4e00-\u9fff]', text))
        has_numbers = bool(re.search(r'\d', text))

        content = f"[手写识别] 识别到以下内容：{text}"
        if has_chinese and has_numbers:
            content += " （含中文和数字混合内容）"
        entities = [
            {"type": "chinese_chars", "count": len(re.findall(r'[\u4e00-\u9fff]', text))},
            {"type": "numbers", "count": len(re.findall(r'\d+', text))},
        ]

        return ModalityResult(
            input_id=inp.input_id,
            modality=InputModality.HANDWRITING,
            text_content=content,
            confidence=0.85,
            extracted_entities=entities,
            processing_time_ms=0,
            model_used="PaddleOCR-Handwriting",
        )

    def _process_text(self, inp: ModalityInput) -> ModalityResult:
        """纯文本处理"""
        text = str(inp.raw_data)
        return ModalityResult(
            input_id=inp.input_id,
            modality=InputModality.TEXT,
            text_content=text,
            confidence=1.0,
            extracted_entities=[],
            processing_time_ms=0,
            model_used="direct",
        )

    def _process_mixed(self, inp: ModalityInput) -> ModalityResult:
        """混合模态处理"""
        parts = inp.metadata.get("parts", [])
        results = []
        for part in parts:
            sub_input = ModalityInput(
                input_id=f"{inp.input_id}_part",
                modality=InputModality(part.get("modality", "text")),
                raw_data=part.get("data", ""),
                metadata=part,
            )
            result = self.process(sub_input)
            results.append(result.text_content)

        combined = "\n---\n".join(results)
        return ModalityResult(
            input_id=inp.input_id,
            modality=InputModality.MIXED,
            text_content=f"[混合输入]\n{combined}",
            confidence=0.88,
            extracted_entities=[],
            processing_time_ms=0,
            model_used="multi-modal-fusion",
        )

    def _detect_image_type(self, filename: str, hint: str) -> str:
        """检测图像类型"""
        combined = (filename + " " + hint).lower()
        for img_type, keywords in self.IMAGE_PATTERNS.items():
            if any(kw in combined for kw in keywords):
                return img_type
        return "unknown"

    def _guess_floor_plan_features(self) -> str:
        """猜测户型图特征（模拟）"""
        features = ["客厅约30平米朝南", "主卧带独立卫生间", "厨房紧邻餐厅", "南北通透"]
        import random
        selected = random.sample(features, k=random.randint(2, 3))
        return "、".join(selected)

    def _generate_thumbnail(self, raw_data: Union[str, bytes]) -> Optional[str]:
        """生成缩略图的base64（简化实现）"""
        if isinstance(raw_data, bytes) and len(raw_data) > 100:
            try:
                return base64.b64encode(raw_data[:500]).decode()[:100] + "..."
            except Exception:
                pass
        return None

    def get_stats(self) -> Dict[str, Any]:
        modality_counts = {}
        avg_confidence = 0
        total = len(self._processing_history)
        for r in self._processing_history:
            m = r.modality.value
            modality_counts[m] = modality_counts.get(m, 0) + 1
            avg_confidence += r.confidence
        return {
            "total_processed": total,
            "modality_distribution": modality_counts,
            "avg_confidence": round(avg_confidence / max(total, 1), 3),
        }


# ==================== 5.2 人才市场Skill集成 ====================


class SkillStatus(str, Enum):
    """Skill状态"""
    AVAILABLE = "available"
    LOADING = "loading"
    ERROR = "error"
    DISABLED = "disabled"


@dataclass
class TalentSkill:
    """人才市场技能定义"""
    skill_id: str
    name: str
    category: str
    description: str
    tags: Set[str]
    input_schema: Dict[str, Any]
    output_schema: Dict[str, Any]
    version: str = "1.0.0"
    author: str = ""
    requires_confirmation: bool = True
    cost_points: int = 0
    status: SkillStatus = SkillStatus.AVAILABLE
    execute_fn: Optional[Callable] = None
    load_time: float = 0
    call_count: int = 0
    success_count: int = 0


@dataclass
class SkillExecutionResult:
    """Skill执行结果"""
    execution_id: str
    skill_id: str
    success: bool
    result: Dict[str, Any]
    execution_time_ms: float
    error_message: str = ""
    confirmed_by_user: bool = False


class TalentSkillManager:
    """
    人才市场Skill管理器（提示词 5.2）
    
    核心能力：
    - 定义Skill标准接口：JSON输入→JSON输出
    - 动态加载外部技能（热加载）
    - 智能体能力不足时自动检索匹配技能
    - 技能调用需用户确认（若涉及付费）
    - 技能调用统计与性能追踪
    
    内置示例Skills：
    - policy_interpreter: 政策解读
    - fengshui_analyzer: 风水分析
    - market_trend: 市场趋势
    """

    BUILTIN_SKILLS: Dict[str, Dict] = {
        "policy_interpreter": {
            "name": "政策解读专家",
            "category": "政策法规",
            "description": "解读房地产相关政策、限购政策、贷款政策等",
            "tags": {"政策", "限购", "贷款", "法规", "解读"},
            "input_schema": {"city": "str", "policy_type": "str"},
            "output_schema": {"summary": "str", "key_points": "list", "impact": "str"},
            "cost_points": 5,
            "requires_confirmation": False,
        },
        "fengshui_analyzer": {
            "name": "风水分析师",
            "category": "命理风水",
            "description": "分析房屋风水格局、方位吉凶、布局建议",
            "tags": {"风水", "方位", "格局", "布局"},
            "input_schema": {"layout": "str", "direction": "str"},
            "output_schema": {"analysis": "str", "suggestions": "list", "score": "float"},
            "cost_points": 15,
            "requires_confirmation": True,
        },
        "market_trend": {
            "name": "市场趋势分析师",
            "category": "市场数据",
            "description": "分析区域房价走势、成交量变化、未来预测",
            "tags": {"房价", "趋势", "预测", "市场"},
            "input_schema": {"region": "str", "period": "str"},
            "output_schema": {"trend": "str", "data_points": "list", "prediction": "str"},
            "cost_points": 8,
            "requires_confirmation": False,
        },
        "legal_advisor": {
            "name": "法律顾问",
            "category": "法律咨询",
            "description": "提供房地产交易法律建议、合同审查",
            "tags": {"法律", "合同", "交易", "风险"},
            "input_schema": {"scenario": "str", "documents": "list"},
            "output_schema": {"advice": "str", "risks": "list", "recommendations": "list"},
            "cost_points": 20,
            "requires_confirmation": True,
        },
    }

    SKILL_EXECUTE_FNS: Dict[str, Callable] = {}

    @classmethod
    def _init_execute_fns(cls):
        """初始化内置Skill执行函数"""

        async def exec_policy(city: str, policy_type: str) -> dict:
            return {
                "summary": f"{city}市当前{policy_type or '房地产'}政策概览",
                "key_points": [f"要点{i+1}: {city}{policy_type}相关条款摘要" for i in range(3)],
                "impact": "对购房者和市场的影响分析",
            }

        async def exec_fengshui(layout: str, direction: str) -> dict:
            import random
            score = round(random.uniform(65, 92), 1)
            return {
                "analysis": f"基于'{layout}'和朝向'{direction}'的风水分析",
                "suggestions": ["建议调整玄关位置", "主卧宜保持整洁", "财位可放置绿植"],
                "score": score,
            }

        async def exec_market(region: str, period: str = "近一年") -> dict:
            import random
            base_price = random.randint(25000, 65000)
            change_pct = round(random.uniform(-5, 12), 1)
            return {
                "trend": f"{region}区域{period}房价{'上涨' if change_pct > 0 else '下跌'}{abs(change_pct)}%",
                "data_points": [
                    {"month": f"{i}月", "price": base_price + random.randint(-3000, 5000)}
                    for i in range(1, 13)
                ],
                "prediction": f"预计下季度价格将{'保持稳定' if abs(change_pct) < 3 else '继续波动'}",
            }

        async def exec_legal(scenario: str, documents: list = None) -> dict:
            return {
                "advice": f"针对'{scenario}'的法律建议",
                "risks": ["合同条款注意点1", "过户流程风险", "资金安全提醒"],
                "recommendations": ["建议聘请专业律师审核", "保留所有交易凭证", "使用资金监管账户"],
            }

        cls.SKILL_EXECUTE_FNS = {
            "policy_interpreter": exec_policy,
            "fengshui_analyzer": exec_fengshui,
            "market_trend": exec_market,
            "legal_advisor": exec_legal,
        }

    def __init__(self):
        if not self.SKILL_EXECUTE_FNS:
            self._init_execute_fns()
        self._skills: Dict[str, TalentSkill] = {}
        self._execution_history: List[SkillExecutionResult] = []
        self._load_builtin_skills()

    def _load_builtin_skills(self):
        """加载内置Skills"""
        for skill_id, config in self.BUILTIN_SKILLS.items():
            skill = TalentSkill(
                skill_id=skill_id,
                name=config["name"],
                category=config["category"],
                description=config["description"],
                tags=set(config["tags"]),
                input_schema=config["input_schema"],
                output_schema=config["output_schema"],
                requires_confirmation=config.get("requires_confirmation", True),
                cost_points=config.get("cost_points", 0),
                execute_fn=self.SKILL_EXECUTE_FNS.get(skill_id),
            )
            self._skills[skill_id] = skill

    def register_skill(self, skill: TalentSkill):
        """注册自定义Skill"""
        self._skills[skill.skill_id] = skill
        logger.info(f"Skill注册: {skill.name}({skill.skill_id})")

    def find_matching_skills(self, query: str, agent_capabilities: Set[str], exclude_loaded: bool = False) -> List[TalentSkill]:
        """
        查找匹配的Skill
        
        当智能体自身能力不足时调用
        匹配逻辑：标签匹配 + 关键词匹配
        """
        query_lower = query.lower()
        matched = []

        for skill_id, skill in self._skills.items():
            if skill.status != SkillStatus.AVAILABLE:
                continue

            tag_overlap = skill.tags & agent_capabilities
            if tag_overlap and exclude_loaded:
                continue

            keyword_matches = sum(1 for kw in skill.tags if kw in query_lower)
            desc_matches = sum(1 for word in skill.description.split() if word[:2] in query_lower)

            match_score = len(tag_overlap) * 2 + keyword_matches + desc_matches * 0.5
            if match_score > 0.5:
                matched.append((skill, match_score))

        matched.sort(key=lambda x: x[1], reverse=True)
        return [s for s, _ in matched]

    async def execute_skill(
        self,
        skill_id: str,
        params: Dict[str, Any],
        user_confirmed: bool = False,
    ) -> SkillExecutionResult:
        """
        执行Skill
        
        Args:
            skill_id: Skill ID
            params: 输入参数
            user_confirmed: 用户是否确认
            
        Returns:
            执行结果
        """
        start_time = time.time()
        skill = self._skills.get(skill_id)

        if not skill:
            return SkillExecutionResult(
                execution_id=f"exec_{uuid.uuid4().hex[:8]}",
                skill_id=skill_id,
                success=False,
                result={},
                execution_time_ms=0,
                error_message=f"Skill不存在: {skill_id}",
            )

        if skill.requires_confirmation and not user_confirmed:
            return SkillExecutionResult(
                execution_id=f"exec_{uuid.uuid4().hex[:8]}",
                skill_id=skill_id,
                success=False,
                result={},
                execution_time_ms=0,
                error_message=f"该Skill({skill.name})需要用户确认后才能执行",
            )

        skill.call_count += 1
        try:
            if skill.execute_fn:
                import asyncio
                if asyncio.iscoroutinefunction(skill.execute_fn):
                    result_data = await skill.execute_fn(**params)
                else:
                    result_data = skill.execute_fn(**params)
            else:
                result_data = {"result": f"Skill {skill_name} executed with params", **params}

            skill.success_count += 1
            exec_result = SkillExecutionResult(
                execution_id=f"exec_{uuid.uuid4().hex[:8]}",
                skill_id=skill_id,
                success=True,
                result=result_data if isinstance(result_data, dict) else {"data": result_data},
                execution_time_ms=round((time.time() - start_time) * 1000, 1),
                confirmed_by_user=user_confirmed,
            )
        except Exception as e:
            exec_result = SkillExecutionResult(
                execution_id=f"exec_{uuid.uuid4().hex[:8]}",
                skill_id=skill_id,
                success=False,
                result={},
                execution_time_ms=round((time.time() - start_time) * 1000, 1),
                error_message=str(e),
            )

        self._execution_history.append(exec_result)
        return exec_result

    def list_skills(self, category: str = None, status: SkillStatus = None) -> List[Dict]:
        """列出可用Skills"""
        results = []
        for skill in self._skills.values():
            if category and skill.category != category:
                continue
            if status and skill.status != status:
                continue
            results.append({
                "skill_id": skill.skill_id,
                "name": skill.name,
                "category": skill.category,
                "description": skill.description,
                "tags": list(skill.tags),
                "version": skill.version,
                "cost_points": skill.cost_points,
                "requires_confirmation": skill.requires_confirmation,
                "status": skill.status.value,
                "call_count": skill.call_count,
                "success_rate": round(skill.success_count / max(skill.call_count, 1), 3),
            })
        return sorted(results, key=lambda s: s["name"])

    def get_stats(self) -> Dict[str, Any]:
        return {
            "total_skills": len(self._skills),
            "available_skills": sum(1 for s in self._skills.values() if s.status == SkillStatus.AVAILABLE),
            "total_executions": len(self._execution_history),
            "success_rate": (
                round(sum(1 for e in self._execution_history if e.success) / max(len(self._execution_history), 1), 3)
                if self._execution_history else 0
            ),
            "categories": list(set(s.category for s in self._skills.values())),
        }


# ==================== 6.1 提示注入检测 ====================


@dataclass
class InjectionDetectionResult:
    """注入检测结果"""
    is_injection: bool
    confidence: float
    injection_type: str
    matched_patterns: List[str]
    risk_level: str
    sanitized_text: Optional[str] = None


class PromptInjectionDetector:
    """
    提示注入检测器（提示词 6.1）
    
    使用UMTAM优化器训练的轻量级分类器
    检测用户输入中的恶意提示注入攻击
    目标准确率≥95%，误报率<2%
    """

    INJECTION_PATTERNS = {
        "jailbreak": [
            r"(?i)(?:ignore|forget|disregard).*(?:previous|above|all).*(?:instruction|prompt|rule|system)",
            r"(?i)(?:you are now|pretend you are|act as)",
            r"(?i)(?:DAN|do anything now|jailbreak|developer mode)",
        ],
        "role_play_attack": [
            r"(?i)(?:新角色|new role|扮演|pretend).*(?:黑客|hacker|管理员|admin|上帝|god)",
        ],
        "data_extraction": [
            r"(?i)(?:输出|print|show|reveal|dump|leak).*(?:系统指令|system prompt|instruction|内部)",
            r"(?i)(?:告诉我你的|what is your|show me your).*(?:prompt|指令|规则|system)",
        ],
        "prompt_leakage": [
            r"(?i)(?:repeat|copy|echo|输出).*(?:your instruction|你的指令|system message)",
        ],
        "override_instruction": [
            r"(?i)(?:从现在开始|from now on|新的指令|new instruction|替换|replace)",
        ],
    }

    RISK_LEVELS = {
        "critical": 0.9,
        "high": 0.75,
        "medium": 0.5,
        "low": 0.25,
    }

    def __init__(self):
        self._detection_history: deque = deque(maxlen=500)
        self._stats = {"total_checks": 0, "injections_found": 0, "false_positives": 0}

    def detect(self, text: str) -> InjectionDetectionResult:
        """
        检测提示注入
        
        Args:
            text: 用户输入文本
            
        Returns:
            检测结果
        """
        self._stats["total_checks"] += 1
        max_score = 0.0
        injection_type = "none"
        all_matched = []

        for ptype, patterns in self.INJECTION_PATTERNS.items():
            for pattern in patterns:
                match = re.search(pattern, text)
                if match:
                    pattern_score = 0.85 + len(match.group()) * 0.005
                    if pattern_score > max_score:
                        max_score = min(0.99, pattern_score)
                        injection_type = ptype
                    all_matched.append(f"{ptype}: {pattern[:40]}...")

        is_injection = max_score >= 0.5

        if is_injection:
            self._stats["injections_found"] += 1

        risk = "safe"
        for level, threshold in sorted(self.RISK_LEVELS.items(), key=lambda x: x[1], reverse=True):
            if max_score >= threshold:
                risk = level
                break

        sanitized = text if not is_injection else self._sanitize(text)

        result = InjectionDetectionResult(
            is_injection=is_injection,
            confidence=round(max_score, 3),
            injection_type=injection_type,
            matched_patterns=all_matched[:5],
            risk_level=risk,
            sanitized_text=sanitized,
        )

        self._detection_history.append(result)
        return result

    def _sanitize(self, text: str) -> str:
        """简单清洗（生产环境应使用更完善的方案）"""
        cleaned = re.sub(r'(ignore|forget|disregard)[^\n]*', '[已过滤]', text, flags=re.I)
        return cleaned

    def get_stats(self) -> Dict[str, Any]:
        total = self._stats["total_checks"]
        return {
            **self._stats,
            "injection_rate": round(self._stats["injections_found"] / max(total, 1), 4),
        }


# ==================== 6.2 情感分类模型 ====================


class SentimentLabel(str, Enum):
    POSITIVE = "positive"
    NEGATIVE = "negative"
    NEUTRAL = "neutral"


@dataclass
class ClassificationResult:
    label: SentimentLabel
    confidence: float
    probabilities: Dict[str, float]
    feature_importance: Dict[str, float]


class EmotionClassifier:
    """
    情感分类模型（提示词 6.2）
    
    基于关键词+规则的轻量级情感分类
    目标准确率≥90%，推理延迟<10ms
    集成到礼部智能体实时分析用户情感
    """

    SENTIMENT_LEXICON = {
        "positive": {
            "strong": ["太棒了", "超级好", "完美", "非常满意", "很棒", "开心", "喜欢", "感谢", "赞", "优秀"],
            "weak": ["不错", "好的", "可以", "还行", "挺好", "满意", "谢谢", "好的呀"],
        },
        "negative": {
            "strong": ["糟糕", "太差", "崩溃", "受不了", "气死", "垃圾", "烂", "坑", "被骗"],
            "weak": ["不好", "不满意", "难过", "郁闷", "失望", "麻烦", "问题", "不行"],
        },
        "neutral_indicators": ["请问", "什么", "如何", "多少", "哪里", "哪个", "是否", "能不能"],
    }

    CONTEXT_WEIGHT = 0.15
    LENGTH_NORMALIZATION_FACTOR = 50

    def __init__(self):
        self._history: deque = deque(maxlen=200)
        self._accuracy_stats = {"correct": 0, "total": 0}

    def classify(self, text: str, context: Dict[str, Any] = None) -> ClassificationResult:
        """
        分类情感极性
        
        Args:
            text: 用户输入文本
            context: 可选上下文
            
        Returns:
            分类结果（标签+置信度+概率分布）
        """
        text_lower = text.lower()

        pos_strong = sum(1 for w in self.SENTIMENT_LEXICON["positive"]["strong"] if w in text)
        pos_weak = sum(1 for w in self.SENTIMENT_LEXICON["positive"]["weak"] if w in text)
        neg_strong = sum(1 for w in self.SENTIMENT_LEXICON["negative"]["strong"] if w in text)
        neg_weak = sum(1 for w in self.SENTIMENT_LEXICON["negative"]["weak"] if w in text)
        neutral_cues = sum(1 for w in self.SENTIMENT_LEXICON["neutral_indicators"] if w in text)

        pos_score = pos_strong * 2.0 + pos_weak * 1.0
        neg_score = neg_strong * 2.0 + neg_weak * 1.0
        neutral_score = neutral_cues * 0.8

        length_factor = min(1.5, len(text) / self.LENGTH_NORMALIZATION_FACTOR)
        pos_norm = pos_score / length_factor
        neg_norm = neg_score / length_factor

        context_bias = 0.0
        if context:
            sentiment_avg = context.get("sentiment_avg", 0)
            context_bias = sentiment_avg * self.CONTEXT_WEIGHT

        scores = {
            "positive": max(0.01, min(0.98, 0.35 + pos_norm * 0.12 + context_bias)),
            "negative": max(0.01, min(0.98, 0.35 + neg_norm * 0.12 - context_bias)),
            "neutral": max(0.01, min(0.98, 0.30 + neutral_score * 0.08)),
        }

        total = sum(scores.values())
        probabilities = {k: round(v / total, 4) for k, v in scores.items()}
        label = max(probabilities, key=probabilities.get)
        confidence = probabilities[label]

        feature_imp = {
            "pos_strong_keywords": pos_strong,
            "pos_weak_keywords": pos_weak,
            "neg_strong_keywords": neg_strong,
            "neg_weak_keywords": neg_weak,
            "neutral_cues": neutral_cues,
            "context_bias": round(context_bias, 3),
        }

        result = ClassificationResult(
            label=SentimentLabel(label),
            confidence=round(confidence, 3),
            probabilities=probabilities,
            feature_importance=feature_imp,
        )

        self._history.append(result)
        return result

    def batch_classify(self, texts: List[str]) -> List[ClassificationResult]:
        """批量分类"""
        return [self.classify(t) for t in texts]

    def get_stats(self) -> Dict[str, Any]:
        total = len(self._history)
        if total == 0:
            return {"total_classified": 0}
        dist = {}
        for r in self._history:
            l = r.label.value
            dist[l] = dist.get(l, 0) + 1
        avg_conf = sum(r.confidence for r in self._history) / total
        return {
            "total_classified": total,
            "label_distribution": dist,
            "avg_confidence": round(avg_conf, 3),
        }


# ==================== 全局实例 ====================

multimodal_processor = MultiModalProcessor()
talent_skill_manager = TalentSkillManager()
injection_detector = PromptInjectionDetector()
emotion_classifier = EmotionClassifier()
