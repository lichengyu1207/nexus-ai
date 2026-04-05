# -*- coding: utf-8 -*-
"""
Skill Registry Service
Manages skill CRUD operations and versioning
"""
from dataclasses import dataclass, field
from typing import Optional, List, Dict, Any
from datetime import datetime
import json
import uuid


class SkillType:
    BUILTIN = "builtin"
    EXTENSION = "extension"
    EXTERNAL = "external"


class SkillCategory:
    PROPERTY = "property"
    DESTINY = "destiny"
    GENERAL = "general"
    DATA = "data"
    SECURITY = "security"


class SkillStatus:
    DRAFT = "draft"
    REVIEW = "review"
    PUBLISHED = "published"
    DEPRECATED = "deprecated"


@dataclass
class Skill:
    id: str
    name: str
    description: str
    type: str
    category: str
    input_schema: Dict[str, Any]
    output_schema: Dict[str, Any]
    dependencies: List[str]
    applicable_agents: List[str]
    cost_points: int
    version: str
    avg_time_ms: int = 0
    success_rate: float = 1.0
    developer_id: Optional[str] = None
    status: str = SkillStatus.DRAFT
    download_count: int = 0
    rating: float = 0.0
    icon_url: Optional[str] = None
    code_config: Dict[str, Any] = field(default_factory=dict)
    tags: List[str] = field(default_factory=list)
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)

    @classmethod
    def from_db_row(cls, row: dict) -> "Skill":
        return cls(
            id=str(row.get("id", "")),
            name=row.get("name", ""),
            description=row.get("description", ""),
            type=row.get("type", SkillType.BUILTIN),
            category=row.get("category", SkillCategory.GENERAL),
            input_schema=row.get("input_schema", {}) or {},
            output_schema=row.get("output_schema", {}) or {},
            dependencies=row.get("dependencies", []) or [],
            applicable_agents=row.get("applicable_agents", []) or [],
            cost_points=row.get("cost_points", 0),
            version=row.get("version", "1.0.0"),
            avg_time_ms=row.get("avg_time_ms", 0),
            success_rate=row.get("success_rate", 1.0),
            developer_id=str(row.get("developer_id")) if row.get("developer_id") else None,
            status=row.get("status", SkillStatus.DRAFT),
            download_count=row.get("download_count", 0),
            rating=row.get("rating", 0.0),
            icon_url=row.get("icon_url"),
            code_config=row.get("code_config", {}) or {},
            tags=row.get("tags", []) or [],
            created_at=row.get("created_at", datetime.now()),
            updated_at=row.get("updated_at", datetime.now())
        )

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "type": self.type,
            "category": self.category,
            "input_schema": self.input_schema,
            "output_schema": self.output_schema,
            "dependencies": self.dependencies,
            "applicable_agents": self.applicable_agents,
            "cost_points": self.cost_points,
            "version": self.version,
            "avg_time_ms": self.avg_time_ms,
            "success_rate": self.success_rate,
            "developer_id": self.developer_id,
            "status": self.status,
            "download_count": self.download_count,
            "rating": self.rating,
            "icon_url": self.icon_url,
            "tags": self.tags,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None
        }


@dataclass
class SkillVersion:
    id: str
    skill_id: str
    version: str
    changelog: str
    code_config: Dict[str, Any]
    status: str
    created_at: datetime

    @classmethod
    def from_db_row(cls, row: dict) -> "SkillVersion":
        return cls(
            id=str(row.get("id", "")),
            skill_id=str(row.get("skill_id", "")),
            version=row.get("version", ""),
            changelog=row.get("changelog", ""),
            code_config=row.get("code_config", {}) or {},
            status=row.get("status", "active"),
            created_at=row.get("created_at", datetime.now())
        )


