"""
分析代理
负责分析采集的数据，生成分析报告
"""
from typing import Dict, Any
from .base import BaseAgent
from .message import AgentMessage, MessageType
import logging

logger = logging.getLogger(__name__)


class AnalystAgent(BaseAgent):
    """
    分析代理
    根据采集的数据进行分析，生成投资建议
    
    Attributes:
        _analysis_styles: 分析风格配置
    """
    
    def __init__(self, agent_name: str, task_id: str, bus, style: str = "balanced", **kwargs):
        """
        初始化分析代理
        
        Args:
            agent_name: 代理名称
            task_id: 任务ID
            bus: 消息总线
            style: 分析风格 (conservative/balanced/aggressive)
            **kwargs: 其他参数
        """
        super().__init__(agent_name, task_id, bus, **kwargs)
        
        self._style = style
        self._analysis_styles = {
            "conservative": {
                "risk_tolerance": "low",
                "focus": "保值稳定性",
                "factors": ["地段成熟度", "配套设施", "交通便利性"]
            },
            "balanced": {
                "risk_tolerance": "medium",
                "focus": "平衡收益与风险",
                "factors": ["地段潜力", "价格合理性", "配套完善度"]
            },
            "aggressive": {
                "risk_tolerance": "high",
                "focus": "高收益潜力",
                "factors": ["升值空间", "政策利好", "新兴区域"]
            }
        }
    
    async def handle_message(self, message: AgentMessage) -> None:
        """
        处理接收到的消息
        
        Args:
            message: 消息对象
        """
        logger.info(f"AnalystAgent received message from {message.sender}")
        
        if message.type == MessageType.REQUEST:
            action = message.content.get("action")
            
            if action == "analyze":
                parsed = message.content.get("parsed", {})
                data = message.content.get("data", {})
                city = parsed.get("city", "未知")
                district = parsed.get("district", "未知")
                
                await self.record_step("开始数据分析", f"正在分析{city} {district}的房产数据...", status="in_progress", input_data={"parsed": parsed})
                
                analysis = await self._analyze_data(parsed, data)
                
                risk_level = analysis.get("risk_level", "未知")
                confidence = analysis.get("confidence", 0)
                await self.record_step("数据分析完成", f"分析完成，风险等级: {risk_level}，置信度: {confidence:.0%}", status="completed", output_data={"analysis": analysis})
                
                await self.respond(message, {"analysis": analysis})
    
    async def _analyze_data(self, parsed: Dict[str, Any], data: Dict[str, Any]) -> Dict[str, Any]:
        """
        分析数据
        
        Args:
            parsed: 解析的需求
            data: 采集的数据
            
        Returns:
            Dict: 分析结果
        """
        style_config = self._analysis_styles.get(self._style, self._analysis_styles["balanced"])
        
        city = parsed.get("city", "未知")
        district = parsed.get("district", "未知")
        budget = parsed.get("budget", 0)
        
        avg_price = data.get("avg_price", 0)
        trend = data.get("trend", "stable")
        properties = data.get("properties", [])
        
        price_analysis = self._analyze_price(avg_price, budget)
        trend_analysis = self._analyze_trend(trend)
        property_analysis = self._analyze_properties(properties, budget)
        
        recommendation = self._generate_recommendation(
            price_analysis,
            trend_analysis,
            property_analysis,
            style_config
        )
        
        analysis = {
            "city": city,
            "district": district,
            "style": self._style,
            "style_config": style_config,
            "price_analysis": price_analysis,
            "trend_analysis": trend_analysis,
            "property_analysis": property_analysis,
            "recommendation": recommendation,
            "risk_level": self._calculate_risk_level(trend, len(properties)),
            "confidence": self._calculate_confidence(data)
        }
        
        logger.info(f"Analysis completed for {city} {district}")
        
        return analysis
    
    def _analyze_price(self, avg_price: float, budget: float) -> Dict[str, Any]:
        """
        分析价格
        
        Args:
            avg_price: 平均单价
            budget: 预算
            
        Returns:
            Dict: 价格分析结果
        """
        if budget <= 0:
            return {"status": "unknown", "message": "预算信息不完整"}
        
        price_per_sqm = avg_price
        
        if price_per_sqm <= 0:
            return {"status": "unknown", "message": "价格数据不完整"}
        
        affordable_area = budget / price_per_sqm if price_per_sqm > 0 else 0
        
        if affordable_area >= 120:
            status = "excellent"
            message = "预算充足，可购买大面积优质房产"
        elif affordable_area >= 90:
            status = "good"
            message = "预算适中，可购买标准三房"
        elif affordable_area >= 60:
            status = "fair"
            message = "预算紧张，建议考虑小户型"
        else:
            status = "tight"
            message = "预算不足，建议增加预算或考虑其他区域"
        
        return {
            "status": status,
            "message": message,
            "avg_price_per_sqm": price_per_sqm,
            "affordable_area": round(affordable_area, 1),
            "budget": budget
        }
    
    def _analyze_trend(self, trend: str) -> Dict[str, Any]:
        """
        分析趋势
        
        Args:
            trend: 价格趋势
            
        Returns:
            Dict: 趋势分析结果
        """
        trend_map = {
            "up": {
                "direction": "上涨",
                "signal": "买入信号",
                "risk": "较高",
                "advice": "市场处于上升期，需谨慎评估入场时机"
            },
            "down": {
                "direction": "下跌",
                "signal": "观望信号",
                "risk": "中等",
                "advice": "市场处于调整期，可等待更好的入场时机"
            },
            "stable": {
                "direction": "平稳",
                "signal": "中性信号",
                "risk": "较低",
                "advice": "市场相对稳定，可根据需求择机购买"
            }
        }
        
        return trend_map.get(trend, trend_map["stable"])
    
    def _analyze_properties(self, properties: list, budget: float) -> Dict[str, Any]:
        """
        分析房产列表
        
        Args:
            properties: 房产列表
            budget: 预算
            
        Returns:
            Dict: 房产分析结果
        """
        if not properties:
            return {
                "count": 0,
                "affordable_count": 0,
                "best_match": None,
                "message": "暂无符合条件的房产"
            }
        
        affordable_properties = [p for p in properties if p.get("price", 0) <= budget]
        
        best_match = None
        if affordable_properties:
            best_match = max(affordable_properties, key=lambda p: p.get("area", 0))
        
        return {
            "count": len(properties),
            "affordable_count": len(affordable_properties),
            "best_match": best_match,
            "message": f"共{len(properties)}套房产，{len(affordable_properties)}套在预算内"
        }
    
    def _generate_recommendation(
        self,
        price_analysis: Dict,
        trend_analysis: Dict,
        property_analysis: Dict,
        style_config: Dict
    ) -> str:
        """
        生成投资建议
        
        Args:
            price_analysis: 价格分析
            trend_analysis: 趋势分析
            property_analysis: 房产分析
            style_config: 风格配置
            
        Returns:
            str: 投资建议
        """
        recommendations = []
        
        if price_analysis.get("status") in ["excellent", "good"]:
            recommendations.append("从预算角度看，当前是较好的入场时机")
        elif price_analysis.get("status") == "tight":
            recommendations.append("建议适当提高预算或考虑周边区域")
        
        if trend_analysis.get("direction") == "上涨":
            if style_config["risk_tolerance"] == "high":
                recommendations.append("市场上涨趋势明显，可考虑积极入场")
            else:
                recommendations.append("市场上涨中，建议谨慎评估价格合理性")
        elif trend_analysis.get("direction") == "下跌":
            recommendations.append("市场调整期，可等待更优价格")
        
        if property_analysis.get("affordable_count", 0) > 0:
            recommendations.append(f"有{property_analysis['affordable_count']}套房产符合预算")
        else:
            recommendations.append("当前无符合预算的房产")
        
        focus = style_config.get("focus", "")
        if focus:
            recommendations.append(f"投资策略：{focus}")
        
        return "；".join(recommendations)
    
    def _calculate_risk_level(self, trend: str, property_count: int) -> str:
        """
        计算风险等级
        
        Args:
            trend: 价格趋势
            property_count: 房产数量
            
        Returns:
            str: 风险等级
        """
        risk_score = 0
        
        if trend == "up":
            risk_score += 2
        elif trend == "down":
            risk_score += 1
        
        if property_count < 3:
            risk_score += 2
        elif property_count < 5:
            risk_score += 1
        
        if risk_score >= 3:
            return "高"
        elif risk_score >= 2:
            return "中"
        else:
            return "低"
    
    def _calculate_confidence(self, data: Dict[str, Any]) -> float:
        """
        计算置信度
        
        Args:
            data: 数据字典
            
        Returns:
            float: 置信度 (0-1)
        """
        confidence = 0.5
        
        if data.get("avg_price", 0) > 0:
            confidence += 0.15
        
        if data.get("trend"):
            confidence += 0.1
        
        if data.get("properties"):
            confidence += 0.15
            if len(data["properties"]) >= 3:
                confidence += 0.1
        
        return min(confidence, 1.0)
