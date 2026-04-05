"""
高级对话处理引擎
包含：二进制转换、智能体分配、关键词匹配、追问机制、过程可视化
优化：预编译正则表达式、缓存机制
"""
import json
import logging
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass, field
from datetime import datetime
import re
from functools import lru_cache

logger = logging.getLogger(__name__)


@dataclass
class ProcessingStep:
    """处理步骤"""
    step_id: str
    step_name: str
    step_type: str
    status: str
    input_data: Any
    output_data: Any
    timestamp: str
    duration_ms: int = 0
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class AgentAssignment:
    """智能体分配"""
    agent_id: str
    agent_name: str
    agent_type: str
    confidence: float
    reason: str
    capabilities: List[str] = field(default_factory=list)
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class KeywordMatch:
    """关键词匹配结果"""
    keyword: str
    category: str
    value: Any
    confidence: float
    source_text: str


@dataclass
class MissingInfo:
    """缺失信息"""
    field_name: str
    field_label: str
    importance: str
    question: str
    suggestions: List[str] = field(default_factory=list)


@dataclass
class DialogueProcess:
    """对话处理过程"""
    session_id: str
    user_input: str
    binary_input: str
    decoded_input: str
    steps: List[ProcessingStep]
    agent_assignments: List[AgentAssignment]
    keywords_matched: List[KeywordMatch]
    missing_info: List[MissingInfo]
    final_response: str
    binary_response: str
    needs_follow_up: bool
    follow_up_question: Optional[str]
    info_collected: bool
    collected_count: int
    created_at: str


class InputProcessor:
    """输入处理器 - 处理二进制转换"""
    
    _binary_cache: Dict[str, str] = {}
    _text_cache: Dict[str, str] = {}
    _cache_max_size = 1000
    
    @staticmethod
    @lru_cache(maxsize=500)
    def text_to_binary(text: str) -> str:
        """将文本转换为二进制字符串（空格分隔）- 带缓存"""
        try:
            binary = ' '.join(format(ord(char), '08b') for char in text)
            return binary
        except Exception as e:
            logger.error(f"Text to binary conversion failed: {e}")
            return ""
    
    @staticmethod
    @lru_cache(maxsize=500)
    def binary_to_text(binary: str) -> str:
        """将二进制字符串转换为文本 - 带缓存"""
        try:
            binary = binary.replace(' ', '')
            text = ''.join(chr(int(binary[i:i+8], 2)) for i in range(0, len(binary), 8))
            return text
        except Exception as e:
            logger.error(f"Binary to text conversion failed: {e}")
            return binary
    
    def process_input(self, text: str, is_binary: bool = False) -> Tuple[str, str, ProcessingStep]:
        """处理用户输入，返回 (二进制, 解码文本, 步骤)"""
        start_time = datetime.now()
        
        if is_binary:
            decoded = self.binary_to_text(text)
            binary = text
        else:
            binary = self.text_to_binary(text)
            decoded = text
        
        end_time = datetime.now()
        duration = int((end_time - start_time).total_seconds() * 1000)
        
        step = ProcessingStep(
            step_id=f"input_{datetime.now().strftime('%Y%m%d%H%M%S%f')}",
            step_name="输入处理",
            step_type="input_processing",
            status="completed",
            input_data=text[:100] + "..." if len(text) > 100 else text,
            output_data={"binary_length": len(binary), "decoded_length": len(decoded)},
            timestamp=datetime.now().isoformat(),
            duration_ms=duration,
            metadata={"encoding": "UTF-8", "is_binary_input": is_binary}
        )
        
        return binary, decoded, step


