"""
子代理模块
实现无状态代理服务
"""
import asyncio
import json
import logging
from typing import Dict, Any, Optional, List
from dataclasses import dataclass, field
from datetime import datetime
from abc import ABC, abstractmethod

logger = logging.getLogger(__name__)

@dataclass
class AgentRequest:
    request_id: str
    input_data: Any
    memories: List[Dict] = field(default_factory=list)
    context: Dict = field(default_factory=dict)
    persona: str = "zhouyu"
    timestamp: datetime = field(default_factory=datetime.utcnow)

@dataclass
class AgentResponse:
    request_id: str
    success: bool
    result: Any = None
    error: Optional[str] = None
    metadata: Dict = field(default_factory=dict)
    timestamp: datetime = field(default_factory=datetime.utcnow)

class BaseAgent(ABC):
    """
    代理基类
    所有子代理需要继承此类
    """
    
    def __init__(self, name: str, description: str = ""):
        self.name = name
        self.description = description
        self._initialized = False
    
    async def initialize(self):
        if not self._initialized:
            await self._setup()
            self._initialized = True
            logger.info(f"Agent '{self.name}' initialized")
    
    async def _setup(self):
        pass
    
    @abstractmethod
    async def handle_message(self, request: AgentRequest) -> AgentResponse:
        pass
    
    async def call_llm(self, prompt: str, system_prompt: str = "") -> str:
        from ..llm_service import llm_service
        
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})
        
        try:
            response = await llm_service.generate(messages)
            return response
        except Exception as e:
            logger.error(f"LLM call failed: {e}")
            return ""
    
    def get_persona_prompt(self, persona: str) -> str:
        prompts = {
            "zhouyu": """你是周瑜，东吴大都督。你儒雅从容、足智多谋、善于用兵。
在房产咨询中，你以战略眼光分析市场，用典故和比喻阐述观点。
称呼用户为"主公"，语气恭敬但不失威严。
你的分析风格：宏观把控、战略布局、权衡利弊。""",
            
            "luxun": """你是陆逊，东吴名将。你沉稳内敛、心思缜密、善于防守反击。
在房产咨询中，你以细致入微的分析见长，善于发现潜在风险。
称呼用户为"主公"，语气谦和但言之有物。
你的分析风格：细节把控、风险评估、稳中求进。"""
        }
        return prompts.get(persona, prompts["zhouyu"])
    
    def build_context_prompt(self, memories: List[Dict], context: Dict) -> str:
        context_parts = []
        
        if memories:
            memory_text = "\n".join([
                f"- {m.get('summary', m.get('input_text', '未知记忆'))}"
                for m in memories[:5]
            ])
            context_parts.append(f"用户历史偏好：\n{memory_text}")
        
        if context:
            for key, value in context.items():
                if value:
                    context_parts.append(f"{key}: {value}")
        
        return "\n".join(context_parts)


class RequirementAgent(BaseAgent):
    """需求分析代理"""
    
    def __init__(self):
        super().__init__("requirement", "分析用户房产需求，提取关键信息")
    
    async def handle_message(self, request: AgentRequest) -> AgentResponse:
        try:
            query = request.input_data
            context_prompt = self.build_context_prompt(request.memories, request.context)
            system_prompt = self.get_persona_prompt(request.persona)
            
            prompt = f"""请分析以下房产需求，提取关键信息：

用户查询：{query}

{context_prompt}

请以JSON格式返回分析结果，包含：
1. region: 目标区域
2. budget: 预算范围
3. house_type: 房屋类型
4. area_range: 面积范围
5. special_needs: 特殊需求列表
6. priority: 优先级排序"""
            
            response = await self.call_llm(prompt, system_prompt)
            
            try:
                if "```json" in response:
                    response = response.split("```json")[1].split("```")[0]
                elif "```" in response:
                    response = response.split("```")[1].split("```")[0]
                result = json.loads(response.strip())
            except:
                result = {
                    "region": "未知",
                    "budget": "未知",
                    "house_type": "未知",
                    "area_range": "未知",
                    "special_needs": [],
                    "priority": [],
                    "raw_analysis": response,
                }
            
            return AgentResponse(
                request_id=request.request_id,
                success=True,
                result=result,
                metadata={"agent": self.name}
            )
        except Exception as e:
            logger.error(f"RequirementAgent error: {e}")
            return AgentResponse(
                request_id=request.request_id,
                success=False,
                result=None,
                error=str(e)
            )


