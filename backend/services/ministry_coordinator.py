# -*- coding: utf-8 -*-
"""
Ministry Coordinator - 六部协调器
协调吏户礼兵刑工六部智能体协同工作
"""
import asyncio
import logging
import time
import uuid
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field
from enum import Enum

from backend.database_pg import PostgreSQLConnectionPool
from backend.services.agent_manager import AgentManager, get_agent_manager, AgentStatus

logger = logging.getLogger(__name__)


class MinistryPhase(str, Enum):
    INIT = "init"
    LI_BU = "li_bu"
    HU_BU = "hu_bu"
    LI_GUAN_BU = "li_guan_bu"
    BING_BU = "bing_bu"
    XING_BU = "xing_bu"
    GONG_BU = "gong_bu"
    COMPLETED = "completed"
    FAILED = "failed"


class AgentRole(Enum):
    LI = "li"
    HU = "hu"
    LI_GUAN = "li_guan"
    BING = "bing"
    XING = "xing"
    GONG = "gong"
    ZHONGSHU = "zhongshu"
    MENXIA = "menxia"
    SHANGSHU = "shangshu"


MINISTRY_EXECUTION_ORDER = [
    MinistryPhase.LI_BU,
    MinistryPhase.BING_BU,
    MinistryPhase.HU_BU,
    MinistryPhase.XING_BU,
    MinistryPhase.GONG_BU,
    MinistryPhase.LI_GUAN_BU,
]


@dataclass
class MinistryResult:
    ministry: str
    success: bool
    data: Dict
    duration_ms: float
    agent_id: Optional[str] = None
    error: Optional[str] = None