class AgentRouter:
    """智能体路由器 - 分配最适合的智能体"""
    
    AGENTS = {
        "property_analyst": {
            "name": "房产分析师",
            "type": "analysis",
            "capabilities": ["房价分析", "市场趋势", "投资建议"],
            "keywords": ["房价", "价格", "投资", "升值", "市场", "趋势", "分析"]
        },
        "area_expert": {
            "name": "区域专家",
            "type": "location",
            "capabilities": ["区域介绍", "周边配套", "交通分析"],
            "keywords": ["区域", "位置", "周边", "配套", "交通", "地铁", "学校", "医院"]
        },
        "loan_advisor": {
            "name": "贷款顾问",
            "type": "finance",
            "capabilities": ["贷款计算", "利率分析", "还款方案"],
            "keywords": ["贷款", "利率", "首付", "月供", "还款", "公积金", "商业贷"]
        },
        "policy_expert": {
            "name": "政策专家",
            "type": "policy",
            "capabilities": ["购房政策", "限购限贷", "税费计算"],
            "keywords": ["政策", "限购", "限贷", "税费", "契税", "资格", "户口"]
        },
        "community_guide": {
            "name": "小区向导",
            "type": "community",
            "capabilities": ["小区介绍", "房源推荐", "户型分析"],
            "keywords": ["小区", "楼盘", "户型", "房源", "推荐", "物业", "开发商"]
        }
    }
    
    _agent_keywords_cache = None
    
    @classmethod
    def _get_agent_keywords(cls):
        if cls._agent_keywords_cache is None:
            cls._agent_keywords_cache = {
                agent_id: set(info["keywords"]) 
                for agent_id, info in cls.AGENTS.items()
            }
        return cls._agent_keywords_cache
    
    def assign_agents(self, text: str) -> Tuple[List[AgentAssignment], ProcessingStep]:
        """根据用户输入分配智能体"""
        start_time = datetime.now()
        assignments = []
        
        text_lower = text.lower()
        agent_keywords = self._get_agent_keywords()
        
        for agent_id, agent_info in self.AGENTS.items():
            matched_keywords = []
            keywords_set = agent_keywords[agent_id]
            
            for keyword in keywords_set:
                if keyword in text_lower:
                    matched_keywords.append(keyword)
            
            if matched_keywords:
                confidence = len(matched_keywords) / len(keywords_set)
                assignments.append(AgentAssignment(
                    agent_id=agent_id,
                    agent_name=agent_info["name"],
                    agent_type=agent_info["type"],
                    confidence=min(confidence * 2, 1.0),
                    reason=f"匹配关键词: {', '.join(matched_keywords)}",
                    capabilities=agent_info["capabilities"]
                ))
        
        assignments.sort(key=lambda x: x.confidence, reverse=True)
        
        if not assignments:
            assignments.append(AgentAssignment(
                agent_id="general_assistant",
                agent_name="通用助手",
                agent_type="general",
                confidence=0.5,
                reason="未匹配特定领域，使用通用助手",
                capabilities=["一般咨询", "基础问答"]
            ))
        
        end_time = datetime.now()
        duration = int((end_time - start_time).total_seconds() * 1000)
        
        step = ProcessingStep(
            step_id=f"agent_{datetime.now().strftime('%Y%m%d%H%M%S%f')}",
            step_name="智能体分配",
            step_type="agent_routing",
            status="completed",
            input_data=text,
            output_data=[{"agent": a.agent_name, "confidence": a.confidence} for a in assignments],
            timestamp=datetime.now().isoformat(),
            duration_ms=duration,
            metadata={"total_agents": len(assignments)}
        )
        
        return assignments[:3], step


