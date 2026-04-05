"""
六部业务智能体实现
Six Ministry Business Agents

吏户礼兵刑工六部智能体的具体实现
集成Attention Residuals实现动态经验聚合
"""

import os
import json
import time
import logging
import threading
import uuid
import asyncio
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple, Set, Callable
from dataclasses import dataclass, field
from enum import Enum
from collections import deque, defaultdict
import random

import numpy as np

from .business_agent import (
    BusinessAgent,
    BusinessAgentStatus,
    BusinessAgentRole,
    BusinessGene,
)

try:
    import torch
    from models.light_attn_res import AgentSwarmAttnRes, chunked_attn_res
    ATTN_RES_AVAILABLE = True
except ImportError:
    ATTN_RES_AVAILABLE = False
    torch = None

logger = logging.getLogger(__name__)


class LiBuAgent(BusinessAgent):
    """
    吏部智能体
    
    职责：管理智能体团队，协调资源分配
    """
    
    def __init__(self, **kwargs):
        kwargs['role'] = BusinessAgentRole.LI_BU
        kwargs['species'] = 'li_bu'
        super().__init__(**kwargs)
        
        self.managed_agents: Dict[str, Dict] = {}
        self.resource_allocations: Dict[str, float] = {}
    
    def _get_role_specific_genes(self) -> List[BusinessGene]:
        return [
            BusinessGene(
                gene_id="gene_coordination",
                name="coordination_ability",
                value=0.8,
                mutation_rate=0.1,
                mutation_range=(-0.2, 0.2),
                business_weight=2.0
            ),
            BusinessGene(
                gene_id="gene_resource_allocation",
                name="resource_allocation_skill",
                value=0.7,
                mutation_rate=0.1,
                mutation_range=(-0.2, 0.2),
                business_weight=1.5
            ),
        ]
    
    def _get_capabilities(self) -> List[str]:
        return [
            "team_management",
            "resource_allocation",
            "agent_training",
            "performance_review",
            "coordination",
        ]
    
    def _get_preferred_tasks(self) -> List[str]:
        return [
            "team_formation",
            "resource_distribution",
            "agent_evaluation",
            "training_coordination",
        ]
    
    async def execute_business(self, request: Dict) -> Dict:
        action = request.get("action", "")
        
        if action == "allocate_resources":
            return await self._allocate_resources(request)
        elif action == "evaluate_agent":
            return await self._evaluate_agent(request)
        elif action == "coordinate_team":
            return await self._coordinate_team(request)
        else:
            return {"success": False, "error": "Unknown action"}
    
    async def _allocate_resources(self, request: Dict) -> Dict:
        agents = request.get("agents", [])
        total_resources = request.get("total_resources", 100)
        
        allocations = {}
        remaining = total_resources
        
        for agent_info in agents:
            agent_id = agent_info.get("agent_id")
            priority = agent_info.get("priority", 1)
            
            allocation = total_resources * (priority / sum(a.get("priority", 1) for a in agents))
            allocations[agent_id] = allocation
            remaining -= allocation
        
        self.resource_allocations.update(allocations)
        
        return {
            "success": True,
            "allocations": allocations,
            "remaining": remaining,
        }
    
    async def _evaluate_agent(self, request: Dict) -> Dict:
        agent_id = request.get("agent_id")
        
        evaluation = {
            "agent_id": agent_id,
            "score": random.uniform(0.5, 1.0),
            "recommendations": [
                "Continue current performance",
                "Consider additional training",
            ],
            "evaluated_at": time.time(),
        }
        
        return {"success": True, "evaluation": evaluation}
    
    async def _coordinate_team(self, request: Dict) -> Dict:
        task_id = request.get("task_id")
        required_skills = request.get("required_skills", [])
        
        coordination_result = {
            "task_id": task_id,
            "team_formed": True,
            "assigned_agents": [],
            "coordination_plan": {},
        }
        
        return {"success": True, "coordination": coordination_result}


