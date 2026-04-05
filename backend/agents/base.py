"""
代理基类模块
提供统一的代理接口和通用功能
"""
import asyncio
import logging
from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, List
from dataclasses import dataclass, field
from datetime import datetime
import json

logger = logging.getLogger(__name__)

@dataclass
class AgentRequest:
    """标准化代理请求"""
    request_id: str
    input_data: Any
    context: Dict[str, Any] = field(default_factory=dict)
    memories: List[Dict] = field(default_factory=list)
    persona: str = "zhouyu"
    
    def to_dict(self) -> dict:
        return {
            "request_id": self.request_id,
            "input_data": self.input_data,
            "context": self.context,
            "memories": self.memories,
            "persona": self.persona,
        }

@dataclass
class AgentResponse:
    """标准化代理响应"""
    request_id: str
    success: bool
    result: Any
    metadata: Dict[str, Any] = field(default_factory=dict)
    error: Optional[str] = None
    timestamp: datetime = field(default_factory=datetime.utcnow)
    
    def to_dict(self) -> dict:
        return {
            "request_id": self.request_id,
            "success": self.success,
            "result": self.result,
            "metadata": self.metadata,
            "error": self.error,
            "timestamp": self.timestamp.isoformat(),
        }

class BaseAgent(ABC):
    """
    代理基类
    所有子代理必须继承此类
    """
    
    def __init__(self, name: str, task_id: str = "", bus=None, description: str = "", **kwargs):
        self.name = name
        self.task_id = task_id
        self.bus = bus
        self.description = description
        self._initialized = False
    
    async def initialize(self):
        """初始化代理"""
        if not self._initialized:
            await self._setup()
            self._initialized = True
            logger.info(f"Agent '{self.name}' initialized")
    
    async def _setup(self):
        """子类可重写的初始化逻辑"""
        pass
    
    async def start(self):
        """启动代理"""
        await self.initialize()
        self._running = True
        logger.info(f"Agent '{self.name}' started")
        if self.bus:
            if self.name not in self.bus._queues:
                self.bus.register_agent(self.name)
            self._message_task = asyncio.create_task(self._message_loop())
    
    async def _message_loop(self):
        """消息循环"""
        if not self.bus:
            return
        
        try:
            queue = await self.bus.subscribe(self.name)
            while self._running:
                try:
                    message = await asyncio.wait_for(queue.get(), timeout=1.0)
                    await self.handle_message(message)
                except asyncio.TimeoutError:
                    continue
                except Exception as e:
                    logger.error(f"Error processing message: {e}")
        except Exception as e:
            logger.error(f"Message loop error: {e}")
    
    async def stop(self):
        """停止代理"""
        self._running = False
        logger.info(f"Agent '{self.name}' stopped")
    
    async def send(
        self,
        recipient: str,
        message_type: 'MessageType',
        content: Dict[str, Any],
        in_reply_to: Optional[str] = None
    ) -> 'AgentMessage':
        """
        发送消息给其他代理
        
        Args:
            recipient: 接收者代理名称
            message_type: 消息类型
            content: 消息内容
            in_reply_to: 回复的消息ID
            
        Returns:
            AgentMessage: 发送的消息
        """
        from .message import AgentMessage
        
        message = AgentMessage(
            task_id=self.task_id,
            sender=self.name,
            recipient=recipient,
            type=message_type,
            content=content,
            in_reply_to=in_reply_to
        )
        
        if self.bus:
            await self.bus.publish(message)
        
        return message
    
    async def respond(self, original_message: 'AgentMessage', content: Dict[str, Any]) -> 'AgentMessage':
        """
        回复消息
        
        Args:
            original_message: 原始消息
            content: 回复内容
            
        Returns:
            AgentMessage: 发送的消息
        """
        from .message import MessageType
        
        return await self.send(
            recipient=original_message.sender,
            message_type=MessageType.RESPONSE,
            content=content,
            in_reply_to=original_message.id
        )
    
    async def record_step(
        self,
        step_name: str,
        description: str = "",
        status: str = "completed",
        input_data: Optional[Dict] = None,
        output_data: Optional[Dict] = None
    ) -> None:
        """
        记录工作流步骤
        
        Args:
            step_name: 步骤名称
            description: 步骤描述
            status: 步骤状态
            input_data: 输入数据
            output_data: 输出数据
        """
        from ..database import AnalysisStepDB, get_db_connection
        from ..sse_manager import sse_manager, SSEEvent
        from datetime import datetime
        import uuid
        
        try:
            conn = await get_db_connection()
            cursor = await conn.execute(
                "SELECT id FROM analysis_steps WHERE task_id = $1 AND step_name = $2",
                (self.task_id, step_name)
            )
            row = await cursor.fetchone()
            
            if row:
                step_id = row["id"]
                await AnalysisStepDB.update_step(
                    step_id=step_id,
                    status=status,
                    output_data=output_data
                )
            else:
                step_id = str(uuid.uuid4())
                step_order = len(self._step_records) if hasattr(self, '_step_records') else 0
                
                await AnalysisStepDB.create_step(
                    step_id=step_id,
                    task_id=self.task_id,
                    step_name=step_name,
                    step_order=step_order,
                    agent_name=self.name,
                    input_data=input_data or {"description": description}
                )
            
            if status == "completed" and output_data:
                await AnalysisStepDB.update_step(
                    step_id=step_id,
                    status=status,
                    output_data=output_data
                )
            
            try:
                step_data = {
                    "id": step_id,
                    "task_id": self.task_id,
                    "step_name": step_name,
                    "step_order": step_order,
                    "agent_name": self.name,
                    "status": status,
                    "input_data": input_data or {"description": description},
                    "output_data": output_data,
                    "created_at": datetime.now().isoformat(),
                    "completed_at": datetime.now().isoformat() if status == "completed" else None,
                    "detail": description
                }
                
                event = SSEEvent(
                    event="step",
                    data=step_data,
                    id=step_id
                )
                await sse_manager.broadcast(self.task_id, event)
            except Exception as sse_error:
                logger.warning(f"Failed to broadcast SSE event: {sse_error}")
                
        except Exception as e:
            logger.error(f"Failed to record step: {e}")
    
    @abstractmethod
    async def handle_message(self, message: 'AgentMessage') -> None:
        """
        处理消息 - 子类必须实现
        
        Args:
            message: 消息对象
        """
        pass
    
    async def call_llm(self, prompt: str, system_prompt: str = "") -> str:
        """
        调用LLM服务
        """
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
        """
        获取角色化提示词
        """
        prompts = {
            "zhouyu": """你是周瑜，东吴大都督。你儒雅从容、足智多谋，善于用兵。
在房产咨询中，你以战略眼光分析市场，用典故和比喻阐述观点。
称呼用户为"主公"，语气恭敬但不失威严。
你的分析风格：宏观把控、战略布局、权衡利弊。""",
            
            "luxun": """你是陆逊，东吴名将。你沉稳内敛、心思缜密，善于防守反击。
在房产咨询中，你以细致入微的分析见长，善于发现潜在风险。
称呼用户为"主公"，语气谦和但言之有物。
你的分析风格：细节把控、风险评估、稳中求进。"""
        }
        return prompts.get(persona, prompts["zhouyu"])
    
    def build_context_prompt(self, memories: List[Dict], context: Dict) -> str:
        """
        构建上下文提示词
        """
        parts = []
        
        if memories:
            memory_text = "\n".join([
                f"- {m.get('summary', m.get('input_text', ''))}"
                for m in memories[:5]
            ])
            parts.append(f"用户历史偏好：\n{memory_text}")
        
        if context:
            context_items = []
            for k, v in context.items():
                if v:
                    context_items.append(f"- {k}: {v}")
            if context_items:
                parts.append("任务上下文：\n" + "\n".join(context_items))
        
        return "\n\n".join(parts) if parts else ""

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
            requirement = request.input_data
            context_prompt = self.build_context_prompt(request.memories, request.context)
            system_prompt = self.get_persona_prompt(request.persona)
            
            prompt = f"""根据以下需求，规划数据采集策略：

需求分析：{json.dumps(requirement, ensure_ascii=False) if isinstance(requirement, dict) else requirement}

{context_prompt}

请返回JSON格式的数据采集计划，包含：
1. data_sources: 数据来源列表
2. collection_strategy: 采集策略
3. estimated_items: 预计数据量
4. key_metrics: 关键指标"""
            
            response = await self.call_llm(prompt, system_prompt)
            
            try:
                if "```json" in response:
                    response = response.split("```json")[1].split("```")[0]
                elif "```" in response:
                    response = response.split("```")[1].split("```")[0]
                result = json.loads(response.strip())
            except:
                result = {
                    "data_sources": ["公开数据"],
                    "collection_strategy": "综合采集",
                    "estimated_items": 100,
                    "key_metrics": ["价格", "面积", "位置"],
                    "raw_response": response,
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
        super().__init__("analyst", "分析房产市场趋势和数据")
    
    async def handle_message(self, request: AgentRequest) -> AgentResponse:
        try:
            data = request.input_data
            context_prompt = self.build_context_prompt(request.memories, request.context)
            system_prompt = self.get_persona_prompt(request.persona)
            
            prompt = f"""基于以下数据进行房产市场分析：

数据：{json.dumps(data, ensure_ascii=False) if isinstance(data, dict) else data}

{context_prompt}

请返回JSON格式的分析结果，包含：
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
        super().__init__("report_writer", "生成结构化分析报告")
    
    async def handle_message(self, request: AgentRequest) -> AgentResponse:
        try:
            analysis = request.input_data
            context_prompt = self.build_context_prompt(request.memories, request.context)
            system_prompt = self.get_persona_prompt(request.persona)
            
            persona_name = "周瑜" if request.persona == "zhouyu" else "陆逊"
            
            prompt = f"""基于以下分析结果，生成一份专业的房产分析报告：

分析数据：{json.dumps(analysis, ensure_ascii=False) if isinstance(analysis, dict) else analysis}

{context_prompt}

请生成一份完整的报告，包含：
1. 摘要
2. 市场分析
3. 区域评估
4. 投资建议
5. 风险提示
6. 结论

以{persona_name}的口吻撰写，最后附上都督寄语。"""
            
            response = await self.call_llm(prompt, system_prompt)
            
            result = {
                "report": response,
                "persona": request.persona,
                "signature": f"\n\n—— {persona_name}大都督",
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

AGENT_REGISTRY: Dict[str, type] = {
    "requirement": RequirementAgent,
    "collector": CollectorAgent,
    "analyst": AnalystAgent,
    "report_writer": ReportWriterAgent,
}

_agent_instances: Dict[str, BaseAgent] = {}

async def get_agent(name: str) -> BaseAgent:
    """获取代理实例"""
    if name not in _agent_instances:
        if name in AGENT_REGISTRY:
            _agent_instances[name] = AGENT_REGISTRY[name]()
            await _agent_instances[name].initialize()
        else:
            raise ValueError(f"Unknown agent: {name}")
    return _agent_instances[name]

async def call_agent(name: str, request: AgentRequest) -> AgentResponse:
    """调用代理"""
    agent = await get_agent(name)
    return await agent.handle_message(request)