class KeywordExtractor:
    """关键词提取器 - 预编译正则表达式"""
    
    _compiled_patterns = None
    
    @classmethod
    def _get_compiled_patterns(cls):
        if cls._compiled_patterns is None:
            patterns = {
                "location": {
                    "city": r"(北京|上海|广州|深圳|杭州|南京|成都|武汉|西安|重庆|天津|苏州|厦门|青岛|大连|宁波|无锡|佛山|东莞|珠海)",
                    "district": r"([^\s]+区|县)",
                },
                "budget": {
                    "price_range": r"(\d+)\s*[-~至]\s*(\d+)\s*(万|百万|千万)?",
                    "max_budget": r"(预算|总价|最高).{0,5}(\d+)\s*(万|百万)?",
                    "min_budget": r"(最低|最少).{0,5}(\d+)\s*(万|百万)?",
                },
                "property_type": {
                    "house_type": r"(\d+)\s*室\s*(\d+)\s*厅?",
                    "area": r"(\d+)\s*(平米|平方米|㎡)",
                    "floor": r"(\d+)\s*层",
                },
                "purpose": {
                    "purchase_purpose": r"(自住|投资|学区房|婚房|养老|改善)",
                },
                "time": {
                    "time_frame": r"(近期|半年内|一年内|明年|后年|急|不急)",
                },
                "family": {
                    "family_structure": r"(单身|夫妻|一家三口|有孩子|有老人|三代同堂)",
                }
            }
            cls._compiled_patterns = {}
            for category, fields in patterns.items():
                cls._compiled_patterns[category] = {}
                for field_name, pattern in fields.items():
                    cls._compiled_patterns[category][field_name] = re.compile(pattern)
        return cls._compiled_patterns
    
    def extract_keywords(self, text: str) -> Tuple[List[KeywordMatch], ProcessingStep]:
        """从文本中提取关键词"""
        start_time = datetime.now()
        matches = []
        
        compiled = self._get_compiled_patterns()
        
        for category, patterns in compiled.items():
            for field_name, regex in patterns.items():
                found = regex.findall(text)
                
                if found:
                    for match in found if isinstance(found, list) else [found]:
                        match_text = match if isinstance(match, str) else str(match)
                        matches.append(KeywordMatch(
                            keyword=field_name,
                            category=category,
                            value=match_text,
                            confidence=0.9,
                            source_text=text
                        ))
        
        end_time = datetime.now()
        duration = int((end_time - start_time).total_seconds() * 1000)
        
        step = ProcessingStep(
            step_id=f"keyword_{datetime.now().strftime('%Y%m%d%H%M%S%f')}",
            step_name="关键词提取",
            step_type="keyword_extraction",
            status="completed",
            input_data=text,
            output_data=[{"keyword": m.keyword, "value": m.value, "category": m.category} for m in matches],
            timestamp=datetime.now().isoformat(),
            duration_ms=duration,
            metadata={"total_keywords": len(matches)}
        )
        
        return matches, step


class MissingInfoDetector:
    """缺失信息检测器"""
    
    REQUIRED_FIELDS = {
        "high": [
            {"field": "city", "label": "城市", "question": "您想在哪个城市购房？", "suggestions": ["北京", "上海", "深圳", "广州", "杭州"]},
            {"field": "budget", "label": "预算", "question": "您的购房预算大概是多少?", "suggestions": ["200-300万", "300-500万", "500-800万", "800万以上"]},
        ],
        "medium": [
            {"field": "house_type", "label": "户型", "question": "您需要几室几厅的房子?", "suggestions": ["两室一厅", "三室两厅", "四室两厅"]},
            {"field": "purpose", "label": "购房目的", "question": "您购房的主要目的是什么?", "suggestions": ["自住", "投资", "学区房", "改善住房"]},
        ],
        "low": [
            {"field": "time_frame", "label": "购房时间", "question": "您计划什么时候购房?", "suggestions": ["近期", "半年内", "一年内", "还在看"]},
            {"field": "family_structure", "label": "家庭情况", "question": "方便告诉我您的家庭情况吗?", "suggestions": ["单身", "夫妻", "有孩子", "三代同堂"]},
        ]
    }
    
    def detect_missing_info(self, keywords: List[KeywordMatch]) -> Tuple[List[MissingInfo], ProcessingStep]:
        """检测缺失的关键信息"""
        start_time = datetime.now()
        
        extracted_fields = {k.keyword for k in keywords}
        missing = []
        
        for importance, fields in self.REQUIRED_FIELDS.items():
            for field_info in fields:
                if field_info["field"] not in extracted_fields:
                    missing.append(MissingInfo(
                        field_name=field_info["field"],
                        field_label=field_info["label"],
                        importance=importance,
                        question=field_info["question"],
                        suggestions=field_info.get("suggestions", [])
                    ))
        
        end_time = datetime.now()
        duration = int((end_time - start_time).total_seconds() * 1000)
        
        step = ProcessingStep(
            step_id=f"missing_{datetime.now().strftime('%Y%m%d%H%M%S%f')}",
            step_name="缺失信息检测",
            step_type="missing_info_detection",
            status="completed",
            input_data=[k.keyword for k in keywords],
            output_data=[{"field": m.field_name, "importance": m.importance} for m in missing],
            timestamp=datetime.now().isoformat(),
            duration_ms=duration,
            metadata={"total_missing": len(missing)}
        )
        
        return missing, step
    
    def detect_missing_info_with_history(
        self, 
        keywords: List[KeywordMatch],
        collected_keywords: Dict[str, Any]
    ) -> Tuple[List[MissingInfo], ProcessingStep]:
        """检测缺失的关键信息（结合历史已收集的关键词）"""
        start_time = datetime.now()
        
        extracted_fields = {k.keyword for k in keywords}
        all_collected = set(collected_keywords.keys()) if collected_keywords else set()
        missing = []
        
        for importance, fields in self.REQUIRED_FIELDS.items():
            for field_info in fields:
                if field_info["field"] not in extracted_fields and field_info["field"] not in all_collected:
                    missing.append(MissingInfo(
                        field_name=field_info["field"],
                        field_label=field_info["label"],
                        importance=importance,
                        question=field_info["question"],
                        suggestions=field_info.get("suggestions", [])
                    ))
        
        end_time = datetime.now()
        duration = int((end_time - start_time).total_seconds() * 1000)
        
        step = ProcessingStep(
            step_id=f"missing_{datetime.now().strftime('%Y%m%d%H%M%S%f')}",
            step_name="缺失信息检测",
            step_type="missing_info_detection",
            status="completed",
            input_data={"current_keywords": [k.keyword for k in keywords], "collected": list(all_collected)},
            output_data=[{"field": m.field_name, "importance": m.importance} for m in missing],
            timestamp=datetime.now().isoformat(),
            duration_ms=duration,
            metadata={"total_missing": len(missing), "already_collected": list(all_collected)}
        )
        
        return missing, step
    
    def generate_follow_up_question(
        self, 
        missing_info: List[MissingInfo],
        history: List[Dict[str, Any]] = None
    ) -> Optional[str]:
        """生成追问问题"""
        asked_fields = set()
        
        if history:
            for msg in history[-6:]:
                if msg["role"] == "assistant" and msg["content"]:
                    for field_info in self.REQUIRED_FIELDS.get("high", []):
                        if field_info["question"] in msg["content"]:
                            asked_fields.add(field_info["field"])
        
        high_priority = [m for m in missing_info if m.importance == "high" and m.field_name not in asked_fields]
        
        if high_priority:
            info = high_priority[0]
            suggestions_text = "、".join(info.suggestions[:3]) if info.suggestions else ""
            if suggestions_text:
                return f"{info.question}\n\n您可以选择：{suggestions_text}"
            return info.question
        
        medium_priority = [m for m in missing_info if m.importance == "medium" and m.field_name not in asked_fields]
        if medium_priority:
            info = medium_priority[0]
            suggestions_text = "、".join(info.suggestions[:3]) if info.suggestions else ""
            if suggestions_text:
                return f"{info.question}\n\n您可以选择：{suggestions_text}"
            return info.question
        
        return None


