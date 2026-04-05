"""
合规知识图谱构建智能体
Compliance Knowledge Graph Agent

负责构建和维护合规知识图谱，提供智能查询服务。
"""

import asyncio
import json
import logging
import hashlib
import uuid
from typing import Dict, Any, Optional, List, Set
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from collections import defaultdict
from enum import Enum

logger = logging.getLogger(__name__)


class EntityType(Enum):
    REGULATION = "regulation"
    ARTICLE = "article"
    OBLIGATION = "obligation"
    RIGHT = "right"
    DATA_CATEGORY = "data_category"
    PROCESSING_ACTIVITY = "processing_activity"
    RISK = "risk"
    CONTROL_MEASURE = "control_measure"
    ORGANIZATION = "organization"


class RelationType(Enum):
    APPLIES_TO = "applies_to"
    REQUIRES = "requires"
    PROHIBITS = "prohibits"
    ALLOWS = "allows"
    FULFILLS = "fulfills"
    CAUSES = "causes"
    MITIGATES = "mitigates"
    RELATES_TO = "relates_to"
    SUPERSEDES = "supersedes"


@dataclass
class GraphEntity:
    entity_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    entity_type: str = ""
    name: str = ""
    description: str = ""
    
    properties: Dict = field(default_factory=dict)
    source: str = ""
    
    created_at: str = field(default_factory=lambda: datetime.utcnow().isoformat())
    updated_at: str = field(default_factory=lambda: datetime.utcnow().isoformat())


@dataclass
class GraphRelation:
    relation_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    source_entity_id: str = ""
    target_entity_id: str = ""
    relation_type: str = ""
    
    properties: Dict = field(default_factory=dict)
    weight: float = 1.0
    
    created_at: str = field(default_factory=lambda: datetime.utcnow().isoformat())


@dataclass
class QueryResult:
    query_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    query: str = ""
    timestamp: str = field(default_factory=lambda: datetime.utcnow().isoformat())
    
    entities: List[Dict] = field(default_factory=list)
    relations: List[Dict] = field(default_factory=list)
    paths: List[List[str]] = field(default_factory=list)
    
    answer: str = ""
    confidence: float = 0.0
    sources: List[str] = field(default_factory=list)


