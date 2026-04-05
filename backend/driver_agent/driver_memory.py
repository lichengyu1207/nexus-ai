# -*- coding: utf-8 -*-
"""
驱动智能体 - 记忆系统 (Driver Memory System)
=============================================
对应设计文档 Ch5(自我修复与优化) + 修炼体系Ch6(元婴期自我反思)的延伸

职责：
1) 长期经验库(ExperienceRepository) — 存储所有决策、执行、反思记录
2) 决策模式学习器(PatternLearner) — 从历史数据中学习最优决策模式
3) 知识图谱构建器(DriverKnowledgeGraph) — 构建跨体系的因果知识图谱
4) 经验检索引擎(ExperienceRetriever) — 基于相似度检索历史经验
5) 记忆压缩与归档(MemoryArchiver) — 自动清理和归档旧记忆
"""

from __future__ import annotations

import json
import time
import math
import hashlib
import logging
import os
import threading
from dataclasses import dataclass, field, asdict
from typing import Any, Dict, List, Optional, Tuple
from datetime import datetime, timedelta
from enum import Enum

logger = logging.getLogger(__name__)


class ExperienceType(Enum):
    DECISION = "decision"
    EXECUTION = "execution"
    REFLECTION = "reflection"
    ANOMALY = "anomaly"
    ROLLBACK = "rollback"
    USER_FEEDBACK = "user_feedback"


@dataclass
class ExperienceEntry:
    experience_id: str
    experience_type: ExperienceType
    timestamp: str
    session_id: str
    summary: str
    data: Dict[str, Any]
    tags: List[str] = field(default_factory=list)
    outcome: Optional[str] = None
    effectiveness_score: float = 0.0
    embedding_hash: Optional[str] = None


@dataclass
class DecisionPattern:
    pattern_id: str
    context_signature: str
    action_chosen: str
    success_count: int
    failure_count: int
    avg_confidence: float
    avg_duration_s: float
    last_used: str
    effectiveness: float = 0.0
    learned_from_experiences: int = 0


@dataclass
class KnowledgeNode:
    node_id: str
    concept: str
    category: str
    properties: Dict[str, Any] = field(default_factory=dict)
    relations: List[Dict[str, str]] = field(default_factory=list)
    created_at: str = ""
    confidence: float = 1.0
    source_systems: List[str] = field(default_factory=list)


@dataclass
class RetrievalResult:
    query: str
    experiences: List[ExperienceEntry]
    total_found: int
    search_time_ms: float
    relevance_scores: List[float] = field(default_factory=list)
    patterns_matched: List[DecisionPattern] = field(default_factory=list)


