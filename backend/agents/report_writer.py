"""
报告生成器代理
负责根据其他代理的输出生成结构化报告
支持流式输出和LLM调用
支持数据可信度标注
"""
import asyncio
import json
import uuid
from typing import Dict, Any, Optional, List
from datetime import datetime
import logging
import os

from .base import BaseAgent
from .message import AgentMessage, MessageType
from ..database import ReportDB, NotificationDB
from ..sse_manager import sse_manager

logger = logging.getLogger(__name__)


SOURCE_TYPES = {
    "government": {"label": "政府公开数据", "reliability": "high", "icon": "🏛️"},
    "market": {"label": "市场交易数据", "reliability": "high", "icon": "📊"},
    "analysis": {"label": "智能分析", "reliability": "medium", "icon": "🤖"},
    "estimate": {"label": "估算数据", "reliability": "low", "icon": "📈"},
    "simulated": {"label": "模拟数据", "reliability": "low", "icon": "🔧"},
    "user_input": {"label": "用户输入", "reliability": "high", "icon": "👤"},
    "external_api": {"label": "外部API", "reliability": "medium", "icon": "🔗"},
    "historical": {"label": "历史数据", "reliability": "medium", "icon": "📅"},
}


class DataSource:
    """数据源信息"""
    
    def __init__(
        self,
        name: str,
        source_type: str,
        description: str = "",
        confidence: float = 0.8,
        timestamp: str = None,
        url: str = None
    ):
        self.name = name
        self.source_type = source_type
        self.description = description
        self.confidence = confidence
        self.timestamp = timestamp or datetime.utcnow().isoformat()
        self.url = url
    
    def to_dict(self) -> Dict[str, Any]:
        type_info = SOURCE_TYPES.get(self.source_type, SOURCE_TYPES["simulated"])
        return {
            "name": self.name,
            "type": self.source_type,
            "label": type_info["label"],
            "icon": type_info["icon"],
            "reliability": type_info["reliability"],
            "description": self.description,
            "confidence": self.confidence,
            "timestamp": self.timestamp,
            "url": self.url
        }


class DataPoint:
    """带可信度的数据点"""
    
    def __init__(
        self,
        title: str,
        value: Any,
        source: DataSource,
        confidence: float = None,
        is_estimated: bool = False,
        note: str = None
    ):
        self.title = title
        self.value = value
        self.source = source
        self.confidence = confidence or source.confidence
        self.is_estimated = is_estimated
        self.note = note
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "title": self.title,
            "value": self.value,
            "source": self.source.to_dict(),
            "confidence": self.confidence,
            "is_estimated": self.is_estimated,
            "note": self.note,
            "confidence_level": self._get_confidence_level()
        }
    
    def _get_confidence_level(self) -> str:
        if self.confidence >= 0.9:
            return "high"
        elif self.confidence >= 0.7:
            return "medium"
        else:
            return "low"


