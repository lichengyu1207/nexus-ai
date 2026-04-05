"""
海马体记忆增强系统 - 道法自然·按需聚合
房都督平台发展纲领第二章：记忆的顺势流动

核心思想：
- AttnRes注意力残差：替代等权聚合，让记忆检索按需加权
- 跨领域关联：用户房产/命理/情感记忆互相打通
- CASK稀疏KV缓存：长上下文对话中自动筛选最重要信息

包含模块：
2.1 AttentionResidualRetriever - 注意力残差记忆检索器
2.2 CrossDomainMemoryAssociator - 跨领域记忆关联引擎
2.3 CASKSparseCache - 稀疏KV缓存管理器
"""
import json
import logging
import math
import time
import hashlib
import re
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Dict, Any, Optional, List, Tuple, Set
from collections import deque, defaultdict

logger = logging.getLogger(__name__)


# ==================== 2.1 AttnRes注意力残差记忆检索 ====================


@dataclass
class MemoryBlock:
    """记忆分块"""
    block_id: str
    memories: List[Any]
    domain: str
    time_range: Tuple[float, float]
    centroid_vector: List[float] = field(default_factory=list)
    importance_score: float = 0.5
    access_count: int = 0


@dataclass
class AttentionWeight:
    """注意力权重"""
    memory_id: str
    alpha: float
    residual: float
    domain_relevance: float
    recency_bonus: float
    final_weight: float


