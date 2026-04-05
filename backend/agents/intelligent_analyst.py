"""
智能分析代理
使用LLM进行深度分析
"""
from typing import Dict, Any
from .memory_agent import MemoryEnabledAgent
from .message import AgentMessage, MessageType
from ..llm_service import llm_service
import logging
import json

logger = logging.getLogger(__name__)


class IntelligentAnalystAgent(MemoryEnabledAgent):
    """
    智能分析代理
    使用LLM进行深度房产分析，具备记忆能力
    
    Attributes:
        _style: 分析风格
    """
    
    STYLE_PROMPTS = {
        "conservative": """你是一位保守型投资顾问，注重风险控制和资产保值。
分析时请重点关注：
1. 地段成熟度和稳定性
2. 配套设施完善程度
3. 交通便利性
4. 历史价格波动
5. 政策风险""",
        
        "balanced": """你是一位平衡型投资顾问，兼顾收益与风险。
分析时请综合考虑：
1. 地段发展潜力
2. 价格合理性
3. 配套完善度
4. 未来升值空间
5. 租金回报率""",
        
        "aggressive": """你是一位进取型投资顾问，追求高收益潜力。
分析时请重点关注：
1. 新兴区域发展机会
2. 政策利好
3. 基建规划影响
4. 周边项目溢价
5. 短期升值空间"""
    }
    
    def __init__(
        self, 
        agent_name: str, 
        task_id: str, 
        bus, 
        style: str = "balanced",
        use_memory: bool = True,
        **kwargs
    ):
        """
        初始化智能分析代理
        
        Args:
            agent_name: 代理名称
            task_id: 任务ID
            bus: 消息总线
            style: 分析风格
            use_memory: 是否使用记忆
            **kwargs: 其他参数
        """
        super().__init__(agent_name, task_id, bus, memory_enabled=use_memory, **kwargs)
        
        self._style = style
    
    async def handle_message(self, message: AgentMessage) -> None:
        """
        处理接收到的消息
        
        Args:
            message: 消息对象
        """
        logger.info(f"IntelligentAnalystAgent received message from {message.sender}")
        
        if message.type == MessageType.REQUEST:
            action = message.content.get("action")
            
            if action == "analyze":
                parsed = message.content.get("parsed", {})
                data = message.content.get("data", {})
                
                analysis = await self._intelligent_analyze(parsed, data)
                
                await self.respond(message, {"analysis": analysis})
    
    async def _intelligent_analyze(
        self, 
        parsed: Dict[str, Any], 
        data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        使用LLM进行智能分析
        
        Args:
            parsed: 解析的需求
            data: 采集的数据
            
        Returns:
            Dict: 分析结果
        """
        query = parsed.get("query", "")
        
        relevant_memories = await self.recall_memories(query, n_results=3)
        
        context = ""
        if relevant_memories:
            context = "相关历史分析：\n"
            for mem in relevant_memories:
                context += f"- {mem['content'][:200]}\n"
        
        system_prompt = self.STYLE_PROMPTS.get(self._style, self.STYLE_PROMPTS["balanced"])
        
        property_data = {
            "city": parsed.get("city"),
            "district": parsed.get("district"),
            "budget": parsed.get("budget"),
            "house_type": parsed.get("house_type"),
            "area_range": parsed.get("area_range")
        }
        
        market_data = {
            "avg_price": data.get("avg_price"),
            "trend": data.get("trend"),
            "properties": data.get("properties", [])[:3],
            "market_stats": data.get("market_stats")
        }
        
        try:
            llm_analysis = await llm_service.analyze_property(
                property_data=property_data,
                market_data=market_data,
                user_preferences={"style": self._style}
            )
        except Exception as e:
            logger.error(f"LLM analysis failed: {e}")
            llm_analysis = {
                "overall_score": 70,
                "recommendation": "基于当前数据的初步分析建议",
                "error": str(e)
            }
        
        analysis = {
            "city": parsed.get("city"),
            "district": parsed.get("district"),
            "style": self._style,
            "llm_analysis": llm_analysis,
            "price_analysis": self._analyze_price(data.get("avg_price", 0), parsed.get("budget", 0)),
            "trend_analysis": self._analyze_trend(data.get("trend", "stable")),
            "property_analysis": self._analyze_properties(data.get("properties", []), parsed.get("budget", 0)),
            "recommendation": llm_analysis.get("recommendation", ""),
            "risk_level": self._calculate_risk(data.get("trend"), len(data.get("properties", []))),
            "confidence": self._calculate_confidence(data, llm_analysis),
            "key_factors": llm_analysis.get("key_factors", []),
            "used_memory": len(relevant_memories) > 0
        }
        
        await self.store_experience(
            situation=f"分析{parsed.get('city')}{parsed.get('district')}房产",
            action=f"使用{self._style}风格进行LLM分析",
            outcome=f"评分{analysis['confidence']}",
            lesson=analysis["recommendation"][:100] if analysis["recommendation"] else None
        )
        
        logger.info(f"Intelligent analysis completed for {parsed.get('city')} {parsed.get('district')}")
        
        return analysis
    
    def _analyze_price(self, avg_price: float, budget: float) -> Dict[str, Any]:
        """分析价格"""
        if budget <= 0 or avg_price <= 0:
            return {"status": "unknown", "message": "数据不完整"}
        
        affordable_area = budget / avg_price
        
        if affordable_area >= 120:
            return {"status": "excellent", "affordable_area": round(affordable_area, 1)}
        elif affordable_area >= 90:
            return {"status": "good", "affordable_area": round(affordable_area, 1)}
        elif affordable_area >= 60:
            return {"status": "fair", "affordable_area": round(affordable_area, 1)}
        else:
            return {"status": "tight", "affordable_area": round(affordable_area, 1)}
    
    def _analyze_trend(self, trend: str) -> Dict[str, Any]:
        """分析趋势"""
        trends = {
            "up": {"direction": "上涨", "signal": "买入信号", "risk": "较高"},
            "down": {"direction": "下跌", "signal": "观望信号", "risk": "中等"},
            "stable": {"direction": "平稳", "signal": "中性信号", "risk": "较低"}
        }
        return trends.get(trend, trends["stable"])
    
    def _analyze_properties(self, properties: list, budget: float) -> Dict[str, Any]:
        """分析房产列表"""
        if not properties:
            return {"count": 0, "affordable_count": 0}
        
        affordable = [p for p in properties if p.get("price", 0) <= budget]
        return {
            "count": len(properties),
            "affordable_count": len(affordable),
            "best_match": affordable[0] if affordable else None
        }
    
    def _calculate_risk(self, trend: str, property_count: int) -> str:
        """计算风险等级"""
        score = 0
        if trend == "up":
            score += 2
        if property_count < 3:
            score += 2
        elif property_count < 5:
            score += 1
        
        return "高" if score >= 3 else "中" if score >= 2 else "低"
    
    def _calculate_confidence(self, data: Dict, llm_analysis: Dict) -> float:
        """计算置信度"""
        base = 0.5
        if data.get("avg_price"):
            base += 0.15
        if data.get("properties"):
            base += 0.15
        if llm_analysis.get("overall_score"):
            base += 0.1
        return min(base, 1.0)