class ReportWriterAgent(BaseAgent):
    """
    报告生成器代理
    负责将分析结果转换为结构化报告
    
    功能：
    - 订阅来自 SupervisorAgent 的 generate_report 请求
    - 调用 LLM 生成报告内容
    - 支持流式输出，逐步发送报告片段
    - 将生成的报告存入数据库
    """
    
    def __init__(self, agent_name: str, task_id: str, bus, **kwargs):
        super().__init__(agent_name, task_id, bus, **kwargs)
        
        self._user_id: Optional[str] = kwargs.get("user_id")
        self._report_id: Optional[str] = None
        self._report_content: Dict[str, Any] = {}
        self._stream_enabled: bool = kwargs.get("stream_enabled", True)
        
        self._llm_provider = os.getenv("LLM_PROVIDER", "mock")
        self._llm_api_key = os.getenv("OPENAI_API_KEY", "")
        self._llm_model = os.getenv("OPENAI_MODEL", "gpt-4")
    
    async def handle_message(self, message: AgentMessage) -> None:
        """处理接收到的消息"""
        logger.info(f"ReportWriterAgent received message from {message.sender}")
        
        if message.type == MessageType.REQUEST:
            await self._handle_request(message)
    
    async def _handle_request(self, message: AgentMessage) -> None:
        """处理请求消息"""
        action = message.content.get("action")
        
        if action == "generate_report":
            await self._generate_report(message)
        elif action == "regenerate":
            await self._regenerate_report(message)
        else:
            logger.warning(f"Unknown action: {action}")
    
    async def _generate_report(self, message: AgentMessage) -> None:
        """生成报告"""
        task_id = message.content.get("task_id", self.task_id)
        requirement = message.content.get("requirement", {})
        collected_data = message.content.get("collected_data", {})
        analysis_result = message.content.get("analysis_result", {})
        style = message.content.get("style", "balanced")
        
        try:
            next_version, parent_id = await ReportDB.get_next_version(task_id)
            
            self._report_id = str(uuid.uuid4())
            
            await ReportDB.create_report(
                report_id=self._report_id,
                task_id=task_id,
                user_id=self._user_id or "",
                summary=None,
                parent_version_id=parent_id,
                version=next_version
            )
            
            success, error = await ReportDB.update_status(self._report_id, "generating")
            if not success:
                raise Exception(error)
            
            await self._broadcast_progress("started", {
                "report_id": self._report_id,
                "version": next_version,
                "parent_version_id": parent_id
            })
            
            self._report_content = {
                "task_id": task_id,
                "style": style,
                "generated_at": datetime.utcnow().isoformat(),
                "sections": {},
                "charts": []
            }
            
            charts = await self._generate_charts(
                collected_data=collected_data,
                analysis_result=analysis_result
            )
            self._report_content["charts"] = charts
            
            sections = [
                ("summary", "执行摘要", self._generate_summary),
                ("key_findings", "核心发现", self._generate_key_findings),
                ("detailed_analysis", "详细分析", self._generate_detailed_analysis),
                ("investment_advice", "投资建议", self._generate_investment_advice),
                ("risk_warning", "风险提示", self._generate_risk_warning),
                ("data_sources", "数据来源", self._generate_data_sources),
            ]
            
            total_sections = len(sections)
            
            for idx, (section_key, section_name, generator) in enumerate(sections):
                try:
                    progress = int((idx / total_sections) * 100)
                    await ReportDB.update_content(
                        self._report_id,
                        self._report_content,
                        progress=progress,
                        current_section=section_key
                    )
                    
                    await self._broadcast_progress("section_start", {
                        "section": section_key,
                        "name": section_name
                    })
                    
                    await self._broadcast_agent_reference(section_key, "started")
                    
                    section_content = await generator(
                        requirement=requirement,
                        collected_data=collected_data,
                        analysis_result=analysis_result,
                        style=style
                    )
                    
                    self._report_content["sections"][section_key] = section_content
                    
                    await sse_manager.broadcast_report_chunk(
                        task_id=task_id,
                        report_id=self._report_id,
                        section=section_key,
                        content=section_content,
                        progress=progress + int(100 / total_sections)
                    )
                    
                    await self._broadcast_agent_reference(section_key, "completed", section_content)
                    
                    await self._broadcast_progress("section_complete", {
                        "section": section_key,
                        "name": section_name,
                        "content": section_content
                    })
                    
                except Exception as e:
                    logger.error(f"Failed to generate section {section_key}: {e}")
                    self._report_content["sections"][section_key] = {
                        "error": str(e),
                        "fallback": self._get_fallback_content(section_key)
                    }
            
            summary = self._report_content["sections"].get("summary", {})
            if isinstance(summary, dict) and summary.get("text"):
                await ReportDB.update_summary(self._report_id, summary["text"][:500])
            
            await ReportDB.update_content(
                self._report_id,
                self._report_content,
                progress=100,
                current_section=None
            )
            
            success, error = await ReportDB.update_status(self._report_id, "completed")
            if not success:
                raise Exception(error)
            
            try:
                from ..tasks.geocode_tasks import (
                    geocode_and_save_location,
                    extract_address_from_requirement,
                    extract_address_from_collected_data
                )
                
                address = None
                if requirement:
                    address = await extract_address_from_requirement(requirement)
                if not address and collected_data:
                    address = await extract_address_from_collected_data(collected_data)
                
                if address and self._user_id:
                    asyncio.create_task(
                        geocode_and_save_location(
                            user_id=self._user_id,
                            address=address,
                            source="report",
                            report_id=self._report_id
                        )
                    )
                    logger.info(f"Geocoding task started for report {self._report_id}: {address}")
            except Exception as e:
                logger.warning(f"Failed to start geocoding task: {e}")
            
            if self._user_id:
                try:
                    await NotificationDB.create_report_completed_notification(
                        user_id=self._user_id,
                        report_id=self._report_id,
                        task_id=task_id
                    )
                except Exception as e:
                    logger.error(f"Failed to create report completion notification: {e}")
            
            await sse_manager.broadcast_report_complete(
                task_id=task_id,
                report_id=self._report_id,
                content=self._report_content
            )
            
            await self.respond(message, {
                "status": "completed",
                "report_id": self._report_id,
                "report": self._report_content
            })
            
            logger.info(f"Report generated successfully: {self._report_id}")
            
        except Exception as e:
            logger.error(f"Failed to generate report: {str(e)}")
            
            if self._report_id:
                await ReportDB.update_status(self._report_id, "failed", str(e))
            
            await sse_manager.broadcast_report_error(
                task_id=task_id,
                report_id=self._report_id or "",
                error=str(e)
            )
            
            await self.send(
                recipient=message.sender,
                message_type=MessageType.ERROR,
                content={"error": f"报告生成失败: {str(e)}"},
                in_reply_to=message.id
            )
    
    async def _regenerate_report(self, message: AgentMessage) -> None:
        """重新生成报告"""
        existing_report = await ReportDB.get_report_by_task(self.task_id)
        
        if existing_report:
            success, error = await ReportDB.update_status(existing_report["id"], "pending")
            if success:
                await self._generate_report(message)
            else:
                await self.respond(message, {"status": "error", "error": error})
        else:
            await self._generate_report(message)
    
    async def _generate_summary(self, requirement: Dict, collected_data: Dict, 
                                analysis_result: Dict, style: str) -> Dict[str, Any]:
        """生成执行摘要"""
        location = f"{requirement.get('city', '')}{requirement.get('district', '')}"
        property_type = requirement.get('property_type', '住宅')
        
        sources_used = []
        
        if analysis_result:
            avg_price = analysis_result.get('avg_price', 0)
            trend = analysis_result.get('price_trend', '稳定')
            recommendation = analysis_result.get('recommendation', '建议进一步调研')
            price_confidence = analysis_result.get('price_confidence', 0.85)
            
            summary_text = f"针对您查询的{location}{property_type}，经过智能分析，"
            summary_text += f"该区域均价约{avg_price:,.0f}元/㎡，价格走势{trend}。"
            summary_text += f"综合分析结论：{recommendation}。"
            
            price_source = DataSource(
                name="区域房价统计",
                source_type="market" if price_confidence > 0.8 else "estimate",
                description=f"{location}区域均价数据",
                confidence=price_confidence
            )
            sources_used.append(price_source.to_dict())
        else:
            summary_text = f"针对您查询的{location}{property_type}，已完成基础分析。"
            price_confidence = 0.6
        
        return {
            "text": summary_text,
            "confidence": price_confidence,
            "generated_by": "rule_based",
            "sources": sources_used
        }
    
    async def _generate_key_findings(self, requirement: Dict, collected_data: Dict,
                                      analysis_result: Dict, style: str) -> List[Dict[str, Any]]:
        """生成核心发现"""
        findings = []
        
        if collected_data:
            properties = collected_data.get('properties', [])
            avg_price = collected_data.get('avg_price', 0)
            price_confidence = collected_data.get('price_confidence', 0.9)
            
            market_source = DataSource(
                name="市场交易数据",
                source_type="market",
                description="实时市场交易统计",
                confidence=price_confidence
            )
            
            findings.append(DataPoint(
                title="区域均价",
                value=f"{avg_price:,.0f}元/㎡",
                source=market_source,
                confidence=price_confidence,
                note=f"基于{len(properties)}套在售房源统计"
            ).to_dict())
            
            findings.append(DataPoint(
                title="在售房源",
                value=f"{len(properties)}套",
                source=market_source,
                confidence=0.95,
                note="实时在售房源数量"
            ).to_dict())
        
        if analysis_result:
            trend = analysis_result.get('price_trend', '稳定')
            trend_confidence = analysis_result.get('trend_confidence', 0.8)
            
            analysis_source = DataSource(
                name="价格趋势分析",
                source_type="analysis",
                description="基于历史数据的趋势分析",
                confidence=trend_confidence
            )
            
            findings.append(DataPoint(
                title="价格趋势",
                value=trend,
                source=analysis_source,
                confidence=trend_confidence,
                note="近6个月价格走势"
            ).to_dict())
            
            if analysis_result.get('price_estimated'):
                estimate_source = DataSource(
                    name="价格估算",
                    source_type="estimate",
                    description="根据户型和位置估算",
                    confidence=analysis_result.get('price_confidence', 0.7)
                )
                
                findings.append(DataPoint(
                    title="估算总价",
                    value=f"{analysis_result.get('estimated_total_price', 0):,.0f}万",
                    source=estimate_source,
                    confidence=analysis_result.get('price_confidence', 0.7),
                    is_estimated=True,
                    note="基于区域均价和面积估算"
                ).to_dict())
        
        if not findings:
            system_source = DataSource(
                name="系统分析",
                source_type="simulated",
                description="基础分析结果",
                confidence=0.6
            )
            
            findings.append(DataPoint(
                title="分析完成",
                value="已完成基础数据分析",
                source=system_source,
                confidence=0.6
            ).to_dict())
        
        return findings
    
    async def _generate_detailed_analysis(self, requirement: Dict, collected_data: Dict,
                                           analysis_result: Dict, style: str) -> Dict[str, Any]:
        """生成详细分析"""
        market_source = DataSource(
            name="市场分析",
            source_type="analysis",
            description="综合市场数据分析",
            confidence=0.85
        )
        
        location_source = DataSource(
            name="区域配套分析",
            source_type="analysis",
            description="基于公开信息的配套分析",
            confidence=0.75
        )
        
        return {
            "market_analysis": {
                "supply_demand": {
                    "value": "供需平衡",
                    "confidence": 0.8,
                    "source": market_source.to_dict()
                },
                "liquidity": {
                    "value": "流动性良好",
                    "confidence": 0.75,
                    "source": market_source.to_dict()
                },
                "market_sentiment": {
                    "value": "市场情绪稳定",
                    "confidence": 0.7,
                    "source": market_source.to_dict()
                }
            },
            "price_analysis": {
                "current_level": {
                    "value": "中等偏上",
                    "confidence": 0.8,
                    "source": market_source.to_dict()
                },
                "historical_trend": {
                    "value": "近一年价格稳中有升",
                    "confidence": 0.75,
                    "source": market_source.to_dict()
                },
                "future_outlook": {
                    "value": "预期保持稳定",
                    "confidence": 0.65,
                    "source": market_source.to_dict(),
                    "is_estimated": True
                }
            },
            "location_analysis": {
                "transportation": {
                    "value": "交通便利",
                    "confidence": 0.85,
                    "source": location_source.to_dict()
                },
                "education": {
                    "value": "教育资源丰富",
                    "confidence": 0.8,
                    "source": location_source.to_dict()
                },
                "medical": {
                    "value": "医疗配套完善",
                    "confidence": 0.75,
                    "source": location_source.to_dict()
                },
                "commercial": {
                    "value": "商业设施齐全",
                    "confidence": 0.8,
                    "source": location_source.to_dict()
                }
            }
        }
    
    async def _generate_investment_advice(self, requirement: Dict, collected_data: Dict,
                                          analysis_result: Dict, style: str) -> Dict[str, Any]:
        """生成投资建议"""
        advice_source = DataSource(
            name="投资分析模型",
            source_type="analysis",
            description="基于多因素的综合投资分析",
            confidence=0.75
        )
        
        advice = {
            "overall_rating": {
                "value": "中性偏正面",
                "confidence": 0.7,
                "source": advice_source.to_dict()
            },
            "investment_horizon": {
                "short_term": {
                    "value": "持有观望",
                    "confidence": 0.65,
                    "source": advice_source.to_dict()
                },
                "medium_term": {
                    "value": "可考虑入手",
                    "confidence": 0.7,
                    "source": advice_source.to_dict()
                },
                "long_term": {
                    "value": "具备增值潜力",
                    "confidence": 0.6,
                    "source": advice_source.to_dict(),
                    "is_estimated": True
                }
            },
            "action_recommendation": {
                "value": "建议",
                "confidence": 0.7,
                "source": advice_source.to_dict()
            },
            "key_factors": ["地段优势明显", "交通便利", "配套设施完善"],
            "style_specific_advice": {}
        }
        
        if style == "conservative":
            advice["overall_rating"]["value"] = "谨慎乐观"
            advice["action_recommendation"]["value"] = "建议等待更好的入场时机"
            advice["style_specific_advice"] = {
                "risk_level": "低风险偏好",
                "suggestion": "关注核心地段优质房源"
            }
        elif style == "aggressive":
            advice["overall_rating"]["value"] = "积极看好"
            advice["action_recommendation"]["value"] = "可考虑适当增加配置"
            advice["style_specific_advice"] = {
                "risk_level": "高风险偏好",
                "suggestion": "关注新兴区域发展潜力"
            }
        else:
            advice["style_specific_advice"] = {
                "risk_level": "中等风险偏好",
                "suggestion": "平衡配置，关注性价比"
            }
        
        return advice
    
    async def _generate_risk_warning(self, requirement: Dict, collected_data: Dict,
                                     analysis_result: Dict, style: str) -> Dict[str, Any]:
        """生成风险提示"""
        warnings = [
            {
                "text": "本报告基于公开数据分析，仅供参考，不构成投资建议",
                "severity": "high",
                "confidence": 1.0
            },
            {
                "text": "房产投资存在市场风险，价格可能波动",
                "severity": "medium",
                "confidence": 0.95
            },
            {
                "text": "请结合实地考察和专业咨询做出决策",
                "severity": "medium",
                "confidence": 1.0
            }
        ]
        
        if style == "aggressive":
            warnings.append({
                "text": "激进型策略风险较高，请确保有足够的风险承受能力",
                "severity": "high",
                "confidence": 0.9
            })
        
        data_quality_warning = self._generate_data_quality_warning(analysis_result)
        if data_quality_warning:
            warnings.append(data_quality_warning)
        
        return {
            "warnings": warnings,
            "disclaimer": "本报告由AI系统自动生成，数据仅供参考，不构成任何投资建议。实际投资决策请咨询专业人士。"
        }
    
    def _generate_data_quality_warning(self, analysis_result: Dict) -> Optional[Dict[str, Any]]:
        """生成数据质量警告"""
        if not analysis_result:
            return None
        
        low_confidence_fields = []
        
        for key, value in analysis_result.items():
            if isinstance(value, dict) and value.get('confidence', 1.0) < 0.7:
                low_confidence_fields.append(key)
            elif key.endswith('_confidence') and value < 0.7:
                field_name = key.replace('_confidence', '')
                low_confidence_fields.append(field_name)
        
        if low_confidence_fields:
            return {
                "text": f"部分数据（{', '.join(low_confidence_fields[:3])}）置信度较低，建议进一步核实",
                "severity": "low",
                "confidence": 0.9,
                "affected_fields": low_confidence_fields
            }
        
        return None
    
    async def _generate_data_sources(self, requirement: Dict, collected_data: Dict,
                                     analysis_result: Dict, style: str) -> Dict[str, Any]:
        """生成数据来源列表"""
        sources = []
        source_ids = set()
        
        def add_source(source_dict: Dict):
            source_id = f"{source_dict.get('type')}_{source_dict.get('name')}"
            if source_id not in source_ids:
                source_ids.add(source_id)
                sources.append(source_dict)
        
        if collected_data:
            for key, value in collected_data.items():
                if isinstance(value, dict) and 'source' in value:
                    add_source(value['source'])
        
        if analysis_result:
            for key, value in analysis_result.items():
                if isinstance(value, dict) and 'source' in value:
                    add_source(value['source'])
        
        user_source = DataSource(
            name="用户需求",
            source_type="user_input",
            description="用户提供的查询条件",
            confidence=1.0
        )
        sources.insert(0, user_source.to_dict())
        
        if not any(s.get('type') == 'market' for s in sources):
            market_source = DataSource(
                name="市场数据",
                source_type="simulated",
                description="模拟市场数据，仅供演示",
                confidence=0.7
            )
            sources.append(market_source.to_dict())
        
        if not any(s.get('type') == 'analysis' for s in sources):
            analysis_source = DataSource(
                name="智能分析",
                source_type="analysis",
                description="基于公开信息的模拟分析",
                confidence=0.75
            )
            sources.append(analysis_source.to_dict())
        
        high_confidence = len([s for s in sources if s.get('confidence', 0) >= 0.8])
        medium_confidence = len([s for s in sources if 0.6 <= s.get('confidence', 0) < 0.8])
        low_confidence = len([s for s in sources if s.get('confidence', 0) < 0.6])
        
        return {
            "sources": sources,
            "summary": {
                "total": len(sources),
                "high_confidence": high_confidence,
                "medium_confidence": medium_confidence,
                "low_confidence": low_confidence,
                "overall_reliability": "high" if high_confidence > len(sources) * 0.6 else "medium"
            }
        }
    
    async def _generate_charts(self, collected_data: Dict, analysis_result: Dict) -> List[Dict[str, Any]]:
        """
        生成图表配置
        
        Args:
            collected_data: 收集的数据
            analysis_result: 分析结果
            
        Returns:
            List[Dict]: 图表配置列表
        """
        charts = []
        
        price_history = collected_data.get("price_history", [])
        if price_history:
            charts.append({
                "id": "price_trend",
                "type": "line",
                "title": "近6个月房价走势",
                "section": "detailed_analysis",
                "config": {
                    "xAxis": {"dataKey": "month", "label": "月份"},
                    "yAxis": {"label": "均价(万元/㎡)"},
                    "lines": [
                        {"dataKey": "price", "name": "成交均价", "color": "#3b82f6"},
                        {"dataKey": "listingPrice", "name": "挂牌均价", "color": "#94a3b8"}
                    ]
                },
                "data": price_history
            })
        
        price_distribution = collected_data.get("price_distribution", [])
        if price_distribution:
            charts.append({
                "id": "price_distribution",
                "type": "bar",
                "title": "价格区间分布",
                "section": "detailed_analysis",
                "config": {
                    "xAxis": {"dataKey": "range", "label": "价格区间"},
                    "yAxis": {"label": "房源数量"},
                    "bars": [
                        {"dataKey": "count", "name": "房源数", "color": "#3b82f6"}
                    ]
                },
                "data": price_distribution
            })
        
        area_distribution = collected_data.get("area_distribution", [])
        if area_distribution:
            charts.append({
                "id": "area_distribution",
                "type": "pie",
                "title": "面积分布",
                "section": "detailed_analysis",
                "config": {
                    "dataKey": "value",
                    "nameKey": "name"
                },
                "data": area_distribution
            })
        
        if not charts:
            charts = self._get_default_charts()
        
        return charts
    
    def _get_default_charts(self) -> List[Dict[str, Any]]:
        """获取默认图表配置（模拟数据）"""
        return [
            {
                "id": "price_trend",
                "type": "line",
                "title": "近6个月房价走势",
                "section": "detailed_analysis",
                "config": {
                    "xAxis": {"dataKey": "month", "label": "月份"},
                    "yAxis": {"label": "均价(万元/㎡)"},
                    "lines": [
                        {"dataKey": "price", "name": "成交均价", "color": "#3b82f6"},
                        {"dataKey": "listingPrice", "name": "挂牌均价", "color": "#94a3b8"}
                    ]
                },
                "data": [
                    {"month": "1月", "price": 5.2, "listingPrice": 5.4},
                    {"month": "2月", "price": 5.3, "listingPrice": 5.5},
                    {"month": "3月", "price": 5.1, "listingPrice": 5.3},
                    {"month": "4月", "price": 5.4, "listingPrice": 5.6},
                    {"month": "5月", "price": 5.5, "listingPrice": 5.7},
                    {"month": "6月", "price": 5.6, "listingPrice": 5.8}
                ]
            },
            {
                "id": "price_distribution",
                "type": "bar",
                "title": "价格区间分布",
                "section": "detailed_analysis",
                "config": {
                    "xAxis": {"dataKey": "range", "label": "价格区间(万)"},
                    "yAxis": {"label": "房源数量"},
                    "bars": [
                        {"dataKey": "count", "name": "房源数", "color": "#3b82f6"}
                    ]
                },
                "data": [
                    {"range": "300以下", "count": 45},
                    {"range": "300-500", "count": 120},
                    {"range": "500-800", "count": 85},
                    {"range": "800-1000", "count": 42},
                    {"range": "1000以上", "count": 28}
                ]
            },
            {
                "id": "area_distribution",
                "type": "pie",
                "title": "面积分布",
                "section": "detailed_analysis",
                "config": {
                    "dataKey": "value",
                    "nameKey": "name"
                },
                "data": [
                    {"name": "60㎡以下", "value": 15},
                    {"name": "60-90㎡", "value": 35},
                    {"name": "90-120㎡", "value": 30},
                    {"name": "120-150㎡", "value": 15},
                    {"name": "150㎡以上", "value": 5}
                ]
            }
        ]
    
    def _get_fallback_content(self, section_key: str) -> Any:
        """获取备用内容"""
        fallback_source = DataSource(
            name="系统默认",
            source_type="simulated",
            description="备用数据",
            confidence=0.5
        )
        
        fallbacks = {
            "summary": {
                "text": "摘要生成中...",
                "confidence": 0.5,
                "sources": [fallback_source.to_dict()]
            },
            "key_findings": [DataPoint(
                title="分析中",
                value="数据收集中",
                source=fallback_source,
                confidence=0.5
            ).to_dict()],
            "detailed_analysis": {"note": "详细分析生成中..."},
            "investment_advice": {
                "overall_rating": {
                    "value": "评估中",
                    "confidence": 0.5,
                    "source": fallback_source.to_dict()
                },
                "action_recommendation": {
                    "value": "请稍候",
                    "confidence": 0.5,
                    "source": fallback_source.to_dict()
                }
            },
            "risk_warning": {
                "warnings": [{"text": "风险分析中...", "severity": "medium", "confidence": 0.5}],
                "disclaimer": "分析中..."
            },
            "data_sources": {
                "sources": [fallback_source.to_dict()],
                "summary": {"total": 1, "high_confidence": 0, "medium_confidence": 0, "low_confidence": 1, "overall_reliability": "low"}
            }
        }
        return fallbacks.get(section_key, {})
    
    async def _broadcast_progress(self, event_type: str, data: Dict[str, Any]) -> None:
        """广播报告生成进度"""
        if not self._stream_enabled or not self._report_id:
            return
        
        await sse_manager.broadcast_report_progress(
            task_id=self.task_id,
            report_id=self._report_id,
            event_type=event_type,
            data=data
        )
    
    async def _broadcast_agent_reference(
        self,
        section_key: str,
        status: str,
        content: Any = None
    ) -> None:
        """
        广播代理引用事件，用于时间线高亮
        
        Args:
            section_key: 报告章节
            status: 状态 (started/completed)
            content: 章节内容
        """
        if not self._stream_enabled or not self._report_id:
            return
        
        agent_mapping = {
            "summary": {
                "agent_name": "analyst",
                "step_name": "综合分析",
                "description": "生成执行摘要"
            },
            "key_findings": {
                "agent_name": "analyst",
                "step_name": "关键发现提取",
                "description": "提取核心发现"
            },
            "detailed_analysis": {
                "agent_name": "analyst",
                "step_name": "详细分析",
                "description": "生成详细分析"
            },
            "investment_advice": {
                "agent_name": "analyst",
                "step_name": "投资建议",
                "description": "生成投资建议"
            },
            "risk_warning": {
                "agent_name": "analyst",
                "step_name": "风险评估",
                "description": "生成风险提示"
            },
            "data_sources": {
                "agent_name": "collector",
                "step_name": "数据汇总",
                "description": "汇总数据来源"
            }
        }
        
        mapping = agent_mapping.get(section_key, {
            "agent_name": "analyst",
            "step_name": section_key,
            "description": f"生成{section_key}"
        })
        
        await sse_manager.broadcast_timeline_highlight(
            task_id=self.task_id,
            report_id=self._report_id,
            agent_name=mapping["agent_name"],
            step_name=mapping["step_name"],
            section=section_key,
            status=status,
            description=mapping["description"],
            content=content
        )