class ExperienceRepository:
    """
    长期经验库 — 持久化存储所有驱动智能体的经验数据
    
    支持的操作：
    - 记录：添加新的经验条目（决策/执行/反思/异常）
    - 查询：按类型、时间范围、标签过滤
    - 统计：成功率趋势、常见失败模式
    - 归档：将过期数据移入冷存储
    """

    def __init__(self, storage_dir: str = "data/driver_agent/memory"):
        self.storage_dir = storage_dir
        os.makedirs(storage_dir, exist_ok=True)
        self._experiences: List[ExperienceEntry] = []
        self._lock = threading.RLock()
        self._load_from_disk()

    def _load_from_disk(self):
        filepath = os.path.join(self.storage_dir, "experiences.json")
        if os.path.exists(filepath):
            try:
                with open(filepath, "r", encoding="utf-8") as f:
                    data = json.load(f)
                self._experiences = [ExperienceEntry(**e) for e in data.get("experiences", [])]
                logger.info(f"[经验库] 从磁盘加载 {len(self._experiences)} 条经验")
            except Exception as e:
                logger.warning(f"[经验库] 加载失败: {e}")

    def save_to_disk(self):
        filepath = os.path.join(self.storage_dir, "experiences.json")
        with open(filepath, "w", encoding="utf-8") as f:
            json.dump({"experiences": [asdict(e) for e in self._experiences]},
                      f, ensure_ascii=False, indent=2, default=str)

    def record(self, exp_type: ExperienceType, session_id: str, summary: str,
                data: Dict[str, Any], tags: Optional[List[str]] = None,
                outcome: Optional[str] = None, effectiveness: float = 0.0) -> ExperienceEntry:
        entry = ExperienceEntry(
            experience_id=f"exp_{int(time.time()*1000)}_{hashlib.md5(summary.encode()).hexdigest()[:8]}",
            experience_type=exp_type,
            timestamp=datetime.now().isoformat(),
            session_id=session_id,
            summary=summary[:200],
            data=data,
            tags=tags or [],
            outcome=outcome,
            effectiveness_score=max(0.0, min(1.0, effectiveness)),
            embedding_hash=hashlib.md5(summary.encode()).hexdigest()[:12],
        )
        with self._lock:
            self._experiences.append(entry)
        if len(self._experiences) % 50 == 0:
            self.save_to_disk()
        return entry

    def query(self, exp_type: Optional[ExperienceType] = None, since_hours: Optional[float] = None,
               limit: int = 50, tags_filter: Optional[List[str]] = None) -> List[ExperienceEntry]:
        with self._lock:
            results = list(self._experiences)
        if exp_type:
            results = [e for e in results if e.experience_type == exp_type]
        if since_hours:
            cutoff = (datetime.now() - timedelta(hours=since_hours)).isoformat()
            results = [e for e in results if e.timestamp >= cutoff]
        if tags_filter:
            results = [e for e in results if any(t in e.tags for t in tags_filter)]
        results.sort(key=lambda e: e.timestamp, reverse=True)
        return results[:limit]

    def get_statistics(self, hours: float = 24.0) -> Dict[str, Any]:
        recent = self.query(since_hours=hours)
        by_type = defaultdict(int)
        by_outcome = defaultdict(int)
        total_effectiveness = 0.0
        for e in recent:
            by_type[e.experience_type.value] += 1
            if e.outcome:
                by_outcome[e.outcome] += 1
            total_effectiveness += e.effectiveness_score
        success_rate = by_outcome.get("success", 0) / max(len(recent), 1)
        failure_patterns = defaultdict(int)
        failed = [e for e in recent if e.outcome == "failure"]
        for f in failed:
            for tag in f.tags:
                failure_patterns[tag] += 1
        top_failures = sorted(failure_patterns.items(), key=lambda x: -x[1])[:5]
        return {
            "period_hours": hours,
            "total_experiences": len(recent),
            "by_type": dict(by_type),
            "by_outcome": dict(by_outcome),
            "success_rate": round(success_rate, 3),
            "avg_effectiveness": round(total_effectiveness / max(len(recent), 1), 3),
            "top_failure_patterns": top_failures,
            "storage_size": len(self._experiences),
        }

    def archive_old(self, max_age_days: int = 30):
        cutoff = (datetime.now() - timedelta(days=max_age_days)).isoformat()
        archived = 0
        with self._lock:
            original_len = len(self._experiences)
            self._experiences = [e for e in self._experiences if e.timestamp >= cutoff or e.effectiveness_score > 0.7]
            archived = original_len - len(self._experiences)
        if archived > 0:
            self.save_to_disk()
            logger.info(f"[经验库] 归档 {archived} 条过期经验")


experience_repository = ExperienceRepository()


