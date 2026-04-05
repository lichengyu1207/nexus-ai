"""
对话智能体系统
集成仪表盘的现有业务逻辑，实现定制化对话流程
优化异步处理逻辑，解决超时和竞争条件问题
"""
import asyncio
import re
from typing import Dict, Any, List, Optional
from datetime import datetime
from .base import BaseAgent
from .message import AgentMessage, MessageType
from .requirement import RequirementAgent
from .collector import CollectorAgent
from .analyst import AnalystAgent
import logging

logger = logging.getLogger(__name__)


class InputProcessorAgent(BaseAgent):
    """输入处理智能体 - 处理二进制转换"""
    
    def __init__(self, agent_name: str, task_id: str, bus, **kwargs):
        super().__init__(agent_name, task_id, bus, **kwargs)
        self.processed_input = None
        self.binary_input = None
    
    @staticmethod
    def text_to_binary(text: str) -> str:
        """将文本转换为二进制字符串（空格分隔）"""
        try:
            return ' '.join(format(ord(char), '08b') for char in text)
        except Exception as e:
            logger.error(f"Text to binary conversion failed: {e}")
            return ""
    
    @staticmethod
    def binary_to_text(binary: str) -> str:
        """将二进制字符串转换为文本"""
        try:
            binary = binary.replace(' ', '')
            if not binary or not all(c in '01' for c in binary):
                return binary
            return ''.join(chr(int(binary[i:i+8], 2)) for i in range(0, len(binary), 8))
        except Exception as e:
            logger.error(f"Binary to text conversion failed: {e}")
            return binary
    
    async def handle_message(self, message: AgentMessage) -> None:
        if message.type == MessageType.REQUEST and message.content.get("action") == "process_input":
            input_text = message.content.get("input", "")
            is_binary = message.content.get("is_binary", False)
            
            try:
                await self.record_step(
                    step_name="输入处理",
                    description=f"处理{'二进制' if is_binary else '文本'}输入",
                    status="running",
                    input_data={"input_length": len(input_text), "is_binary": is_binary}
                )
                
                if is_binary:
                    decoded = self.binary_to_text(input_text)
                    binary = input_text
                else:
                    binary = self.text_to_binary(input_text)
                    decoded = input_text
                
                self.processed_input = decoded
                self.binary_input = binary
                
                await self.record_step(
                    step_name="输入处理",
                    description="输入处理完成",
                    status="completed",
                    output_data={"decoded_length": len(decoded), "binary_length": len(binary)}
                )
                
                await self.respond(message, {
                    "status": "success",
                    "decoded_input": decoded,
                    "binary_input": binary
                })
            except Exception as e:
                logger.error(f"InputProcessorAgent error: {e}")
                await self.respond(message, {
                    "status": "error",
                    "message": str(e)
                })