class HuBuAgent(BusinessAgent):
    """
    户部智能体
    
    职责：管理用户积分、资产数据
    """
    
    def __init__(self, **kwargs):
        kwargs['role'] = BusinessAgentRole.HU_BU
        kwargs['species'] = 'hu_bu'
        super().__init__(**kwargs)
        
        self.user_points: Dict[str, float] = {}
        self.asset_records: Dict[str, List[Dict]] = defaultdict(list)
    
    def _get_role_specific_genes(self) -> List[BusinessGene]:
        return [
            BusinessGene(
                gene_id="gene_accuracy",
                name="data_accuracy",
                value=0.9,
                mutation_rate=0.05,
                mutation_range=(-0.1, 0.1),
                business_weight=2.0
            ),
            BusinessGene(
                gene_id="gene_security",
                name="data_security",
                value=0.95,
                mutation_rate=0.05,
                mutation_range=(-0.1, 0.1),
                business_weight=2.5
            ),
        ]
    
    def _get_capabilities(self) -> List[str]:
        return [
            "points_management",
            "asset_tracking",
            "user_statistics",
            "reward_distribution",
            "data_security",
        ]
    
    def _get_preferred_tasks(self) -> List[str]:
        return [
            "points_update",
            "asset_registration",
            "reward_calculation",
            "user_summary",
        ]
    
    async def execute_business(self, request: Dict) -> Dict:
        action = request.get("action", "")
        
        if action == "update_points":
            return await self._update_points(request)
        elif action == "get_user_summary":
            return await self._get_user_summary(request)
        elif action == "register_asset":
            return await self._register_asset(request)
        else:
            return {"success": False, "error": "Unknown action"}
    
    async def _update_points(self, request: Dict) -> Dict:
        user_id = request.get("user_id")
        points_delta = request.get("points_delta", 0)
        reason = request.get("reason", "")
        
        current_points = self.user_points.get(user_id, 0)
        new_points = max(0, current_points + points_delta)
        self.user_points[user_id] = new_points
        
        return {
            "success": True,
            "user_id": user_id,
            "previous_points": current_points,
            "new_points": new_points,
            "change": points_delta,
            "reason": reason,
        }
    
    async def _get_user_summary(self, request: Dict) -> Dict:
        user_id = request.get("user_id")
        
        summary = {
            "user_id": user_id,
            "total_points": self.user_points.get(user_id, 0),
            "asset_count": len(self.asset_records.get(user_id, [])),
            "recent_activities": self.asset_records.get(user_id, [])[-5:],
        }
        
        return {"success": True, "summary": summary}
    
    async def _register_asset(self, request: Dict) -> Dict:
        user_id = request.get("user_id")
        asset_info = request.get("asset_info", {})
        
        asset_id = f"asset_{uuid.uuid4().hex[:8]}"
        asset_record = {
            "asset_id": asset_id,
            "user_id": user_id,
            "info": asset_info,
            "registered_at": time.time(),
        }
        
        self.asset_records[user_id].append(asset_record)
        
        return {"success": True, "asset_id": asset_id}