class SkillRegistry:
    def __init__(self, db_pool):
        self.db_pool = db_pool

    async def create_skill(self, skill: Skill) -> Skill:
        skill.id = str(uuid.uuid4())
        skill.created_at = datetime.now()
        skill.updated_at = datetime.now()
        
        async with self.db_pool.acquire() as conn:
            await conn.execute("""
                INSERT INTO skills (id, name, description, type, category, input_schema, output_schema,
                                   dependencies, applicable_agents, cost_points, version, avg_time_ms,
                                   success_rate, developer_id, status, download_count, rating, icon_url,
                                   code_config, tags, created_at, updated_at)
                VALUES ($1, $2, $3, $4, $5, $6::jsonb, $7::jsonb, $8, $9, $10, $11, $12, $13, $14, $15, $16, $17, $18, $19::jsonb, $20, $21, $22)
            """, skill.id, skill.name, skill.description, skill.type, skill.category,
                json.dumps(skill.input_schema), json.dumps(skill.output_schema),
                skill.dependencies, skill.applicable_agents, skill.cost_points, skill.version,
                skill.avg_time_ms, skill.success_rate, skill.developer_id, skill.status,
                skill.download_count, skill.rating, skill.icon_url,
                json.dumps(skill.code_config), skill.tags, skill.created_at, skill.updated_at)
        
        return skill

    async def get_skill(self, skill_id: str) -> Optional[Skill]:
        async with self.db_pool.acquire() as conn:
            row = await conn.fetchrow(
                "SELECT * FROM skills WHERE id = $1", skill_id
            )
            if row:
                return Skill.from_db_row(dict(row))
        return None

    async def list_skills(
        self,
        category: Optional[str] = None,
        skill_type: Optional[str] = None,
        status: Optional[str] = None,
        keyword: Optional[str] = None,
        sort_by: str = "created_at",
        sort_order: str = "DESC",
        page: int = 1,
        size: int = 20
    ) -> tuple[List[Skill], int]:
        conditions = []
        params = []
        param_idx = 1
        
        if category:
            conditions.append(f"category = ${param_idx}")
            params.append(category)
            param_idx += 1
        
        if skill_type:
            conditions.append(f"type = ${param_idx}")
            params.append(skill_type)
            param_idx += 1
        
        if status:
            conditions.append(f"status = ${param_idx}")
            params.append(status)
            param_idx += 1
        
        if keyword:
            conditions.append(f"(name ILIKE ${param_idx} OR description ILIKE ${param_idx})")
            params.append(f"%{keyword}%")
            param_idx += 1
        
        where_clause = " AND ".join(conditions) if conditions else "1=1"
        
        valid_sort_fields = ["created_at", "download_count", "rating", "cost_points", "name"]
        if sort_by not in valid_sort_fields:
            sort_by = "created_at"
        if sort_order.upper() not in ["ASC", "DESC"]:
            sort_order = "DESC"
        
        async with self.db_pool.acquire() as conn:
            count_row = await conn.fetchrow(
                f"SELECT COUNT(*) as total FROM skills WHERE {where_clause}", *params
            )
            total = count_row["total"] if count_row else 0
            
            offset = (page - 1) * size
            rows = await conn.fetch(
                f"SELECT * FROM skills WHERE {where_clause} ORDER BY {sort_by} {sort_order} LIMIT ${param_idx} OFFSET ${param_idx + 1}",
                *params, size, offset
            )
            
            skills = [Skill.from_db_row(dict(row)) for row in rows]
            return skills, total

    async def update_skill(self, skill_id: str, updates: Dict[str, Any]) -> Optional[Skill]:
        updates["updated_at"] = datetime.now()
        
        set_clauses = []
        params = []
        param_idx = 1
        
        for key, value in updates.items():
            if key in ["input_schema", "output_schema", "code_config"]:
                set_clauses.append(f"{key} = ${param_idx}::jsonb")
                params.append(json.dumps(value))
            elif key in ["dependencies", "applicable_agents", "tags"]:
                set_clauses.append(f"{key} = ${param_idx}")
                params.append(value)
            elif key in ["name", "description", "type", "category", "status", "version", "icon_url"]:
                set_clauses.append(f"{key} = ${param_idx}")
                params.append(value)
            elif key in ["cost_points", "avg_time_ms", "download_count"]:
                set_clauses.append(f"{key} = ${param_idx}")
                params.append(value)
            elif key in ["success_rate", "rating"]:
                set_clauses.append(f"{key} = ${param_idx}")
                params.append(value)
            elif key == "updated_at":
                set_clauses.append(f"{key} = ${param_idx}")
                params.append(value)
            param_idx += 1
        
        if not set_clauses:
            return await self.get_skill(skill_id)
        
        params.append(skill_id)
        
        async with self.db_pool.acquire() as conn:
            await conn.execute(
                f"UPDATE skills SET {', '.join(set_clauses)} WHERE id = ${param_idx}",
                *params
            )
        
        return await self.get_skill(skill_id)

    async def delete_skill(self, skill_id: str) -> bool:
        async with self.db_pool.acquire() as conn:
            result = await conn.execute(
                "DELETE FROM skills WHERE id = $1", skill_id
            )
            return result == "DELETE 1"

    async def increment_download_count(self, skill_id: str):
        async with self.db_pool.acquire() as conn:
            await conn.execute(
                "UPDATE skills SET download_count = download_count + 1 WHERE id = $1",
                skill_id
            )

    async def update_rating(self, skill_id: str):
        async with self.db_pool.acquire() as conn:
            await conn.execute("""
                UPDATE skills SET rating = (
                    SELECT COALESCE(AVG(rating), 0) FROM skill_reviews WHERE skill_id = $1
                ) WHERE id = $1
            """, skill_id)

    async def create_version(self, skill_id: str, version: str, changelog: str, code_config: Dict[str, Any]) -> SkillVersion:
        version_id = str(uuid.uuid4())
        
        async with self.db_pool.acquire() as conn:
            await conn.execute("""
                INSERT INTO skill_versions (id, skill_id, version, changelog, code_config, status)
                VALUES ($1, $2, $3, $4, $5::jsonb, 'active')
            """, version_id, skill_id, version, changelog, json.dumps(code_config))
        
        return SkillVersion(
            id=version_id,
            skill_id=skill_id,
            version=version,
            changelog=changelog,
            code_config=code_config,
            status="active",
            created_at=datetime.now()
        )

    async def get_versions(self, skill_id: str) -> List[SkillVersion]:
        async with self.db_pool.acquire() as conn:
            rows = await conn.fetch(
                "SELECT * FROM skill_versions WHERE skill_id = $1 ORDER BY created_at DESC",
                skill_id
            )
            return [SkillVersion.from_db_row(dict(row)) for row in rows]


_skill_registry: Optional[SkillRegistry] = None


def get_skill_registry() -> Optional[SkillRegistry]:
    return _skill_registry


async def init_skill_registry(db_pool):
    global _skill_registry
    _skill_registry = SkillRegistry(db_pool)
    return _skill_registry
