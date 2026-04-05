"""
主管代理
负责接收用户请求，分解任务，协调其他代理，汇总结果
支持并行执行子代理任务
集成记忆系统实现跨会话记忆能力
"""
import asyncio
import uuid
import json
from typing import Dict, Any, Optional, List
from .base import BaseAgent
from .message import AgentMessage, MessageType
from ..database import AnalysisStepDB, ReportDB
from ..memory.service import memory_service
import logging

logger = logging.getLogger(__name__)


class SubTask:
    """
    子任务类
    用于跟踪子任务的执行状态
    """
    def __init__(self, task_id: str, target_agent: str, action: str, params: dict):
        self.task_id = task_id
        self.target_agent = target_agent
        self.action = action
        self.params = params
        self.status = "pending"
        self.result: Optional[Dict[str, Any]] = None
        self.request_message_id: Optional[str] = None
        self.response_message_id: Optional[str] = None
        self.done_event = asyncio.Event()


class SupervisorAgent(BaseAgent):
    """
    主管代理
    负责协调其他代理的工作流程，支持并行执行
    
    工作流程：
    1. 收到 "start" 请求
    2. 解析用户需求
    3. 并行分配任务给需求分析师、数据采集师、市场分析师
    4. 等待所有子代理完成
    5. 生成最终报告
    """
    
    def __init__(self, agent_name: str, task_id: str, bus, **kwargs):
        super().__init__(agent_name, task_id, bus, **kwargs)
        
        self._pending_requests: Dict[str, SubTask] = {}
        self._sub_tasks: List[SubTask] = []
        self._workflow_state = "idle"
        self._original_request: Optional[AgentMessage] = None
        self._workflow_result: Dict[str, Any] = {}
        
        self._parsed_data: Optional[Dict] = None
        self._collected_data: Optional[Dict] = None
        self._analyzed_data: Optional[Dict] = None
        
        self._requirement_done = asyncio.Event()
        self._collector_done = asyncio.Event()
        self._analyst_done = asyncio.Event()
    
    async def handle_message(self, message: AgentMessage) -> None:
        logger.info(f"SupervisorAgent received message from {message.sender}, type={message.type.value}")
        
        if message.type == MessageType.REQUEST:
            await self._handle_request(message)
        elif message.type == MessageType.RESPONSE:
            await self._handle_response(message)
        elif message.type == MessageType.ERROR:
            await self._handle_error(message)
    
    async def _handle_request(self, message: AgentMessage) -> None:
        action = message.content.get("action")
        
        if action == "start":
            asyncio.create_task(self._start_workflow(message))
        elif action == "status":
            await self._report_status(message)
        else:
            logger.warning(f"Unknown action: {action}")
    
    async def _handle_response(self, message: AgentMessage) -> None:
        if message.in_reply_to and message.in_reply_to in self._pending_requests:
            sub_task = self._pending_requests.pop(message.in_reply_to)
            sub_task.status = "completed"
            sub_task.result = message.content
            sub_task.response_message_id = message.id
            sub_task.done_event.set()
            
            logger.info(f"SubTask completed: {sub_task.target_agent}.{sub_task.action}")
            
            await self._process_subtask_result(sub_task)
    
    async def _handle_error(self, message: AgentMessage) -> None:
        if message.in_reply_to and message.in_reply_to in self._pending_requests:
            sub_task = self._pending_requests.pop(message.in_reply_to)
            sub_task.status = "failed"
            sub_task.result = message.content
            sub_task.done_event.set()
            
            logger.error(f"SubTask failed: {sub_task.target_agent}.{sub_task.action}")
            
            await self._handle_workflow_failure(sub_task)
    
    async def _start_workflow(self, message: AgentMessage) -> None:
        """
        启动工作流 - 支持并行执行
        集成记忆系统：检索相关记忆，工作流结束后存储记忆
        """
        self._original_request = message
        self._workflow_state = "parsing"
        
        query = message.content.get("query", "")
        user_id = message.content.get("user_id", "anonymous")
        self._user_id = user_id
        
        logger.info(f"Starting workflow for query: {query}, user: {user_id}")
        
        try:
            memory_context = await memory_service.get_context(user_id, query, max_memories=5)
            if memory_context:
                logger.info(f"Retrieved memory context for user {user_id}")
                self._memory_context = memory_context
            else:
                self._memory_context = None
        except Exception as e:
            logger.warning(f"Failed to retrieve memories: {e}")
            self._memory_context = None
        
        await self.record_step("开始处理", f"收到用户请求: {query}", status="completed")
        
        await self.record_step("需求解析", "正在从查询中提取关键信息...", status="running")
        
        requirement_task = SubTask(
            task_id=self.task_id,
            target_agent="requirement",
            action="parse",
            params={"query": query}
        )
        
        await self._dispatch_subtask(requirement_task)
        
        await self._requirement_done.wait()
        
        if self._parsed_data:
            await self.record_step("需求解析完成", f"提取到: {self._parsed_data}", status="completed")
            
            await self.record_step("任务分配", "正在并行分配任务给各代理...", status="running")
            
            collector_task = SubTask(
                task_id=self.task_id,
                target_agent="collector",
                action="collect",
                params={"parsed": self._parsed_data}
            )
            
            analyst_task = SubTask(
                task_id=self.task_id,
                target_agent="analyst",
                action="analyze",
                params={"parsed": self._parsed_data, "data": {}}
            )
            
            await self._dispatch_subtask(collector_task)
            await self._dispatch_subtask(analyst_task)
            
            await self.record_step("任务分配完成", "已并行分配任务给数据采集师和市场分析师", status="completed")
            
            await self.record_step("等待结果", "等待各代理完成任务...", status="running")
            
            await asyncio.gather(
                self._collector_done.wait(),
                self._analyst_done.wait()
            )
            
            await self.record_step("结果汇总", "所有代理已完成，开始生成报告...", status="completed")
            
            await self._generate_report()
    
    async def _dispatch_subtask(self, sub_task: SubTask) -> None:
        """
        分发子任务 - 直接调用子代理方法
        """
        sub_task.status = "running"
        self._sub_tasks.append(sub_task)
        
        agent_names = {
            "requirement": "需求分析师",
            "collector": "数据采集师",
            "analyst": "市场分析师"
        }
        
        await self.record_step(
            f"分配任务给{agent_names.get(sub_task.target_agent, sub_task.target_agent)}",
            f"正在通知{agent_names.get(sub_task.target_agent, sub_task.target_agent)}开始工作...",
            status="completed",
            input_data=sub_task.params
        )
        
        asyncio.create_task(self._execute_subtask(sub_task))
        
        logger.info(f"Dispatched subtask: {sub_task.target_agent}.{sub_task.action}")
    
    async def _execute_subtask(self, sub_task: SubTask) -> None:
        """
        执行子任务 - 直接调用子代理方法
        """
        try:
            from .message import AgentMessage
            
            message = AgentMessage(
                task_id=self.task_id,
                sender=self.name,
                recipient=sub_task.target_agent,
                type=MessageType.REQUEST,
                content={
                    "action": sub_task.action,
                    **sub_task.params
                }
            )
            
            if self.bus and sub_task.target_agent in self.bus._queues:
                agent_queue = self.bus._queues[sub_task.target_agent]
                
                self._pending_requests[message.id] = sub_task
                sub_task.request_message_id = message.id
                
                await agent_queue.put(message)
                
                await sub_task.done_event.wait()
            else:
                logger.warning(f"Agent {sub_task.target_agent} not registered in bus")
                sub_task.status = "failed"
                sub_task.result = {"error": f"Agent {sub_task.target_agent} not registered"}
                sub_task.done_event.set()
                
        except Exception as e:
            logger.error(f"Subtask execution failed: {e}")
            sub_task.status = "failed"
            sub_task.result = {"error": str(e)}
            sub_task.done_event.set()
    
    async def _process_subtask_result(self, sub_task: SubTask) -> None:
        """
        处理子任务结果
        """
        agent_names = {
            "requirement": "需求分析师",
            "collector": "数据采集师",
            "analyst": "市场分析师"
        }
        
        await self.record_step(
            f"{agent_names.get(sub_task.target_agent, sub_task.target_agent)}完成",
            f"{agent_names.get(sub_task.target_agent, sub_task.target_agent)}已完成任务",
            status="completed",
            output_data={"result": "success"}
        )
        
        if sub_task.target_agent == "requirement" and sub_task.action == "parse":
            self._parsed_data = sub_task.result.get("parsed", {})
            self._workflow_state = "collecting"
            self._requirement_done.set()
        
        elif sub_task.target_agent == "collector" and sub_task.action == "collect":
            self._collected_data = sub_task.result.get("data", {})
            self._workflow_state = "analyzing"
            self._collector_done.set()
            
            if sub_task.target_agent == "analyst":
                pass
        
        elif sub_task.target_agent == "analyst" and sub_task.action == "analyze":
            self._analyzed_data = sub_task.result.get("analysis", {})
            self._workflow_state = "reporting"
            self._analyst_done.set()
    
    async def _get_db_connection(self):
        from ..database import get_db_connection
        return await get_db_connection()
    
    async def _generate_report(self) -> None:
        """
        生成最终报告
        """
        summary = self._create_summary()
        key_findings = self._create_key_findings()
        detailed_analysis = self._create_detailed_analysis()
        investment_advice = self._create_investment_advice()
        risk_warnings = self._create_risk_warning()
        
        core_findings = self._create_core_findings()
        
        data_sources = [
            {"name": "房都督AI数据平台", "description": "房产交易数据", "reliability": "high"},
            {"name": "市场分析引擎", "description": "AI分析结果", "reliability": "medium"}
        ]
        
        report = {
            "task_id": self.task_id,
            "query": self._original_request.content.get("query", "") if self._original_request else "",
            "style": "balanced",
            "confidence_score": 0.85,
            "executive_summary": summary.get("text", "分析完成"),
            "core_findings": core_findings,
            "parsed": self._parsed_data,
            "data": self._collected_data,
            "analysis": self._analyzed_data,
            "summary": summary,
            "key_findings": key_findings,
            "detailed_analysis": detailed_analysis,
            "investment_advice": investment_advice,
            "risk_warning": risk_warnings,
            "risk_warnings": risk_warnings,
            "data_sources": data_sources,
            "sections": {
                "summary": summary,
                "key_findings": key_findings,
                "detailed_analysis": detailed_analysis,
                "investment_advice": investment_advice,
                "risk_warning": risk_warnings
            },
            "sub_tasks": [
                {"agent": st.target_agent, "action": st.action, "status": st.status}
                for st in self._sub_tasks
            ]
        }
        
        self._workflow_result = report
        self._workflow_state = "completed"
        
        await self.record_step("报告生成", "分析报告已生成", status="completed", output_data={"report_id": self.task_id})
        
        try:
            user_id = getattr(self, '_user_id', 'anonymous')
            query = self._original_request.content.get("query", "") if self._original_request else ""
            summary_text = summary.get("text", "分析完成") if summary else "分析完成"
            
            await memory_service.store(
                user_id=user_id,
                agent_name="supervisor",
                input_text=query,
                output_text=summary_text,
                session_id=self.task_id,
                metadata={
                    "category": "event",
                    "importance": 7.0,
                    "tags": ["analysis", "report", "property"]
                }
            )
            logger.info(f"Stored memory for user {user_id}")
        except Exception as e:
            logger.warning(f"Failed to store memory: {e}")
        
        try:
            report_id = str(uuid.uuid4())
            await ReportDB.create_report(
                report_id=report_id,
                task_id=self.task_id,
                user_id=self._user_id if hasattr(self, '_user_id') and self._user_id else "system",
                summary=json.dumps(summary, ensure_ascii=False)
            )
            await ReportDB.update_status(report_id, "generating")
            await ReportDB.update_content(report_id, report, progress=100)
            await ReportDB.update_status(report_id, "completed")
            logger.info(f"Report saved to database: {report_id}")
        except Exception as e:
            logger.error(f"Failed to save report: {e}")
        
        if self._original_request:
            await self.send(
                recipient=self._original_request.sender,
                message_type=MessageType.NOTIFY,
                content={"action": "report", "report": report},
                in_reply_to=self._original_request.id
            )
        
        logger.info(f"Workflow completed for task {self.task_id}")
    
    def _create_summary(self) -> Dict[str, Any]:
        summary_text = "分析完成"
        location = ""
        
        if self._parsed_data:
            location = f"{self._parsed_data.get('city', '')} {self._parsed_data.get('district', '')} {self._parsed_data.get('community', '')}".strip()
            summary_text = f"本次分析针对{location}的房产市场情况，"
        
        if self._collected_data:
            avg_price = self._collected_data.get("avg_price", 0)
            properties_count = len(self._collected_data.get("properties", []))
            summary_text += f"该区域平均房价为{avg_price}元/㎡，目前在售房源{properties_count}套。"
        
        if self._analyzed_data:
            recommendation = self._analyzed_data.get("recommendation", "")
            if recommendation:
                summary_text += f"综合建议：{recommendation}"
        
        return {
            "text": summary_text,
            "confidence": 0.85,
            "generated_by": "AI分析引擎",
            "status": "completed",
            "message": "分析完成",
            "location": location,
            "sources": [{"name": "市场数据", "type": "database", "reliability": "高"}]
        }
    
    def _create_core_findings(self) -> Dict[str, Any]:
        location = {}
        market_overview = {}
        price_analysis = {}
        property_insights = []
        
        if self._parsed_data:
            location = {
                "city": self._parsed_data.get("city", ""),
                "district": self._parsed_data.get("district", ""),
                "community": self._parsed_data.get("community", "")
            }
        
        if self._collected_data:
            properties = self._collected_data.get("properties", [])
            avg_price = self._collected_data.get("avg_price", 0)
            market_stats = self._collected_data.get("market_stats", {})
            
            market_overview = {
                "total_properties": len(properties),
                "average_price": avg_price,
                "price_range": {
                    "min": min([p.get("price_per_sqm", 0) for p in properties]) if properties else 0,
                    "max": max([p.get("price_per_sqm", 0) for p in properties]) if properties else 0
                },
                "transaction_volume_30d": market_stats.get("transaction_count_30d", 0)
            }
            
            price_analysis = {
                "current_price": avg_price,
                "trend": self._collected_data.get("trend", "stable"),
                "trend_direction": "稳定" if self._collected_data.get("trend", "stable") == "stable" else ("上涨" if self._collected_data.get("trend") == "rising" else "下跌"),
                "forecast": "预计价格保持稳定",
                "confidence": 0.85,
                "year_over_year": 2.5,
                "month_over_month": 0.8
            }
            
            for prop in properties[:3]:
                property_insights.append({
                    "name": prop.get("name", ""),
                    "price": prop.get("price", 0),
                    "area": prop.get("area", 0),
                    "price_per_sqm": prop.get("price_per_sqm", 0),
                    "highlights": []
                })
        
        return {
            "location": location,
            "market_overview": market_overview,
            "price_analysis": price_analysis,
            "property_insights": property_insights,
            "key_insights": ["该区域房价相对稳定，适合自住需求", "周边配套完善，生活便利", "交通便利，通勤方便"]
        }
    
    def _create_key_findings(self) -> List[Dict[str, Any]]:
        findings = []
        
        if self._collected_data:
            avg_price = self._collected_data.get("avg_price", 0)
            if avg_price:
                findings.append({
                    "title": "区域均价分析",
                    "description": f"该区域平均房价为 {avg_price} 元/㎡",
                    "confidence": 0.85,
                    "source": "市场数据采集"
                })
            
            properties = self._collected_data.get("properties", [])
            if properties:
                findings.append({
                    "title": "在售房源情况",
                    "description": f"该区域目前有 {len(properties)} 套在售房源",
                    "confidence": 0.9,
                    "source": "房源数据"
                })
        
        if self._analyzed_data:
            llm_analysis = self._analyzed_data.get("llm_analysis", {})
            if llm_analysis:
                factors = llm_analysis.get("factors", [])
                for factor in factors[:3]:
                    findings.append({
                        "title": factor,
                        "description": f"分析因素: {factor}",
                        "confidence": 0.8,
                        "source": "AI分析"
                    })
        
        return findings
    
    def _create_detailed_analysis(self) -> Dict[str, Any]:
        market_analysis = {}
        price_analysis = {}
        location_analysis = {}
        
        if self._collected_data:
            market_stats = self._collected_data.get("market_stats", {})
            trend = self._collected_data.get("trend", "stable")
            
            market_analysis = {
                "supply_demand": f"该区域在售房源{market_stats.get('listing_count', 'N/A')}套，近30天成交{market_stats.get('transaction_count_30d', 'N/A')}套",
                "liquidity": f"平均挂牌周期{market_stats.get('avg_days_on_market', 'N/A')}天",
                "market_sentiment": "市场活跃度中等" if trend == "stable" else "市场活跃度较高"
            }
            
            avg_price = self._collected_data.get("avg_price", 0)
            price_analysis = {
                "current_level": f"当前均价{avg_price}元/㎡",
                "historical_trend": "价格走势平稳" if trend == "stable" else "价格有波动",
                "future_outlook": "预计未来价格保持稳定"
            }
        
        if self._parsed_data:
            location_analysis = {
                "transportation": "交通便利，周边有多条公交线路",
                "education": "周边有学校资源",
                "medical": "医疗配套完善",
                "commercial": "商业配套齐全"
            }
        
        return {
            "market_analysis": market_analysis,
            "price_analysis": price_analysis,
            "location_analysis": location_analysis
        }
    
    def _create_investment_advice(self) -> Dict[str, Any]:
        overall_rating = "中等"
        action_recommendation = "建议观望"
        
        if self._analyzed_data:
            recommendation = self._analyzed_data.get("recommendation", "")
            risk_level = self._analyzed_data.get("risk_level", "中")
            confidence = self._analyzed_data.get("confidence", 0)
            
            if risk_level in ["低", "low"]:
                overall_rating = "推荐"
                action_recommendation = "建议关注"
            elif risk_level in ["高", "high"]:
                overall_rating = "谨慎"
                action_recommendation = "建议观望"
            
            return {
                "overall_rating": overall_rating,
                "action_recommendation": action_recommendation,
                "key_factors": ["价格合理", "位置优越", "配套完善"],
                "investment_horizon": {
                    "short_term": "短期价格稳定",
                    "medium_term": "中期有增值潜力",
                    "long_term": "长期投资价值良好"
                },
                "style_specific_advice": {
                    "risk_level": risk_level,
                    "suggestion": recommendation or "建议根据自身需求决策"
                },
                "confidence": confidence
            }
        
        if self._collected_data:
            trend = self._collected_data.get("trend", "stable")
            if trend == "rising":
                return {
                    "overall_rating": "推荐",
                    "action_recommendation": "建议关注入市时机",
                    "key_factors": ["价格上涨趋势"],
                    "confidence": 0.8
                }
            elif trend == "falling":
                return {
                    "overall_rating": "谨慎",
                    "action_recommendation": "建议等待更好的时机",
                    "key_factors": ["价格下跌趋势"],
                    "confidence": 0.75
                }
        
        return {
            "overall_rating": overall_rating,
            "action_recommendation": action_recommendation,
            "key_factors": ["市场数据有限"],
            "confidence": 0.6
        }
    
    def _create_risk_warning(self) -> List[str]:
        warnings = []
        
        if self._parsed_data:
            missing_fields = self._parsed_data.get("missing_fields", [])
            if missing_fields:
                warnings.append(f"数据完整性警告: 缺少以下字段: {', '.join(missing_fields)}")
            
            confidence = self._parsed_data.get("confidence", 1)
            if confidence < 0.8:
                warnings.append(f"解析置信度较低 ({confidence * 100:.0f}%)，建议核实输入信息")
        
        if self._analyzed_data:
            risk_level = self._analyzed_data.get("risk_level", "中")
            if risk_level in ["高", "high"]:
                warnings.append("投资风险较高，建议谨慎决策")
        
        warnings.append("本报告由AI生成，仅供参考，不构成投资建议")
        warnings.append("房产投资存在风险，请结合实际情况做出决策")
        warnings.append("市场行情波动可能影响投资回报")
        
        return warnings
    
    async def _handle_workflow_failure(self, failed_task: SubTask) -> None:
        self._workflow_state = "failed"
        
        # 积分返还逻辑
        user_id = self._user_id
        if user_id:
            try:
                from ..services.integral import IntegralService
                refund_result = await IntegralService.add_integral(
                    user_id=user_id,
                    amount=1,  # 返还1积分
                    reason=f"任务失败返还: {failed_task.target_agent}.{failed_task.action} 失败",
                    action_type="task_failure_refund",
                    resource_id=self.task_id,
                    resource_type="analysis_task"
                )
                logger.info(f"Refunded 1 integral to user {user_id} due to task failure")
            except Exception as e:
                logger.error(f"Failed to refund integral: {e}")
        
        await self.record_step(
            "工作流失败",
            f"任务在 {failed_task.target_agent}.{failed_task.action} 阶段失败",
            status="failed",
            output_data={"error": failed_task.result}
        )
        
        if self._original_request:
            await self.send(
                recipient=self._original_request.sender,
                message_type=MessageType.ERROR,
                content={
                    "error": f"Workflow failed at {failed_task.target_agent}.{failed_task.action}",
                    "details": failed_task.result,
                    "refund": "已返还1积分"  # 添加返还提示
                },
                in_reply_to=self._original_request.id
            )
        
        logger.error(f"Workflow failed for task {self.task_id}")
    
    async def _report_status(self, message: AgentMessage) -> None:
        status = {
            "workflow_state": self._workflow_state,
            "sub_tasks": [
                {"agent": st.target_agent, "action": st.action, "status": st.status}
                for st in self._sub_tasks
            ],
            "pending_requests": len(self._pending_requests)
        }
        
        await self.respond(message, status)
    
    def get_workflow_state(self) -> str:
        return self._workflow_state
    
    def get_workflow_result(self) -> Dict[str, Any]:
        return self._workflow_result
    
    async def run_workflow(self, query: str, user_id: str = "anonymous") -> None:
        """
        直接运行工作流（不依赖消息循环）
        
        Args:
            query: 用户查询
            user_id: 用户ID
        """
        self._workflow_state = "parsing"
        self._user_id = user_id
        
        from .message import AgentMessage
        self._original_request = AgentMessage(
            task_id=self.task_id,
            sender="scheduler",
            recipient=self.name,
            type=MessageType.REQUEST,
            content={"query": query}
        )
        
        logger.info(f"Starting workflow for query: {query}, user: {user_id}")
        
        try:
            memory_context = await memory_service.get_context(user_id, query, max_memories=5)
            if memory_context:
                logger.info(f"Retrieved memory context for user {user_id}")
                self._memory_context = memory_context
            else:
                self._memory_context = None
        except Exception as e:
            logger.warning(f"Failed to retrieve memories: {e}")
            self._memory_context = None
        
        await self.record_step("开始处理", f"收到用户请求: {query}", status="completed")
        
        await self.record_step("需求解析", "正在从查询中提取关键信息...", status="running")
        
        try:
            from .requirement import RequirementAgent
            
            requirement_agent = RequirementAgent(
                name="requirement",
                task_id=self.task_id,
                bus=self.bus
            )
            await requirement_agent.initialize()
            
            parsed = await requirement_agent._parse_requirement(query)
            self._parsed_data = parsed
            
            await self.record_step("需求解析完成", f"提取到: {parsed}", status="completed")
            
            await self.record_step("任务分配", "正在并行分配任务给各代理...", status="running")
            
            from .collector import CollectorAgent
            from .analyst import AnalystAgent
            
            collector_agent = CollectorAgent(
                name="collector",
                task_id=self.task_id,
                bus=self.bus
            )
            await collector_agent.initialize()
            
            analyst_agent = AnalystAgent(
                name="analyst",
                task_id=self.task_id,
                bus=self.bus
            )
            await analyst_agent.initialize()
            
            await self.record_step("任务分配完成", "已并行分配任务给数据采集师和市场分析师", status="completed")
            
            await self.record_step("等待结果", "等待各代理完成任务...", status="running")
            
            collected, analyzed = await asyncio.gather(
                collector_agent._collect_data(parsed),
                analyst_agent._analyze_data(parsed, {})
            )
            
            self._collected_data = collected.get("data", {})
            self._analyzed_data = analyzed.get("analysis", {})
            
            await self.record_step("结果汇总", "所有代理已完成，开始生成报告...", status="completed")
            
            await self._generate_report()
            
        except Exception as e:
            logger.error(f"Workflow failed: {e}")
            self._workflow_state = "failed"
            self._workflow_result = {"error": str(e)}
            await self.record_step("工作流失败", f"错误: {str(e)}", status="failed")
        
        logger.info(f"Workflow completed for task {self.task_id}")
