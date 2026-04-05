"""
用户心理分析服务
类似DeepSeek的心理描述机制，分析用户购房心理状态
"""
import re
from typing import Dict, Any, List, Optional
from dataclasses import dataclass
from enum import Enum
import logging

logger = logging.getLogger(__name__)


class UserIntent(Enum):
    """用户意图类型"""
    INVESTMENT = "投资导向"
    OWNER_OCCUPIED = "自住需求"
    FIRST_TIME_BUYER = "首次购房"
    IMPROVEMENT = "改善置换"
    SCHOOL_DISTRICT = "学区刚需"
    RETIREMENT = "养老置业"
    UNCERTAIN = "犹豫观望"


class EmotionalState(Enum):
    """情绪状态"""
    ANXIOUS = "焦虑"
    EXCITED = "兴奋"
    CONFUSED = "困惑"
    CONFIDENT = "自信"
    URGE = "急迫"
    CALM = "冷静"
    HESITANT = "犹豫"


class DecisionStage(Enum):
    """决策阶段"""
    EXPLORATION = "探索期"
    COMPARISON = "比较期"
    DECISION = "决策期"
    ACTION = "行动期"


@dataclass
class PsychologicalProfile:
    """用户心理画像"""
    intent: UserIntent
    emotional_state: EmotionalState
    decision_stage: DecisionStage
    confidence_level: float
    urgency_level: float
    price_sensitivity: float
    risk_preference: str
    key_concerns: List[str]
    hidden_needs: List[str]
    communication_style: str
    recommended_approach: str
    psychological_description: str


