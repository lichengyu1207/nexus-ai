# -*- coding: utf-8 -*-
"""
Report Version Manager
Manages report versions, history, and comparison
"""
import logging
import uuid
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field
from enum import Enum
import json
from datetime import datetime

from backend.database_pg import PostgreSQLConnectionPool

logger = logging.getLogger(__name__)


class VersionChangeType(Enum):
    INITIAL = "initial"
    REVISION = "revision"
    RECALL = "recall"
    UPDATE = "update"
    CORRECTION = "correction"


@dataclass
class VersionDiff:
    field: str
    old_value: Any
    new_value: Any
    change_type: str


@dataclass
class VersionInfo:
    version: int
    report_id: str
    created_at: str
    change_type: str
    change_reason: str
    changes: List[VersionDiff]


class ReportVersionManager:
    def __init__(self, db: PostgreSQLConnectionPool = None):
        self.db = db
        self._max_versions = 10
    
    async def create_version(
        self,
        report_id: str,
        content: Dict,
        change_type: str = VersionChangeType.INITIAL.value,
        change_reason: str = "初始版本",
        parent_id: str = None
    ) -> str:
        if not self.db:
            return report_id
        
        async with self.db.get_connection() as conn:
            if parent_id:
                parent = await conn.fetchrow(
                    "SELECT version FROM consultation_reports WHERE id = $1",
                    parent_id
                )
                version = (parent["version"] + 1) if parent else 1
            else:
                version = 1
            
            await conn.execute("""
                UPDATE consultation_reports 
                SET is_latest = false 
                WHERE session_id = (
                    SELECT session_id FROM consultation_reports WHERE id = $1
                )
            """, report_id)
            
            new_report_id = str(uuid.uuid4())
            
            await conn.execute("""
                INSERT INTO consultation_reports 
                (id, session_id, user_id, title, content, persona, gene_dimensions,
                 data_sources, referenced_cases, version, is_latest, parent_report_id)
                SELECT $1, session_id, user_id, title, $2::jsonb, persona, gene_dimensions,
                       data_sources, referenced_cases, $3, true, $4
                FROM consultation_reports 
                WHERE id = $5
            """, new_report_id, content, version, parent_id, report_id)
            
            await self._cleanup_old_versions(conn, report_id)
            
            return new_report_id
    
    async def get_version_history(
        self,
        session_id: str
    ) -> List[VersionInfo]:
        if not self.db:
            return []
        
        async with self.db.get_connection() as conn:
            rows = await conn.fetch("""
                SELECT id, version, generated_at, parent_report_id, content
                FROM consultation_reports 
                WHERE session_id = $1 
                ORDER BY version DESC
            """, session_id)
            
            versions = []
            prev_content = None
            
            for row in rows:
                content = row["content"]
                changes = []
                
                if prev_content:
                    changes = self._compare_contents(prev_content, content)
                
                change_type = VersionChangeType.INITIAL.value
                change_reason = "初始版本"
                
                if row["parent_report_id"]:
                    change_type = VersionChangeType.REVISION.value
                    change_reason = "修订版本"
                
                versions.append(VersionInfo(
                    version=row["version"],
                    report_id=str(row["id"]),
                    created_at=str(row["generated_at"]),
                    change_type=change_type,
                    change_reason=change_reason,
                    changes=changes
                ))
                
                prev_content = content
            
            return versions
    
    async def get_version(
        self,
        report_id: str
    ) -> Optional[Dict]:
        if not self.db:
            return None
        
        async with self.db.get_connection() as conn:
            row = await conn.fetchrow(
                "SELECT * FROM consultation_reports WHERE id = $1",
                report_id
            )
            
            if row:
                return dict(row)
        
        return None
    
    async def get_latest_version(
        self,
        session_id: str
    ) -> Optional[Dict]:
        if not self.db:
            return None
        
        async with self.db.get_connection() as conn:
            row = await conn.fetchrow(
                "SELECT * FROM consultation_reports WHERE session_id = $1 AND is_latest = true",
                session_id
            )
            
            if row:
                return dict(row)
        
        return None
    
    async def compare_versions(
        self,
        report_id_1: str,
        report_id_2: str
    ) -> List[VersionDiff]:
        if not self.db:
            return []
        
        async with self.db.get_connection() as conn:
            report1 = await conn.fetchrow(
                "SELECT content FROM consultation_reports WHERE id = $1",
                report_id_1
            )
            report2 = await conn.fetchrow(
                "SELECT content FROM consultation_reports WHERE id = $1",
                report_id_2
            )
            
            if not report1 or not report2:
                return []
            
            return self._compare_contents(report1["content"], report2["content"])
    
    def _compare_contents(self, content1: Dict, content2: Dict) -> List[VersionDiff]:
        diffs = []
        
        def compare_dicts(d1, d2, path=""):
            if isinstance(d1, dict) and isinstance(d2, dict):
                all_keys = set(d1.keys()) | set(d2.keys())
                for key in all_keys:
                    new_path = f"{path}.{key}" if path else key
                    if key not in d1:
                        diffs.append(VersionDiff(
                            field=new_path,
                            old_value=None,
                            new_value=d2[key],
                            change_type="added"
                        ))
                    elif key not in d2:
                        diffs.append(VersionDiff(
                            field=new_path,
                            old_value=d1[key],
                            new_value=None,
                            change_type="removed"
                        ))
                    elif d1[key] != d2[key]:
                        if isinstance(d1[key], (dict, list)) and isinstance(d2[key], (dict, list)):
                            compare_dicts(d1[key], d2[key], new_path)
                        else:
                            diffs.append(VersionDiff(
                                field=new_path,
                                old_value=d1[key],
                                new_value=d2[key],
                                change_type="modified"
                            ))
            elif isinstance(d1, list) and isinstance(d2, list):
                if len(d1) != len(d2):
                    diffs.append(VersionDiff(
                        field=path,
                        old_value=f"length={len(d1)}",
                        new_value=f"length={len(d2)}",
                        change_type="list_modified"
                    ))
        
        compare_dicts(content1, content2)
        return diffs
    
    async def _cleanup_old_versions(self, conn, report_id: str):
        session_id = await conn.fetchval(
            "SELECT session_id FROM consultation_reports WHERE id = $1",
            report_id
        )
        
        if not session_id:
            return
        
        count = await conn.fetchval(
            "SELECT COUNT(*) FROM consultation_reports WHERE session_id = $1",
            session_id
        )
        
        if count > self._max_versions:
            to_delete = count - self._max_versions
            
            old_ids = await conn.fetch("""
                SELECT id FROM consultation_reports 
                WHERE session_id = $1 AND is_latest = false
                ORDER BY version ASC
                LIMIT $2
            """, session_id, to_delete)
            
            for row in old_ids:
                await conn.execute(
                    "DELETE FROM consultation_reports WHERE id = $1",
                    row["id"]
                )
    
    async def rollback_to_version(
        self,
        report_id: str,
        target_version: int
    ) -> Optional[str]:
        if not self.db:
            return None
        
        async with self.db.get_connection() as conn:
            session_id = await conn.fetchval(
                "SELECT session_id FROM consultation_reports WHERE id = $1",
                report_id
            )
            
            if not session_id:
                return None
            
            target_report = await conn.fetchrow(
                "SELECT * FROM consultation_reports WHERE session_id = $1 AND version = $2",
                session_id, target_version
            )
            
            if not target_report:
                return None
            
            await conn.execute("""
                UPDATE consultation_reports 
                SET is_latest = false 
                WHERE session_id = $1
            """, session_id)
            
            new_report_id = str(uuid.uuid4())
            new_version = await conn.fetchval(
                "SELECT MAX(version) FROM consultation_reports WHERE session_id = $1",
                session_id
            ) + 1
            
            await conn.execute("""
                INSERT INTO consultation_reports 
                (id, session_id, user_id, title, content, persona, gene_dimensions,
                 data_sources, referenced_cases, version, is_latest, parent_report_id)
                VALUES ($1, $2, $3, $4, $5::jsonb, $6, $7::jsonb, $8::jsonb, $9, $10, true, $11)
            """, new_report_id, session_id, target_report["user_id"],
                target_report["title"], target_report["content"],
                target_report["persona"], target_report["gene_dimensions"],
                target_report["data_sources"], target_report["referenced_cases"],
                new_version, target_report["id"])
            
            return new_report_id
    
    def format_diff_for_display(self, diffs: List[VersionDiff]) -> str:
        if not diffs:
            return "无变化"
        
        lines = []
        for diff in diffs:
            if diff.change_type == "added":
                lines.append(f"+ {diff.field}: {diff.new_value}")
            elif diff.change_type == "removed":
                lines.append(f"- {diff.field}: {diff.old_value}")
            elif diff.change_type == "modified":
                lines.append(f"~ {diff.field}: {diff.old_value} → {diff.new_value}")
            else:
                lines.append(f"* {diff.field}: {diff.change_type}")
        
        return "\n".join(lines)


report_version_manager: Optional[ReportVersionManager] = None


async def get_report_version_manager(db: PostgreSQLConnectionPool = None) -> ReportVersionManager:
    global report_version_manager
    if report_version_manager is None:
        report_version_manager = ReportVersionManager(db)
    return report_version_manager