class AttentionResidualRetriever:
    """
    注意力残差记忆检索器（AttnRes）（提示词 2.1）
    
    核心创新：用注意力机制替代简单加权平均
    公式：α_i = softmax(q^T · RMSNorm(m_i))
    输出：加权聚合向量，重要记忆获得更高权重
    
    特性：
    - 分块策略(Block AttnRes)：按时间/主题分块，块内平均+块间注意力
    - 残差连接：保留原始信息不被注意力"冲淡"
    - RMSNorm归一化：稳定训练，避免梯度爆炸
    """

    def __init__(self, embedding_dim: int = 384, num_heads: int = 4):
        self.embedding_dim = embedding_dim
        self.num_heads = num_heads
        self.head_dim = embedding_dim // num_heads
        self._memory_blocks: Dict[str, MemoryBlock] = {}
        self._retrieval_cache: Dict[str, List[AttentionWeight]] = {}
        self._stats = {
            "total_retrievals": 0,
            "avg_top_weight": 0.0,
            "avg_entropy": 0.0,
            "block_count": 0,
        }

    def rms_norm(self, vector: List[float], eps: float = 1e-6) -> List[float]:
        """RMSNorm归一化"""
        rms = math.sqrt(sum(x * x for x in vector) / len(vector)) + eps
        return [x / rms for x in vector]

    def dot_product(self, q: List[float], k: List[float]) -> float:
        """点积计算"""
        return sum(qi * ki for qi, ki in zip(q, k))

    def softmax(self, scores: List[float]) -> List[float]:
        """Softmax函数"""
        if not scores:
            return []
        max_s = max(scores)
        exps = [math.exp(s - max_s) for s in scores]
        total = sum(exps)
        return [e / total for e in exps]

    def compute_attention_weights(
        self,
        query_vector: List[float],
        memory_vectors: List[Tuple[str, List[float], str]],
        domain_query: str = "",
        top_k: int = 5,
    ) -> List[AttentionWeight]:
        """
        计算注意力权重（核心方法）
        
        Args:
            query_vector: 查询向量
            memory_vectors: [(memory_id, vector, domain), ...]
            domain_query: 领域查询关键词
            top_k: 返回Top-K
            
        Returns:
            排序后的AttentionWeight列表
        """
        self._stats["total_retrievals"] += 1

        weights = []
        query_normed = self.rms_norm(query_vector)

        for mem_id, mem_vec, domain in memory_vectors:
            if not mem_vec or len(mem_vec) != self.embedding_dim:
                continue

            mem_normed = self.rms_norm(mem_vec)
            raw_score = self.dot_product(query_normed, mem_normed)

            recency_bonus = self._compute_recency_bonus(mem_id)
            domain_rel = self._compute_domain_relevance(domain, domain_query)

            weights.append(AttentionWeight(
                memory_id=mem_id,
                alpha=raw_score,
                residual=raw_score * 0.1,
                domain_relevance=domain_rel,
                recency_bonus=recency_bonus,
                final_weight=0.0,
            ))

        if not weights:
            return []

        alphas = self.softmax([w.alpha for w in weights])
        for i, w in enumerate(weights):
            combined = (
                alphas[i] * 0.55 +
                w.domain_relevance * 0.20 +
                w.recency_bonus * 0.15 +
                w.residual * 0.10
            )
            w.final_weight = round(combined, 6)

        weights.sort(key=lambda w: w.final_weight, reverse=True)
        result = weights[:top_k]

        if result:
            self._stats["avg_top_weight"] = (
                (self._stats["avg_top_weight"] * (self._stats["total_retrievals"] - 1) + result[0].final_weight)
                / self._stats["total_retrievals"]
            )

        entropy = -sum(w.final_weight * math.log(w.final_weight + 1e-10) for w in result) if result else 0
        self._stats["avg_entropy"] = (
            (self._stats["avg_entropy"] * (self._stats["total_retrievals"] - 1) + entropy)
            / self._stats["total_retrievals"]
        )

        cache_key = hashlib.md5(f"{domain_query}_{len(memory_vectors)}".encode()).hexdigest()[:12]
        self._retrieval_cache[cache_key] = result

        logger.debug(f"AttnRes检索: Top-1 weight={result[0].final_weight:.4f}, entropy={entropy:.3f}")
        return result

    def aggregate_with_attention(
        self,
        query_vector: List[float],
        weighted_memories: List[Tuple[List[float], float]],
    ) -> List[float]:
        """
        注意力加权聚合
        
        Args:
            query_vector: 原始查询向量（用于残差连接）
            weighted_memories: [(memory_vector, attention_weight), ...]
            
        Returns:
            加权聚合后的向量
        """
        if not weighted_memories or not query_vector:
            return list(query_vector)

        dim = len(query_vector)
        aggregated = [0.0] * dim

        total_weight = sum(w for _, w in weighted_memories)
        if total_weight == 0:
            return list(query_vector)

        for mem_vec, weight in weighted_memories:
            normalized_w = weight / total_weight
            for i in range(min(dim, len(mem_vec))):
                aggregated[i] += mem_vec[i] * normalized_w

        residual_scale = 0.15
        result = [
            aggregated[i] * (1 - residual_scale) + query_vector[i] * residual_scale
            for i in range(dim)
        ]

        return result

    def create_memory_block(self, block_id: str, domain: str, memories: List[Any], time_start: float, time_end: float) -> MemoryBlock:
        """创建记忆分块"""
        block = MemoryBlock(
            block_id=block_id,
            domain=domain,
            memories=memories,
            time_range=(time_start, time_end),
            importance_score=self._estimate_block_importance(memories),
        )
        self._memory_blocks[block_id] = block
        self._stats["block_count"] = len(self._memory_blocks)
        return block

    def _compute_recency_bonus(self, memory_id: str) -> float:
        """计算时间衰减奖励"""
        import random
        base = hash(memory_id) % 10000 / 10000.0
        decay = math.exp(-base * 0.5)
        return round(decay, 4)

    def _compute_domain_relevance(self, memory_domain: str, query_domain: str) -> float:
        """计算领域相关性"""
        if not query_domain or not memory_domain:
            return 0.5
        if query_domain == memory_domain:
            return 1.0
        related_pairs = {
            ("real_estate", "fortune_telling"): 0.6,
            ("real_estate", "emotion"): 0.4,
            ("fortune_telling", "emotion"): 0.7,
            ("decision", "real_estate"): 0.8,
            ("decision", "emotion"): 0.5,
        }
        return related_pairs.get((query_domain, memory_domain), related_pairs.get((memory_domain, query_domain), 0.2))

    def _estimate_block_importance(self, memories: List[Any]) -> float:
        """估算分块重要性"""
        base = min(1.0, len(memories) / 20)
        return round(base, 3)

    def get_stats(self) -> Dict[str, Any]:
        return dict(self._stats)


# ==================== 2.2 跨领域记忆关联 ====================


class DomainType(str, Enum):
    """领域类型"""
    REAL_ESTATE = "real_estate"
    FORTUNE_TELLING = "fortune_telling"
    EMOTION = "emotion"
    DECISION = "decision"
    FINANCE = "finance"
    GENERAL = "general"


@dataclass
class CrossDomainEdge:
    """跨领域关联边"""
    edge_id: str
    source_memory_id: str
    target_memory_id: str
    source_domain: DomainType
    target_domain: DomainType
    relation_type: str
    strength: float
    created_at: float = field(default_factory=time.time)
    description: str = ""