class PatternLearner:
    """
    决策模式学习器 — 从历史经验中学习最优决策模式
    
    功能：
    - 从决策-结果对中提取重复出现的模式
    - 为每个模式计算有效性评分
    - 在新决策时推荐历史最优行动
    - 自适应更新模式权重
    """

    MIN_SAMPLES_FOR_PATTERN = 3
    PATTERN_DECAY_DAYS = 14

    def __init__(self):
        self._patterns: Dict[str, DecisionPattern] = {}
        self._learning_log: List[Dict[str, Any]] = []

    def learn_from_experience(self, experience: ExperienceEntry):
        if experience.experience_type != ExperienceType.DECISION:
            return
        context_data = experience.data
        action_taken = context_data.get("chosen_action", "")
        context_sig = self._compute_context_signature(context_data)
        pattern_key = f"{context_sig}::{action_taken}"
        if pattern_key not in self._patterns:
            self._patterns[pattern_key] = DecisionPattern(
                pattern_id=f"pat_{len(self._patterns)}",
                context_signature=context_sig,
                action_chosen=action_taken,
                success_count=0,
                failure_count=0,
                avg_confidence=context_data.get("confidence", 0.5),
                avg_duration_s=context_data.get("duration_s", 10.0),
                last_used=experience.timestamp,
                learned_from_experiences=1,
            )
        pattern = self._patterns[pattern_key]
        pattern.learned_from_experiences += 1
        pattern.last_used = experience.timestamp
        if experience.outcome == "success":
            pattern.success_count += 1
        elif experience.outcome == "failure":
            pattern.failure_count += 1
        total = pattern.success_count + pattern.failure_count
        pattern.effectiveness = pattern.success_count / max(total, 1)
        decay_factor = max(0.1, 1.0 - (datetime.now() - datetime.fromisoformat(experience.timestamp.replace("Z", "+00:00").replace("+00:00", ""))).days / self.PATTERN_DECAY_DAYS)
        pattern.effectiveness *= decay_factor
        log_entry = {
            "timestamp": experience.timestamp,
            "pattern_key": pattern_key[:40],
            "outcome": experience.outcome,
            "new_effectiveness": round(pattern.effectiveness, 3),
        }
        self._learning_log.append(log_entry)

    def _compute_context_signature(self, context_data: Dict[str, str]) -> str:
        sig_parts = [
            context_data.get("intent_type", ""),
            context_data.get("target_systems", [""])[0] if isinstance(context_data.get("target_systems"), list) else "",
            context_data.get("priority", ""),
        ]
        raw = "|".join(str(p) for p in sig_parts)
        return hashlib.md5(raw.encode()).hexdigest()[:10]

    def recommend_action(self, current_context: Dict[str, Any], top_k: int = 3) -> List[Tuple[DecisionPattern, float]]:
        context_sig = self._compute_context_signature(current_context)
        candidates = []
        for key, pattern in self._patterns.items():
            if key.startswith(context_sig + "::") or context_sig in key.split("::")[0]:
                candidates.append((pattern, pattern.effectiveness))
        candidates.sort(key=lambda x: -x[1])
        scored = [(p, s * self._recency_bonus(p)) for p, s in candidates[:top_k * 3]]
        scored.sort(key=lambda x: -x[1])
        return scored[:top_k]

    def _recency_bonus(self, pattern: DecisionPattern) -> float:
        try:
            days_ago = (datetime.now() - datetime.fromisoformat(pattern.last_used.replace("Z", "+00:00").replace("+00-08", ""))).days
            return math.exp(-days_ago / 30.0)
        except Exception:
            return 0.5

    def get_top_patterns(self, limit: int = 20) -> List[Dict[str, Any]]:
        patterns = sorted(self._patterns.values(), key=lambda p: (-p.effectiveness, -p.learned_from_experiences))
        return [{
            "pattern_id": p.pattern_id[:16],
            "action": p.action_chosen,
            "effectiveness": round(p.effectiveness, 3),
            "samples": p.learned_from_experiences,
            "success_rate": round(p.success_count / max(p.success_count + p.failure_count, 1), 3),
            "last_used": p.last_used[:19],
        } for p in patterns[:limit]]

    def get_learning_stats(self) -> Dict[str, Any]:
        total_patterns = len(self._patterns)
        effective_patterns = sum(1 for p in self._patterns.values() if p.effectiveness >= 0.6 and p.learned_from_experiences >= self.MIN_SAMPLES_FOR_PATTERN)
        highly_reliable = sum(1 for p in self._patterns.values() if p.effectiveness >= 0.8)
        return {
            "total_patterns_discovered": total_patterns,
            "effective_patterns": effective_patterns,
            "highly_reliable_patterns": highly_reliable,
            "learning_entries": len(self._learning_log),
            "coverage_quality": round(effective_patterns / max(total_patterns, 1), 3) if total_patterns else 0,
        }


pattern_learner = PatternLearner()