class DialogueSupervisorAgent(BaseAgent):
    """
    对话主管智能体 - 协调整个对话流程
    集成仪表盘的现有业务逻辑（RequirementAgent, CollectorAgent, AnalystAgent）
    
    优化：
    1. 使用同步处理替代异步任务
    2. 添加结果事件通知机制
    3. 优化超时处理
    """
    
    REQUIRED_FIELDS = {
        "high": [
            {"field": "city", "label": "城市", "question": "您想在哪个城市购房?"},
            {"field": "price_max", "label": "预算", "question": "您的购房预算大概是多少?"}
        ],
        "medium": [
            {"field": "room_count", "label": "户型", "question": "您需要几室几厅的房子?"},
            {"field": "district", "label": "区域", "question": "您有偏好的区域吗?"}
        ],
        "low": [
            {"field": "area_min", "label": "面积", "question": "您对面积有什么要求?"},
            {"field": "orientation", "label": "朝向", "question": "您对朝向有要求吗?"}
        ]
    }
    
    AGENT_TYPES = {
        "property_analyst": {
            "name": "房产分析师",
            "keywords": ["房价", "价格", "投资", "升值", "市场", "趋势", "分析"],
            "capabilities": ["房价分析", "市场趋势", "投资建议", "区域对比"]
        },
        "area_expert": {
            "name": "区域专家",
            "keywords": ["区域", "位置", "周边", "配套", "交通", "地铁", "学校", "医院"],
            "capabilities": ["区域介绍", "周边配套", "交通分析", "学区查询"]
        },
        "loan_advisor": {
            "name": "贷款顾问",
            "keywords": ["贷款", "利率", "首付", "月供", "公积金", "商业贷"],
            "capabilities": ["贷款计算", "利率分析", "还款方案", "公积金咨询"]
        },
        "policy_expert": {
            "name": "政策专家",
            "keywords": ["政策", "限购", "限贷", "税费", "契税", "资格"],
            "capabilities": ["购房政策", "限购限贷", "税费计算", "资格审核"]
        },
        "community_guide": {
            "name": "小区向导",
            "keywords": ["小区", "楼盘", "户型", "房源", "物业", "绿化"],
            "capabilities": ["小区介绍", "房源推荐", "户型分析", "物业评价"]
        }
    }
    
    def __init__(self, agent_name: str, task_id: str, bus, **kwargs):
        super().__init__(agent_name, task_id, bus, **kwargs)
        self.workflow_state = "idle"
        self.workflow_result = {}
        self.collected_keywords = {}
        self._parsed_data = None
        self._collected_data = None
        self._analysis_data = None
        self._result_event = asyncio.Event()
        self._processing_lock = asyncio.Lock()
    
    async def handle_message(self, message: AgentMessage) -> None:
        """处理消息 - 直接同步处理，避免异步任务问题"""
        if message.type == MessageType.REQUEST and message.content.get("action") == "start":
            async with self._processing_lock:
                await self._run_workflow_sync(message)
    
    async def _run_workflow_sync(self, message: AgentMessage) -> None:
        """同步运行工作流，确保消息处理完整性"""
        try:
            query = message.content.get("query", "")
            is_binary = message.content.get("is_binary", False)
            collected_keywords = message.content.get("collected_keywords", {})
            
            self.collected_keywords = collected_keywords.copy()
            self._result_event.clear()
            
            await self.record_step(
                step_name="对话流程启动",
                description=f"处理用户输入: {query[:50]}...",
                status="running"
            )
            
            self.workflow_state = "processing"
            
            decoded_input = query
            binary_input = ""
            
            try:
                input_result = await asyncio.wait_for(
                    self.request("input_processor", {
                        "action": "process_input",
                        "input": query,
                        "is_binary": is_binary
                    }),
                    timeout=5.0
                )
                
                if input_result and input_result.get("status") == "success":
                    decoded_input = input_result.get("decoded_input", query)
                    binary_input = input_result.get("binary_input", "")
            except asyncio.TimeoutError:
                logger.warning("Input processor timeout, using original input")
            except Exception as e:
                logger.warning(f"Input processor error: {e}")
            
            await self.record_step(
                step_name="需求解析",
                description="调用仪表盘需求解析智能体...",
                status="running",
                input_data={"query": decoded_input}
            )
            
            try:
                requirement_result = await asyncio.wait_for(
                    self.request("requirement", {
                        "action": "parse_with_inference",
                        "query": decoded_input
                    }),
                    timeout=10.0
                )
                
                if not requirement_result:
                    self.workflow_state = "failed"
                    self.workflow_result = {"status": "error", "message": "需求解析失败"}
                    await self.respond(message, self.workflow_result)
                    return
                
                self._parsed_data = requirement_result.get("parsed", {})
                
                await self.record_step(
                    step_name="需求解析完成",
                    description=f"提取到: 城市={self._parsed_data.get('city')}, 区域={self._parsed_data.get('district')}",
                    status="completed",
                    output_data={"parsed": self._parsed_data}
                )
                
            except asyncio.TimeoutError:
                logger.warning("Requirement parser timeout")
                self._parsed_data = {"city": None, "district": None}
                await self.record_step(
                    step_name="需求解析",
                    description="需求解析超时，使用默认值",
                    status="completed"
                )
            except Exception as e:
                logger.error(f"Requirement parser error: {e}")
                self._parsed_data = {"city": None, "district": None}
            
            self._update_collected_keywords_from_parsed(self._parsed_data)
            
            agents = self._route_agents(decoded_input, self._parsed_data)
            
            await self.record_step(
                step_name="智能体路由",
                description=f"分配了 {len(agents)} 个智能体",
                status="completed",
                output_data={"agents": [a["agent_name"] for a in agents]}
            )
            
            info_collected, missing_info = self._check_info_collected()
            
            if info_collected and self._parsed_data.get("city"):
                await self.record_step(
                    step_name="数据采集",
                    description="调用仪表盘数据采集智能体...",
                    status="running",
                    input_data={"parsed": self._parsed_data}
                )
                
                try:
                    collector_result = await asyncio.wait_for(
                        self.request("collector", {
                            "action": "collect",
                            "parsed": self._parsed_data
                        }),
                        timeout=10.0
                    )
                    
                    if collector_result:
                        self._collected_data = collector_result.get("data", {})
                        
                        await self.record_step(
                            step_name="数据采集完成",
                            description=f"采集到 {len(self._collected_data.get('properties', []))} 套房源",
                            status="completed",
                            output_data={"data": self._collected_data}
                        )
                except asyncio.TimeoutError:
                    logger.warning("Collector timeout")
                    await self.record_step(
                        step_name="数据采集",
                        description="数据采集超时",
                        status="completed"
                    )
                except Exception as e:
                    logger.error(f"Collector error: {e}")
            
            final_response = self._generate_response(
                decoded_input=decoded_input,
                agents=agents,
                info_collected=info_collected,
                missing_info=missing_info
            )
            
            self.workflow_state = "completed"
            self.workflow_result = {
                "status": "success",
                "decoded_input": decoded_input,
                "binary_input": binary_input,
                "keywords": self._extract_keywords_from_parsed(self._parsed_data),
                "agents": agents,
                "response": final_response,
                "binary_response": InputProcessorAgent.text_to_binary(final_response),
                "needs_follow_up": not info_collected,
                "follow_up_question": missing_info[0]["question"] if missing_info else None,
                "info_collected": info_collected,
                "collected_count": len(self.collected_keywords),
                "missing_info": missing_info,
                "collected_keywords": self.collected_keywords,
                "parsed_data": self._parsed_data,
                "collected_data": self._collected_data
            }
            
            await self.record_step(
                step_name="对话流程完成",
                description="所有智能体处理完成",
                status="completed"
            )
            
            self._result_event.set()
            
            await self.respond(message, self.workflow_result)
            
        except Exception as e:
            logger.error(f"Workflow error: {e}")
            self.workflow_state = "failed"
            self.workflow_result = {"status": "error", "message": str(e)}
            self._result_event.set()
            await self.respond(message, self.workflow_result)
    
    def _update_collected_keywords_from_parsed(self, parsed: Dict[str, Any]):
        """从解析结果更新已收集的关键词"""
        field_mapping = {
            "city": "城市",
            "district": "区域",
            "community": "小区",
            "room_count": "户型",
            "area_min": "面积",
            "area_max": "面积",
            "price_min": "预算",
            "price_max": "预算",
            "orientation": "朝向",
            "decoration": "装修"
        }
        
        for field, label in field_mapping.items():
            value = parsed.get(field)
            if value is not None:
                if field == "room_count":
                    hall = parsed.get("hall_count", 1)
                    self.collected_keywords["户型"] = f"{value}室{hall}厅"
                elif field in ["area_min", "area_max"]:
                    area_min = parsed.get("area_min")
                    area_max = parsed.get("area_max")
                    if area_min and area_max:
                        self.collected_keywords["面积"] = f"{area_min}-{area_max}㎡"
                    elif area_min:
                        self.collected_keywords["面积"] = f"{area_min}㎡以上"
                elif field in ["price_min", "price_max"]:
                    price_max = parsed.get("price_max")
                    if price_max:
                        self.collected_keywords["预算"] = f"{price_max}万以内"
                else:
                    self.collected_keywords[label] = str(value)
    
    def _extract_keywords_from_parsed(self, parsed: Dict[str, Any]) -> Dict[str, str]:
        """从解析结果提取关键词"""
        keywords = {}
        if parsed.get("city"):
            keywords["city"] = parsed["city"]
        if parsed.get("district"):
            keywords["district"] = parsed["district"]
        if parsed.get("community"):
            keywords["community"] = parsed["community"]
        if parsed.get("room_count"):
            keywords["room_count"] = parsed["room_count"]
        if parsed.get("price_max"):
            keywords["price_max"] = parsed["price_max"]
        if parsed.get("area_min"):
            keywords["area_min"] = parsed["area_min"]
        return keywords
    
    def _route_agents(self, text: str, parsed: Dict[str, Any]) -> List[Dict[str, Any]]:
        """路由分配智能体"""
        scores = {}
        
        for agent_id, agent_info in self.AGENT_TYPES.items():
            score = 0
            matched_keywords = []
            
            for kw in agent_info["keywords"]:
                if kw in text:
                    score += 1
                    matched_keywords.append(kw)
            
            if parsed.get("price_max") or parsed.get("price_min"):
                if agent_id in ["property_analyst", "loan_advisor"]:
                    score += 1
            
            if parsed.get("district") or parsed.get("community"):
                if agent_id in ["area_expert", "community_guide"]:
                    score += 1
            
            if score > 0:
                scores[agent_id] = {
                    "agent_id": agent_id,
                    "agent_name": agent_info["name"],
                    "confidence": min(score / len(agent_info["keywords"]), 1.0),
                    "matched_keywords": matched_keywords,
                    "capabilities": agent_info["capabilities"]
                }
        
        sorted_agents = sorted(scores.values(), key=lambda x: x["confidence"], reverse=True)
        return sorted_agents[:3]
    
    def _check_info_collected(self) -> tuple:
        """检查信息是否收集完整"""
        missing = []
        
        for importance, fields in self.REQUIRED_FIELDS.items():
            for field_info in fields:
                field = field_info["field"]
                has_value = False
                
                if field == "city":
                    has_value = self._parsed_data.get("city") is not None
                elif field == "price_max":
                    has_value = self._parsed_data.get("price_max") is not None
                elif field == "room_count":
                    has_value = self._parsed_data.get("room_count") is not None
                elif field == "district":
                    has_value = self._parsed_data.get("district") is not None
                elif field == "area_min":
                    has_value = self._parsed_data.get("area_min") is not None
                elif field == "orientation":
                    has_value = self._parsed_data.get("orientation") is not None
                
                if not has_value:
                    missing.append({**field_info, "importance": importance})
        
        high_priority_missing = [m for m in missing if m["importance"] == "high"]
        info_collected = len(high_priority_missing) == 0 and len(self.collected_keywords) >= 2
        
        return info_collected, missing
    
    def _generate_response(
        self,
        decoded_input: str,
        agents: List[Dict[str, Any]],
        info_collected: bool,
        missing_info: List[Dict[str, Any]]
    ) -> str:
        """生成最终响应"""
        response_parts = []
        
        if self.collected_keywords:
            collected_summary = [f"**{k}**: {v}" for k, v in self.collected_keywords.items()]
            response_parts.append(f"📋 **已收集信息 ({len(self.collected_keywords)}项)：**\n" + "\n".join([f"  - {s}" for s in collected_summary]))
        
        if agents:
            primary_agent = agents[0]
            response_parts.append(f"\n🔍 已为您分配 **{primary_agent['agent_name']}** 来处理您的咨询")
        
        if self._parsed_data:
            inferences = self._parsed_data.get("inferences", [])
            if inferences:
                response_parts.append("\n💡 **智能推断：**")
                for inf in inferences[:2]:
                    response_parts.append(f"  - {inf.get('reasoning', '')}")
        
        if info_collected:
            response_parts.append("\n✅ **信息收集完成！** 正在为您启动智能分析...")
            
            if self._collected_data:
                avg_price = self._collected_data.get("avg_price", 0)
                properties = self._collected_data.get("properties", [])
                response_parts.append(f"\n📊 **市场数据：**")
                response_parts.append(f"  - 区域均价: {avg_price:,}元/㎡")
                response_parts.append(f"  - 在售房源: {len(properties)}套")
                
                if properties:
                    top_prop = properties[0]
                    response_parts.append(f"\n🏠 **推荐房源：**")
                    response_parts.append(f"  - {top_prop.get('name', '未知小区')}")
                    response_parts.append(f"  - 面积: {top_prop.get('area', 0)}㎡ | 总价: {top_prop.get('price', 0):,}万")
            
            if agents:
                response_parts.append(f"\n🎯 **{agents[0]['agent_name']}** 正在分析您的需求...")
                response_parts.append(f"\n💡 基于您的需求，我可以为您提供：")
                for cap in agents[0].get("capabilities", [])[:3]:
                    response_parts.append(f"  - {cap}")
        else:
            high_priority_missing = [m for m in missing_info if m["importance"] == "high"]
            if high_priority_missing:
                response_parts.append(f"\n❓ {high_priority_missing[0]['question']}")
        
        return "\n".join(response_parts)
    
    def get_workflow_state(self) -> str:
        return self.workflow_state
    
    def get_workflow_result(self) -> dict:
        return self.workflow_result
    
    async def wait_for_result(self, timeout: float = 30.0) -> bool:
        """等待工作流完成"""
        try:
            await asyncio.wait_for(self._result_event.wait(), timeout=timeout)
            return True
        except asyncio.TimeoutError:
            return False