class LiBuConsultAgent(BusinessAgent):
    """
    礼部智能体
    
    职责：提供房产咨询服务，生成回复
    """
    
    def __init__(self, **kwargs):
        kwargs['role'] = BusinessAgentRole.LI_BU_CONSULT
        kwargs['species'] = 'li_bu_consult'
        super().__init__(**kwargs)
        
        self.consultation_history: Dict[str, List[Dict]] = defaultdict(list)
        self.response_templates: Dict[str, str] = {}
    
    def _get_role_specific_genes(self) -> List[BusinessGene]:
        return [
            BusinessGene(
                gene_id="gene_politeness",
                name="politeness_level",
                value=0.9,
                mutation_rate=0.1,
                mutation_range=(-0.2, 0.2),
                business_weight=1.5
            ),
            BusinessGene(
                gene_id="gene_helpfulness",
                name="helpfulness_score",
                value=0.85,
                mutation_rate=0.1,
                mutation_range=(-0.2, 0.2),
                business_weight=2.0
            ),
        ]
    
    def _get_capabilities(self) -> List[str]:
        return [
            "consultation",
            "response_generation",
            "user_guidance",
            "faq_handling",
            "personalized_advice",
        ]
    
    def _get_preferred_tasks(self) -> List[str]:
        return [
            "user_consultation",
            "inquiry_response",
            "guidance_provision",
            "faq_generation",
        ]
    
    async def execute_business(self, request: Dict) -> Dict:
        action = request.get("action", "")
        
        if action == "consult":
            return await self._handle_consultation(request)
        elif action == "generate_response":
            return await self._generate_response(request)
        else:
            return {"success": False, "error": "Unknown action"}
    
    async def _handle_consultation(self, request: Dict) -> Dict:
        user_id = request.get("user_id")
        query = request.get("query", "")
        
        response = f"感谢您的咨询。关于您的问题「{query[:50]}...」，我为您提供以下建议..."
        
        consultation_record = {
            "query": query,
            "response": response,
            "timestamp": time.time(),
        }
        
        self.consultation_history[user_id].append(consultation_record)
        
        return {
            "success": True,
            "response": response,
            "consultation_id": f"cons_{uuid.uuid4().hex[:8]}",
        }
    
    async def _generate_response(self, request: Dict) -> Dict:
        context = request.get("context", {})
        user_id = request.get("user_id")
        
        user_pref = self.get_user_preference(user_id)
        
        response = {
            "content": "根据您的需求，我为您生成以下回复...",
            "personalized": len(user_pref) > 0,
            "timestamp": time.time(),
        }
        
        return {"success": True, "response": response}


class BingBuAgent(BusinessAgent):
    """
    兵部智能体
    
    职责：采集房产数据，更新数据源
    """
    
    def __init__(self, **kwargs):
        kwargs['role'] = BusinessAgentRole.BING_BU
        kwargs['species'] = 'bing_bu'
        super().__init__(**kwargs)
        
        self.data_sources: Dict[str, Dict] = {}
        self.collection_stats: Dict[str, int] = defaultdict(int)
    
    def _get_role_specific_genes(self) -> List[BusinessGene]:
        return [
            BusinessGene(
                gene_id="gene_collection_speed",
                name="collection_speed",
                value=1.0,
                mutation_rate=0.1,
                mutation_range=(-0.3, 0.3),
                business_weight=1.5
            ),
            BusinessGene(
                gene_id="gene_data_quality",
                name="data_quality_threshold",
                value=0.8,
                mutation_rate=0.1,
                mutation_range=(-0.2, 0.2),
                business_weight=2.0
            ),
        ]
    
    def _get_capabilities(self) -> List[str]:
        return [
            "data_collection",
            "source_management",
            "data_validation",
            "update_scheduling",
            "quality_monitoring",
        ]
    
    def _get_preferred_tasks(self) -> List[str]:
        return [
            "collect_data",
            "update_source",
            "validate_data",
            "schedule_update",
        ]
    
    async def execute_business(self, request: Dict) -> Dict:
        action = request.get("action", "")
        
        if action == "collect":
            return await self._collect_data(request)
        elif action == "update_source":
            return await self._update_source(request)
        else:
            return {"success": False, "error": "Unknown action"}
    
    async def _collect_data(self, request: Dict) -> Dict:
        source_id = request.get("source_id")
        data_type = request.get("data_type")
        
        collection_result = {
            "source_id": source_id,
            "data_type": data_type,
            "records_collected": random.randint(10, 100),
            "quality_score": random.uniform(0.7, 1.0),
            "collected_at": time.time(),
        }
        
        self.collection_stats[source_id] += collection_result["records_collected"]
        
        return {"success": True, "result": collection_result}
    
    async def _update_source(self, request: Dict) -> Dict:
        source_id = request.get("source_id")
        update_config = request.get("config", {})
        
        if source_id not in self.data_sources:
            self.data_sources[source_id] = {
                "source_id": source_id,
                "status": "active",
                "last_updated": time.time(),
            }
        
        self.data_sources[source_id].update(update_config)
        
        return {"success": True, "source": self.data_sources[source_id]}