class DriverKnowledgeGraph:
    """
    知识图谱构建器 — 跨体系因果知识图谱
    
    节点类型：
    - system_node: 子系统（炼丹/修炼/自进化/治理）
    - metric_node: 可观测指标（胜率/延迟/内存/CPU）
    - action_node: 可执行操作（训练/部署/回滚）
    - event_node: 异常事件/里程碑
    - rule_node: 业务规则（通关标准/告警阈值）
    
    边类型：
    - causes: A导致B
    - prevents: A阻止B
    - improves: A改善B
    - requires: A需要B
    - correlates_with: A与B相关
    """

    EDGE_TYPES = ["causes", "prevents", "improves", "requires", "correlates_with"]

    def __init__(self):
        self._nodes: Dict[str, KnowledgeNode] = {}
        self._edges: List[Dict[str, str]] = []

    def add_node(self, node_id: str, concept: str, category: str,
                 properties: Optional[Dict[str, Any]] = None,
                 source_systems: Optional[List[str]] = None,
                 confidence: float = 1.0) -> KnowledgeNode:
        node = KnowledgeNode(
            node_id=node_id,
            concept=concept,
            category=category,
            properties=properties or {},
            created_at=datetime.now().isoformat(),
            confidence=confidence,
            source_systems=source_systems or [],
        )
        self._nodes[node_id] = node
        return node

    def add_edge(self, source_id: str, target_id: str, relation: str, weight: float = 1.0):
        if relation not in self.EDGE_TYPES:
            raise ValueError(f"未知边类型: {relation}, 允许: {self.EDGE_TYPES}")
        edge = {"source": source_id, "target": target_id, "relation": relation, "weight": round(weight, 3)}
        self._edges.append(edge)
        if source_id in self._nodes:
            self._nodes[source_id].relations.append(edge)
        return edge

    def build_default_graph(self):
        systems = [
            ("sys_governance", "道法自然治理体系", "system_node", {"layer": 1}, ["governance"]),
            ("sys_evolution", "自进化数据引擎", "system_node", {"layer": 2}, ["evolution"]),
            ("sys_alchemy", "炼丹训练引擎", "system_node", {"layer": 3}, ["alchemy"]),
            ("sys_cultivation", "修炼进化体系", "system_node", {"layer": 4}, ["cultivation"]),
            ("sys_driver", "驱动智能体大脑", "system_node", {"layer": 5, "autonomous": True}, ["driver"]),
        ]
        metrics = [
            ("metric_win_rate", "对抗胜率", "metric_node", {"unit": "%", "target": 90}, ["cultivation", "alchemy"]),
            ("metric_completion", "修炼完成度", "metric_node", {"unit": "%", "target": 100}, ["cultivation"]),
            ("metric_dao_achievement", "道法成就度", "metric_node", {"unit": "%", "target": 80}, ["cultivation"]),
            ("metric_error_rate", "错误率", "metric_node", {"unit": "%", "target": "<0.5"}, ["all"]),
            ("metric_response_time", "响应时间", "metric_node", {"unit": "ms", "target": "<1000"}, ["all"]),
            ("metric_health_score", "健康分数", "metric_node", {"unit": "分", "target": ">75"}, ["driver"]),
        ]
        actions = [
            ("act_train", "执行训练", "action_node", {"type": "evolution"}, ["alchemy", "cultivation"]),
            ("act_evolve", "执行进化循环", "action_node", {"type": "full_cycle"}, ["driver"]),
            ("act_validate", "验证结果", "action_node", {"type": "check"}, ["all"]),
            ("act_rollback", "回滚操作", "action_node", {"type": "recovery"}, ["executor"]),
            ("act_deploy", "部署发布", "action_node", {"type": "deployment"}, ["integration"]),
        ]
        events = [
            ("event_bottleneck", "阶段瓶颈", "event_node", {"severity": "warning"}, ["dashboard"]),
            ("event_anomaly", "异常检测", "event_node", {"severity": "variable"}, ["perception"]),
            ("event_breakthrough", "突破进展", "event_node", {"severity": "positive"}, ["cultivation"]),
        ]
        rules = [
            ("rule_pass_win_rate", "通关胜率≥90%", "rule_node", {"threshold": 0.9}, ["cultivation"]),
            ("rule_convergence", "收敛条件满足", "rule_node", {"iterations": 3}, ["alchemy"]),
            ("rule_health_good", "健康分数>75", "rule_node", {"score": 75}, ["driver"]),
        ]
        all_nodes = systems + metrics + actions + events + rules
        for nid, concept, cat, props, srcs in all_nodes:
            self.add_node(nid, concept, cat, props, srcs)
        default_edges = [
            ("sys_driver", "act_evolve", "requires", 1.0),
            ("act_evolve", "sys_cultivation", "improves", 0.8),
            ("act_evolve", "sys_alchemy", "uses", 0.7),
            ("sys_alchemy", "sys_cultivation", "drives", 0.9),
            ("sys_evolution", "sys_cultivation", "feeds", 0.8),
            ("sys_governance", "sys_driver", "coordinates", 0.7),
            ("act_train", "metric_win_rate", "improves", 0.6),
            ("act_validate", "metric_health_score", "checks", 1.0),
            ("event_bottleneck", "act_evolve", "prevents", 0.9),
            ("event_anomaly", "act_rollback", "triggers", 0.85),
            ("event_breakthrough", "rule_convergence", "satisfies", 0.95),
            ("metric_error_rate", "metric_health_score", "degrades", 0.7),
            ("metric_completion", "rule_pass_win_rate", "contributes_to", 0.8),
        ]
        for src, tgt, rel, w in default_edges:
            self.add_edge(src, tgt, rel, w)
        logger.info(f"[知识图谱] 默认图谱已构建 | {len(all_nodes)} 个节点 | {len(default_edges)} 条边")

    def query_related(self, node_id: str, depth: int = 2, relation_filter: Optional[str] = None) -> Dict[str, Any]:
        visited = set()
        related_nodes = []
        related_edges = []
        queue = [(node_id, 0)]
        while queue:
            current, d = queue.pop(0)
            if current in visited or d > depth:
                continue
            visited.add(current)
            if current != node_id and current in self._nodes:
                related_nodes.append({
                    "node_id": current,
                    "concept": self._nodes[current].concept,
                    "category": self._nodes[current].category,
                    "distance": d,
                })
            for edge in self._edges:
                if edge["source"] == current and edge["target"] not in visited:
                    if relation_filter is None or edge["relation"] == relation_filter:
                        queue.append((edge["target"], d + 1))
                        related_edges.append({**edge, "distance": d + 1})
        return {
            "query_node": node_id,
            "query_concept": self._nodes.get(node_id, KnowledgeNode("", "", "")).concept,
            "related_nodes": related_nodes,
            "related_edges": related_edges[:20],
            "total_reachable": len(visited) - 1,
        }

    def get_graph_summary(self) -> Dict[str, Any]:
        by_category = defaultdict(int)
        for node in self._nodes.values():
            by_category[node.category] += 1
        by_relation = defaultdict(int)
        for edge in self._edges:
            by_relation[edge["relation"]] += 1
        return {
            "total_nodes": len(self._nodes),
            "total_edges": len(self._edges),
            "by_category": dict(by_category),
            "by_relation": dict(by_relation),
        }