class PsychologicalAnalyzer:
    """心理分析器"""
    
    INTENT_KEYWORDS = {
        UserIntent.INVESTMENT: [
            "投资", "升值", "回报", "租金", "收益", "保值", "理财",
            "未来价值", "涨价", "潜力", "转手", "赚"
        ],
        UserIntent.OWNER_OCCUPIED: [
            "自住", "自己住", "居住", "生活", "安家", "落户",
            "结婚", "婚房", "家庭"
        ],
        UserIntent.FIRST_TIME_BUYER: [
            "首套", "第一次", "刚需", "小白", "不懂", "新手",
            "没买过", "开始看"
        ],
        UserIntent.IMPROVEMENT: [
            "改善", "置换", "换房", "升级", "大一点", "换大",
            "二套", "第二套", "更好的"
        ],
        UserIntent.SCHOOL_DISTRICT: [
            "学区", "学校", "孩子上学", "教育", "小学", "中学",
            "幼儿园", "名校", "学位"
        ],
        UserIntent.RETIREMENT: [
            "养老", "退休", "老人", "父母住", "环境好", "安静",
            "空气好", "养老房"
        ],
    }
    
    EMOTIONAL_INDICATORS = {
        EmotionalState.ANXIOUS: [
            "急", "担心", "怕", "焦虑", "不知道怎么办", "纠结",
            "怕买贵", "怕买错", "来不及", "错过"
        ],
        EmotionalState.EXCITED: [
            "期待", "兴奋", "终于", "太好了", "很想", "迫不及待",
            "马上", "立刻"
        ],
        EmotionalState.CONFUSED: [
            "不懂", "迷茫", "不知道", "搞不清楚", "分不清", "困惑",
            "怎么选", "哪个好", "没头绪"
        ],
        EmotionalState.CONFIDENT: [
            "确定", "肯定", "就要", "只看", "明确", "清楚",
            "了解", "知道"
        ],
        EmotionalState.URGE: [
            "急用", "马上", "尽快", "越快越好", "等不了", "这周",
            "这个月", "立刻"
        ],
        EmotionalState.CALM: [
            "慢慢看", "不急", "先了解", "参考", "看看再说",
            "比较一下", "慢慢选"
        ],
        EmotionalState.HESITANT: [
            "犹豫", "纠结", "再想想", "考虑", "不确定", "也许",
            "可能", "还是", "但是"
        ],
    }
    
    DECISION_INDICATORS = {
        DecisionStage.EXPLORATION: [
            "想了解", "看看", "咨询", "了解一下", "大概", "初步",
            "刚开始", "先看看"
        ],
        DecisionStage.COMPARISON: [
            "比较", "对比", "哪个好", "区别", "优缺点", "选择",
            "A还是B", "哪个更"
        ],
        DecisionStage.DECISION: [
            "决定", "选定", "就这个", "差不多", "准备买", "考虑买",
            "想买"
        ],
        DecisionStage.ACTION: [
            "马上买", "这周", "签约", "定金", "首付", "贷款",
            "过户", "成交"
        ],
    }
    
    CONCERN_KEYWORDS = {
        "价格": ["价格", "贵", "便宜", "预算", "多少钱", "划算", "性价比"],
        "位置": ["位置", "地段", "交通", "地铁", "距离", "方便", "远"],
        "学区": ["学校", "学区", "教育", "孩子", "上学"],
        "环境": ["环境", "绿化", "安静", "噪音", "空气", "采光"],
        "户型": ["户型", "朝向", "面积", "房间", "格局", "通透"],
        "品质": ["品质", "物业", "开发商", "质量", "烂尾", "交付"],
        "投资": ["升值", "保值", "转手", "租金", "回报"],
    }
    
    def analyze(self, text: str, parsed_data: Dict[str, Any] = None) -> PsychologicalProfile:
        """
        分析用户心理
        
        Args:
            text: 用户输入文本
            parsed_data: 解析后的需求数据
            
        Returns:
            PsychologicalProfile: 用户心理画像
        """
        intent = self._detect_intent(text)
        emotional_state = self._detect_emotional_state(text)
        decision_stage = self._detect_decision_stage(text)
        confidence_level = self._calculate_confidence(text, parsed_data)
        urgency_level = self._calculate_urgency(text)
        price_sensitivity = self._calculate_price_sensitivity(text, parsed_data)
        risk_preference = self._determine_risk_preference(text, intent)
        key_concerns = self._extract_key_concerns(text)
        hidden_needs = self._infer_hidden_needs(text, intent, emotional_state)
        communication_style = self._detect_communication_style(text)
        recommended_approach = self._generate_approach(intent, emotional_state, decision_stage)
        psychological_description = self._generate_description(
            intent, emotional_state, decision_stage, confidence_level, urgency_level
        )
        
        return PsychologicalProfile(
            intent=intent,
            emotional_state=emotional_state,
            decision_stage=decision_stage,
            confidence_level=confidence_level,
            urgency_level=urgency_level,
            price_sensitivity=price_sensitivity,
            risk_preference=risk_preference,
            key_concerns=key_concerns,
            hidden_needs=hidden_needs,
            communication_style=communication_style,
            recommended_approach=recommended_approach,
            psychological_description=psychological_description
        )
    
    def _detect_intent(self, text: str) -> UserIntent:
        """检测用户意图"""
        scores = {}
        for intent, keywords in self.INTENT_KEYWORDS.items():
            score = sum(1 for kw in keywords if kw in text)
            if score > 0:
                scores[intent] = score
        
        if scores:
            return max(scores, key=scores.get)
        return UserIntent.UNCERTAIN
    
    def _detect_emotional_state(self, text: str) -> EmotionalState:
        """检测情绪状态"""
        scores = {}
        for state, indicators in self.EMOTIONAL_INDICATORS.items():
            score = sum(1 for ind in indicators if ind in text)
            if score > 0:
                scores[state] = score
        
        if scores:
            return max(scores, key=scores.get)
        return EmotionalState.CALM
    
    def _detect_decision_stage(self, text: str) -> DecisionStage:
        """检测决策阶段"""
        scores = {}
        for stage, indicators in self.DECISION_INDICATORS.items():
            score = sum(1 for ind in indicators if ind in text)
            if score > 0:
                scores[stage] = score
        
        if scores:
            return max(scores, key=scores.get)
        return DecisionStage.EXPLORATION
    
    def _calculate_confidence(self, text: str, parsed_data: Dict[str, Any]) -> float:
        """计算信心程度"""
        confidence = 0.5
        
        confident_phrases = ["确定", "肯定", "明确", "就要", "清楚"]
        uncertain_phrases = ["可能", "也许", "不确定", "不知道", "纠结"]
        
        for phrase in confident_phrases:
            if phrase in text:
                confidence += 0.1
        
        for phrase in uncertain_phrases:
            if phrase in text:
                confidence -= 0.1
        
        if parsed_data:
            if parsed_data.get("city"):
                confidence += 0.1
            if parsed_data.get("district"):
                confidence += 0.1
            if parsed_data.get("price_max"):
                confidence += 0.1
            if parsed_data.get("room_count"):
                confidence += 0.05
        
        return max(0.1, min(1.0, confidence))
    
    def _calculate_urgency(self, text: str) -> float:
        """计算紧迫程度"""
        urgency = 0.3
        
        high_urgency = ["马上", "立刻", "急", "这周", "这个月", "等不了"]
        medium_urgency = ["尽快", "想买", "准备"]
        low_urgency = ["慢慢", "不急", "先看看", "了解一下"]
        
        for phrase in high_urgency:
            if phrase in text:
                urgency += 0.3
        
        for phrase in medium_urgency:
            if phrase in text:
                urgency += 0.15
        
        for phrase in low_urgency:
            if phrase in text:
                urgency -= 0.2
        
        return max(0.1, min(1.0, urgency))
    
    def _calculate_price_sensitivity(self, text: str, parsed_data: Dict[str, Any]) -> float:
        """计算价格敏感度"""
        sensitivity = 0.5
        
        sensitive_phrases = ["贵", "便宜", "预算", "划算", "性价比", "多少钱", "能便宜"]
        insensitive_phrases = ["不在乎", "无所谓", "主要看", "价格不是问题"]
        
        for phrase in sensitive_phrases:
            if phrase in text:
                sensitivity += 0.15
        
        for phrase in insensitive_phrases:
            if phrase in text:
                sensitivity -= 0.2
        
        if parsed_data and parsed_data.get("price_max"):
            sensitivity += 0.1
        
        return max(0.1, min(1.0, sensitivity))
    
    def _determine_risk_preference(self, text: str, intent: UserIntent) -> str:
        """确定风险偏好"""
        conservative = ["稳妥", "安全", "确定", "现房", "成熟"]
        aggressive = ["潜力", "升值", "新盘", "期房", "投资"]
        
        conservative_score = sum(1 for p in conservative if p in text)
        aggressive_score = sum(1 for p in aggressive if p in text)
        
        if intent == UserIntent.INVESTMENT:
            aggressive_score += 2
        elif intent == UserIntent.FIRST_TIME_BUYER:
            conservative_score += 1
        
        if aggressive_score > conservative_score:
            return "进取型"
        elif conservative_score > aggressive_score:
            return "保守型"
        else:
            return "平衡型"
    
    def _extract_key_concerns(self, text: str) -> List[str]:
        """提取关键关注点"""
        concerns = []
        for concern, keywords in self.CONCERN_KEYWORDS.items():
            if any(kw in text for kw in keywords):
                concerns.append(concern)
        return concerns[:5] if concerns else ["综合考量"]
    
    def _infer_hidden_needs(self, text: str, intent: UserIntent, emotional_state: EmotionalState) -> List[str]:
        """推断潜在需求"""
        hidden_needs = []
        
        if intent == UserIntent.FIRST_TIME_BUYER:
            hidden_needs.append("需要专业指导和信任建立")
        
        if emotional_state == EmotionalState.ANXIOUS:
            hidden_needs.append("需要安抚和确定性信息")
        
        if emotional_state == EmotionalState.CONFUSED:
            hidden_needs.append("需要清晰的对比和解释")
        
        if intent == UserIntent.INVESTMENT:
            hidden_needs.append("关注投资回报和风险分析")
        
        if "孩子" in text or "学区" in text:
            hidden_needs.append("教育资源配置是核心决策因素")
        
        if "父母" in text or "养老" in text:
            hidden_needs.append("医疗配套和交通便利是关键")
        
        if not hidden_needs:
            hidden_needs.append("需要进一步沟通了解深层需求")
        
        return hidden_needs
    
    def _detect_communication_style(self, text: str) -> str:
        """检测沟通风格"""
        if len(text) < 15:
            return "简洁型"
        
        if "？" in text or "?" in text:
            return "提问型"
        
        if any(word in text for word in ["我觉得", "我认为", "我的想法"]):
            return "表达型"
        
        if any(word in text for word in ["帮我", "请问", "咨询"]):
            return "求助型"
        
        return "信息型"
    
    def _generate_approach(self, intent: UserIntent, emotional_state: EmotionalState, 
                          decision_stage: DecisionStage) -> str:
        """生成沟通策略建议"""
        approaches = []
        
        if emotional_state == EmotionalState.ANXIOUS:
            approaches.append("先安抚情绪，提供确定性信息")
        
        if emotional_state == EmotionalState.CONFUSED:
            approaches.append("使用对比表格，简化决策")
        
        if decision_stage == DecisionStage.EXPLORATION:
            approaches.append("提供全面信息，建立信任")
        elif decision_stage == DecisionStage.COMPARISON:
            approaches.append("重点对比分析，突出优势")
        elif decision_stage == DecisionStage.DECISION:
            approaches.append("强化信心，推动决策")
        elif decision_stage == DecisionStage.ACTION:
            approaches.append("提供行动指引，促成成交")
        
        if intent == UserIntent.FIRST_TIME_BUYER:
            approaches.append("耐心解释专业术语，避免信息过载")
        elif intent == UserIntent.INVESTMENT:
            approaches.append("重点分析投资回报和风险")
        
        return "；".join(approaches) if approaches else "标准咨询服务流程"
    
    def _generate_description(self, intent: UserIntent, emotional_state: EmotionalState,
                             decision_stage: DecisionStage, confidence: float, urgency: float) -> str:
        """生成心理描述"""
        intent_desc = {
            UserIntent.INVESTMENT: "投资型买家，关注资产增值",
            UserIntent.OWNER_OCCUPIED: "自住型买家，注重生活品质",
            UserIntent.FIRST_TIME_BUYER: "首次购房者，需要更多指导",
            UserIntent.IMPROVEMENT: "改善型买家，追求更好居住体验",
            UserIntent.SCHOOL_DISTRICT: "学区刚需，教育是首要考量",
            UserIntent.RETIREMENT: "养老置业，环境配套是关键",
            UserIntent.UNCERTAIN: "需求尚不明确，需要深入沟通",
        }
        
        emotion_desc = {
            EmotionalState.ANXIOUS: "当前处于焦虑状态",
            EmotionalState.EXCITED: "对购房充满期待",
            EmotionalState.CONFUSED: "面临选择困惑",
            EmotionalState.CONFIDENT: "目标明确，信心充足",
            EmotionalState.URGE: "购房意愿迫切",
            EmotionalState.CALM: "心态平和，理性决策",
            EmotionalState.HESITANT: "存在决策犹豫",
        }
        
        stage_desc = {
            DecisionStage.EXPLORATION: "处于信息探索阶段",
            DecisionStage.COMPARISON: "正在比较不同选项",
            DecisionStage.DECISION: "接近最终决策",
            DecisionStage.ACTION: "准备付诸行动",
        }
        
        confidence_desc = "信心充足" if confidence > 0.6 else "信心一般" if confidence > 0.4 else "信心不足"
        urgency_desc = "时间紧迫" if urgency > 0.6 else "时间适中" if urgency > 0.4 else "时间充裕"
        
        description = f"【用户心理画像】{intent_desc[intent]}，{emotion_desc[emotional_state]}，{stage_desc[decision_stage]}。{confidence_desc}，{urgency_desc}。"
        
        return description


