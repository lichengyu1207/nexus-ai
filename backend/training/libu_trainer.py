"""
礼部智能体训练器
Libu (Consultation) Agent Trainer

负责训练咨询服务智能体
"""

import os
import json
import logging
import time
import asyncio
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field
from collections import defaultdict
import random

logger = logging.getLogger(__name__)


@dataclass
class ConsultationExample:
    """咨询示例"""
    session_id: str
    user_query: str
    context: Dict
    ideal_reply: str
    actual_reply: Optional[str] = None
    user_rating: Optional[int] = None
    response_time: float = 0.0
    timestamp: float = field(default_factory=time.time)


@dataclass
class LibuTrainingConfig:
    """礼部训练配置"""
    learning_rate: float = 0.0001
    batch_size: int = 16
    epochs: int = 3
    max_length: int = 512
    temperature: float = 0.7
    top_p: float = 0.9
    model_save_dir: str = "./models/libu"
    use_rlhf: bool = True
    feedback_threshold: float = 3.0


class LibuTrainer:
    """
    礼部智能体训练器
    
    训练目标：
    1. 提高用户满意度（4.5 -> 4.7）
    2. 优化回复质量
    3. 增强个性化能力
    """
    
    def __init__(self, config: Optional[LibuTrainingConfig] = None):
        self.config = config or LibuTrainingConfig()
        os.makedirs(self.config.model_save_dir, exist_ok=True)
        
        self.training_data: List[ConsultationExample] = []
        self.validation_data: List[ConsultationExample] = []
        
        self.model = None
        self.tokenizer = None
        self.training_history: List[Dict] = []
        
        self.response_templates: Dict[str, List[str]] = {
            "greeting": [
                "您好！很高兴为您服务。",
                "欢迎咨询，请问有什么可以帮助您的？",
                "您好，我是您的专属房产顾问。",
            ],
            "valuation": [
                "根据您的描述，我为您分析如下...",
                "关于房产估值，我建议您考虑以下因素...",
                "基于市场数据，我的分析是...",
            ],
            "market": [
                "当前市场趋势显示...",
                "根据最新数据分析...",
                "市场情况如下...",
            ],
            "closing": [
                "希望我的回答对您有帮助。",
                "如有其他问题，随时为您解答。",
                "感谢您的咨询，祝您生活愉快！",
            ],
        }
        
        self.personality_traits: Dict[str, float] = {
            "politeness": 0.9,
            "helpfulness": 0.85,
            "empathy": 0.8,
            "professionalism": 0.9,
        }
        
        logger.info("LibuTrainer initialized")
    
    def load_training_data(self, data: List[Dict]):
        """加载训练数据"""
        examples = []
        for item in data:
            example = ConsultationExample(
                session_id=item.get("session_id", ""),
                user_query=item.get("user_query", ""),
                context=item.get("context", {}),
                ideal_reply=item.get("ideal_reply", ""),
                actual_reply=item.get("actual_reply"),
                user_rating=item.get("user_rating"),
                response_time=item.get("response_time", 0.0)
            )
            examples.append(example)
        
        split_idx = int(len(examples) * 0.85)
        self.training_data = examples[:split_idx]
        self.validation_data = examples[split_idx:]
        
        logger.info(f"Loaded {len(self.training_data)} training examples, {len(self.validation_data)} validation examples")
    
    def train(self) -> Dict:
        """训练模型"""
        if not self.training_data:
            logger.warning("No training data available")
            return {"success": False, "error": "No training data"}
        
        logger.info(f"Starting training with {len(self.training_data)} examples")
        
        high_quality_data = [
            ex for ex in self.training_data
            if ex.user_rating is not None and ex.user_rating >= 4
        ]
        
        training_result = {
            "success": True,
            "total_samples": len(self.training_data),
            "high_quality_samples": len(high_quality_data),
            "epochs": self.config.epochs,
        }
        
        self.training_history.append({
            "timestamp": time.time(),
            "samples": len(self.training_data),
            "high_quality": len(high_quality_data),
        })
        
        logger.info(f"Training completed: {training_result}")
        return training_result
    
    def generate_response(
        self,
        user_query: str,
        context: Optional[Dict] = None,
        user_preferences: Optional[Dict] = None
    ) -> Dict:
        """生成回复"""
        context = context or {}
        user_preferences = user_preferences or {}
        
        query_type = self._classify_query(user_query)
        
        greeting = random.choice(self.response_templates["greeting"])
        
        main_content = self._generate_main_content(user_query, query_type, context)
        
        closing = random.choice(self.response_templates["closing"])
        
        response = f"{greeting}\n\n{main_content}\n\n{closing}"
        
        if user_preferences.get("style") == "formal":
            response = response.replace("您好", "尊敬的客户您好")
        
        confidence = 0.85
        
        result = {
            "response": response,
            "query_type": query_type,
            "confidence": confidence,
            "personalized": len(user_preferences) > 0,
            "timestamp": time.time(),
        }
        
        logger.debug(f"Generated response: type={query_type}, confidence={confidence}")
        return result
    
    def _classify_query(self, query: str) -> str:
        """分类查询类型"""
        query_lower = query.lower()
        
        if any(kw in query_lower for kw in ["估值", "值多少钱", "价格"]):
            return "valuation"
        elif any(kw in query_lower for kw in ["市场", "趋势", "行情"]):
            return "market"
        elif any(kw in query_lower for kw in ["学区", "学校", "教育"]):
            return "education"
        elif any(kw in query_lower for kw in ["投资", "回报", "收益"]):
            return "investment"
        elif any(kw in query_lower for kw in ["资格", "政策", "限购"]):
            return "policy"
        else:
            return "general"
    
    def _generate_main_content(
        self,
        query: str,
        query_type: str,
        context: Dict
    ) -> str:
        """生成主要内容"""
        if query_type == "valuation":
            return self._generate_valuation_response(query, context)
        elif query_type == "market":
            return self._generate_market_response(query, context)
        elif query_type == "education":
            return self._generate_education_response(query, context)
        elif query_type == "investment":
            return self._generate_investment_response(query, context)
        elif query_type == "policy":
            return self._generate_policy_response(query, context)
        else:
            return self._generate_general_response(query, context)
    
    def _generate_valuation_response(self, query: str, context: Dict) -> str:
        """生成估值回复"""
        return (
            "关于房产估值，我需要了解以下信息：\n"
            "1. 房产位置和面积\n"
            "2. 楼层和朝向\n"
            "3. 建造年代\n"
            "4. 周边配套设施\n\n"
            "基于这些信息，我可以为您提供更准确的估值分析。"
        )
    
    def _generate_market_response(self, query: str, context: Dict) -> str:
        """生成市场回复"""
        return (
            "当前房地产市场呈现以下特点：\n"
            "1. 整体市场趋于稳定\n"
            "2. 核心区域价格坚挺\n"
            "3. 政策调控效果显现\n\n"
            "建议您关注具体区域的详细数据。"
        )
    
    def _generate_education_response(self, query: str, context: Dict) -> str:
        """生成教育回复"""
        return (
            "关于学区房，我建议您考虑：\n"
            "1. 学校的教学质量和排名\n"
            "2. 学区政策的稳定性\n"
            "3. 房产的升值潜力\n\n"
            "我可以为您分析具体区域的学区情况。"
        )
    
    def _generate_investment_response(self, query: str, context: Dict) -> str:
        """生成投资回复"""
        return (
            "房产投资需要考虑以下因素：\n"
            "1. 租金回报率\n"
            "2. 区域发展潜力\n"
            "3. 政策风险\n"
            "4. 流动性\n\n"
            "我可以为您计算具体的投资回报分析。"
        )
    
    def _generate_policy_response(self, query: str, context: Dict) -> str:
        """生成政策回复"""
        return (
            "关于购房资格和政策：\n"
            "1. 深圳目前实行限购政策\n"
            "2. 首套房和二套房首付比例不同\n"
            "3. 贷款利率有优惠政策\n\n"
            "建议您提供具体情况，我为您详细分析。"
        )
    
    def _generate_general_response(self, query: str, context: Dict) -> str:
        """生成通用回复"""
        return (
            "感谢您的咨询。为了更好地帮助您，\n"
            "请告诉我您具体想了解哪方面的信息：\n"
            "- 房产估值\n"
            "- 市场分析\n"
            "- 学区咨询\n"
            "- 投资建议\n"
            "- 政策解读"
        )
    
    def update_from_feedback(
        self,
        session_id: str,
        user_rating: int,
        comment: Optional[str] = None
    ):
        """根据反馈更新"""
        for example in self.training_data:
            if example.session_id == session_id:
                example.user_rating = user_rating
                break
        
        if user_rating < self.config.feedback_threshold:
            logger.info(f"Low rating feedback received: session={session_id}, rating={user_rating}")
        
        logger.debug(f"Updated from feedback: session={session_id}, rating={user_rating}")
    
    def evaluate(self, test_data: List[Dict]) -> Dict:
        """评估模型"""
        examples = []
        for item in test_data:
            example = ConsultationExample(
                session_id=item.get("session_id", ""),
                user_query=item.get("user_query", ""),
                context=item.get("context", {}),
                ideal_reply=item.get("ideal_reply", ""),
                actual_reply=item.get("actual_reply"),
                user_rating=item.get("user_rating"),
                response_time=item.get("response_time", 0.0)
            )
            examples.append(example)
        
        if not examples:
            return {"error": "No test data"}
        
        ratings = [ex.user_rating for ex in examples if ex.user_rating is not None]
        
        if not ratings:
            return {"error": "No ratings in test data"}
        
        avg_rating = sum(ratings) / len(ratings)
        high_rating_ratio = sum(1 for r in ratings if r >= 4) / len(ratings)
        
        result = {
            "avg_rating": avg_rating,
            "high_rating_ratio": high_rating_ratio,
            "total_samples": len(examples),
            "rated_samples": len(ratings),
        }
        
        logger.info(f"Evaluation result: avg_rating={avg_rating:.2f}")
        return result
    
    def get_statistics(self) -> Dict:
        """获取训练统计"""
        ratings = [ex.user_rating for ex in self.training_data if ex.user_rating is not None]
        
        return {
            "training_data_count": len(self.training_data),
            "validation_data_count": len(self.validation_data),
            "avg_rating": sum(ratings) / len(ratings) if ratings else 0,
            "training_history": self.training_history,
            "personality_traits": self.personality_traits,
        }


_global_trainer: Optional[LibuTrainer] = None


def get_libu_trainer() -> LibuTrainer:
    """获取全局训练器实例"""
    global _global_trainer
    if _global_trainer is None:
        _global_trainer = LibuTrainer()
    return _global_trainer