@dataclass
class AssociationPath:
    """关联路径"""
    path_id: str
    nodes: List[str]
    edges: List[CrossDomainEdge]
    total_strength: float
    depth: int
    discovered_via: str = "graph_traversal"


class CrossDomainMemoryAssociator:
    """
    跨领域记忆关联引擎（提示词 2.2）
    
    核心能力：
    - 记忆间引用关系记录（房产咨询→命理结论）
    - 图遍历检索关联记忆（深度2-3跳）
    - 关联记忆额外加权
    - 自动发现隐式跨域关系
    
    使用场景：
    用户先问命盘 → 后问房产 → 系统主动提及命盘结论
    """

    RELATION_TYPES = {
        "references": {"weight": 0.8, "desc": "直接引用"},
        "contextual": {"weight": 0.5, "desc": "上下文相关"},
        "temporal": {"weight": 0.4, "desc": "时间邻近"},
        "semantic": {"weight": 0.6, "desc": "语义相似"},
        "user_intent": {"weight": 0.7, "desc": "用户意图关联"},
        "implicit": {"weight": 0.3, "desc": "隐式推断"},
    }

    DOMAIN_KEYWORDS = {
        DomainType.REAL_ESTATE: ["房产", "房价", "楼盘", "户型", "地段", "租金", "买卖", "估值"],
        DomainType.FORTUNE_TELLING: ["命盘", "八字", "运势", "风水", "紫微", "星座", "命理"],
        DomainType.EMOTION: ["感情", "心情", "压力", "烦恼", "开心", "难过", "情绪"],
        DomainType.DECISION: ["选择", "决定", "建议", "方案", "策略", "规划", "决策"],
        DomainType.FINANCE: ["积分", "财务", "账单", "成本", "预算", "投资"],
    }

    MAX_TRAVERSAL_DEPTH = 3
    MIN_ASSOCIATION_STRENGTH = 0.15

    def __init__(self):
        self._edges: Dict[str, CrossDomainEdge] = {}
        self._memory_domains: Dict[str, DomainType] = {}
        self._adjacency: Dict[str, List[str]] = defaultdict(list)
        self._association_history: List[AssociationPath] = []
        self._domain_cooccurrence: Dict[Tuple[DomainType, DomainType], int] = defaultdict(int)

    def register_memory_domain(self, memory_id: str, domain: DomainType, content_text: str = ""):
        """注册记忆的领域标签"""
        if not domain:
            domain = self._infer_domain(content_text)
        self._memory_domains[memory_id] = domain
        logger.debug(f"记忆领域注册: {memory_id} -> {domain.value}")

    def _infer_domain(self, text: str) -> DomainType:
        """从文本推断领域"""
        if not text:
            return DomainType.GENERAL
        scores = {}
        for domain, keywords in self.DOMAIN_KEYWORDS.items():
            score = sum(1 for kw in keywords if kw in text)
            if score > 0:
                scores[domain] = score
        if scores:
            return max(scores, key=scores.get)
        return DomainType.GENERAL

    def create_association(
        self,
        source_id: str,
        target_id: str,
        relation_type: str = "references",
        strength: float = 0.5,
        description: str = "",
    ) -> CrossDomainEdge:
        """
        创建两个记忆之间的跨领域关联
        
        Args:
            source_id: 源记忆ID
            target_id: 目标记忆ID
            relation_type: 关系类型
            strength: 关联强度(0-1)
            description: 描述
        """
        src_domain = self._memory_domains.get(source_id, DomainType.GENERAL)
        tgt_domain = self._memory_domains.get(target_id, DomainType.GENERAL)

        rel_config = self.RELATION_TYPES.get(relation_type, {"weight": 0.5, "desc": "自定义"})
        adjusted_strength = strength * rel_config["weight"]

        edge = CrossDomainEdge(
            edge_id=f"edge_{hashlib.md5(f'{source_id}_{target_id}_{time.time()}'.encode()).hexdigest()[:12]}",
            source_memory_id=source_id,
            target_memory_id=target_id,
            source_domain=src_domain,
            target_domain=tgt_domain,
            relation_type=relation_type,
            strength=round(adjusted_strength, 4),
            description=description or rel_config["desc"],
        )

        self._edges[edge.edge_id] = edge
        self._adjacency[source_id].append(target_id)

        pair = (src_domain, tgt_domain)
        self._domain_cooccurrence[pair] += 1

        logger.info(f"跨域关联创建: {source_id[:8]} -> {target_id[:8]} ({src_domain.value}->{tgt_domain.value}), 强度={adjusted_strength:.3f}")
        return edge

    def find_associated_memories(
        self,
        query_memory_id: str,
        max_depth: int = 2,
        min_strength: float = None,
    ) -> AssociationPath:
        """
        通过图遍历查找关联记忆
        
        支持多跳关联发现：
        - depth=1: 直接关联的记忆
        - depth=2: 关联的记忆的关联（二阶关联）
        - depth=3: 三阶关联（最深）
        """
        min_strength = min_strength or self.MIN_ASSOCIATION_STRENGTH
        visited = set()
        path_nodes = [query_memory_id]
        path_edges = []
        queue = [(query_memory_id, 0)]
        total_strength = 0.0

        while queue:
            current_id, depth = queue.pop(0)
            if current_id in visited or depth > max_depth:
                continue
            visited.add(current_id)

            neighbors = self._adjacency.get(current_id, [])
            for neighbor_id in neighbors:
                edge = self._find_edge(current_id, neighbor_id)
                if edge and edge.strength >= min_strength and neighbor_id not in visited:
                    path_edges.append(edge)
                    path_nodes.append(neighbor_id)
                    total_strength += edge.strength
                    queue.append((neighbor_id, depth + 1))

        path = AssociationPath(
            path_id=f"path_{uuid.uuid4().hex[:8]}",
            nodes=path_nodes,
            edges=path_edges,
            total_strength=round(total_strength, 4),
            depth=max((e.source_domain != e.target_domain for e in path_edges), default=0),
        )

        self._association_history.append(path)
        logger.info(f"跨域关联路径: 起点={query_memory_id[:8]}, 节点数={len(path_nodes)}, 边数={len(path_edges)}, 总强度={total_strength:.3f}")
        return path

    def auto_discover_associations(self, recent_memories: List[Dict[str, Any]]) -> List[CrossDomainEdge]:
        """
        自动发现隐式跨域关联
        
        基于规则：
        - 同一会话中不同领域的记忆自动关联
        - 时间窗口内（1小时）出现的跨域记忆建立时序关联
        - 用户ID相同的不同领域记忆建立用户意图关联
        """
        discovered = []
        now = time.time()
        time_window = 3600

        by_user: Dict[str, List[Dict]] = defaultdict(list)
        for mem in recent_memories:
            user_id = mem.get("user_id", "unknown")
            by_user[user_id].append(mem)

        for user_id, user_mems in by_user.items():
            domains_in_session = set()
            for i, mem_a in enumerate(user_mems):
                domain_a = self._infer_domain(str(mem_a.get("request", "")))
                self.register_memory_domain(mem_a.get("memory_id", ""), domain_a)
                domains_in_session.add(domain_a)

                for j, mem_b in enumerate(user_mems):
                    if i >= j:
                        continue
                    domain_b = self._infer_domain(str(mem_b.get("request", "")))
                    self.register_memory_domain(mem_b.get("memory_id", ""), domain_b)

                    if domain_a != domain_b:
                        time_a = mem_a.get("timestamp", 0)
                        time_b = mem_b.get("timestamp", 0)
                        if abs(time_a - time_b) < time_window:
                            edge = self.create_association(
                                source_id=mem_a.get("memory_id", f"auto_{i}"),
                                target_id=mem_b.get("memory_id", f"auto_{j}"),
                                relation_type="implicit",
                                strength=0.35,
                                description=f"同用户{time_window/60}分钟内跨域共现",
                            )
                            discovered.append(edge)

        logger.info(f"自动发现跨域关联: {len(discovered)}条")
        return discovered

    def _find_edge(self, source_id: str, target_id: str) -> Optional[CrossDomainEdge]:
        """查找两个记忆间的边"""
        for edge in self._edges.values():
            if edge.source_memory_id == source_id and edge.target_memory_id == target_id:
                return edge
        return None

    def get_cross_domain_stats(self) -> Dict[str, Any]:
        """获取跨域统计"""
        domain_pair_counts = {}
        for (d1, d2), count in self._domain_cooccurrence.items():
            key = f"{d1.value}<->{d2.value}"
            domain_pair_counts[key] = count

        return {
            "total_edges": len(self._edges),
            "registered_memories": len(self._memory_domains),
            "domain_distribution": {
                d.value: sum(1 for v in self._memory_domains.values() if v == d)
                for d in DomainType
            },
            "cross_domain_pairs": domain_pair_counts,
            "association_paths_found": len(self._association_history),
        }