class CollectorAgent(BaseAgent):
    """数据采集代理"""
    
    def __init__(self):
        super().__init__("collector", "采集房产相关数据")
    
    async def handle_message(self, request: AgentRequest) -> AgentResponse:
        try:
            requirement_result = request.input_data
            context_prompt = self.build_context_prompt(request.memories, request.context)
            system_prompt = self.get_persona_prompt(request.persona)
            
            prompt = f"""基于以下需求分析，采集相关房产数据：

需求分析：{json.dumps(requirement_result, ensure_ascii=False)}

{context_prompt}

请以JSON格式返回采集结果，包含：
1. listings: 房源列表（每个包含标题、价格、面积、位置）
2. market_data: 市场数据（均价、涨跌幅等）
3. nearby_facilities: 周边设施
4. data_sources: 数据来源"""
            
            response = await self.call_llm(prompt, system_prompt)
            
            try:
                if "```json" in response:
                    response = response.split("```json")[1].split("```")[0]
                elif "```" in response:
                    response = response.split("```")[1].split("```")[0]
                result = json.loads(response.strip())
            except:
                result = {
                    "listings": [],
                    "market_data": {},
                    "nearby_facilities": [],
                    "data_sources": [],
                    "raw_collection": response,
                }
            
            return AgentResponse(
                request_id=request.request_id,
                success=True,
                result=result,
                metadata={"agent": self.name}
            )
        except Exception as e:
            logger.error(f"CollectorAgent error: {e}")
            return AgentResponse(
                request_id=request.request_id,
                success=False,
                result=None,
                error=str(e)
            )


class AnalystAgent(BaseAgent):
    """市场分析代理"""
    
    def __init__(self):
        super().__init__("analyst", "分析房产市场趋势")
    
    async def handle_message(self, request: AgentRequest) -> AgentResponse:
        try:
            collection_result = request.input_data
            context_prompt = self.build_context_prompt(request.memories, request.context)
            system_prompt = self.get_persona_prompt(request.persona)
            
            prompt = f"""基于以下采集数据，进行市场分析：

采集数据：{json.dumps(collection_result, ensure_ascii=False)}

{context_prompt}

请以JSON格式返回分析结果，包含：
1. market_trend: 市场趋势
2. price_analysis: 价格分析
3. location_insights: 区域洞察
4. investment_advice: 投资建议
5. risk_assessment: 风险评估"""
            
            response = await self.call_llm(prompt, system_prompt)
            
            try:
                if "```json" in response:
                    response = response.split("```json")[1].split("```")[0]
                elif "```" in response:
                    response = response.split("```")[1].split("```")[0]
                result = json.loads(response.strip())
            except:
                result = {
                    "market_trend": "稳定",
                    "price_analysis": response[:200],
                    "location_insights": [],
                    "investment_advice": [],
                    "risk_assessment": [],
                    "raw_analysis": response,
                }
            
            return AgentResponse(
                request_id=request.request_id,
                success=True,
                result=result,
                metadata={"agent": self.name}
            )
        except Exception as e:
            logger.error(f"AnalystAgent error: {e}")
            return AgentResponse(
                request_id=request.request_id,
                success=False,
                result=None,
                error=str(e)
            )


class ReportWriterAgent(BaseAgent):
    """报告生成代理"""
    
    def __init__(self):
        super().__init__("report_writer", "生成房产分析报告")
    
    async def handle_message(self, request: AgentRequest) -> AgentResponse:
        try:
            analysis_result = request.input_data
            system_prompt = self.get_persona_prompt(request.persona)
            
            prompt = f"""基于以下分析结果，生成一份专业的房产分析报告：

分析数据：{json.dumps(analysis_result, ensure_ascii=False)}

请生成一份结构化的报告，包含：
1. 摘要
2. 市场分析
3. 价格评估
4. 区域分析
5. 投资建议
6. 风险提示
7. 都督寄语（用{request.persona}的口吻写一段总结性建议）"""
            
            response = await self.call_llm(prompt, system_prompt)
            
            result = {
                "report": response,
                "persona": request.persona,
                "generated_at": datetime.utcnow().isoformat(),
            }
            
            return AgentResponse(
                request_id=request.request_id,
                success=True,
                result=result,
                metadata={"agent": self.name}
            )
        except Exception as e:
            logger.error(f"ReportWriterAgent error: {e}")
            return AgentResponse(
                request_id=request.request_id,
                success=False,
                result=None,
                error=str(e)
            )


_agents: Dict[str, BaseAgent] = {}

async def get_agent(name: str) -> BaseAgent:
    global _agents
    if name not in _agents:
        agent_classes = {
            "requirement": RequirementAgent,
            "collector": CollectorAgent,
            "analyst": AnalystAgent,
            "report_writer": ReportWriterAgent,
        }
        if name in agent_classes:
            _agents[name] = agent_classes[name]()
            await _agents[name].initialize()
    return _agents.get(name)

async def call_agent(name: str, request: AgentRequest) -> AgentResponse:
    agent = await get_agent(name)
    if agent:
        return await agent.handle_message(request)
    return AgentResponse(
        request_id=request.request_id,
        success=False,
        result=None,
        error=f"Agent '{name}' not found"
    )