class XingBuAgent(BusinessAgent):
    """
    刑部智能体
    
    职责：风控审核，检测异常行为
    """
    
    def __init__(self, **kwargs):
        kwargs['role'] = BusinessAgentRole.XING_BU
        kwargs['species'] = 'xing_bu'
        super().__init__(**kwargs)
        
        self.risk_rules: Dict[str, Dict] = {}
        self.alert_history: deque = deque(maxlen=1000)
    
    def _get_role_specific_genes(self) -> List[BusinessGene]:
        return [
            BusinessGene(
                gene_id="gene_risk_sensitivity",
                name="risk_sensitivity",
                value=0.8,
                mutation_rate=0.1,
                mutation_range=(-0.2, 0.2),
                business_weight=2.0
            ),
            BusinessGene(
                gene_id="gene_false_positive",
                name="false_positive_rate",
                value=0.1,
                mutation_rate=0.05,
                mutation_range=(-0.05, 0.05),
                business_weight=1.5
            ),
        ]
    
    def _get_capabilities(self) -> List[str]:
        return [
            "risk_assessment",
            "anomaly_detection",
            "fraud_prevention",
            "compliance_check",
            "alert_generation",
        ]
    
    def _get_preferred_tasks(self) -> List[str]:
        return [
            "assess_risk",
            "detect_anomaly",
            "check_compliance",
            "generate_alert",
        ]
    
    async def execute_business(self, request: Dict) -> Dict:
        action = request.get("action", "")
        
        if action == "assess_risk":
            return await self._assess_risk(request)
        elif action == "detect_anomaly":
            return await self._detect_anomaly(request)
        else:
            return {"success": False, "error": "Unknown action"}
    
    async def _assess_risk(self, request: Dict) -> Dict:
        target_id = request.get("target_id")
        target_type = request.get("target_type")
        data = request.get("data", {})
        
        risk_score = random.uniform(0, 1)
        risk_level = "low"
        
        if risk_score > 0.7:
            risk_level = "high"
        elif risk_score > 0.4:
            risk_level = "medium"
        
        assessment = {
            "target_id": target_id,
            "target_type": target_type,
            "risk_score": risk_score,
            "risk_level": risk_level,
            "factors": ["behavior_pattern", "historical_data"],
            "assessed_at": time.time(),
        }
        
        return {"success": True, "assessment": assessment}
    
    async def _detect_anomaly(self, request: Dict) -> Dict:
        data = request.get("data", {})
        threshold = request.get("threshold", 0.8)
        
        is_anomaly = random.random() > 0.9
        
        result = {
            "is_anomaly": is_anomaly,
            "confidence": random.uniform(0.7, 1.0) if is_anomaly else random.uniform(0.6, 0.9),
            "detected_at": time.time(),
        }
        
        if is_anomaly:
            alert = {
                "alert_id": f"alert_{uuid.uuid4().hex[:8]}",
                "type": "anomaly",
                "severity": "medium",
                "data": data,
                "timestamp": time.time(),
            }
            self.alert_history.append(alert)
            result["alert"] = alert
        
        return {"success": True, "result": result}