class DialogueEngine:
    """对话引擎 - 整合所有处理模块，支持二进制转换和上下文记忆"""
    
    MIN_REQUIRED_INFO = 2
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance.input_processor = InputProcessor()
            cls._instance.agent_router = AgentRouter()
            cls._instance.keyword_extractor = KeywordExtractor()
            cls._instance.missing_detector = MissingInfoDetector()
        return cls._instance
    
    async def process_message(
        self, 
        session_id: str, 
        user_input: str,
        history: List[Dict[str, Any]] = None,
        collected_keywords: Dict[str, Any] = None,
        is_binary: bool = False
    ) -> DialogueProcess:
        """处理用户消息，支持二进制输入和上下文记忆"""
        steps = []
        
        binary, decoded, input_step = self.input_processor.process_input(user_input, is_binary)
        steps.append(input_step)
        
        agents, agent_step = self.agent_router.assign_agents(decoded)
        steps.append(agent_step)
        
        keywords, keyword_step = self.keyword_extractor.extract_keywords(decoded)
        steps.append(keyword_step)
        
        all_keywords = {k.keyword: k.value for k in keywords}
        if collected_keywords:
            all_keywords.update(collected_keywords)
        
        missing, missing_step = self.missing_detector.detect_missing_info_with_history(
            keywords, 
            collected_keywords or {}
        )
        steps.append(missing_step)
        
        high_priority_missing = [m for m in missing if m.importance == "high"]
        collected_count = len(all_keywords)
        info_collected = collected_count >= self.MIN_REQUIRED_INFO
        
        if info_collected or len(high_priority_missing) == 0:
            follow_up = None
            needs_follow_up = False
        else:
            follow_up = self.missing_detector.generate_follow_up_question(missing, history)
            needs_follow_up = follow_up is not None
        
        response = self._generate_response(
            agents, keywords, missing, follow_up, history, 
            collected_keywords, info_collected, collected_count
        )
        
        binary_response = self.input_processor.text_to_binary(response)
        
        return DialogueProcess(
            session_id=session_id,
            user_input=user_input,
            binary_input=binary,
            decoded_input=decoded,
            steps=steps,
            agent_assignments=agents,
            keywords_matched=keywords,
            missing_info=missing,
            final_response=response,
            binary_response=binary_response,
            needs_follow_up=needs_follow_up,
            follow_up_question=follow_up,
            info_collected=info_collected,
            collected_count=collected_count,
            created_at=datetime.now().isoformat()
        )
    
    def _generate_response(
        self,
        agents: List[AgentAssignment],
        keywords: List[KeywordMatch],
        missing: List[MissingInfo],
        follow_up: Optional[str],
        history: List[Dict[str, Any]] = None,
        collected_keywords: Dict[str, Any] = None,
        info_collected: bool = False,
        collected_count: int = 0
    ) -> str:
        """生成响应"""
        response_parts = []
        
        if collected_keywords and len(collected_keywords) > 0:
            collected_summary = [f"**{k}**: {v}" for k, v in collected_keywords.items()]
            response_parts.append(f"📋 **已收集信息 ({collected_count}项)：**\n" + "\n".join([f"  - {s}" for s in collected_summary]))
        
        if agents:
            primary_agent = agents[0]
            response_parts.append(f"\n🔍 已为您分配 **{primary_agent.agent_name}** 来处理您的咨询")
        
        if keywords:
            keyword_summary = []
            for kw in keywords[:5]:
                keyword_summary.append(f"  - **{kw.keyword}**: {kw.value}")
            response_parts.append("\n📝 **本次识别信息：**\n" + "\n".join(keyword_summary))
        
        if info_collected:
            response_parts.append("\n✅ **信息收集完成！** 正在为您启动智能分析...")
            if agents:
                response_parts.append(f"\n🎯 **{primary_agent.agent_name}** 正在分析您的需求...")
                response_parts.append(f"\n💡 基于您的需求，我可以为您提供：")
                for cap in primary_agent.capabilities[:3]:
                    response_parts.append(f"  - {cap}")
        elif follow_up:
            response_parts.append(f"\n❓ {follow_up}")
        
        return "\n".join(response_parts)
    
    def to_dict(self, process: DialogueProcess) -> Dict[str, Any]:
        """将处理过程转换为字典"""
        return {
            "session_id": process.session_id,
            "user_input": process.user_input[:200] if len(process.user_input) > 200 else process.user_input,
            "binary_input": process.binary_input[:500] if len(process.binary_input) > 500 else process.binary_input,
            "decoded_input": process.decoded_input,
            "steps": [
                {
                    "step_id": s.step_id,
                    "step_name": s.step_name,
                    "step_type": s.step_type,
                    "status": s.status,
                    "input_data": s.input_data,
                    "output_data": s.output_data,
                    "timestamp": s.timestamp,
                    "duration_ms": s.duration_ms,
                    "metadata": s.metadata
                }
                for s in process.steps
            ],
            "agent_assignments": [
                {
                    "agent_id": a.agent_id,
                    "agent_name": a.agent_name,
                    "agent_type": a.agent_type,
                    "confidence": a.confidence,
                    "reason": a.reason,
                    "capabilities": a.capabilities
                }
                for a in process.agent_assignments
            ],
            "keywords_matched": [
                {
                    "keyword": k.keyword,
                    "category": k.category,
                    "value": k.value,
                    "confidence": k.confidence
                }
                for k in process.keywords_matched
            ],
            "missing_info": [
                {
                    "field_name": m.field_name,
                    "field_label": m.field_label,
                    "importance": m.importance,
                    "question": m.question,
                    "suggestions": m.suggestions
                }
                for m in process.missing_info
            ],
            "final_response": process.final_response,
            "binary_response": process.binary_response,
            "needs_follow_up": process.needs_follow_up,
            "follow_up_question": process.follow_up_question,
            "info_collected": process.info_collected,
            "collected_count": process.collected_count,
            "created_at": process.created_at
        }