class ComplianceKnowledgeGraphAgent:
    """
    合规知识图谱构建智能体
    
    功能：
    1. 数据源：法律法规条款、行业标准、审计案例、隐私政策、用户授权记录
    2. 实体类型：法规、条款、义务、权利、数据类别、处理活动、风险、控制措施
    3. 关系类型：适用于、要求、禁止、允许、履行、导致、缓解
    4. 图谱构建：使用NLP从文档中抽取实体和关系
    5. 智能查询：支持自然语言查询，返回结构化答案
    """
    
    def __init__(self, config: Optional[Dict] = None):
        self.name = "ComplianceKnowledgeGraphAgent"
        self.description = "构建和维护合规知识图谱，提供智能查询服务"
        self.config = config or {}
        
        self.entities: Dict[str, GraphEntity] = {}
        self.relations: Dict[str, GraphRelation] = {}
        
        self.entity_by_type: Dict[str, Set[str]] = defaultdict(set)
        self.entity_by_name: Dict[str, str] = {}
        
        self.outgoing_relations: Dict[str, Set[str]] = defaultdict(set)
        self.incoming_relations: Dict[str, Set[str]] = defaultdict(set)
        
        self._init_default_graph()
        
        self.stats = {
            "total_entities": 0,
            "total_relations": 0,
            "entities_by_type": defaultdict(int),
            "relations_by_type": defaultdict(int),
            "queries_processed": 0,
        }
        
        self._initialized = False
    
    def _init_default_graph(self):
        regulations = [
            {
                "name": "个人信息保护法",
                "type": EntityType.REGULATION.value,
                "description": "中华人民共和国个人信息保护法",
                "properties": {"effective_date": "2021-11-01", "authority": "全国人大常委会"},
            },
            {
                "name": "数据安全法",
                "type": EntityType.REGULATION.value,
                "description": "中华人民共和国数据安全法",
                "properties": {"effective_date": "2021-09-01", "authority": "全国人大常委会"},
            },
            {
                "name": "网络安全法",
                "type": EntityType.REGULATION.value,
                "description": "中华人民共和国网络安全法",
                "properties": {"effective_date": "2017-06-01", "authority": "全国人大常委会"},
            },
        ]
        
        for reg_data in regulations:
            entity = GraphEntity(
                entity_type=reg_data["type"],
                name=reg_data["name"],
                description=reg_data["description"],
                properties=reg_data.get("properties", {}),
                source="official",
            )
            self._add_entity(entity)
        
        articles = [
            {
                "name": "个保法第13条",
                "type": EntityType.ARTICLE.value,
                "description": "处理个人信息应当取得个人同意",
                "regulation": "个人信息保护法",
            },
            {
                "name": "个保法第29条",
                "type": EntityType.ARTICLE.value,
                "description": "处理敏感个人信息应当取得个人单独同意",
                "regulation": "个人信息保护法",
            },
            {
                "name": "个保法第32条",
                "type": EntityType.ARTICLE.value,
                "description": "处理不满十四周岁未成年人个人信息应当取得监护人同意",
                "regulation": "个人信息保护法",
            },
        ]
        
        for art_data in articles:
            entity = GraphEntity(
                entity_type=art_data["type"],
                name=art_data["name"],
                description=art_data["description"],
                properties={"regulation": art_data["regulation"]},
                source="official",
            )
            self._add_entity(entity)
        
        obligations = [
            {
                "name": "获取用户同意",
                "type": EntityType.OBLIGATION.value,
                "description": "处理个人信息前获取用户明确同意",
            },
            {
                "name": "告知处理目的",
                "type": EntityType.OBLIGATION.value,
                "description": "告知用户个人信息处理的目的、方式、范围",
            },
            {
                "name": "获取监护人同意",
                "type": EntityType.OBLIGATION.value,
                "description": "处理未成年人个人信息时获取监护人同意",
            },
            {
                "name": "数据最小化",
                "type": EntityType.OBLIGATION.value,
                "description": "只收集实现处理目的所需的最少信息",
            },
        ]
        
        for obl_data in obligations:
            entity = GraphEntity(
                entity_type=obl_data["type"],
                name=obl_data["name"],
                description=obl_data["description"],
            )
            self._add_entity(entity)
        
        data_categories = [
            {
                "name": "个人信息",
                "type": EntityType.DATA_CATEGORY.value,
                "description": "以电子或者其他方式记录的与已识别或者可识别的自然人有关的各种信息",
            },
            {
                "name": "敏感个人信息",
                "type": EntityType.DATA_CATEGORY.value,
                "description": "一旦泄露或者非法使用，容易导致自然人的人格尊严受到侵害或者人身、财产安全受到危害的个人信息",
                "properties": {"sensitivity": "high"},
            },
            {
                "name": "未成年人信息",
                "type": EntityType.DATA_CATEGORY.value,
                "description": "不满十四周岁未成年人的个人信息",
                "properties": {"sensitivity": "high", "age_restriction": "<14"},
            },
        ]
        
        for cat_data in data_categories:
            entity = GraphEntity(
                entity_type=cat_data["type"],
                name=cat_data["name"],
                description=cat_data["description"],
                properties=cat_data.get("properties", {}),
            )
            self._add_entity(entity)
        
        self._create_default_relations()
    
    def _add_entity(self, entity: GraphEntity):
        self.entities[entity.entity_id] = entity
        self.entity_by_type[entity.entity_type].add(entity.entity_id)
        self.entity_by_name[entity.name] = entity.entity_id
        
        self.stats["total_entities"] += 1
        self.stats["entities_by_type"][entity.entity_type] += 1
    
    def _create_default_relations(self):
        relations = [
            ("个保法第13条", "获取用户同意", RelationType.REQUIRES.value),
            ("个保法第13条", "告知处理目的", RelationType.REQUIRES.value),
            ("个保法第29条", "敏感个人信息", RelationType.APPLIES_TO.value),
            ("个保法第32条", "未成年人信息", RelationType.APPLIES_TO.value),
            ("个保法第32条", "获取监护人同意", RelationType.REQUIRES.value),
            ("获取用户同意", "个人信息", RelationType.APPLIES_TO.value),
            ("数据最小化", "个人信息", RelationType.APPLIES_TO.value),
        ]
        
        for source_name, target_name, rel_type in relations:
            source_id = self.entity_by_name.get(source_name)
            target_id = self.entity_by_name.get(target_name)
            
            if source_id and target_id:
                self._add_relation(source_id, target_id, rel_type)
    
    def _add_relation(
        self,
        source_id: str,
        target_id: str,
        relation_type: str,
        properties: Optional[Dict] = None,
    ):
        relation = GraphRelation(
            source_entity_id=source_id,
            target_entity_id=target_id,
            relation_type=relation_type,
            properties=properties or {},
        )
        
        self.relations[relation.relation_id] = relation
        self.outgoing_relations[source_id].add(relation.relation_id)
        self.incoming_relations[target_id].add(relation.relation_id)
        
        self.stats["total_relations"] += 1
        self.stats["relations_by_type"][relation_type] += 1
    
    async def initialize(self):
        if not self._initialized:
            await self._setup()
            self._initialized = True
            logger.info(f"Agent '{self.name}' initialized")
    
    async def _setup(self):
        pass
    
    async def add_entity(
        self,
        entity_type: str,
        name: str,
        description: str = "",
        properties: Optional[Dict] = None,
        source: str = "",
    ) -> GraphEntity:
        if name in self.entity_by_name:
            return self.entities[self.entity_by_name[name]]
        
        entity = GraphEntity(
            entity_type=entity_type,
            name=name,
            description=description,
            properties=properties or {},
            source=source,
        )
        
        self._add_entity(entity)
        
        return entity
    
    async def add_relation(
        self,
        source_name: str,
        target_name: str,
        relation_type: str,
        properties: Optional[Dict] = None,
    ) -> Optional[GraphRelation]:
        source_id = self.entity_by_name.get(source_name)
        target_id = self.entity_by_name.get(target_name)
        
        if not source_id or not target_id:
            return None
        
        self._add_relation(source_id, target_id, relation_type, properties)
        
        return list(self.relations.values())[-1]
    
    async def query(
        self,
        query_text: str,
    ) -> QueryResult:
        result = QueryResult(query=query_text)
        
        keywords = self._extract_keywords(query_text)
        
        matched_entities = []
        for keyword in keywords:
            for entity in self.entities.values():
                if keyword.lower() in entity.name.lower() or keyword.lower() in entity.description.lower():
                    matched_entities.append(entity)
        
        result.entities = [
            {
                "entity_id": e.entity_id,
                "type": e.entity_type,
                "name": e.name,
                "description": e.description,
            }
            for e in matched_entities[:10]
        ]
        
        for entity in matched_entities[:3]:
            entity_relations = self.outgoing_relations.get(entity.entity_id, set()) | self.incoming_relations.get(entity.entity_id, set())
            
            for rel_id in entity_relations:
                rel = self.relations.get(rel_id)
                if rel:
                    result.relations.append({
                        "relation_id": rel.relation_id,
                        "type": rel.relation_type,
                        "source": rel.source_entity_id,
                        "target": rel.target_entity_id,
                    })
        
        result.answer = self._generate_answer(query_text, matched_entities)
        result.confidence = min(1.0, len(matched_entities) * 0.2 + 0.3)
        result.sources = list(set(e.source for e in matched_entities if e.source))
        
        self.stats["queries_processed"] += 1
        
        return result
    
    def _extract_keywords(self, text: str) -> List[str]:
        important_terms = [
            "个人信息", "敏感", "未成年人", "同意", "授权", "收集", "使用",
            "共享", "跨境", "删除", "查阅", "复制", "更正",
            "个保法", "数据安全法", "网络安全法",
            "监护人", "处理目的", "最小化",
        ]
        
        keywords = []
        for term in important_terms:
            if term in text:
                keywords.append(term)
        
        return keywords
    
    def _generate_answer(
        self,
        query: str,
        matched_entities: List[GraphEntity],
    ) -> str:
        if not matched_entities:
            return "未找到相关信息，建议咨询合规官。"
        
        answer_parts = []
        
        if "未成年人" in query or "儿童" in query:
            answer_parts.append("根据个人信息保护法第32条，")
            answer_parts.append("处理不满十四周岁未成年人个人信息应当取得监护人同意。")
            answer_parts.append("应当制定专门的个人信息处理规则。")
        
        elif "敏感" in query:
            answer_parts.append("根据个人信息保护法第29条，")
            answer_parts.append("处理敏感个人信息应当取得个人单独同意。")
            answer_parts.append("应当向个人告知处理敏感个人信息的必要性以及对个人权益的影响。")
        
        elif "同意" in query or "授权" in query:
            answer_parts.append("根据个人信息保护法第13条，")
            answer_parts.append("处理个人信息应当取得个人同意。")
            answer_parts.append("同意应当由个人在充分知情的前提下自愿、明确作出。")
        
        elif "删除" in query:
            answer_parts.append("根据个人信息保护法，")
            answer_parts.append("个人有权请求删除其个人信息。")
            answer_parts.append("处理者应当在十五个工作日内予以答复。")
        
        else:
            for entity in matched_entities[:2]:
                answer_parts.append(f"{entity.name}: {entity.description}")
        
        return " ".join(answer_parts)
    
    async def find_path(
        self,
        source_name: str,
        target_name: str,
        max_depth: int = 3,
    ) -> List[List[str]]:
        source_id = self.entity_by_name.get(source_name)
        target_id = self.entity_by_name.get(target_name)
        
        if not source_id or not target_id:
            return []
        
        paths = []
        visited = set()
        
        def dfs(current_id: str, path: List[str], depth: int):
            if depth > max_depth:
                return
            
            if current_id == target_id:
                paths.append(path.copy())
                return
            
            if current_id in visited:
                return
            
            visited.add(current_id)
            
            for rel_id in self.outgoing_relations.get(current_id, set()):
                rel = self.relations.get(rel_id)
                if rel:
                    entity = self.entities.get(rel.target_entity_id)
                    if entity:
                        path.append(f"{rel.relation_type} -> {entity.name}")
                        dfs(rel.target_entity_id, path, depth + 1)
                        path.pop()
            
            visited.remove(current_id)
        
        source_entity = self.entities.get(source_id)
        if source_entity:
            dfs(source_id, [source_entity.name], 0)
        
        return paths
    
    async def get_related_entities(
        self,
        entity_name: str,
        relation_types: Optional[List[str]] = None,
        depth: int = 1,
    ) -> List[Dict]:
        entity_id = self.entity_by_name.get(entity_name)
        if not entity_id:
            return []
        
        related = []
        visited = {entity_id}
        queue = [(entity_id, 0)]
        
        while queue:
            current_id, current_depth = queue.pop(0)
            
            if current_depth >= depth:
                continue
            
            for rel_id in self.outgoing_relations.get(current_id, set()) | self.incoming_relations.get(current_id, set()):
                rel = self.relations.get(rel_id)
                if not rel:
                    continue
                
                if relation_types and rel.relation_type not in relation_types:
                    continue
                
                neighbor_id = rel.target_entity_id if rel.source_entity_id == current_id else rel.source_entity_id
                
                if neighbor_id not in visited:
                    visited.add(neighbor_id)
                    neighbor_entity = self.entities.get(neighbor_id)
                    
                    if neighbor_entity:
                        related.append({
                            "entity": {
                                "id": neighbor_entity.entity_id,
                                "name": neighbor_entity.name,
                                "type": neighbor_entity.entity_type,
                            },
                            "relation": rel.relation_type,
                            "depth": current_depth + 1,
                        })
                    
                    queue.append((neighbor_id, current_depth + 1))
        
        return related
    
    async def get_entity(self, entity_name: str) -> Optional[Dict]:
        entity_id = self.entity_by_name.get(entity_name)
        if not entity_id:
            return None
        
        entity = self.entities[entity_id]
        
        return {
            "entity_id": entity.entity_id,
            "type": entity.entity_type,
            "name": entity.name,
            "description": entity.description,
            "properties": entity.properties,
            "source": entity.source,
            "created_at": entity.created_at,
        }
    
    async def get_stats(self) -> Dict:
        return {
            "name": self.name,
            "total_entities": self.stats["total_entities"],
            "total_relations": self.stats["total_relations"],
            "entities_by_type": dict(self.stats["entities_by_type"]),
            "relations_by_type": dict(self.stats["relations_by_type"]),
            "queries_processed": self.stats["queries_processed"],
        }