class GongBuAgent(BusinessAgent):
    """
    工部智能体
    
    职责：生成分析报告，数据可视化
    """
    
    def __init__(self, **kwargs):
        kwargs['role'] = BusinessAgentRole.GONG_BU
        kwargs['species'] = 'gong_bu'
        super().__init__(**kwargs)
        
        self.report_templates: Dict[str, Dict] = {}
        self.generated_reports: Dict[str, Dict] = {}
    
    def _get_role_specific_genes(self) -> List[BusinessGene]:
        return [
            BusinessGene(
                gene_id="gene_report_quality",
                name="report_quality",
                value=0.85,
                mutation_rate=0.1,
                mutation_range=(-0.2, 0.2),
                business_weight=2.0
            ),
            BusinessGene(
                gene_id="gene_visualization",
                name="visualization_skill",
                value=0.8,
                mutation_rate=0.1,
                mutation_range=(-0.2, 0.2),
                business_weight=1.5
            ),
        ]
    
    def _get_capabilities(self) -> List[str]:
        return [
            "report_generation",
            "data_analysis",
            "visualization",
            "insight_extraction",
            "summary_creation",
        ]
    
    def _get_preferred_tasks(self) -> List[str]:
        return [
            "generate_report",
            "analyze_data",
            "create_visualization",
            "extract_insights",
        ]
    
    async def execute_business(self, request: Dict) -> Dict:
        action = request.get("action", "")
        
        if action == "generate_report":
            return await self._generate_report(request)
        elif action == "analyze":
            return await self._analyze_data(request)
        else:
            return {"success": False, "error": "Unknown action"}
    
    async def _generate_report(self, request: Dict) -> Dict:
        report_type = request.get("report_type")
        data = request.get("data", {})
        user_id = request.get("user_id")
        
        report_id = f"report_{uuid.uuid4().hex[:8]}"
        
        report = {
            "report_id": report_id,
            "report_type": report_type,
            "title": f"{report_type}分析报告",
            "sections": [
                {
                    "title": "概述",
                    "content": "本报告基于提供的数据进行分析...",
                },
                {
                    "title": "关键发现",
                    "content": "通过分析发现以下关键信息...",
                },
                {
                    "title": "建议",
                    "content": "基于分析结果，建议...",
                },
            ],
            "generated_at": time.time(),
            "data_points": len(data) if isinstance(data, list) else 1,
        }
        
        self.generated_reports[report_id] = report
        
        return {"success": True, "report": report}
    
    async def _analyze_data(self, request: Dict) -> Dict:
        data = request.get("data", [])
        analysis_type = request.get("analysis_type", "general")
        
        analysis = {
            "analysis_type": analysis_type,
            "summary": {
                "total_records": len(data) if isinstance(data, list) else 1,
                "key_metrics": {},
            },
            "insights": [
                "数据整体呈现稳定趋势",
                "存在若干异常值需要关注",
            ],
            "recommendations": [
                "建议进一步收集相关数据",
                "可考虑进行深度分析",
            ],
            "analyzed_at": time.time(),
        }
        
        return {"success": True, "analysis": analysis}


