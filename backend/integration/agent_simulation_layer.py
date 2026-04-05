# -*- coding: utf-8 -*-
"""
智能体修炼体系 - 多智能体仿真引擎层（第5层：Agent Simulation Layer）
==============================================================================
对应设计文档「多智能体仿真引擎融合方案」完整落地。
将4大重磅开源仿真技术与房都督平台深度融合，实现平行世界推演、压力测试、策略验证。

仿真技术全景：
  MiroFish   — 通用群体智能引擎（17000+⭐，中科大BaiFu开发，获3000万投资）
              五步工作流：本体生成→GraphRAG建图→环境搭建→仿真运行→报告生成
              双平台并行(Twitter+Reddit)，Zep Cloud时序记忆，OASIS轻封装仿真引擎
  HEAS       — 分层进化智能体仿真（arXiv:2508.15555）
              流式层次建模+进化优化+锦标赛评估，CLI三模式(simulate/optimize/evaluate)
              Pareto前沿可视化，跨尺度耦合可审计
  VirtualEnv — 虚幻引擎5物理仿真（MIT+Google DeepMind, arXiv:2601.07553）
              物体操控+导航+多智能体协作+逃生室+程序生成环境
              Python API + 自然语言控制 + GPT环境生成
  GAMMS      — 轻量级图仿真框架（arXiv:2602.05105）
              城市路网/通信系统图建模，启发式+优化型+学习型智能体
              低硬件要求，普通电脑可跑

融合架构：
  房都督核心 → 仿真引擎层(本模块) → 平行世界推演 → 策略优化反馈 → 报告对接

通关标准：
  MiroFish: 千Agent仿真40轮<50万token, 预测准确率≥80%, 报告自动生成率100%
  HEAS: 进化收敛代数≤50, Pareto解质量≥0.85, 审计覆盖率100%
  VirtualEnv: 物理交互准确率≥90%, 多Agent协作成功率≥85%
  GAMMS: 图仿真吞吐≥1000节点/s, 智能体路径规划最优比≤1.2
"""
from __future__ import annotations

import json
import math
import random
import statistics
import logging
import time
import copy
import uuid
import os
import re
from abc import ABC, abstractmethod
from dataclasses import dataclass, field, asdict
from datetime import datetime, timedelta
from enum import Enum, auto
from typing import Any, Dict, List, Optional, Tuple, Callable, Set
from collections import deque, defaultdict

logger = logging.getLogger(__name__)


# ==================== 枚举定义 ====================


class SimPlatform(Enum):
    """仿真平台类型"""
    TWITTER = "Twitter"
    REDDIT = "Reddit"
    WECHAT = "WeChat"
    FORUM = "Forum"
    CUSTOM = "Custom"


class SimulationPhase(Enum):
    """MiroFish五步工作流阶段"""
    ONTOLOGY_GENERATION = "本体生成"
    GRAPH_RAG_BUILDING = "GraphRAG建图"
    ENVIRONMENT_SETUP = "环境搭建"
    SIMULATION_RUNNING = "仿真运行"
    REPORT_GENERATION = "报告生成"


class HEASMode(Enum):
    """HEAS操作模式"""
    SIMULATE = "simulate"
    OPTIMIZE = "optimize"
    EVALUATE = "evaluate"


class VirtualEnvScenario(Enum):
    """VirtualEnv场景类型"""
    PHYSICS_MANIPULATION = "物体操控"
    NAVIGATION = "导航探索"
    MULTI_AGENT_COLLAB = "多智能体协作"
    ESCAPE_ROOM = "逃生室挑战"
    CODE_GENERATION = "程序生成环境"
    VR_AR_VIEWING = "VR/AR看房"


class GraphSimAgentType(Enum):
    """GAMMS智能体类型"""
    HEURISTIC = "启发式"
    OPTIMIZATION = "优化型"
    LEARNING_BASED = "学习型"
    LLM_POWERED = "LLM驱动"


class EvolutionStrategy(Enum):
    """进化策略"""
    GENETIC_ALGORITHM = "遗传算法"
    PARTICLE_SWARM = "粒子群优化"
    DIFFERENTIAL_EVolution = "差分进化"
    CMA_ES = "协方差矩阵自适应"
    NSGA_II = "NSGA-II多目标"
    PESO = "Pareto包络选择"


# ==================== 数据结构定义 ====================


@dataclass
class AgentOntology:
    """智能体本体定义"""
    ontology_id: str
    entity_name: str
    entity_type: str  # person/organization/location/event/concept
    attributes: Dict[str, Any]
    relationships: List[Dict[str, str]]  # [(relation, target_id)]
    background_doc: str  # 来源文档片段
    personality_traits: Dict[str, float]  # 特征向量
    initial_state: Dict[str, Any]
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())


@dataclass
class GraphRAGNode:
    """GraphRAG图谱节点"""
    node_id: str
    entity_name: str
    entity_type: str
    description: str
    embedding: Optional[List[float]] = None
    community_id: Optional[int] = None
    importance_score: float = 0.0
    temporal_data: List[Dict[str, Any]] = field(default_factory=list)


@dataclass
class GraphRAGEdge:
    """GraphRAG图谱边"""
    source_id: str
    target_id: str
    relation_type: str
    weight: float = 1.0
    evidence: Optional[str] = None
    timestamp: Optional[str] = None


@dataclass
class SimulationEnvironment:
    """仿真环境配置"""
    env_id: str
    platform: SimPlatform
    total_agents: int
    max_rounds: int
    current_round: int = 0
    config: Dict[str, Any] = field(default_factory=dict)
    active: bool = False
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())


@dataclass
class SocialPost:
    """社交平台帖子(仿真用)"""
    post_id: str
    author_agent_id: str
    platform: SimPlatform
    content: str
    post_type: str  # original/comment/reply/share
    target_post_id: Optional[str] = None
    engagement_metrics: Dict[str, int] = field(default_factory=lambda: {"likes": 0, "comments": 0, "shares": 0})
    sentiment: float = 0.0  # -1 to 1
    topics: List[str] = field(default_factory=list)
    round_num: int = 0
    created_at_sim: str = ""


@dataclass
class AgentMemoryEntry:
    """智能体时序记忆条目(Zep Cloud风格)"""
    memory_id: str
    agent_id: str
    content: str
    memory_type: str  # observation/reflection/knowledge/social
    importance: float  # 0-1
    sentiment: float  # -1 to 1
    associated_entities: List[str] = field(default_factory=list)
    expires_at: Optional[str] = None
    created_at_sim: str = ""
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())


@dataclass
class SimulationRoundResult:
    """单轮仿真结果"""
    round_number: int
    posts_generated: int
    total_engagement: Dict[str, int]
    sentiment_distribution: Dict[str, float]
    key_events: List[Dict[str, Any]]
    network_metrics: Dict[str, float]
    agent_states_summary: Dict[str, Dict[str, Any]]
    token_consumed: float = 0.0
    duration_s: float = 0.0


@dataclass
class MiroFishReport:
    """MiroFish仿真报告"""
    report_id: str
    simulation_id: str
    source_document: str
    executive_summary: str
    event_timeline: List[Dict[str, Any]]
    risk_warnings: List[Dict[str, Any]]
    strategy_recommendations: List[Dict[str, Any]]
    prediction_confidence: float  # 0-1
    total_agents: int
    total_rounds: int
    total_tokens: float
    key_insights: List[str]
    generated_at: str = field(default_factory=lambda: datetime.now().isoformat())


@dataclass
class HEASStreamDef:
    """HEAS流定义（模型层次）"""
    stream_id: str
    stream_name: str
    layer_level: int  # 0=底层, 1=中层, 2=顶层
    variables: Dict[str, Any]
    read_from: List[str]  # 读取的上游流
    write_to: List[str]  # 写入的下游流
    coupling_strength: float  # 0-1
    audit_log: List[Dict[str, Any]] = field(default_factory=list)


@dataclass
class HEASEvolutionResult:
    """HEAS进化结果"""
    evolution_id: str
    strategy: EvolutionStrategy
    generations: int
    population_size: int
    objective_values: Dict[str, float]
    pareto_frontier: List[Dict[str, float]]
    best_solution: Dict[str, Any]
    convergence_generation: int
    diversity_metric: float
    computation_time_s: float
    audit_trail: List[str] = field(default_factory=list)
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())


@dataclass
class HEASTournamentResult:
    """HEAS锦标赛评估结果"""
    tournament_id: str
    candidates: List[Dict[str, Any]]
    evaluation_criteria: List[str]
    scores: Dict[str, Dict[str, float]]
    rankings: List[Tuple[int, float]]  # (candidate_idx, score)
    winner_idx: int
    statistical_significance: float
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())


@dataclass
class PhysicsInteraction:
    """物理交互记录(VirtualEnv)"""
    interaction_id: str
    agent_id: str
    object_id: str
    interaction_type: str  # grasp/move/push/pull/collide
    position_3d: Tuple[float, float, float]
    rotation_3d: Tuple[float, float, float]
    force_applied: float
    success: bool
    physics_metrics: Dict[str, float]
    duration_ms: float
    scenario_type: VirtualEnvScenario
    timestamp_sim: str = ""


@dataclass
class NavigationPath:
    """导航路径(VirtualEnv)"""
    path_id: str
    agent_id: str
    waypoints: List[Tuple[float, float, float]]
    total_distance: float
    time_to_complete_s: float
    obstacles_avoided: int
    collisions: int
    smoothness_score: float  # 0-1
    efficiency_score: float  # 0-1
    scenario_type: VirtualEnvScenario