driver_knowledge_graph = DriverKnowledgeGraph()


class ExperienceRetriever:
    """
    经验检索引擎 — 基于相似度的历史经验检索
    
    支持多种检索策略：
    - 标签匹配：精确标签交集
    - 语义相似度：基于摘要文本的哈希近似
    - 时间邻近性：查找相近时间段的经验
    - 模式匹配：使用已学习的决策模式
    """

    def __init__(self, repository: ExperienceRepository = None, pattern_learner: PatternLearner = None):
        self.repository = repository or experience_repository
        self.pattern_learner = pattern_learner or pattern_learner

    def retrieve(self, query_text: str, query_tags: Optional[List[str]] = None,
                  experience_types: Optional[List[ExperienceType]] = None,
                  limit: int = 10) -> RetrievalResult:
        start_time = time.time()
        all_exp = self.repository.query(exp_type=None, since_hours=720, limit=500,
                                          tags_filter=query_tags)
        if experience_types:
            all_exp = [e for e in all_exp if e.experience_type in experience_types]
        query_hash = hashlib.md5(query_text.lower().encode()).hexdigest()[:12]
        scored = []
        for exp in all_exp:
            score = 0.0
            text_overlap = len(set(query_text.lower().split()) & set(exp.summary.lower().split()))
            score += min(text_overlap * 0.05, 0.3)
            tag_match = len(set(query_tags or []) & set(exp.tags)) if query_tags else 0
            score += min(tag_match * 0.15, 0.3)
            hash_similarity = sum(c1 == c2 for c1, c2 in zip(query_hash, exp.embedding_hash or "")) / max(len(query_hash), 1)
            score += hash_similarity * 0.25
            if exp.outcome == "success":
                score += 0.15
            elif exp.outcome == "failure":
                score -= 0.10
            score += exp.effectiveness_score * 0.15
            scored.append((exp, max(0.0, score)))
        scored.sort(key=lambda x: -x[1])
        top_results = scored[:limit]
        patterns_matched = []
        if self.pattern_learner and query_tags:
            mock_context = {"intent_type": query_tags[0] if query_tags else "", "target_systems": query_tags}
            recs = self.pattern_learner.recommend_action(mock_context, top_k=3)
            patterns_matched = [{"action": p.action_chosen, "effectiveness": round(s, 3)}
                             for p, s in recs]
        retrieval_time_ms = (time.time() - start_time) * 1000
        result = RetrievalResult(
            query=query_text[:100],
            experiences=[e for e, s in top_results],
            total_found=len(scored),
            search_time_ms=round(retrieval_time_ms, 1),
            relevance_scores=[round(s, 3) for _, s in top_results],
            patterns_matched=patterns_matched,
        )
        logger.info(f"[经验检索] 查询='{query_text[:50]}' → 找到{result.total_found}条相关经验 "
                     f"(返回{len(result.experiences)}条, 耗时{result.search_time_ms:.0f}ms)")
        return result