class AttnResMinistryCoordinator:
    """
    基于Attention Residuals的六部智能体协同协调器
    
    核心功能：
    1. 任务分配时动态聚合历史经验
    2. 根据任务特征选择最合适的智能体组合
    3. 智能体间经验共享与协同学习
    """
    
    MINISTRY_AGENTS = {
        0: "li_bu",      # 吏部 - 团队协调
        1: "hu_bu",      # 户部 - 数据管理
        2: "li_bu_consult",  # 礼部 - 咨询服务
        3: "bing_bu",    # 兵部 - 数据采集
        4: "xing_bu",    # 刑部 - 风控审核
        5: "gong_bu",    # 工部 - 报告生成
    }
    
    def __init__(self, dim: int = 256, use_gpu: bool = False):
        self.dim = dim
        self.use_gpu = use_gpu and ATTN_RES_AVAILABLE and torch.cuda.is_available()
        self.device = "cuda" if self.use_gpu else "cpu"
        
        self.agents: Dict[str, BusinessAgent] = {}
        self.experience_history: Dict[str, List[np.ndarray]] = defaultdict(list)
        self.task_embeddings: Dict[str, np.ndarray] = {}
        
        if ATTN_RES_AVAILABLE:
            self.swarm_attn = AgentSwarmAttnRes(dim=dim, num_agents=6)
            if self.use_gpu:
                self.swarm_attn = self.swarm_attn.to(self.device)
            logger.info(f"AttnResMinistryCoordinator initialized with dim={dim}, device={self.device}")
        else:
            self.swarm_attn = None
            logger.warning("AttnResMinityCoordinator initialized without AttnRes (torch not available)")
    
    def register_agent(self, agent: BusinessAgent):
        """注册智能体"""
        agent_key = agent.species if hasattr(agent, 'species') else agent.agent_id
        self.agents[agent_key] = agent
        logger.debug(f"Registered agent: {agent_key}")
    
    def _encode_task(self, task_description: str) -> np.ndarray:
        """将任务描述编码为向量"""
        np.random.seed(hash(task_description) % (2**32))
        embedding = np.random.randn(self.dim).astype(np.float32)
        norm = np.linalg.norm(embedding)
        if norm > 0:
            embedding = embedding / norm
        return embedding
    
    def _encode_experience(self, experience: Dict) -> np.ndarray:
        """将经验数据编码为向量"""
        np.random.seed(hash(str(experience)) % (2**32))
        embedding = np.random.randn(self.dim).astype(np.float32)
        norm = np.linalg.norm(embedding)
        if norm > 0:
            embedding = embedding / norm
        return embedding
    
    async def allocate_task_with_attn_res(
        self,
        task_description: str,
        task_type: str,
        context: Optional[Dict] = None
    ) -> Dict:
        """
        使用AttnRes进行任务分配
        
        核心公式: task_emb + Attention(task_emb, agent_embs + exp_history)
        
        Args:
            task_description: 任务描述
            task_type: 任务类型
            context: 额外上下文
            
        Returns:
            分配结果，包含选中的智能体和权重
        """
        task_emb = self._encode_task(task_description)
        
        agent_ids = list(range(6))
        
        if ATTN_RES_AVAILABLE and self.swarm_attn is not None:
            task_tensor = torch.from_numpy(task_emb).float().unsqueeze(0)
            if self.use_gpu:
                task_tensor = task_tensor.to(self.device)
            
            exp_history = []
            for agent_key in self.MINISTRY_AGENTS.values():
                if agent_key in self.experience_history and self.experience_history[agent_key]:
                    recent_exp = self.experience_history[agent_key][-5:]
                    exp_emb = np.mean(recent_exp, axis=0)
                    exp_tensor = torch.from_numpy(exp_emb).float()
                    if self.use_gpu:
                        exp_tensor = exp_tensor.to(self.device)
                    exp_history.append(exp_tensor)
            
            with torch.no_grad():
                coord_output, agent_weights = self.swarm_attn(
                    task_tensor, agent_ids, exp_history if exp_history else None
                )
            
            weights = agent_weights.squeeze().cpu().numpy()
        else:
            weights = np.ones(6) / 6
        
        agent_rankings = sorted(
            [(self.MINISTRY_AGENTS[i], weights[i]) for i in range(6)],
            key=lambda x: x[1],
            reverse=True
        )
        
        primary_agent_key = agent_rankings[0][0]
        primary_agent = self.agents.get(primary_agent_key)
        
        result = {
            "task_description": task_description,
            "task_type": task_type,
            "primary_agent": primary_agent_key,
            "agent_rankings": agent_rankings,
            "coordination_weights": {k: float(v) for k, v in agent_rankings},
            "attn_res_used": ATTN_RES_AVAILABLE and self.swarm_attn is not None,
        }
        
        if primary_agent:
            result["agent_available"] = True
        else:
            result["agent_available"] = False
        
        return result
    
    def record_experience(
        self,
        agent_key: str,
        task_result: Dict,
        success: bool
    ):
        """
        记录智能体执行经验
        
        经验会被编码并存储，用于未来的AttnRes聚合
        """
        experience = {
            "result": task_result,
            "success": success,
            "timestamp": time.time(),
        }
        
        exp_emb = self._encode_experience(experience)
        self.experience_history[agent_key].append(exp_emb)
        
        if len(self.experience_history[agent_key]) > 100:
            self.experience_history[agent_key] = self.experience_history[agent_key][-100:]
    
    async def collaborative_execute(
        self,
        task_description: str,
        task_type: str,
        request: Dict,
        top_k: int = 3
    ) -> Dict:
        """
        协同执行任务
        
        根据AttnRes权重选择多个智能体协同处理
        """
        allocation = await self.allocate_task_with_attn_res(
            task_description, task_type, request
        )
        
        results = []
        selected_agents = allocation["agent_rankings"][:top_k]
        
        for agent_key, weight in selected_agents:
            agent = self.agents.get(agent_key)
            if agent is None:
                continue
            
            try:
                result = await agent.execute_business(request)
                self.record_experience(agent_key, result, result.get("success", False))
                
                results.append({
                    "agent": agent_key,
                    "weight": float(weight),
                    "result": result,
                })
            except Exception as e:
                logger.error(f"Agent {agent_key} execution failed: {e}")
                results.append({
                    "agent": agent_key,
                    "weight": float(weight),
                    "error": str(e),
                })
        
        aggregated_result = self._aggregate_results(results)
        
        return {
            "success": True,
            "task_description": task_description,
            "task_type": task_type,
            "agent_results": results,
            "aggregated": aggregated_result,
            "attn_res_used": allocation["attn_res_used"],
        }
    
    def _aggregate_results(self, results: List[Dict]) -> Dict:
        """聚合多个智能体的结果"""
        if not results:
            return {}
        
        successful_results = [r for r in results if "result" in r and r["result"].get("success")]
        
        if not successful_results:
            return {"success": False, "error": "All agents failed"}
        
        total_weight = sum(r["weight"] for r in successful_results)
        
        if ATTN_RES_AVAILABLE and len(successful_results) > 1:
            result_embeddings = []
            for r in successful_results:
                emb = self._encode_experience(r["result"])
                result_embeddings.append(emb)
            
            embeddings_tensor = torch.from_numpy(np.stack(result_embeddings)).float()
            if self.use_gpu:
                embeddings_tensor = embeddings_tensor.to(self.device)
            
            weights_tensor = torch.tensor([r["weight"] for r in successful_results]).float()
            if self.use_gpu:
                weights_tensor = weights_tensor.to(self.device)
            
            with torch.no_grad():
                weighted_sum = (embeddings_tensor * weights_tensor.unsqueeze(1)).sum(dim=0)
                aggregated_emb = weighted_sum / total_weight
            
            aggregated = {
                "success": True,
                "contributing_agents": [r["agent"] for r in successful_results],
                "confidence": float(total_weight / len(results)),
                "aggregation_method": "attn_res_weighted",
            }
        else:
            aggregated = {
                "success": True,
                "contributing_agents": [r["agent"] for r in successful_results],
                "confidence": float(total_weight / len(results)),
                "aggregation_method": "simple_weighted",
            }
        
        return aggregated
    
    def get_agent_statistics(self) -> Dict:
        """获取智能体统计信息"""
        stats = {}
        for agent_key, exp_list in self.experience_history.items():
            stats[agent_key] = {
                "experience_count": len(exp_list),
                "registered": agent_key in self.agents,
            }
        return stats


_ministry_coordinator: Optional[AttnResMinistryCoordinator] = None


def get_ministry_coordinator() -> AttnResMinistryCoordinator:
    """获取全局六部协调器实例"""
    global _ministry_coordinator
    if _ministry_coordinator is None:
        _ministry_coordinator = AttnResMinistryCoordinator()
    return _ministry_coordinator


async def allocate_task_to_ministry(
    task_description: str,
    task_type: str,
    context: Optional[Dict] = None
) -> Dict:
    """便捷函数：使用AttnRes分配任务到六部"""
    coordinator = get_ministry_coordinator()
    return await coordinator.allocate_task_with_attn_res(
        task_description, task_type, context
    )