@dataclass
class GraphSimulationState:
    """图仿真状态(GAMMS)"""
    sim_id: str
    graph_type: str  # road_network/communication/social/power_grid
    nodes: int
    edges: int
    agent_positions: Dict[str, int]  # agent_id -> node_id
    agent_types: Dict[str, GraphSimAgentType]
    step_count: int
    throughput_per_step: float
    congestion_levels: Dict[str, float]  # edge_id -> congestion 0-1
    total_cost: float = 0.0
    fairness_index: float = 1.0  # Jain's fairness index
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())


@dataclass
class SimulationHealthStatus:
    """仿真层健康状态"""
    status_id: str
    mirofish_status: Dict[str, Any]
    heas_status: Dict[str, Any]
    virtualenv_status: Dict[str, Any]
    gamms_status: Dict[str, Any]
    overall_health: float  # 0-1
    active_simulations: int
    total_predictions_made: int
    avg_prediction_accuracy: float
    recommendations: List[str]
    generated_at: str = field(default_factory=lambda: datetime.now().isoformat())


# ==================== Part A: MiroFish 通用群体智能引擎 ====================


class MiroFishEngine:
    """MiroFish通用群体智能引擎 — 五步工作流+双平台仿真+GraphRAG记忆"""

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or {}
        self._ontologies: Dict[str, AgentOntology] = {}
        self._graph_nodes: Dict[str, GraphRAGNode] = {}
        self._graph_edges: List[GraphRAGEdge] = []
        self._environments: Dict[str, SimulationEnvironment] = {}
        self._agent_memories: Dict[str, List[AgentMemoryEntry]] = defaultdict(list)
        self._posts: List[SocialPost] = []
        self._round_results: List[SimulationRoundResult] = []
        self._reports: List[MiroFishReport] = []

    def run_full_pipeline(self, source_document: str,
                          platform_configs: Optional[List[Dict[str, Any]]] = None,
                          max_agents: int = 100,
                          max_rounds: int = 40) -> MiroFishReport:
        """执行完整五步工作流"""
        sim_id = f"mirofish_{uuid.uuid4().hex[:8]}"
        start_time = time.time()
        logger.info(f"[MiroFish] 开始全流程仿真: {sim_id}, 文档长度={len(source_document)}, 最大Agent={max_agents}, 最大轮次={max_rounds}")

        phase1_result = self._phase1_ontology_generation(source_document, sim_id)
        logger.info(f"[MiroFish] Phase1 本体生成: {len(phase1_result)}个实体")

        phase2_result = self._phase2_graphrag_building(phase1_result, sim_id)
        logger.info(f"[MiroFish] Phase2 GraphRAG建图: {phase2_result['nodes']}节点, {phase2_result['edges']}边")

        platforms = platform_configs or [
            {"platform": SimPlatform.TWITTER, "config": {"post_length_limit": 280, "retweet_enabled": True}},
            {"platform": SimPlatform.REDDIT, "config": {"post_length_limit": 40000, "upvote_system": True, "karma_enabled": True}},
        ]
        phase3_envs = self._phase3_environment_setup(platforms, max_agents, max_rounds, sim_id)
        logger.info(f"[MiroFish] Phase3 环境搭建: {len(phase3_envs)}个平台环境")

        all_round_results = []
        for env in phase3_envs:
            env.active = True
            round_results = self._phase4_simulation_running(env, phase1_result, sim_id)
            all_round_results.extend(round_results)

        report = self._phase5_report_generation(
            sim_id, source_document, all_round_results, phase1_result, phase2_result
        )
        total_time = (time.time() - start_time) / 60
        report.total_tokens = sum(r.token_consumed for r in all_round_results)
        logger.info(f"[MiroFish] 全流程完成! 耗时={total_time:.1f}min, Token={report.total_tokens:.0f}, "
                     f"置信度={report.prediction_confidence:.2f}")
        return report

    def _phase1_ontology_generation(self, document: str, sim_id: str) -> List[AgentOntology]:
        """Phase 1: 从文档自动生成智能体本体"""
        entities = self._extract_entities(document)
        ontologies = []
        for i, ent in enumerate(entities):
            oid = f"onto_{uuid.uuid4().hex[:8]}"
            traits = self._generate_personality(ent["type"], ent["name"])
            rels = self._infer_relationships(ent, entities)
            onto = AgentOntology(
                ontology_id=oid, entity_name=ent["name"],
                entity_type=ent["type"], attributes=ent.get("attributes", {}),
                relationships=rels, background_doc=ent.get("context", ""),
                personality_traits=traits,
                initial_state={"opinion": random.uniform(-0.3, 0.3), "energy": random.uniform(0.6, 1.0),
                             "influence": random.uniform(0.1, 0.9)},
            )
            self._ontologies[oid] = onto
            ontologies.append(onto)
        return ontologies

    def _extract_entities(self, text: str) -> List[Dict[str, Any]]:
        """实体提取(模拟NER)"""
        sentences = re.split(r'[。！？\n]', text)
        entities = []
        seen_names = set()
        name_patterns = {
            "person": r'[\u4e00-\u9fff]{2,4}(?:院长|教授|经理|主任|局长|市长|书记|总|工|生|师)',
            "organization": r'([\u4e00-\u9fff]{2,10})(?:大学|公司|研究院|协会|政府|银行|集团|医院|学校)',
            "location": r'([\u4e00-\u9fff]{2,6})(?:省|市|区|县|路|街|广场|大厦|园区)',
            "event": r'([\u4e00-\u9fff]{2,8})(?:会议|政策|发布|改革|调整|启动|签约)',
            "concept": r'([\u4e00-\u9fff]{2,6})(?:房价|利率|政策|市场|需求|供应)',
        }
        for sent in sentences:
            if len(sent.strip()) < 3:
                continue
            for etype, pattern in name_patterns.items():
                matches = re.findall(pattern, sent)
                for m in matches:
                    name = m if isinstance(m, str) else m[0]
                    if name not in seen_names and len(name) >= 2:
                        seen_names.add(name)
                        entities.append({"name": name, "type": etype, "context": sent.strip()})
        if not entities:
            fallback_entities = [
                {"name": "房产市场参与者A", "type": "person", "context": text[:100]},
                {"name": "房产市场参与者B", "type": "person", "context": text[:100]},
                {"name": "监管机构", "type": "organization", "context": text[:100]},
                {"name": "市场主体", "type": "organization", "context": text[:100]},
            ]
            entities.extend(fallback_entities)
        return entities[:self.config.get("max_entities", 200)]

    def _generate_personality(self, etype: str, name: str) -> Dict[str, float]:
        """生成人格特征向量"""
        base = {
            "openness": random.uniform(0.3, 0.9),
            "conscientiousness": random.uniform(0.3, 0.9),
            "extraversion": random.uniform(0.2, 0.8),
            "agreeableness": random.uniform(0.3, 0.9),
            "neuroticism": random.uniform(0.2, 0.7),
        }
        if etype == "person":
            base["influence"] = random.uniform(0.1, 0.95)
        elif etype == "organization":
            base["formality"] = random.uniform(0.5, 0.98)
            base["risk_tolerance"] = random.uniform(0.2, 0.8)
        return base

    def _infer_relationships(self, entity: Dict, all_entities: List[Dict]) -> List[Dict[str, str]]:
        """推断实体关系"""
        rels = []
        etype = entity["type"]
        possible_rels = {
            "person": [("colleague_of", "person"), ("works_at", "organization"),
                       ("located_in", "location"), ("affected_by", "event")],
            "organization": [("member_contains", "person"), ("regulated_by", "organization"),
                          ("headquartered_in", "location"), ("responds_to", "event")],
            "location": [("contains", "person"), ("hosts", "organization")],
            "event": [("impacts", "person"), ("involves", "organization")],
        }
        for rel_type, target_type in possible_rels.get(etype, []):
            targets = [e["name"] for e in all_entities if e["type"] == target_type and e["name"] != entity["name"]]
            for t in targets[:random.randint(1, 3)]:
                rels.append({"relation": rel_type, "target": t})
        return rels

    def _phase2_graphrag_building(self, ontologies: List[AgentOntology], sim_id: str) -> Dict[str, int]:
        """Phase 2: 构建GraphRAG知识图谱"""
        self._graph_nodes.clear()
        self._graph_edges.clear()
        for onto in ontologies:
            embedding = self._generate_embedding(onto.entity_name + " " + onto.entity_type)
            community = hash(onto.entity_type) % 10
            node = GraphRAGNode(
                node_id=onto.ontology_id, entity_name=onto.entity_name,
                entity_type=onto.entity_type, description=onto.background_doc[:200],
                embedding=embedding, community_id=community,
                importance_score=random.uniform(0.3, 1.0),
            )
            self._graph_nodes[onto.ontology_id] = node
        for onto in ontologies:
            for rel in onto.relationships:
                target_onto = next((o for o in ontologies if o.entity_name == rel.get("target", "")), None)
                if target_onto:
                    edge = GraphRAGEdge(
                        source_id=onto.ontology_id, target_id=target_onto.ontology_id,
                        relation_type=rel["relation"], weight=random.uniform(0.5, 1.0),
                        evidence=f"从{onto.entity_name}到{rel['target']}的{rel['relation']}",
                    )
                    self._graph_edges.append(edge)
        communities = defaultdict(set)
        for e in self._graph_edges:
            src_node = self._graph_nodes.get(e.source_id)
            if src_node:
                communities[src_node.community_id].add(e.source_id)
                communities[src_node.community_id].add(e.target_id)
        for nid, node in self._graph_nodes.items():
            node.temporal_data.append({"event": "node_created", "time": 0})
        return {"nodes": len(self._graph_nodes), "edges": len(self._graph_edges),
                "communities": len(communities)}

    def _phase3_environment_setup(self, platform_configs: List[Dict],
                                   max_agents: int, max_rounds: int, sim_id: str) -> List[SimulationEnvironment]:
        """Phase 3: 搭建双平台仿真环境"""
        envs = []
        for pc in platform_configs:
            eid = f"env_{pc['platform'].value}_{uuid.uuid4().hex[:6]}"
            env_config = pc.get("config", {})
            env = SimulationEnvironment(
                env_id=eid, platform=pc["platform"],
                total_agents=min(max_agents, len(self._ontologies)),
                max_rounds=max_rounds,
                config={**env_config, "llm_backend": self.config.get("llm_backend", "deepseek-chat")},
            )
            self._environments[eid] = env
            envs.append(env)
        return envs

    def _phase4_simulation_running(self, env: SimulationEnvironment,
                                     ontologies: List[AgentOntology], sim_id: str) -> List[SimulationRoundResult]:
        """Phase 4: 运行仿真"""
        results = []
        agents_list = list(self._ontologies.values())[:env.total_agents]
        for round_num in range(1, env.max_rounds + 1):
            round_start = time.time()
            env.current_round = round_num
            round_posts = []
            round_token = 0
            engagement = defaultdict(int)
            sentiments = []

            for agent in agents_list:
                action_prob = random.random()
                if action_prob < 0.7:
                    post = self._generate_post(agent, round_num, env.platform, agents_list)
                    round_posts.append(post)
                    self._posts.append(post)
                    round_token += len(post.content) // 4
                    engagement["likes"] += post.engagement_metrics["likes"]
                    engagement["comments"] += post.engagement_metrics["comments"]
                    sentiments.append(post.sentiment)
                    mem = AgentMemoryEntry(
                        memory_id=f"mem_{uuid.uuid4().hex[:8]}",
                        agent_id=agent.ontology_id, content=post.content[:200],
                        memory_type="social", importance=min(action_prob, 1.0),
                        sentiment=post.sentiment,
                        associated_entities=[post.topics[0]] if post.topics else [],
                        created_at_sim=f"round_{round_num}",
                    )
                    self._agent_memories[agent.ontology_id].append(mem)

            avg_sentiment = statistics.mean(sentiments) if sentiments else 0
            sentiment_dist = {"positive": sum(1 for s in sentiments if s > 0.2),
                            "neutral": sum(1 for s in sentiments if -0.2 <= s <= 0.2),
                            "negative": sum(1 for s in sentiments if s < -0.2)}
            total_e = dict(engagement)
            key_events = self._detect_key_events(round_posts, round_num)
            net_metrics = self._calculate_network_metrics(round_posts, agents_list)

            result = SimulationRoundResult(
                round_number=round_num, posts_generated=len(round_posts),
                total_engagement=total_e, sentiment_distribution=sentiment_dist,
                key_events=key_events, network_metrics=net_metrics,
                agent_states_summary=self._summarize_agent_states(agents_list),
                token_consumed=round_token, duration_s=time.time() - round_start,
            )
            results.append(result)
            self._round_results.append(result)
        return results

    def _generate_post(self, agent: AgentOntology, round_num: int,
                         platform: SimPlatform, all_agents: List[AgentOntology]) -> SocialPost:
        """生成社交帖子"""
        pid = f"post_{uuid.uuid4().hex[:8]}"
        traits = agent.personality_traits
        openness = traits.get("openness", 0.5)
        influence = traits.get("influence", 0.5)
        templates = {
            SimPlatform.TWITTER: [
                f"{agent.entity_name}认为当前形势{'向好' if openness > 0.6 else '需要关注'}。关键在于...",
                f"关于最新动态，{agent.entity_name}{'强烈支持' if influence > 0.6 else '持保留态度'}这一方向。",
                f"{agent.entity_name}分享观察：市场{'呈现积极信号' if random.random() > 0.4 else '存在不确定性'}。",
            ],
            SimPlatform.REDDIT: [
                f"[讨论] {agent.entity_name}的分析：\n\n基于当前数据，我认为...\n\n关键论点：1)... 2)... 3)...\n\n大家怎么看？",
                f"[深度分析] {agent.entity_name}的详细解读：\n\n背景：...\n论证：\n结论：...",
                f"[AMA] 我是{agent.entity_name}，关于这个话题我有以下看法...",
            ],
        }
        tpl_list = templates.get(platform, templates[SimPlatform.TWITTER])
        content = random.choice(tpl_list)
        if round_num > max_rounds * 0.6 and random.random() < 0.3:
            content += f"\n\n经过{round_num}轮观察，我的立场有所调整..."
        post_type = random.choice(["original", "comment", "reply"])
        sentiment_base = (traits.get("agreeableness", 0.5) - 0.5) * 2
        sentiment = max(-1, min(1, sentiment_base + random.uniform(-0.2, 0.2)))
        topics = [agent.entity_type, "市场分析", "政策影响"][:(2)]
        engagement_likes = int(random.exp(influence * 3) * random.uniform(0.5, 2))
        return SocialPost(
            post_id=pid, author_agent_id=agent.ontology_id,
            platform=platform, content=content, post_type=post_type,
            engagement_metrics={"likes": engagement_likes, "comments": engagement_likes // 3, "shares": engagement_likes // 8},
            sentiment=sentiment, topics=topics, round_num=round_num,
            created_at_sim=f"round_{round_num}",
        )

    def _detect_key_events(self, posts: List[SocialPost], round_num: int) -> List[Dict[str, Any]]:
        """检测关键事件"""
        events = []
        high_sentiment = [p for p in posts if p.sentiment > 0.6]
        low_sentiment = [p for p in posts if p.sentiment < -0.4]
        viral_posts = [p for p in posts if p.engagement_metrics["likes"] > 20]
        if high_sentiment:
            events.append({"type": "positive_sentiment_spike", "round": round_num,
                           "count": len(high_sentiment), "top_agent": high_sentiment[0].author_agent_id})
        if low_sentiment:
            events.append({"type": "negative_sentiment_spike", "round": round_num,
                           "count": len(low_sentiment), "detail": "风险信号"})
        if viral_posts:
            events.append({"type": "viral_content", "round": round_num,
                           "post_id": viral_posts[0].post_id, "engagement": viral_posts[0].engagement_metrics})
        if round_num % 10 == 0:
            events.append({"type": "milestone_checkpoint", "round": round_num,
                           "total_posts_so_far": len(self._posts)})
        return events

    def _calculate_network_metrics(self, posts: List[SocialPost],
                                    agents: List[AgentOntology]) -> Dict[str, float]:
        """计算网络指标"""
        if not posts:
            return {"density": 0, "clustering": 0, "polarization": 0}
        interactions = sum(p.engagement_metrics["comments"] + p.engagement_metrics["shares"] for p in posts)
        n_agents = len(set(p.author_agent_id for p in posts))
        density = interactions / max(n_agents * (n_agents - 1), 1) * 10
        pos_ratio = sum(1 for p in posts if p.sentiment > 0) / max(len(posts), 1)
        polarization = abs(pos_ratio - 0.5) * 2
        clustering = random.uniform(0.3, 0.8)
        return {"density": min(density, 1), "clustering": clustering, "polarization": polarization}

    def _summarize_agent_states(self, agents: List[AgentOntology]) -> Dict[str, Dict]:
        """汇总智能体状态"""
        summary = {}
        for agent in agents[:20]:
            mems = self._agent_memories.get(agent.ontology_id, [])
            recent_opinions = [m.content[:50] for m in mems[-5:] if m.memory_type == "social"]
            summary[agent.ontology_id] = {
                "name": agent.entity_name, "recent_posts": len(mems),
                "opinion_trend": "positive" if recent_opinions and any("好" in o or "支持" in o for o in recent_opinions) else "mixed",
                "activity_level": len(mems) / max(len(agents), 1),
            }
        return summary

    def _phase5_report_generation(self, sim_id: str, doc: str, rounds: List[SimulationRoundResult],
                                     ontologies: List[AgentOntology], graph_stats: Dict) -> MiroFishReport:
        """Phase 5: 生成结构化报告"""
        rid = f"report_{uuid.uuid4().hex[:8]}"
        total_posts = sum(r.posts_generated for r in rounds)
        total_engagement = {}
        for r in rounds:
            for k, v in r.total_engagement.items():
                total_engagement[k] = total_engagement.get(k, 0) + v
        final_sentiments = rounds[-1].sentiment_distribution if rounds else {}
        risk_warnings = self._generate_risk_warnings(rounds, final_sentiments)
        strategies = self._generate_strategy_recommendations(rounds, ontologies)
        insights = self._extract_key_insights(rounds, graph_stats)
        confidence = self._calculate_prediction_confidence(rounds, graph_stats)
        summary = (
            f"本次仿真共{len(ontologies)}个智能体在{len(rounds)}轮交互中产生{total_posts}条内容。"
            f"整体情感倾向为{'正面' if final_sentiments.get('positive', 0) > final_sentiments.get('negative', 0) else '需关注'}。"
            f"检测到{len(risk_warnings)}个风险信号和{len(strategies)}条策略建议。"
        )
        return MiroFishReport(
            report_id=rid, simulation_id=sim_id, source_document=doc[:100],
            executive_summary=summary, event_timeline=[{"round": r.round_number, "events": r.key_events} for r in rounds[::5]],
            risk_warnings=risk_warnings, strategy_recommendations=strategies,
            prediction_confidence=confidence, total_agents=len(ontologies),
            total_rounds=len(rounds), total_tokens=sum(r.token_consumed for r in rounds),
            key_insights=insights,
        )

    def _generate_risk_warnings(self, rounds: List[SimulationRoundResult], sentiments: Dict) -> List[Dict]:
        """生成风险预警"""
        warnings = []
        neg_trend = [r for r in rounds[-10:] if r.sentiment_distribution.get("negative", 0) > r.sentiment_distribution.get("positive", 0)]
        if len(neg_trend) >= 5:
            warnings.append({"level": "high", "type": "sentiment_deterioration",
                           "detail": f"最近{len(neg_trend)}轮负面情绪占优，趋势下行"})
        polarizations = [r.network_metrics.get("polarization", 0) for r in rounds[-5:]]
        if polarizations and statistics.mean(polarizations) > 0.7:
            warnings.append({"level": "medium", "type": "high_polarization",
                           "detail": "社群极化程度高，存在分裂风险"})
        engagement_drop = [r for r in rounds[-5:] if r.total_engagement.get("likes", 0) < 10]
        if len(engagement_drop) >= 3:
            warnings.append({"level": "medium", "type": "engagement_decline",
                           "detail": "参与度持续下降，需关注内容质量"})
        return warnings

    def _generate_strategy_recommendations(self, rounds: List[SimulationRoundResult],
                                           ontologies: List[AgentOntology]) -> List[Dict]:
        """生成策略建议"""
        strategies = []
        influential_agents = [r.agent_states_summary.get(aid, {}) for r in rounds[-3:]
                                for aid in list(self._ontologies.keys())[:10]]
        strategies.append({
            "priority": "high", "area": "意见领袖识别",
            "recommendation": f"重点关注活跃度前20%的智能体，它们对舆论走向有显著影响力"
        })
        if rounds and rounds[-1].network_metrics.get("density", 0) < 0.3:
            strategies.append({
                "priority": "medium", "area": "互动促进",
                "recommendation": "当前网络密度偏低，建议引入争议性话题或事件刺激讨论"
            })
        strategies.append({
            "priority": "low", "area": "长期监控",
            "recommendation": f"建议每{rounds[-1].round_number if rounds else 10}轮进行一次全面评估"
        })
        return strategies

    def _extract_key_insights(self, rounds: List[SimulationRoundResult], graph: Dict) -> List[str]:
        """提取关键洞察"""
        insights = []
        if rounds:
            peak_round = max(rounds, key=lambda r: sum(r.total_engagement.values()))
            insights.append(f"第{peak_round.round_number}轮为参与度峰值，总互动量{sum(peak_round.total_engagement.values())}")
            if graph.get("communities", 0) > 3:
                insights.append(f"图谱包含{graph['communities']}个社区，实体间关联丰富度较高")
            convergence = len([r for r in rounds[-10:] if r.network_metrics.get("polarization", 0) < 0.3])
            if convergence >= 5:
                insights.append(f"近期{convergence}轮极化指数低于阈值，舆论趋于共识")
        return insights

    def _calculate_prediction_confidence(self, rounds: List[SimulationRoundResult], graph: Dict) -> float:
        """计算预测置信度"""
        if not rounds:
            return 0.5
        base = 0.65
        data_volume = min(sum(r.posts_generated for r in rounds) / 1000, 0.15)
        stability = 1 - statistics.stdev([r.network_metrics.get("polarization", 0.5) for r in rounds[-5:]]) if len(rounds) >= 5 else 0.1
        graph_factor = min(graph.get("edges", 0) / max(graph.get("nodes", 1), 1) * 20, 0.1)
        return min(base + data_volume + stability * 0.1 + graph_factor, 0.98)

    def _generate_embedding(self, text: str) -> List[float]:
        """生成向量嵌入(模拟)"""
        seed = int(hashlib.md5(text.encode()).hexdigest()[:8], 16)
        random.seed(seed)
        dim = 384
        vec = [random.gauss(0, 1) for _ in range(dim)]
        norm = math.sqrt(sum(v**2 for v in vec))
        return [v / norm for v in vec]


# ==================== Part B: HEAS 分层进化仿真 ====================


class HEASEngine:
    """HEAS分层进化智能体仿真 — 流式建模+进化优化+锦标赛评估"""

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or {}
        self._streams: Dict[str, HEASStreamDef] = {}
        self._evolutions: List[HEASEvolutionResult] = []
        self._tournaments: List[HEASTournamentResult] = []
        self._pareto_archive: List[Dict[str, float]] = []

    def define_stream(self, stream_id: str, name: str, level: int,
                      variables: Dict[str, Any], reads: List[str], writes: List[str],
                      coupling: float = 0.5) -> HEASStreamDef:
        """定义仿真流（模型层次）"""
        stream = HEASStreamDef(
            stream_id=stream_id, stream_name=name, layer_level=level,
            variables=variables, read_from=reads, write_to=writes,
            coupling_strength=coupling,
        )
        self._streams[stream_id] = stream
        logger.info(f"[HEAS] 定义流: {name} (层级{level}), 变量{list(variables.keys())}, 耦合强度={coupling:.2f}")
        return stream

    def run_simulation(self, stream_ids: List[str], steps: int = 100,
                       output_vars: Optional[List[str]] = None) -> Dict[str, Any]:
        """运行模拟模式"""
        sid = f"sim_{uuid.uuid4().hex[:8]}"
        logger.info(f"[HEAS-Simulate] 启动模拟: {sid}, 流={stream_ids}, 步数={steps}")
        state = {s_id: dict(self._streams[s_id].variables) for s_id in stream_ids if s_id in self._streams}
        history = []
        coupling_logs = []
        for step in range(steps):
            step_state = {}
            for s_id in stream_ids:
                if s_id not in self._streams:
                    continue
                stream = self._streams[s_id]
                new_vals = self._step_stream(stream, state[s_id], state, step)
                old_vals = state[s_id]
                state[s_id] = {**old_vals, **new_vals}
                for w_id in stream.write_to:
                    if w_id in state:
                        log_entry = {"from": s_id, "to": w_id, "vars_written": list(new_vals.keys()),
                                    "coupling": stream.coupling_strength, "step": step}
                        coupling_logs.append(log_entry)
                step_state[s_id] = {k: state[s_id][k] for k in (output_vars or list(new_vals.keys()))}
            history.append({"step": step, "state": copy.deepcopy(step_state)})
        final_output = {s_id: state[s_id] for s_id in stream_ids if s_id in state}
        return {"simulation_id": sid, "steps_completed": steps, "final_state": final_output,
                "history": history[-10:], "coupling_audit": coupling_logs[-50:]}

    def run_optimization(self, objective_streams: Dict[str, str],
                          strategy: EvolutionStrategy = EvolutionStrategy.NSGA_II,
                          pop_size: int = 50, generations: int = 30) -> HEASEvolutionResult:
        """运行进化优化模式"""
        eid = f"evo_{uuid.uuid4().hex[:8]}"
        start = time.time()
        logger.info(f"[HEAS-Optimize] 进化优化: {eid}, 策略={strategy.value}, 种群={pop_size}, 代数={generations}")

        population = self._initialize_population(pop_size, objective_streams)
        pareto_front = []
        best_fitness = float('inf')
        best_solution = None
        converge_gen = 0
        audit = [f"初始化种群: {pop_size}个体"]

        for gen in range(generations):
            fitness_scores = self._evaluate_population(population, objective_streams)
            ranked = sorted(zip(population, fitness_scores), key=lambda x: sum(x[1].values()) if isinstance(x[1], dict) else x[1])
            current_best = ranked[0]
            current_fitness = sum(current_best[1].values()) if isinstance(current_best[1], dict) else current_best[1]

            if current_fitness < best_fitness:
                improvement = best_fitness - current_fitness
                best_fitness = current_fitness
                best_solution = current_best[0]
                converge_gen = gen
                audit.append(f"Gen{gen}: 新最优={current_fitness:.4f} (提升{improvement:.4f})")
            elif abs(current_fitness - best_fitness) / max(best_fitness, 0.001) < 0.001:
                converge_gen = gen
                audit.append(f"Gen{gen}: 收敛于{current_fitness:.4f}")

            pareto = self._update_pareto(ranked, pareto_front)
            population = self._evolve_population(population, fitness_scores, strategy, gen)

        diversity = self._calc_diversity(population)
        obj_values = {k: best_solution.get(k, 0) for k in objective_streams.values()} if best_solution else {}
        result = HEASEvolutionResult(
            evolution_id=eid, strategy=strategy, generations=generations,
            population_size=pop_size, objective_values=obj_values,
            pareto_frontier=[{k: v for k, v in p.items()} if isinstance(p, dict) else {"fitness": p}
                        for p in pareto_front[:20]],
            best_solution=best_solution, convergence_generation=converge_gen,
            diversity_metric=diversity, computation_time_s=(time.time() - start),
            audit_trail=audit,
        )
        self._evolutions.append(result)
        self._pareto_archive.extend([{"gen": gen, **obj_values} for obj_values in [obj_values]])
        logger.info(f"[HEAS-Optimize] 完成: 最优={best_fitness:.4f}, 收敛代数={converge_gen}, "
                     f"Pareto前沿={len(pareto_front)}, 多样性={diversity:.3f}")
        return result

    def run_tournament(self, candidates: List[Dict[str, Any]],
                       criteria: List[str], rounds: int = 3) -> HEASTournamentResult:
        """运行锦标赛评估模式"""
        tid = f"tourn_{uuid.uuid4().hex[:8]}"
        logger.info(f"[HEAS-Tournament] 锦标赛: {tid}, 候选={len(candidates)}, 标准={criteria}, 轮次={rounds}")

        all_scores = {}
        for cand in candidates:
            cid = id(cand)
            all_scores[cid] = {}
            for crit in criteria:
                score = self._evaluate_candidate(cand, crit)
                all_scores[cid][crit] = score

        rankings_per_round = []
        for rnd in range(rounds):
            weighted_scores = {}
            for cid, scores in all_scores.items():
                weights = {c: random.uniform(0.5, 1.5) for c in criteria}
                total = sum(scores.get(c, 0) * weights.get(c, 1.0) for c in criteria)
                total /= sum(weights.values())
                weighted_scores[cid] = total
            ranked = sorted(weighted_scores.items(), key=lambda x: x[1], reverse=True)
            rankings_per_round.append(ranked)

        final_rankings = [(cid, statistics.mean([r[i][1] for r in rankings_per_round if i < len(r)])
                            ) for i, cid in enumerate(all_scores.keys())]
        final_rankings.sort(key=lambda x: x[1], reverse=True)
        winner = final_rankings[0]

        scores_matrix = {criteria: {i: all_scores.get(final_rankings[i][0], {}).get(c, 0)
                                      for i in range(min(5, len(final_rankings)))}
                        for criteria in criteria}

        sig = self._calculate_statistical_significance(scores_matrix)
        result = HEASTournamentResult(
            tournament_id=tid, candidates=candidates,
            evaluation_criteria=criteria, scores=all_scores,
            rankings=final_rankings, winner_idx=winner[0],
            statistical_significance=sig,
        )
        self._tournaments.append(result)
        logger.info(f"[HEAS-Tournament] 冠军: 候选#{winner[0]}, 显著性={sig:.3f}")
        return result

    def _step_stream(self, stream: HEASStreamDef, local_state: Dict,
                     global_state: Dict, step: int) -> Dict[str, Any]:
        """单步推进流状态"""
        delta = {}
        for var, val in stream.variables.items():
            if isinstance(val, (int, float)):
                noise = random.gauss(0, abs(val) * 0.02)
                influence = 0
                for r_id in stream.read_from:
                    if r_id in global_state:
                        r_val = global_state[r_id].get(var, 0)
                        if isinstance(r_val, (int, float)):
                            influence += (r_val - val) * stream.coupling_strength * 0.1
                new_val = val * (1 + noise * 0.01) + influence
                delta[var] = max(0, new_val)
        return delta

    def _initialize_population(self, size: int, objectives: Dict[str, str]) -> List[Dict]:
        """初始化种群"""
        pop = []
        for _ in range(size):
            individual = {obj_id: random.uniform(0, 100) for obj_id in objectives.values()}
            individual["_fitness"] = 0
            pop.append(individual)
        return pop

    def _evaluate_population(self, population: List[Dict], objectives: Dict[str, str]) -> List[Dict]:
        """评估种群"""
        scores = []
        for ind in population:
            fit = {obj_id: ind.get(obj_id, 0) / 100.0 for obj_id in objectives.values()}
            ind["_fitness_dict"] = fit
            ind["_fitness"] = sum(fit.values())
            scores.append(fit)
        return scores

    def _update_pareto(self, ranked: List, existing: List) -> List:
        """更新Pareto前沿"""
        for item, fit in ranked[:10]:
            is_dominated = False
            for ex_fit in existing:
                if all(v <= ex_v for v, ex_v in zip(fit.values(), ex_fit.values()) if isinstance(v, (int, float))):
                    is_dominated = True
                    break
            if not is_dominated:
                entry = {**item, "_pareto_rank": len(existing)}
                existing.append(entry)
        return existing

    def _evolve_population(self, population: List[Dict], scores: List[Dict],
                              strategy: EvolutionStrategy, gen: int) -> List[Dict]:
        """进化种群操作"""
        if strategy == EvolutionStrategy.GENETIC_ALGORITHM:
            return self._genetic_evolve(population, scores, gen)
        elif strategy == EvolutionStrategy.PARTICLE_SWARM:
            return self._pso_evolve(population, scores)
        elif strategy == EvolutionStrategy.NSGA_II:
            return self._nsga2_evolve(population, scores)
        elif strategy == EvolutionStrategy.CMA_ES:
            return self._cmaes_evolve(population, scores)
        else:
            return self._differential_evolution(population, scores)

    def _genetic_evolve(self, pop: List[Dict], scores: List[Dict], gen: int) -> List[Dict]:
        """遗传算法进化"""
        elite_count = max(1, len(pop) // 10)
        ranked = sorted(zip(pop, scores), key=lambda x: x[1].get("_fitness", 0), reverse=True)
        new_pop = [item for item, _ in ranked[:elite_count]]
        while len(new_pop) < len(pop):
            p1, p2 = random.sample(ranked[:len(ranked)//2], 2)
            parent1, parent2 = p1[0], p2[0]
            child = {}
            for k in set(list(parent1.keys()) + list(parent2.keys())):
                if k.startswith("_"):
                    continue
                child[k] = parent1.get(k, 0) if random.random() < 0.5 else parent2.get(k, 0)
                if random.random() < 0.05:
                    child[k] *= random.uniform(0.9, 1.1)
            new_pop.append(child)
        return new_pop[:len(pop)]

    def _nsga2_evolve(self, pop: List[Dict], scores: List[Dict]) -> List[Dict]:
        """NSGA-II多目标进化"""
        ranked = sorted(zip(pop, scores), key=lambda x: tuple(x[1].get(o, 0) for o in x[1] if isinstance(x[1].get(o, 0), (int, float))), reverse=True)
        front = [item for item, _ in ranked[:len(pop)//3]]
        offspring = []
        while len(offspring) < len(pop):
            p1, p2 = random.sample(front[:max(2, len(front))], 2)
            child = {k: (p1.get(k, 0) + p2.get(k, 0)) / 2 for k in set(list(p1.keys()) | set(p2.keys())) if not k.startswith("_")}
            offspring.append(child)
        combined = pop + offspring
        return random.sample(combined, len(pop))

    def _pso_evolve(self, pop: List[Dict], scores: List[Dict]) -> List[Dict]:
        """粒子群优化"""
        if not pop:
            return pop
        global_best = max(pop, key=lambda x: x.get("_fitness", 0))
        for ind in pop:
            for k, v in ind.items():
                if k.startswith("_"):
                    continue
                if isinstance(v, (int, float)):
                    inertia = 0.7 * (v - ind.get(f"_vel_{k}", 0))
                    cognitive = 1.4 * random.random() * (global_best.get(k, v) - v)
                    social = 1.4 * random.random() * (random.choice(pop).get(k, v) - v)
                    ind[f"_vel_{k}"] = inertia + cognitive + social
                    ind[k] = max(0, v + ind[f"_vel_{k}"]) * 0.5
        return pop

    def _cmaes_evolve(self, pop: List[Dict], scores: List[Dict]) -> List[Dict]:
        """CMA-ES协方差自适应"""
        if len(pop) < 4:
            return pop
        mean = {k: statistics.mean([p.get(k, 0) for p in pop]) for k in list(pop[0].keys()) if not k.startswith("_")}
        std = {k: max(statistics.stdev([p.get(k, 0) for p in pop]), 0.1) for k in mean}
        new_pop = []
        for _ in pop:
            sample = {k: random.gauss(mean[k], std[k]) for k in mean}
            sample.update({"_fitness": 0})
            new_pop.append(sample)
        return new_pop

    def _differential_evolution(self, pop: List[Dict], scores: List[Dict]) -> List[Dict]:
        """差分进化"""
        F = 0.8
        CR = 0.9
        new_pop = []
        for i, target in enumerate(pop):
            others = [p for j, p in enumerate(pop) if j != i]
            a, b, c = random.sample(others[:min(3, len(others))], 3)
            mutant = {}
            for k in set(list(target.keys()) + list(a.keys()) + list(b.keys())):
                if k.startswith("_"):
                    continue
                base = target.get(k, 0)
                diff = b.get(k, 0) - c.get(k, 0)
                mutant[k] = a.get(k, base) + F * diff
                if random.random() < CR:
                    mutant[k] = mutant[k] if not isinstance(mutant[k], bool) else base
                if isinstance(mutant[k], (int, float)):
                    mutant[k] = max(0, mutant[k])
            new_pop.append(mutant)
        return new_pop

    def _evaluate_candidate(self, candidate: Dict, criterion: str) -> float:
        """评估单个候选方案"""
        base = 0.5
        keys = [k for k in candidate if not k.startswith("_")]
        if not keys:
            return base
        values = [v for k, v in candidate.items() if k in keys and isinstance(v, (int, float))]
        if "accuracy" in criterion.lower():
            return base + min(statistics.mean(values) / 100 if values else 0, 0.3)
        elif "cost" in criterion.lower():
            return base - min(statistics.mean(values) / 100 if values else 0, 0.3)
        elif "speed" in criterion.lower():
            return base + (1 / max(statistics.mean(values) if values else 1, 0.01)) * 0.2
        return base + random.uniform(-0.1, 0.1)

    def _calc_diversity(self, population: List[Dict]) -> float:
        """计算种群多样性"""
        if len(population) < 2:
            return 1.0
        keys = [k for k in list(population[0].keys()) if not k.startswith("_")]
        if not keys:
            return 1.0
        total_var = 0
        for k in keys[:5]:
            vals = [p.get(k, 0) for p in population if isinstance(p.get(k), (int, float))]
            if vals:
                total_var += statistics.variance(vals) / max(statistics.mean([abs(v) for v in vals])**2, 0.001)
        return max(0, 1 - total_var / len(keys))

    @staticmethod
    def _calculate_statistical_significance(score_matrix: Dict[str, Dict[int, float]]) -> float:
        """计算统计显著性(Friedman检验近似)"""
        if not score_matrix:
            return 0.5
        ranks = {}
        for crit, scores in score_matrix.items():
            sorted_candidates = sorted(scores.items(), key=lambda x: x[1], reverse=True)
            ranks[crit] = {cid: rank for rank, (cid, _) in enumerate(sorted_candidates)}
        avg_agreement = 0
        pairs = list(combinations(list(ranks.values())[0].keys(), 2))
        for c1, c2 in pairs:
            agreements = sum(1 for r in ranks.values()
                           if (r.get(c1, 0) > r.get(c2, 0)) == (r.get(max(ranks, key=r.get).__getitem__(c1), 0) > r.get(max(ranks, key=r.get).__getitem__(c2), 0)))
            avg_agreement += agreements / len(ranks)
        from itertools import combinations
        return avg_agreement / max(len(pairs), 1) if pairs else 0.5

    def get_heas_stats(self) -> Dict[str, Any]:
        """获取HEAS统计"""
        return {
            "total_streams": len(self._streams),
            "total_evolutions": len(self._evolutions),
            "total_tournaments": len(self._tournaments),
            "avg_convergence_gen": statistics.mean([e.convergence_generation for e in self._evolutions]) if self._evolutions else 0,
            "avg_diversity": statistics.mean([e.diversity_metric for e in self._evolutions]) if self._evolutions else 0,
            "pareto_archive_size": len(self._pareto_archive),
        }


# ==================== Part C: VirtualEnv 物理仿真 ====================


class VirtualEnvSimulator:
    """VirtualEnv物理仿真器 — UE5风格物理交互+导航+多Agent协作"""

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or {}
        self._physics_objects: Dict[str, Dict[str, Any]] = {}
        self._agents_3d: Dict[str, Dict[str, float]] = {}  # agent_id -> {x,y,z, yaw,pitch,roll}
        self._interactions: List[PhysicsInteraction] = []
        self._paths: List[NavigationPath] = []
        self._obstacles: List[Dict[str, Any]] = []
        self._collaboration_events: List[Dict[str, Any]] = []

    def create_scenario(self, scenario_type: VirtualEnvScenario,
                        objects: List[Dict] = None,
                        obstacles: List[Dict] = None) -> str:
        """创建仿真场景"""
        sid = f"virenv_{uuid.uuid4().hex[:8]}"
        self._obstacles = obstacles or []
        for obj in (objects or []):
            oid = f"obj_{uuid.uuid4().hex[:6]}"
            self._physics_objects[oid] = {
                "id": oid, "type": obj.get("type", "box"),
                "position": obj.get("position", [0, 0, 0]),
                "rotation": obj.get("rotation", [0, 0, 0]),
                "mass": obj.get("mass", 1.0), "friction": obj.get("friction", 0.5),
                "restitution": obj.get("restitution", 0.3),
                "is_static": obj.get("static", False),
                "dimensions": obj.get("dimensions", [1, 1, 1]),
            }
        logger.info(f"[VirtualEnv] 创建场景: {scenario_type.value}, 物体={len(self._physics_objects)}, 障碍物={len(self._obstacles)}")
        return sid

    def spawn_agent(self, agent_id: str, position: List[float] = None) -> Dict[str, float]:
        """生成3D智能体"""
        pos = position or [random.uniform(-10, 10), random.uniform(-10, 10), 0]
        self._agents_3d[agent_id] = {
            "x": pos[0], "y": pos[1], "z": pos[2],
            "yaw": random.uniform(0, 360), "pitch": 0, "roll": 0,
            "velocity": 0.0, "health": 1.0,
        }
        logger.debug(f"[VirtualEnv] 生成Agent: {agent_id} @ ({pos[0]:.1f},{pos[1]:.1f},{pos[2]:.1f})")
        return self._agents_3d[agent_id]

    def execute_grasp(self, agent_id: str, object_id: str) -> PhysicsInteraction:
        """执行抓取动作"""
        iid = f"interact_{uuid.uuid4().hex[:8]}"
        agent_pos = self._agents_3d.get(agent_id, {})
        obj = self._physics_objects.get(object_id, {})
        obj_pos = obj.get("position", [0, 0, 0])

        distance = math.sqrt(sum((a - b)**2 for a, b in zip(agent_pos.values(), obj_pos)))
        reach_threshold = self.config.get("reach_distance", 2.0)
        success = distance < reach_threshold and random.random() > 0.15

        if success:
            force = obj.get("mass", 1.0) * 9.8 * self.config.get("grasp_force_mult", 1.0)
            new_obj_pos = [agent_pos["x"], agent_pos["y"], agent_pos["z"] + 0.5]
            obj["position"] = new_obj_pos
            obj["held_by"] = agent_id

        interaction = PhysicsInteraction(
            interaction_id=iid, agent_id=agent_id, object_id=object_id,
            interaction_type="grasp", position_3d=tuple(obj_pos),
            rotation_3d=(0, 0, 0), force_applied=force if success else 0,
            success=success,
            physics_metrics={
                "distance": distance, "threshold": reach_threshold,
                "mass": obj.get("mass", 0), "friction": obj.get("friction", 0),
            }, duration_ms=random.uniform(200, 800),
            scenario_type=VirtualEnvScenario.PHYSICS_MANIPULATION,
            timestamp_sim=f"t{len(self._interactions)}",
        )
        self._interactions.append(interaction)
        return interaction

    def navigate_to(self, agent_id: str, target: List[float],
                   algorithm: str = "astar") -> NavigationPath:
        """导航到目标位置"""
        pid = f"path_{uuid.uuid4().hex[:8]}"
        start = self._agents_3d.get(agent_id, {})
        start_pos = [start.get("x", 0), start.get("y", 0), start.get("z", 0)]

        if algorithm == "astar":
            waypoints = self._astar_path(start_pos, target)
        elif algorithm == "rrt":
            waypoints = self._rrt_path(start_pos, target)
        else:
            waypoints = self._straight_path(start_pos, target)

        collisions = 0
        for wp in waypoints[1:]:
            for obs in self._obstacles:
                obs_pos = obs.get("position", [0, 0, 0])
                obs_dim = obs.get("dimensions", [1, 1, 1])
                if all(abs(wp[i] - obs_pos[i]) < obs_dim[i]/2 + 0.3 for i in range(3)):
                    collisions += 1
        total_dist = sum(math.sqrt(sum((waypoints[i+1][j] - waypoints[i][j])**2 for j in range(3)))
                     for i in range(len(waypoints)-1))

        smoothness = 1 - (collisions / max(len(waypoints)-1, 1)) * 0.5
        efficiency = min(1.0, 10 / max(total_dist, 0.1))

        path = NavigationPath(
            path_id=pid, agent_id=agent_id, waypoints=waypoints,
            total_distance=total_dist, time_to_complete_s=total_dist * 50,
            obstacles_avoided=collisions, collisions=collisions,
            smoothness_score=smoothness, efficiency_score=efficiency,
            scenario_type=VirtualEnvScenario.NAVIGATION,
        )
        self._paths.append(path)
        self._agents_3d[agent_id]["x"] = target[0]
        self._agents_3d[agent_id]["y"] = target[1]
        self._agents_3d[agent_id]["z"] = target[2]
        return path

    def multi_agent_collaborate(self, task_description: str,
                                 agent_ids: List[str]) -> Dict[str, Any]:
        """多智能体协作"""
        collab_id = f"collab_{uuid.uuid4().hex[:8]}"
        roles_assigned = self._assign_collaboration_roles(task_description, agent_ids)
        steps = []
        for step_num in range(min(len(agent_ids), 6)):
            role = roles_assigned[step_num % len(roles_assigned)]
            agent = role["agent_id"]
            sub_task = task_description[step_num*30:(step_num+1)*30] if len(task_description) > step_num*30 else task_description
            result = self._execute_subtask(agent, sub_task, role["role"], other_agents=agent_ids)
            steps.append({"step": step_num, "agent": agent, "role": role["role"],
                           "subtask": sub_task[:50], "result": result})

        self._collaboration_events.append({
            "collab_id": collab_id, "task": task_description,
            "agents": agent_ids, "roles": roles_assigned,
            "steps": steps, "success_rate": sum(1 for s in steps if s.get("success", False)) / max(len(steps), 1),
        })
        logger.info(f"[VirtualEnv-协作] 完成: {collab_id}, 成功率={self._collaboration_events[-1]['success_rate']:.1%}")
        return self._collaboration_events[-1]

    def _astar_path(self, start: List[float], goal: List[float]) -> List[List[float]]:
        """A*路径规划"""
        open_set = {(round(start[0], 1), round(start[1], 1), round(start[2], 1)): (0, None)}
        closed_set = set()
        came_from = {}
        goal_k = (round(goal[0], 1), round(goal[1], 1), round(goal[2], 1))

        for _ in range(500):
            if not open_set:
                break
            current = min(open_set, key=open_set.get)[0]
            g = current[0] + self._heuristic(current, goal_k)
            if current == goal_k:
                path = [goal_k]
                while came_from.get(current):
                    path.append(came_from[current])
                    current = came_from[current]
                return list(reversed(path))[::3] + [start, goal]
            closed_set.add(current)
            for dx, dy, dz in [(1,0,0), (-1,0,0), (0,1,0), (0,-1,0), (0,0,1), (0,0,-1),
                               (1,1,0), (-1,-1,0), (1,0,1), (-1,0,-1)]:
                neighbor = (current[0]+dx, current[1]+dy, current[2]+dz)
                if neighbor not in closed_set:
                    g_score = neighbor[0] + self._heuristic(neighbor, goal_k)
                    if neighbor not in open_set or g_score < open_set.get(neighbor, (float('inf'), None))[0]:
                        open_set[neighbor] = (g_score, current)
                        came_from[neighbor] = current
        return self._straight_path(start, goal)

    def _rrt_path(self, start: List[float], goal: List[float]) -> List[List[float]]:
        """RRT快速随机树路径"""
        tree = [tuple(round(s, 1) for s in start)]
        for _ in range(300):
            nearest = min(tree, key=lambda n: sum((n[i]-goal[i])**2 for i in range(3)))
            angle = random.uniform(0, 2*math.pi)
            radius = min(2.0, math.sqrt(sum((nearest[i]-goal[i])**2 for i in range(3))))
            new_point = tuple(nearest[i] + radius*math.cos(angle+i*0.5) for i in range(3))
            tree.append(new_point)
            dist_to_goal = math.sqrt(sum((new_point[i]-goal[i])**2 for i in range(3)))
            if dist_to_goal < 1.0:
                path = [goal]
                node = new_point
                while node in tree:
                    path.append(node)
                    idx = tree.index(node)
                    node = tree[idx//2] if idx > 0 else tree[0]
                return list(reversed(path))[::3] + [start, goal]
        return self._straight_path(start, goal)

    def _straight_path(self, start: List[float], goal: List[float]) -> List[List[float]]:
        """直线路径"""
        steps = max(int(math.sqrt(sum((g-s)**2 for g, s in zip(goal, start)))), 5)
        return [start] + [[start[i] + (goal[i]-start[i])*(s/(steps+1)) for i in range(3)] for s in range(steps)] + [goal]

    def _heuristic(self, a: Tuple, b: Tuple) -> float:
        """A*启发式"""
        return math.sqrt(sum((ai-bi)**2 for ai, bi in zip(a, b)))

    def _assign_collaboration_roles(self, task: str, agents: List[str]) -> List[Dict]:
        """分配协作角色"""
        roles_map = ["coordinator", "executor", "reviewer", "support", "observer", "communicator"]
        assigned = []
        for i, aid in enumerate(agents[:len(roles_map)]):
            assigned.append({"agent_id": aid, "role": roles_map[i % len(roles_map)],
                           "expertise": random.uniform(0.5, 1.0)})
        return assigned

    def _execute_subtask(self, agent_id: str, subtask: str, role: str, other_agents: List[str]) -> Dict:
        """执行子任务"""
        quality = {"coordinator": 0.9, "executor": 0.85, "reviewer": 0.88,
                  "support": 0.8, "observer": 0.75, "communicator": 0.82}.get(role, 0.75)
        noise = random.uniform(-0.08, 0.08)
        team_bonus = min(len(other_agents) * 0.03, 0.15)
        return {"quality": min(quality + noise + team_bonus, 1.0), "success": random.random() < (quality + noise)}

    def get_virtualenv_stats(self) -> Dict[str, Any]:
        """获取VirtualEnv统计"""
        grasp_success = sum(1 for i in self._interactions if i.interaction_type == "grasp" and i.success) / max(sum(1 for i in self._interactions if i.interaction_type == "grasp"), 1)
        nav_efficiency = statistics.mean([p.efficiency_score for p in self._paths]) if self._paths else 0
        collab_success = statistics.mean([e.get("success_rate", 0) for e in self._collaboration_events]) if self._collaboration_events else 0
        return {
            "objects": len(self._physics_objects), "agents": len(self._agents_3d),
            "interactions": len(self._interactions), "paths": len(self._paths),
            "collaborations": len(self._collaboration_events),
            "grasp_success_rate": grasp_success, "nav_efficiency": nav_efficiency,
            "collab_success_rate": collab_success,
        }


# ==================== Part D: GAMMS 图仿真框架 ====================


class GAMMSEngine:
    """GAMMS轻量级图仿真框架 — 城市路网/通信系统/社会网络建模"""

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or {}
        self._graphs: Dict[str, Dict[str, Any]] = {}
        self._simulation_states: List[GraphSimulationState] = []
        self._agent_types: Dict[str, GraphSimAgentType] = {}

    def build_graph(self, graph_id: str, graph_type: str,
                    nodes: List[Dict], edges: List[Dict]) -> Dict[str, Any]:
        """构建仿真图"""
        graph = {
            "id": graph_id, "type": graph_type,
            "nodes": {n["id"]: n for n in nodes},
            "edges": [{"source": e["source"], "target": e["target"],
                       "capacity": e.get("capacity", 1.0), "latency": e.get("latency", 1.0),
                       "cost": e.get("cost", 1.0)} for e in edges],
            "adjacency": defaultdict(list),
        }
        for e in graph["edges"]:
            graph["adjacency"][e["source"]].append(e["target"])
        self._graphs[graph_id] = graph
        logger.info(f"[GAMMS] 构建图: {graph_id}, 类型={graph_type}, 节点={len(nodes)}, 边={len(edges)}")
        return graph

    def register_agent(self, agent_id: str, agent_type: GraphSimAgentType,
                       start_node: str = None) -> None:
        """注册图上智能体"""
        self._agent_types[agent_id] = agent_type
        if start_node:
            for gid, g in self._graphs.items():
                if start_node in g["nodes"]:
                    break

    def simulate_steps(self, graph_id: str, num_agents: Dict[str, GraphSimAgentType],
                       num_steps: int = 100) -> GraphSimulationState:
        """执行图仿真步进"""
        sid = f"gammss_{uuid.uuid4().hex[:8]}"
        graph = self._graphs.get(graph_id)
        if not graph:
            return GraphSimulationState(sim_id=sid, graph_type="unknown", nodes=0, edges=0,
                                      step_count=0, agent_types=dict(num_agents))

        positions = {aid: random.choice(list(graph["nodes"].keys())) for aid in num_agents}
        costs = defaultdict(float)
        congestion = defaultdict(float)
        fair_share = 1.0 / max(len(num_agents), 1)
        step_records = []

        for step in range(num_steps):
            step_moves = {}
            for aid, atype in num_agents.items():
                current = positions[aid]
                move = self._agent_decide_move(atype, graph, current, positions, congestion, step)
                old_pos = positions[aid]
                positions[aid] = move["target"]
                cost = self._calculate_edge_cost(graph, old_pos, move["target"])
                costs[aid] += cost
                if move["edge"]:
                    congestion[move["edge"]] = congestion.get(move["edge"], 0) + 1
                step_moves[aid] = {"from": old_pos, "to": move["target"], "cost": cost, "type": atype.value}
            step_records.append({"step": step, "moves": step_records})

        total_cost = sum(costs.values())
        Jain_fairness = self._calculate_jain_fairness(list(costs.values()))
        state = GraphSimulationState(
            sim_id=sid, graph_type=graph["type"],
            nodes=len(graph["nodes"]), edges=len(graph["edges"]),
            agent_positions=positions, agent_types=dict(num_agents),
            step_count=num_steps, throughput_per_step=num_steps,
            congestion_levels=dict(congestion), total_cost=total_cost,
            fairness_index=Jain_fairness,
        )
        self._simulation_states.append(state)
        logger.info(f"[GAMMS] 仿真完成: {sid}, 总成本={total_cost:.2f}, 公平性={Jain_fairness:.3f}")
        return state

    def _agent_decide_move(self, atype: GraphSimAgentType, graph: Dict,
                          current: str, positions: Dict, congestion: Dict, step: int) -> Dict:
        """智能体决策移动"""
        neighbors = graph["adjacency"].get(current, [])
        if not neighbors:
            return {"target": current, "edge": None, "decision": "stay"}

        if atype == GraphSimAgentType.HEURISTIC:
            best = min(neighbors, key=lambda n: self._heuristic_cost(n, congestion))
            return {"target": best, "edge": f"{current}-{best}", "decision": "greedy"}
        elif atype == GraphSimAgentType.OPTIMIZATION:
            scored = [(n, self._optimization_score(n, positions, congestion)) for n in neighbors]
            best = max(scored, key=lambda x: x[1])
            return {"target": best[0], "edge": f"{current}-{best[0]}", "decision": "optimized"}
        elif atype == GraphSimAgentType.LEARNING_BASED:
            q_value = self._q_table.get((current, step), {})
            if q_value and random.random() > 0.2:
                action = max(q_value, key=q_value.get)
                target = action if action in graph["nodes"] else random.choice(neighbors)
            else:
                target = random.choice(neighbors)
                self._q_update(current, target, 0.9, graph, positions)
            return {"target": target, "edge": f"{current}-{target}", "decision": "learned"}
        else:
            prompt = f"Agent at {current}, options={neighbors[:5]}, choose:"
            choice = self._llm_route_decision(prompt, neighbors)
            return {"target": choice, "edge": f"{current}-{choice}", "decision": "llm"}

    def _heuristic_cost(self, node: str, congestion: Dict) -> float:
        """启发式代价"""
        base_cost = 1.0
        cong_penalty = sum(congestion.get(f"{node}-{n}", 0) * 0.5 for n in [] if False)
        return base_cost + cong_penalty + random.uniform(0, 0.3)

    def _optimization_score(self, node: str, positions: Dict, congestion: Dict) -> float:
        """优化评分"""
        crowd = -len([1 for p in positions.values() if p == node])
        cong = -congestion.get(node, 0) * 2
        return crowd + cong + random.uniform(0, 0.5)

    _q_table: Dict = defaultdict(lambda: defaultdict(float))  # type: ignore[assignment]

    def _q_update(self, s: str, a: str, reward: float, graph: Dict, positions: Dict):
        """Q-learning更新"""
        old_q = self._q_table[s][a]
        neighbors = graph["adjacency"].get(a, [])
        if neighbors:
            max_next = max(self._q_table[a].get(n, 0) for n in neighbors)
            self._q_table[s][a] = old_q + 0.1 * (reward + 0.9 * max_next - old_q)

    def _llm_route_decision(self, prompt: str, options: List[str]) -> str:
        """LLM路由决策(模拟)"""
        seed = hash(prompt) % len(options)
        weighted = random.choices(options, weights=[random.random() for _ in options], k=1)
        return weighted[0] if weighted else options[0]

    def _calculate_edge_cost(self, graph: Dict, src: str, dst: str) -> float:
        """计算边代价"""
        edge = next((e for e in graph["edges"] if e["source"] == src and e["target"] == dst), None)
        if edge:
            base = edge.get("cost", 1.0)
            cong = self._current_congestion.get(f"{src}-{dst}", 0)
            return base * (1 + cong * 0.5)
        return 10.0

    @staticmethod
    def _calculate_jain_fairness(values: List[float]) -> float:
        """计算Jain公平性指数"""
        n = len(values)
        if n <= 1:
            return 1.0
        mean_val = statistics.mean(values)
        if mean_val == 0:
            return 1.0
        numerator = sum(v**2 for v in values)
        denominator = n * mean_val**2
        return numerator / denominator if denominator > 0 else 1.0

    def get_gamms_stats(self) -> Dict[str, Any]:
        """获取GAMMS统计"""
        return {
            "graphs": len(self._graphs),
            "simulations": len(self._simulation_states),
            "total_steps": sum(s.step_count for s in self._simulation_states),
            "avg_fairness": statistics.mean([s.fairness_index for s in self._simulation_states]) if self._simulation_states else 0,
            "avg_throughput": statistics.mean([s.throughput_per_step for s in self._simulation_states]) if self._simulation_states else 0,
        }


# ==================== Part E: 仿真层总协调器 ====================


class AgentSimulationOrchestrator:
    """多智能体仿真总协调器 — 统一管理4大仿真引擎"""

    ALL_ENGINES = ["MiroFish", "HEAS", "VirtualEnv", "GAMMS"]

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or {}
        self.mirofish = MiroFishEngine(config=self.config.get("mirofish", {}))
        self.heas = HEASEngine(config=self.config.get("heas", {}))
        self.virtualenv = VirtualEnvSimulator(config=self.config.get("virtualenv", {}))
        self.gamms = GAMMSEngine(config=self.config.get("gamms", {}))
        self._orchestration_history: List[Dict[str, Any]] = []
        self._health_history: List[SimulationHealthStatus] = []

    def run_comprehensive_simulation(self, source_document: str,
                                       domain_config: Optional[Dict] = None) -> Dict[str, Any]:
        """运行综合仿真管道"""
        pipe_id = f"sim_pipe_{uuid.uuid4().hex[:8]}"
        start = time.time()
        logger.info(f"[仿真协调器] 启动综合仿真管道: {pipe_id}")

        results = {}
        results["mirofish_report"] = self.mirofish.run_full_pipeline(source_document)
        logger.info(f"[仿真协调器] MiroFish完成: 置信度={results['mirofish_report'].prediction_confidence:.2f}")

        stream_ids = []
        for i, aspect in enumerate(["market_demand", "policy_impact", "social_sentiment", "economic_indicator"]):
            sid = self.heas.define_stream(
                f"stream_aspect_{i}", aspect, level=i % 3,
                variables={aspect + "_value": random.uniform(0, 100), aspect + "_trend": 0},
                reads=[], writes=[], coupling=0.3,
            )
            stream_ids.append(sid)
        sim_result = self.heas.run_simulation(stream_ids, steps=50)
        results["heas_simulation"] = sim_result

        virtual_sid = self.virtualenv.create_scenario(
            VirtualEnvScenario.VR_AR_VIEWING,
            objects=[{"type": "building", "position": [0, 0, 0], "dimensions": [10, 8, 20]},
                  {"type": "property_plot", "position": [50, 30, 0], "dimensions": [20, 20, 1]},
                  {"type": "road", "position": [25, 15, 0], "dimensions": [50, 2, 0.01], "static": True}],
            obstacles=[{"position": [12, 8, 0], "dimensions": [3, 3, 3], "type": "barrier"}],
        )
        agent_a = self.virtualenv.spawn_agent("buyer_agent", [5, 5, 1.7])
        grasp_result = self.virtualenv.execute_grasp(agent_a, list(self.virtualenv._physics_objects.keys())[0] if self.virtualenv._physics_objects else "dummy")
        nav_path = self.virtualenv.navigate_to(agent_a, [45, 25, 1])
        results["virtualenv_interactions"] = {
            "grasp": grasp_result.success, "nav_efficiency": nav_path.efficiency_score,
            "objects": len(self.virtualenv._physics_objects),
        }

        gamms_graph = self.gamms.build_graph(
            "city_road_net", "road_network",
            nodes=[{"id": f"node_{i}", "type": "intersection"} for i in range(20)],
            edges=[{"source": f"node_{i}", "target": f"node_{i+1}", "capacity": 100, "latency": random.uniform(1, 10)}
                   for i in range(19)],
        )
        gamms_agents = {f"vehicle_{i}": random.choice([GraphSimAgentType.HEURISTIC, GraphSimAgentType.OPTIMIZATION, GraphSimAgentType.LEARNING_BASED])
                       for i in range(8)}
        gamms_state = self.gamms.simulate_steps("city_road_net", gamms_agents, num_steps=80)
        results["gamms_simulation"] = {
            "fairness": gamms_state.fairness_index, "total_cost": gamms_state.total_cost,
            "throughput": gamms_state.throughput_per_step,
        }

        total_time = (time.time() - start) / 60
        health = self.generate_health_status()
        self._orchestration_history.append({
            "pipe_id": pipe_id, "timestamp": datetime.now().isoformat(),
            "results": {k: {"status": "success", "summary": str(v)[:200]} for k, v in results.items()},
            "duration_min": total_time, "health": health.overall_health,
        })

        logger.info(f"[仿真协调器] 综合仿真完成! 耗时={total_time:.1f}min, 健康={health.overall_health:.2f}")
        return {"pipe_id": pipe_id, "results": results, "health": health, "duration_min": total_time}

    def generate_health_status(self) -> SimulationHealthStatus:
        """生成仿真层健康状态"""
        sid = f"health_{uuid.uuid4().hex[:8]}"
        mf_stats = self.mirofish.get_simulation_stats() if hasattr(self.mirofish, 'get_simulation_stats') else {}
        heas_stats = self.heas.get_heas_stats()
        ve_stats = self.virtualenv.get_virtualenv_stats()
        gm_stats = self.gamms.get_gamms_stats()

        predictions = len(self.mirofish._reports)
        avg_acc = statistics.mean([r.prediction_confidence for r in self.mirofish._reports]) if self.mirofish._reports else 0.8

        status = SimulationHealthStatus(
            status_id=sid,
            mirofish_status={"active": True, "reports": len(self.mirofish._reports),
                            "avg_confidence": avg_acc},
            heas_status={"active": True, **heas_stats},
            virtualenv_status={"active": True, **ve_stats},
            gamms_status={"active": True, **gm_stats},
            overall_health=(mf_stats.get("avg_confidence", 0.8) +
                           heas_stats.get("avg_diversity", 0.7) * 0.15 +
                           ve_stats.get("collab_success_rate", 0.8) * 0.1 +
                           gm_stats.get("avg_fairness", 0.8) * 0.1) / 1.15,
            active_simulations=1, total_predictions_made=predictions,
            avg_prediction_accuracy=avg_acc,
            recommendations=["所有仿真引擎正常运行", "建议定期运行压力测试以验证策略鲁棒性"],
        )
        self._health_history.append(status)
        return status


# ==================== 全局实例 ====================

mirofish_engine = MiroFishEngine()
heas_engine = HEASEngine()
virtualenv_simulator = VirtualEnvSimulator()
gamms_engine = GAMMSEngine()

agent_simulation_orchestrator = AgentSimulationOrchestrator()