experience_retriever = ExperienceRetriever()


class MemoryArchiver:
    """
    记忆压缩与归档 — 自动管理记忆生命周期
    
    功能：
    - 定期压缩低价值记忆（保留高效果分的）
    - 将冷数据移入长期存储
    - 清理重复或矛盾的记忆条目
    - 生成记忆健康报告
    """

    COMPRESS_THRESHOLD_EFFECTIVENESS = 0.3
    ARCHIVE_AGE_DAYS = 30
    MAX_ACTIVE_EXPERIENCES = 5000

    def __init__(self, repository: ExperienceRepository = None):
        self.repository = repository or experience_repository

    def run_maintenance_cycle(self) -> Dict[str, Any]:
        start_time = time.time()
        stats_before = self.repository.get_statistics(hours=8760)
        compressed = self._compress_low_value_memories()
        archived = self.repository.archive_old(max_age_days=self.ARCHIVE_AGE_DAYS)
        deduped = self._deduplicate_memories()
        cleaned = self._clean_contradictions()
        self.repository.save_to_disk()
        stats_after = self.repository.get_statistics(hours=8760)
        duration_s = time.time() - start_time
        report = {
            "cycle_timestamp": datetime.now().isoformat(),
            "duration_s": round(duration_s, 2),
            "before_stats": stats_before,
            "after_stats": stats_after,
            "compressed": compressed,
            "archived": archived,
            "deduped": deduped,
            "cleaned": cleaned,
            "health_status": "healthy",
        }
        total_changes = compressed + archived + deduped + cleaned
        if total_changes > 100:
            report["health_status"] = "maintenance_performed"
        logger.info(f"[记忆归档] 维护周期完成 | 压缩={compressed} 归档={archived} "
                     f"去重={deduped} 清洗={cleaned} | 耗时={duration_s:.1f}s")
        return report

    def _compress_low_value_memories(self) -> int:
        count = 0
        with self.repository._lock:
            low_value = [e for e in self.repository._experiences
                         if e.effectiveness_score < self.COMPRESS_THRESHOLD_EFFECTIVENESS
                         and e.experience_type not in (ExperienceType.ANOMALY, ExperienceType.ROLLBACK)]
            for entry in low_value:
                entry.data = {"compressed": True, "original_summary": entry.summary[:100]}
                entry.summary = "[已压缩]"
                count += 1
        return count

    def _deduplicate_memories(self) -> int:
        seen_signatures: Dict[str, List[str]] = defaultdict(list)
        duplicates = 0
        with self.repository._lock:
            for i, entry in enumerate(self.repository._experiences):
                sig = f"{entry.experience_type.value}:{entry.session_id}:{entry.embedding_hash}"
                seen_signatures[sig].append(i)
            for sig, indices in seen_signatures.items():
                if len(indices) > 1:
                    keep_idx = indices[0]
                    remove_indices = indices[1:]
                    for idx in reversed(remove_indices):
                        removed = self.repository._experiences.pop(idx)
                        if removed is not None:
                            duplicates += 1
        return duplicates

    def _clean_contradictions(self) -> int:
        cleaned = 0
        decision_exps = self.repository.query(exp_type=ExperienceType.DECISION, limit=200)
        by_session = defaultdict(list)
        for exp in decision_exps:
            by_session[exp.session_id].append(exp)
        for session_id, exps in by_session.items():
            outcomes = set(e.outcome for e in exps if e.outcome)
            if "success" in outcomes and "failure" in outcomes:
                worst = min(exps, key=lambda e: e.effectiveness_score)
                with self.repository._lock:
                    if worst in self.repository._experiences:
                        self.repository._experiences.remove(worst)
                        cleaned += 1
        return cleaned

    def get_health_report(self) -> Dict[str, Any]:
        stats = self.repository.get_statistics(hours=168)
        active = len(self.repository._experiences)
        health_pct = min(100, active / max(self.MAX_ACTIVE_EXPERIENCES, 1) * 100)
        status = "healthy"
        if health_pct < 20:
            status = "needs_attention"
        elif health_pct < 5:
            status = "critical"
        return {
            "active_experiences": active,
            "capacity_utilization": round(health_pct, 1),
            "status": status,
            **stats,
        }


memory_archiver = MemoryArchiver()