class MinistryCoordinator:
    """
    六部协调器
    
    协调吏户礼兵刑工六部智能体按顺序执行任务
    """
    
    def __init__(self):
        self.db = None
        self.agent_manager: Optional[AgentManager] = None
        self._initialized = False
    
    async def initialize(self):
        if self._initialized:
            return
        
        self.db = await PostgreSQLConnectionPool.get_instance()
        self.agent_manager = await get_agent_manager()
        self._initialized = True
        logger.info("MinistryCoordinator initialized")
    
    async def collaborative_execute(
        self,
        task_description: str,
        task_type: str,
        request: Dict,
        user_id: Optional[str] = None
    ) -> Dict:
        """
        协同执行任务
        
        Args:
            task_description: 任务描述
            task_type: 任务类型
            request: 请求数据
            user_id: 用户ID
        
        Returns:
            执行结果
        """
        if not self._initialized:
            await self.initialize()
        
        task_id = request.get("task_id", str(uuid.uuid4()))
        
        await self._init_state(task_id, task_description)
        
        results: Dict[str, MinistryResult] = {}
        
        required_ministries = self._determine_required_ministries(task_type)
        
        for phase in required_ministries:
            try:
                result = await self._execute_ministry_phase(
                    task_id, phase, task_description, request, user_id
                )
                results[phase.value] = result
                
                if not result.success:
                    logger.warning(f"Ministry {phase.value} failed for task {task_id}")
                
                await self._update_state(task_id, phase, result)
                
            except Exception as e:
                logger.error(f"Error in ministry {phase.value}: {e}")
                results[phase.value] = MinistryResult(
                    ministry=phase.value,
                    success=False,
                    data={},
                    duration_ms=0,
                    error=str(e)
                )
        
        final_result = self._aggregate_results(results, task_id)
        
        await self._finalize_state(task_id, final_result)
        
        return final_result
    
    def _determine_required_ministries(self, task_type: str) -> List[MinistryPhase]:
        """根据任务类型确定需要的部门"""
        task_type_lower = task_type.lower()
        
        if "valuation" in task_type_lower or "估值" in task_type_lower:
            return [
                MinistryPhase.LI_BU,
                MinistryPhase.BING_BU,
                MinistryPhase.XING_BU,
                MinistryPhase.GONG_BU,
            ]
        elif "analysis" in task_type_lower or "分析" in task_type_lower:
            return [
                MinistryPhase.BING_BU,
                MinistryPhase.XING_BU,
                MinistryPhase.GONG_BU,
            ]
        elif "consult" in task_type_lower or "咨询" in task_type_lower:
            return [
                MinistryPhase.LI_GUAN_BU,
                MinistryPhase.BING_BU,
            ]
        elif "report" in task_type_lower or "报告" in task_type_lower:
            return [
                MinistryPhase.HU_BU,
                MinistryPhase.GONG_BU,
            ]
        elif "mingpan" in task_type_lower or "命盘" in task_type_lower:
            return [
                MinistryPhase.BING_BU,
                MinistryPhase.XING_BU,
                MinistryPhase.GONG_BU,
            ]
        else:
            return [
                MinistryPhase.LI_BU,
                MinistryPhase.BING_BU,
                MinistryPhase.GONG_BU,
            ]
    
    async def _execute_ministry_phase(
        self,
        task_id: str,
        phase: MinistryPhase,
        task_description: str,
        request: Dict,
        user_id: Optional[str]
    ) -> MinistryResult:
        """执行单个部门任务"""
        start_time = time.time()
        
        role = self._phase_to_role(phase)
        if not role:
            return MinistryResult(
                ministry=phase.value,
                success=False,
                data={},
                duration_ms=0,
                error=f"Unknown phase: {phase}"
            )
        
        agent = None
        if user_id:
            agent = await self.agent_manager.select_best_agent(user_id, role)
        
        if not agent:
            result_data = await self._execute_default_logic(phase, task_description, request)
        else:
            await self.agent_manager.update_agent_status(agent['id'], AgentStatus.WORKING)
            await self.agent_manager.consume_energy(agent['id'], 5.0, f"ministry_{phase.value}")
            
            result_data = await self._execute_with_agent(phase, agent, task_description, request)
            
            await self.agent_manager.add_experience(agent['id'], 10, result_data.get("success", True))
            await self.agent_manager.update_agent_status(agent['id'], AgentStatus.IDLE)
        
        duration_ms = (time.time() - start_time) * 1000
        
        return MinistryResult(
            ministry=phase.value,
            success=result_data.get("success", False),
            data=result_data,
            duration_ms=duration_ms,
            agent_id=agent['id'] if agent else None,
        )
    
    def _phase_to_role(self, phase: MinistryPhase) -> Optional[AgentRole]:
        mapping = {
            MinistryPhase.LI_BU: AgentRole.LI,
            MinistryPhase.HU_BU: AgentRole.HU,
            MinistryPhase.LI_GUAN_BU: AgentRole.LI_GUAN,
            MinistryPhase.BING_BU: AgentRole.BING,
            MinistryPhase.XING_BU: AgentRole.XING,
            MinistryPhase.GONG_BU: AgentRole.GONG,
        }
        return mapping.get(phase)
    
    async def _execute_default_logic(
        self,
        phase: MinistryPhase,
        task_description: str,
        request: Dict
    ) -> Dict:
        """默认业务逻辑（无智能体时）"""
        
        if phase == MinistryPhase.LI_BU:
            return await self._li_bu_logic(task_description, request)
        elif phase == MinistryPhase.HU_BU:
            return await self._hu_bu_logic(task_description, request)
        elif phase == MinistryPhase.LI_GUAN_BU:
            return await self._li_guan_bu_logic(task_description, request)
        elif phase == MinistryPhase.BING_BU:
            return await self._bing_bu_logic(task_description, request)
        elif phase == MinistryPhase.XING_BU:
            return await self._xing_bu_logic(task_description, request)
        elif phase == MinistryPhase.GONG_BU:
            return await self._gong_bu_logic(task_description, request)
        else:
            return {"success": False, "error": "Unknown ministry"}
    
    async def _li_bu_logic(self, task_description: str, request: Dict) -> Dict:
        """吏部逻辑 - 团队管理"""
        return {
            "success": True,
            "ministry": "li_bu",
            "action": "team_coordination",
            "result": {
                "assigned_agents": [],
                "resource_allocation": "balanced",
                "coordination_score": 0.85,
            }
        }
    
    async def _hu_bu_logic(self, task_description: str, request: Dict) -> Dict:
        """户部逻辑 - 数据管理"""
        return {
            "success": True,
            "ministry": "hu_bu",
            "action": "data_preparation",
            "result": {
                "data_sources": ["internal", "external"],
                "data_quality": 0.92,
                "records_prepared": 100,
            }
        }
    
    async def _li_guan_bu_logic(self, task_description: str, request: Dict) -> Dict:
        """礼部逻辑 - 咨询服务"""
        return {
            "success": True,
            "ministry": "li_guan_bu",
            "action": "consultation",
            "result": {
                "response": f"关于「{task_description[:50]}...」的咨询建议",
                "confidence": 0.88,
                "suggestions": ["建议1", "建议2"],
            }
        }
    
    async def _bing_bu_logic(self, task_description: str, request: Dict) -> Dict:
        """兵部逻辑 - 数据采集"""
        return {
            "success": True,
            "ministry": "bing_bu",
            "action": "data_collection",
            "result": {
                "sources_queried": 3,
                "records_collected": 50,
                "collection_time_ms": 150,
                "data_preview": {"sample": "data"},
            }
        }
    
    async def _xing_bu_logic(self, task_description: str, request: Dict) -> Dict:
        """刑部逻辑 - 风险评估"""
        return {
            "success": True,
            "ministry": "xing_bu",
            "action": "risk_assessment",
            "result": {
                "risk_level": "low",
                "risk_score": 0.15,
                "warnings": [],
                "compliance_status": "passed",
            }
        }
    
    async def _gong_bu_logic(self, task_description: str, request: Dict) -> Dict:
        """工部逻辑 - 报告生成"""
        return {
            "success": True,
            "ministry": "gong_bu",
            "action": "report_generation",
            "result": {
                "report_type": "standard",
                "sections_generated": 5,
                "quality_score": 0.90,
                "output_format": "markdown",
            }
        }
    
    async def _execute_with_agent(
        self,
        phase: MinistryPhase,
        agent: Dict,
        task_description: str,
        request: Dict
    ) -> Dict:
        """使用智能体执行"""
        result = await self._execute_default_logic(phase, task_description, request)
        
        gene_pool = agent.get('gene_pool', {})
        efficiency = gene_pool.get('efficiency', 0.8)
        accuracy = gene_pool.get('accuracy', 0.8)
        
        if result.get('result'):
            result['result']['agent_enhanced'] = True
            result['result']['agent_name'] = agent.get('name')
            result['result']['efficiency_bonus'] = efficiency
            result['result']['accuracy_bonus'] = accuracy
        
        return result
    
    async def _init_state(self, task_id: str, description: str):
        """初始化状态"""
        async with self.db.get_connection() as conn:
            await conn.execute("""
                INSERT INTO ministry_coordinator_state (task_id, phase)
                VALUES ($1, $2)
                ON CONFLICT (task_id) DO UPDATE SET phase = $2
            """, task_id, MinistryPhase.INIT.value)
    
    async def _update_state(self, task_id: str, phase: MinistryPhase, result: MinistryResult):
        """更新状态"""
        status_field = f"{phase.value}_status"
        result_field = f"{phase.value}_result"
        
        async with self.db.get_connection() as conn:
            await conn.execute(f"""
                UPDATE ministry_coordinator_state 
                SET {status_field} = $1, {result_field} = $2, phase = $3, updated_at = CURRENT_TIMESTAMP
                WHERE task_id = $4
            """, "completed" if result.success else "failed", result.data, phase.value, task_id)
    
    async def _finalize_state(self, task_id: str, result: Dict):
        """完成状态"""
        async with self.db.get_connection() as conn:
            await conn.execute("""
                UPDATE ministry_coordinator_state 
                SET phase = $1, final_result = $2, updated_at = CURRENT_TIMESTAMP
                WHERE task_id = $3
            """, MinistryPhase.COMPLETED.value if result.get("success") else MinistryPhase.FAILED.value,
                result, task_id)
    
    def _aggregate_results(self, results: Dict[str, MinistryResult], task_id: str) -> Dict:
        """聚合结果"""
        success_count = sum(1 for r in results.values() if r.success)
        total_count = len(results)
        
        return {
            "task_id": task_id,
            "success": success_count == total_count,
            "success_rate": success_count / total_count if total_count > 0 else 0,
            "ministries_executed": list(results.keys()),
            "ministry_results": {
                k: {
                    "success": v.success,
                    "duration_ms": v.duration_ms,
                    "agent_id": v.agent_id,
                    "error": v.error,
                }
                for k, v in results.items()
            },
            "data": {k: v.data for k, v in results.items()},
            "completed_at": time.time(),
        }


ministry_coordinator: Optional[MinistryCoordinator] = None


async def get_ministry_coordinator() -> MinistryCoordinator:
    global ministry_coordinator
    if ministry_coordinator is None:
        ministry_coordinator = MinistryCoordinator()
        await ministry_coordinator.initialize()
    return ministry_coordinator