psychological_analyzer = PsychologicalAnalyzer()


async def analyze_user_psychology(text: str, parsed_data: Dict[str, Any] = None) -> Dict[str, Any]:
    """
    分析用户心理（便捷函数）
    
    Args:
        text: 用户输入文本
        parsed_data: 解析后的需求数据
        
    Returns:
        心理分析结果
    """
    profile = psychological_analyzer.analyze(text, parsed_data)
    
    return {
        "intent": {
            "type": profile.intent.value,
            "description": f"用户意图：{profile.intent.value}"
        },
        "emotional_state": {
            "type": profile.emotional_state.value,
            "description": f"情绪状态：{profile.emotional_state.value}"
        },
        "decision_stage": {
            "type": profile.decision_stage.value,
            "description": f"决策阶段：{profile.decision_stage.value}"
        },
        "metrics": {
            "confidence_level": round(profile.confidence_level, 2),
            "urgency_level": round(profile.urgency_level, 2),
            "price_sensitivity": round(profile.price_sensitivity, 2),
        },
        "risk_preference": profile.risk_preference,
        "key_concerns": profile.key_concerns,
        "hidden_needs": profile.hidden_needs,
        "communication_style": profile.communication_style,
        "recommended_approach": profile.recommended_approach,
        "psychological_description": profile.psychological_description,
    }
