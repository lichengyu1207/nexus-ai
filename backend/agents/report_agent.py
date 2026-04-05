"""
报告生成代理
负责生成结构化的房产分析报告
"""
import uuid
from typing import Dict, Any, List, Optional
from datetime import datetime
import logging

from .base import BaseAgent
from .message import AgentMessage, MessageType
from ..database import AnalysisReportDB

logger = logging.getLogger(__name__)


class ReportAgent(BaseAgent):
    """
    报告生成代理
    负责将分析结果转换为结构化报告
    
    报告结构:
    - executive_summary: 执行摘要
    - core_findings: 核心发现
    - detailed_analysis: 详细分析
    - investment_advice: 投资建议
    - risk_warnings: 风险提示
    - data_sources: 数据来源
    """
    
    def __init__(self, agent_name: str, task_id: str, bus, style: str = "balanced", **kwargs):
        super().__init__(agent_name, task_id, bus, **kwargs)
        self.style = style
        self._report_data: Optional[Dict[str, Any]] = None
        self._user_id: Optional[str] = kwargs.get("user_id")
    
    async def handle_message(self, message: AgentMessage) -> None:
        """
        处理接收到的消息
        
        Args:
            message: 消息对象
        """
        logger.info(f"ReportAgent received message from {message.sender}, type={message.type.value}")
        
        if message.type == MessageType.REQUEST:
            await self._handle_request(message)
    
    async def _handle_request(self, message: AgentMessage) -> None:
        """
        处理请求消息
        
        Args:
            message: 请求消息
        """
        action = message.content.get("action")
        
        if action == "generate":
            await self._generate_report(message)
        else:
            logger.warning(f"Unknown action: {action}")
    
    async def _generate_report(self, message: AgentMessage) -> None:
        """
        生成结构化报告
        
        Args:
            message: 生成报告请求
        """
        query = message.content.get("query", "")
        parsed_data = message.content.get("parsed", {})
        collected_data = message.content.get("data", {})
        analyzed_data = message.content.get("analysis", {})
        
        try:
            executive_summary = self._create_executive_summary(query, parsed_data, analyzed_data)
            core_findings = self._create_core_findings(parsed_data, collected_data, analyzed_data)
            detailed_analysis = self._create_detailed_analysis(parsed_data, collected_data, analyzed_data)
            investment_advice = self._create_investment_advice(parsed_data, analyzed_data)
            risk_warnings = self._create_risk_warnings(parsed_data, analyzed_data)
            data_sources = self._create_data_sources(collected_data)
            confidence_score = self._calculate_confidence_score(collected_data, analyzed_data)
            
            report_id = str(uuid.uuid4())
            
            await AnalysisReportDB.create_report(
                report_id=report_id,
                task_id=self.task_id,
                user_id=self._user_id or "",
                query=query,
                style=self.style,
                executive_summary=executive_summary,
                core_findings=core_findings,
                detailed_analysis=detailed_analysis,
                investment_advice=investment_advice,
                risk_warnings=risk_warnings,
                data_sources=data_sources,
                confidence_score=confidence_score
            )
            
            self._report_data = {
                "report_id": report_id,
                "task_id": self.task_id,
                "executive_summary": executive_summary,
                "core_findings": core_findings,
                "detailed_analysis": detailed_analysis,
                "investment_advice": investment_advice,
                "risk_warnings": risk_warnings,
                "data_sources": data_sources,
                "confidence_score": confidence_score
            }
            
            await self.respond(message, {
                "status": "completed",
                "report_id": report_id,
                "report": self._report_data
            })
            
            logger.info(f"Report generated for task {self.task_id}")
            
        except Exception as e:
            logger.error(f"Failed to generate report: {str(e)}")
            await self.send(
                recipient=message.sender,
                message_type=MessageType.ERROR,
                content={"error": f"报告生成失败: {str(e)}"},
                in_reply_to=message.id
            )
    
    def _create_executive_summary(self, query: str, parsed: Dict, analysis: Dict) -> str:
        """
        创建执行摘要
        
        Args:
            query: 用户查询
            parsed: 解析数据
            analysis: 分析数据
            
        Returns:
            str: 执行摘要
        """
        location = f"{parsed.get('city', '')}{parsed.get('district', '')}"
        property_type = parsed.get('property_type', '住宅')
        
        if analysis:
            avg_price = analysis.get('avg_price', 0)
            trend = analysis.get('price_trend', '稳定')
            recommendation = analysis.get('recommendation', '建议进一步调研')
            
            summary = f"针对您查询的{location}{property_type}，经过智能分析，"
            summary += f"该区域均价约{avg_price:,.0f}元/㎡，价格走势{trend}。"
            summary += f"综合分析结论：{recommendation}。"
            
            return summary
        
        return f"针对您查询的{location}{property_type}，正在进行分析。"
    
    def _create_core_findings(self, parsed: Dict, collected: Dict, analysis: Dict) -> Dict[str, Any]:
        """
        创建核心发现
        
        Args:
            parsed: 解析数据
            collected: 采集数据
            analysis: 分析数据
            
        Returns:
            Dict: 核心发现
        """
        findings = {
            "location": {
                "city": parsed.get('city', ''),
                "district": parsed.get('district', ''),
                "community": parsed.get('community', '')
            },
            "market_overview": {},
            "price_analysis": {},
            "key_insights": []
        }
        
        if collected:
            properties = collected.get('properties', [])
            avg_price = collected.get('avg_price', 0)
            
            findings["market_overview"] = {
                "total_properties": len(properties),
                "average_price": avg_price,
                "price_range": collected.get('price_range', {})
            }
        
        if analysis:
            findings["price_analysis"] = {
                "trend": analysis.get('price_trend', '稳定'),
                "year_over_year": analysis.get('yoy_change', 0),
                "month_over_month": analysis.get('mom_change', 0)
            }
            
            insights = analysis.get('insights', [])
            findings["key_insights"] = insights if insights else [
                "该区域房产市场活跃度较高",
                "交通便利，配套设施完善",
                "建议关注学区资源"
            ]
        
        return findings
    
    def _create_detailed_analysis(self, parsed: Dict, collected: Dict, analysis: Dict) -> Dict[str, Any]:
        """
        创建详细分析
        
        Args:
            parsed: 解析数据
            collected: 采集数据
            analysis: 分析数据
            
        Returns:
            Dict: 详细分析
        """
        detailed = {
            "market_analysis": {
                "supply_demand": "供需平衡",
                "liquidity": "流动性良好",
                "market_sentiment": "市场情绪稳定"
            },
            "price_analysis": {
                "current_level": "中等偏上",
                "historical_trend": "近一年价格稳中有升",
                "future_outlook": "预期保持稳定"
            },
            "location_analysis": {
                "transportation": "交通便利",
                "education": "教育资源丰富",
                "medical": "医疗配套完善",
                "commercial": "商业设施齐全"
            },
            "property_analysis": {}
        }
        
        if parsed:
            area = parsed.get('area')
            if area:
                detailed["property_analysis"]["area"] = f"{area}㎡"
            
            budget = parsed.get('budget')
            if budget:
                detailed["property_analysis"]["budget_range"] = budget
        
        if analysis:
            detailed["market_analysis"]["supply_demand"] = analysis.get('supply_demand', '供需平衡')
            detailed["price_analysis"]["current_level"] = analysis.get('price_level', '中等偏上')
        
        return detailed
    
    def _create_investment_advice(self, parsed: Dict, analysis: Dict) -> Dict[str, Any]:
        """
        创建投资建议
        
        Args:
            parsed: 解析数据
            analysis: 分析数据
            
        Returns:
            Dict: 投资建议
        """
        advice = {
            "overall_rating": "中性偏正面",
            "investment_horizon": {
                "short_term": "持有观望",
                "medium_term": "可考虑入手",
                "long_term": "具备增值潜力"
            },
            "action_recommendation": "建议",
            "key_factors": [],
            "style_specific_advice": {}
        }
        
        if self.style == "conservative":
            advice["overall_rating"] = "谨慎乐观"
            advice["investment_horizon"]["short_term"] = "暂不建议入手"
            advice["action_recommendation"] = "建议等待更好的入场时机"
            advice["style_specific_advice"] = {
                "risk_level": "低风险偏好",
                "suggestion": "关注核心地段优质房源，优先考虑学区房"
            }
        elif self.style == "aggressive":
            advice["overall_rating"] = "积极看好"
            advice["investment_horizon"]["short_term"] = "可积极布局"
            advice["action_recommendation"] = "可考虑适当增加配置"
            advice["style_specific_advice"] = {
                "risk_level": "高风险偏好",
                "suggestion": "关注新兴区域发展潜力，可考虑投资性房产"
            }
        else:
            advice["style_specific_advice"] = {
                "risk_level": "中等风险偏好",
                "suggestion": "平衡配置，关注性价比"
            }
        
        if analysis:
            factors = analysis.get('investment_factors', [])
            advice["key_factors"] = factors if factors else [
                "地段优势明显",
                "交通便利",
                "配套设施完善"
            ]
        
        return advice
    
    def _create_risk_warnings(self, parsed: Dict, analysis: Dict) -> List[str]:
        """
        创建风险提示
        
        Args:
            parsed: 解析数据
            analysis: 分析数据
            
        Returns:
            List[str]: 风险提示列表
        """
        warnings = [
            "本报告基于公开数据分析，仅供参考，不构成投资建议",
            "房产投资存在市场风险，价格可能波动",
            "请结合实地考察和专业咨询做出决策"
        ]
        
        if analysis:
            risk_level = analysis.get('risk_level', 'medium')
            if risk_level == 'high':
                warnings.append("当前市场波动较大，建议谨慎决策")
            
            specific_risks = analysis.get('risks', [])
            warnings.extend(specific_risks)
        
        if self.style == "aggressive":
            warnings.append("激进型策略风险较高，请确保有足够的风险承受能力")
        
        return warnings
    
    def _create_data_sources(self, collected: Dict) -> List[Dict[str, str]]:
        """
        创建数据来源标注
        
        Args:
            collected: 采集数据
            
        Returns:
            List[Dict]: 数据来源列表
        """
        sources = [
            {
                "name": "市场数据",
                "type": "simulated",
                "description": "模拟市场数据，仅供演示",
                "reliability": "medium"
            },
            {
                "name": "区域分析",
                "type": "simulated",
                "description": "基于公开信息的模拟分析",
                "reliability": "medium"
            }
        ]
        
        if collected:
            data_sources = collected.get('sources', [])
            if data_sources:
                sources = []
                for src in data_sources:
                    sources.append({
                        "name": src.get('name', '未知来源'),
                        "type": src.get('type', 'simulated'),
                        "description": src.get('description', ''),
                        "reliability": src.get('reliability', 'medium')
                    })
        
        return sources
    
    def _calculate_confidence_score(self, collected: Dict, analysis: Dict) -> float:
        """
        计算置信度分数
        
        Args:
            collected: 采集数据
            analysis: 分析数据
            
        Returns:
            float: 置信度分数 (0-1)
        """
        score = 0.5
        
        if collected:
            properties = collected.get('properties', [])
            if len(properties) > 5:
                score += 0.2
            elif len(properties) > 0:
                score += 0.1
            
            if collected.get('avg_price'):
                score += 0.1
        
        if analysis:
            if analysis.get('insights'):
                score += 0.1
            if analysis.get('recommendation'):
                score += 0.1
        
        return min(score, 1.0)
    
    def get_report_data(self) -> Optional[Dict[str, Any]]:
        """
        获取报告数据
        
        Returns:
            Dict: 报告数据
        """
        return self._report_data
    
    def generate_report(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        同步生成报告方法（用于测试和直接调用）
        
        Args:
            data: 包含以下字段的字典:
                - query: 用户查询字符串
                - parsed: 解析数据（可选）
                - collected: 采集数据（可选）
                - analysis: 分析数据（可选）
                - style: 分析风格（可选）
        
        Returns:
            Dict: 生成的报告数据
        """
        query = data.get("query", "")
        parsed = data.get("parsed", {})
        collected = data.get("collected", {})
        analysis = data.get("analysis", {})
        style = data.get("style", self.style)
        
        self.style = style
        
        if not parsed:
            parsed = {
                "city": "深圳",
                "district": "南山区",
                "property_type": "住宅"
            }
        
        if not collected:
            collected = {
                "properties": [],
                "avg_price": 85000,
                "sources": []
            }
        
        if not analysis:
            analysis = {
                "avg_price": 85000,
                "price_trend": "稳定",
                "recommendation": "建议进一步调研",
                "insights": [],
                "risk_level": "medium"
            }
        
        executive_summary = self._create_executive_summary(query, parsed, analysis)
        core_findings = self._create_core_findings(parsed, collected, analysis)
        detailed_analysis = self._create_detailed_analysis(parsed, collected, analysis)
        investment_advice = self._create_investment_advice(parsed, analysis)
        risk_warnings = self._create_risk_warnings(parsed, analysis)
        data_sources = self._create_data_sources(collected)
        confidence_score = self._calculate_confidence_score(collected, analysis)
        
        self._report_data = {
            "report_id": str(uuid.uuid4()),
            "task_id": self.task_id,
            "query": query,
            "style": style,
            "executive_summary": executive_summary,
            "core_findings": core_findings,
            "detailed_analysis": detailed_analysis,
            "investment_advice": investment_advice,
            "risk_warnings": risk_warnings,
            "data_sources": data_sources,
            "confidence_score": confidence_score,
            "created_at": datetime.now().isoformat()
        }
        
        return self._report_data