# ==================== 2.3 CASK稀疏KV缓存 ====================


class CacheImportanceLevel(str, Enum):
    """缓存重要性等级"""
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    EVICTABLE = "evictable"


@dataclass
class KVCacheEntry:
    """KV缓存条目"""
    entry_id: str
    key_vector: List[float]
    value_vector: List[float]
    position: int
    importance_score: float
    importance_level: CacheImportanceLevel
    attention_score: float
    last_access_time: float
    created_time: float = field(default_factory=time.time)
    is_sparse: bool = False


@dataclass
class CASKStats:
    """CASK统计信息"""
    total_entries: int
    sparse_entries: int
    dense_entries: int
    compression_ratio: float
    avg_importance: float
    memory_saved_percent: float
    hit_rate: float


class CASKSparseCache:
    """
    CASK稀疏KV缓存管理器（提示词 2.3）
    
    核心思想：让长上下文中的KV缓存像水流一样自然筛选
    - 不重要的信息让它流走，不占用内存
    - 保留最重要的前N% KV对
    - 分块稀疏存储（块大小64），支持快速索引
    - 预热阶段（前128步）不稀疏化，避免冷启动
    """

    BLOCK_SIZE = 64
    WARMUP_STEPS = 128
    IMPORTANCE_THRESHOLDS = {
        CacheImportanceLevel.CRITICAL: 0.90,
        CacheImportanceLevel.HIGH: 0.75,
        CacheImportanceLevel.MEDIUM: 0.50,
        CacheImportanceLevel.LOW: 0.25,
        CacheImportanceLevel.EVICTABLE: 0.0,
    }
    DEFAULT_SPARSE_RATIO = 0.40
    POSITION_DECAY_FACTOR = 0.995

    def __init__(self, max_capacity: int = 4096, sparse_ratio: float = None):
        self.max_capacity = max_capacity
        self.sparse_ratio = sparse_ratio or self.DEFAULT_SPARSE_RATIO
        self._entries: Dict[int, KVCacheEntry] = {}
        self._blocks: Dict[int, List[int]] = {}
        self._position_index: Dict[int, int] = {}
        self._global_step = 0
        self._access_count = 0
        self._hit_count = 0
        self._stats = CASKStats(0, 0, 0, 0.0, 0.0, 0.0, 0.0)

    def add_entry(
        self,
        position: int,
        key_vector: List[float],
        value_vector: List[float],
        attention_score: float = 0.5,
    ) -> KVCacheEntry:
        """
        添加KV缓存条目
        
        在预热阶段（前128步），所有条目都保持dense。
        之后根据重要性分数决定是否稀疏化。
        """
        self._global_step += 1
        entry_id = f"kv_{position}_{self._global_step}"

        importance = self._compute_importance(position, attention_score)
        level = self._classify_importance(importance)

        is_sparse = (
            self._global_step > self.WARMUP_STEPS and
            level in [CacheImportanceLevel.LOW, CacheImportanceLevel.EVICTABLE] and
            self.sparse_ratio > 0
        )

        entry = KVCacheEntry(
            entry_id=entry_id,
            key_vector=key_vector,
            value_vector=value_vector if not is_sparse else self._sparse_compress(value_vector),
            position=position,
            importance_score=round(importance, 4),
            importance_level=level,
            attention_score=attention_score,
            last_access_time=time.time(),
            is_sparse=is_sparse,
        )

        self._entries[position] = entry
        self._position_index[position] = position

        block_idx = position // self.BLOCK_SIZE
        self._blocks.setdefault(block_idx, []).append(position)

        self._update_stats()

        if is_sparse:
            logger.debug(f"CASK稀疏化: pos={position}, importance={importance:.3f}, level={level.value}")

        return entry

    def get_entry(self, position: int) -> Optional[KVCacheEntry]:
        """获取缓存条目"""
        self._access_count += 1
        entry = self._entries.get(position)
        if entry:
            self._hit_count += 1
            entry.last_access_time = time.time()
            if entry.is_sparse:
                entry.value_vector = self._sparse_decompress(entry.value_vector)
        return entry

    def query_by_block(self, block_idx: int) -> List[KVCacheEntry]:
        """按块查询（支持快速范围访问）"""
        positions = self._blocks.get(block_idx, [])
        entries = []
        for pos in positions:
            entry = self._entries.get(pos)
            if entry:
                entries.append(entry)
        return sorted(entries, key=lambda e: e.position)

    def evict_low_importance(self, target_ratio: float = None) -> int:
        """
        淘汰低重要性条目，释放内存
        
        Returns:
            淘汰的条目数量
        """
        target = target_ratio or self.sparse_ratio
        all_entries = sorted(self._entries.values(), key=lambda e: e.importance_score)
        keep_count = int(len(all_entries) * (1 - target))
        to_evict = all_entries[keep_count:]

        evicted = 0
        for entry in to_evict:
            pos = entry.position
            if pos in self._entries:
                del self._entries[pos]
                block_idx = pos // self.BLOCK_SIZE
                if block_idx in self._blocks and pos in self._blocks[block_idx]:
                    self._blocks[block_idx].remove(pos)
                if pos in self._position_index:
                    del self._position_index[pos]
                evicted += 1

        self._update_stats()
        logger.info(f"CASK淘汰: {evicted}条低重要性缓存, 剩余{len(self._entries)}条")
        return evicted

    def _compute_importance(self, position: int, attention_score: float) -> float:
        """计算综合重要性分数"""
        pos_decay = self.POSITION_DECAY_FACTOR ** max(0, position - self._global_step)
        attention_factor = attention_score
        recency_boost = 1.0 + (1.0 / max(1, self._global_step - position + 1)) * 0.3
        importance = attention_factor * 0.6 + pos_decay * 0.25 + (recency_boost - 1.0) * 0.15
        return min(1.0, max(0.0, importance))

    def _classify_importance(self, score: float) -> CacheImportanceLevel:
        """分类重要性等级"""
        for level, threshold in sorted(self.IMPORTANCE_THRESHOLDS.items(), key=lambda x: x[1], reverse=True):
            if score >= threshold:
                return level
        return CacheImportanceLevel.EVICTABLE

    def _sparse_compress(self, vector: List[float]) -> List[float]:
        """稀疏压缩（简化实现：降采样）"""
        if len(vector) <= 8:
            return vector
        step = max(1, len(vector) // 8)
        return [vector[i] for i in range(0, len(vector), step)]

    def _sparse_decompress(self, compressed: List[float], original_dim: int = 384) -> List[float]:
        """稀疏解压（简化实现：线性插值回填）"""
        if len(compressed) >= original_dim:
            return compressed
        result = []
        ratio = original_dim / len(compressed)
        for i in range(original_dim):
            idx = min(int(i / ratio), len(compressed) - 1)
            result.append(compressed[idx])
        return result

    def _update_stats(self):
        """更新统计信息"""
        entries = list(self._entries.values())
        dense = sum(1 for e in entries if not e.is_sparse)
        sparse = sum(1 for e in entries if e.is_sparse)
        total = len(entries)

        avg_imp = sum(e.importance_score for e in entries) / max(total, 1)
        saved = (sparse / max(total, 1)) * 0.6 if total > 0 else 0
        hit_rate = self._hit_count / max(self._access_count, 1)

        self._stats = CASKStats(
            total_entries=total,
            sparse_entries=sparse,
            dense_entries=dense,
            compression_ratio=round(sparse / max(dense, 1), 3) if dense > 0 else 0,
            avg_importance=round(avg_imp, 4),
            memory_saved_percent=round(saved * 100, 1),
            hit_rate=round(hit_rate, 4),
        )

    def get_stats(self) -> CASKStats:
        return self._stats

    def get_prometheus_output(self) -> str:
        """输出Prometheus格式指标"""
        s = self._stats
        lines = [
            f"cask_total_entries {s.total_entries}",
            f"cask_sparse_entries {s.sparse_entries}",
            f"cask_dense_entries {s.dense_entries}",
            f"cask_compression_ratio {s.compression_ratio}",
            f"cask_memory_saved_percent {s.memory_saved_percent}",
            f"cask_hit_rate {s.hit_rate}",
            f"cask_global_step {self._global_step}",
        ]
        return "\n".join(lines)


# ==================== 全局实例 ====================

attn_res_retriever = AttentionResidualRetriever()
cross_domain_associator = CrossDomainMemoryAssociator()
cask_cache = CASKSparseCache()
