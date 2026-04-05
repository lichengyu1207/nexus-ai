"""
慢查询监控模块 - pg_stat_statements
监控慢查询，定期优化，性能分析
"""

from enum import Enum
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, field
from datetime import datetime, timedelta
import asyncio
import asyncpg
import logging
import json
from collections import defaultdict

logger = logging.getLogger(__name__)


class QueryType(Enum):
    SELECT = "SELECT"
    INSERT = "INSERT"
    UPDATE = "UPDATE"
    DELETE = "DELETE"
    OTHER = "OTHER"


class OptimizationType(Enum):
    ADD_INDEX = "add_index"
    MODIFY_INDEX = "modify_index"
    REWRITE_QUERY = "rewrite_query"
    VACUUM = "vacuum"
    ANALYZE = "analyze"
    PARTITION = "partition"


@dataclass
class SlowQuery:
    query_id: str
    query_text: str
    query_type: QueryType
    calls: int
    total_time_ms: float
    mean_time_ms: float
    min_time_ms: float
    max_time_ms: float
    rows_affected: int
    shared_blks_hit: int
    shared_blks_read: int
    timestamp: datetime
    database_name: str = ""
    user_name: str = ""
    client_addr: str = ""
    plan: Optional[str] = None
    
    @property
    def cache_hit_ratio(self) -> float:
        total = self.shared_blks_hit + self.shared_blks_read
        if total == 0:
            return 1.0
        return self.shared_blks_hit / total
        
    @property
    def time_per_row(self) -> float:
        if self.rows_affected == 0:
            return self.mean_time_ms
        return self.mean_time_ms / self.rows_affected


@dataclass
class QueryPlan:
    plan_text: str
    total_cost: float
    plan_rows: int
    plan_width: int
    execution_time_ms: float
    planning_time_ms: float
    nodes: List[Dict[str, Any]] = field(default_factory=list)


@dataclass
class OptimizationSuggestion:
    query_id: str
    optimization_type: OptimizationType
    description: str
    sql_command: str
    estimated_improvement: float
    priority: int
    applied: bool = False


class PgStatStatementsMonitor:
    def __init__(self, connection_pool: asyncpg.Pool):
        self.pool = connection_pool
        self._slow_queries: List[SlowQuery] = []
        self._suggestions: List[OptimizationSuggestion] = []
        self._slow_query_threshold_ms = 100
        self._top_n_queries = 20
        
    async def enable_pg_stat_statements(self):
        async with self.pool.acquire() as conn:
            try:
                await conn.execute("CREATE EXTENSION IF NOT EXISTS pg_stat_statements;")
                logger.info("pg_stat_statements extension enabled")
            except Exception as e:
                logger.warning(f"Could not enable pg_stat_statements: {e}")
                
    async def collect_slow_queries(self) -> List[SlowQuery]:
        async with self.pool.acquire() as conn:
            try:
                rows = await conn.fetch("""
                    SELECT 
                        queryid,
                        query,
                        calls,
                        total_exec_time,
                        mean_exec_time,
                        min_exec_time,
                        max_exec_time,
                        rows,
                        shared_blks_hit,
                        shared_blks_read,
                        dbid,
                        userid
                    FROM pg_stat_statements
                    WHERE mean_exec_time > $1
                    ORDER BY total_exec_time DESC
                    LIMIT $2
                """, self._slow_query_threshold_ms, self._top_n_queries)
            except Exception as e:
                logger.error(f"Error querying pg_stat_statements: {e}")
                return []
                
        slow_queries = []
        for row in rows:
            query_text = row["query"]
            query_type = self._determine_query_type(query_text)
            
            query = SlowQuery(
                query_id=str(row["queryid"]),
                query_text=query_text,
                query_type=query_type,
                calls=row["calls"],
                total_time_ms=row["total_exec_time"],
                mean_time_ms=row["mean_exec_time"],
                min_time_ms=row["min_exec_time"],
                max_time_ms=row["max_exec_time"],
                rows_affected=row["rows"],
                shared_blks_hit=row["shared_blks_hit"],
                shared_blks_read=row["shared_blks_read"],
                timestamp=datetime.now()
            )
            slow_queries.append(query)
            
        self._slow_queries = slow_queries
        return slow_queries
        
    def _determine_query_type(self, query: str) -> QueryType:
        query_upper = query.strip().upper()
        if query_upper.startswith("SELECT"):
            return QueryType.SELECT
        elif query_upper.startswith("INSERT"):
            return QueryType.INSERT
        elif query_upper.startswith("UPDATE"):
            return QueryType.UPDATE
        elif query_upper.startswith("DELETE"):
            return QueryType.DELETE
        return QueryType.OTHER
        
    async def explain_query(self, query: str) -> Optional[QueryPlan]:
        async with self.pool.acquire() as conn:
            try:
                result = await conn.fetch(f"EXPLAIN (ANALYZE, BUFFERS, FORMAT JSON) {query}")
                
                if result:
                    plan_data = result[0]
                    plan_json = json.loads(plan_data[0]) if isinstance(plan_data[0], str) else plan_data[0]
                    
                    plan = plan_json.get("Plan", {})
                    
                    return QueryPlan(
                        plan_text=json.dumps(plan_json, indent=2),
                        total_cost=plan.get("Total Cost", 0),
                        plan_rows=plan.get("Plan Rows", 0),
                        plan_width=plan.get("Plan Width", 0),
                        execution_time_ms=plan_json.get("Execution Time", 0),
                        planning_time_ms=plan_json.get("Planning Time", 0),
                        nodes=self._extract_plan_nodes(plan)
                    )
            except Exception as e:
                logger.error(f"Error explaining query: {e}")
                
        return None
        
    def _extract_plan_nodes(self, plan: Dict[str, Any]) -> List[Dict[str, Any]]:
        nodes = []
        
        def extract(node: Dict[str, Any], depth: int = 0):
            if not isinstance(node, dict):
                return
                
            nodes.append({
                "type": node.get("Node Type", "Unknown"),
                "cost": node.get("Total Cost", 0),
                "rows": node.get("Plan Rows", 0),
                "depth": depth
            })
            
            if "Plans" in node:
                for child in node["Plans"]:
                    extract(child, depth + 1)
                    
        extract(plan)
        return nodes
        
    async def analyze_query_patterns(self) -> Dict[str, Any]:
        if not self._slow_queries:
            await self.collect_slow_queries()
            
        by_type = defaultdict(list)
        for query in self._slow_queries:
            by_type[query.query_type.value].append(query)
            
        patterns = {
            "total_slow_queries": len(self._slow_queries),
            "by_type": {
                query_type: {
                    "count": len(queries),
                    "avg_time_ms": sum(q.mean_time_ms for q in queries) / len(queries) if queries else 0,
                    "total_calls": sum(q.calls for q in queries)
                }
                for query_type, queries in by_type.items()
            },
            "top_by_total_time": [
                {
                    "query_id": q.query_id,
                    "mean_time_ms": q.mean_time_ms,
                    "calls": q.calls,
                    "total_time_ms": q.total_time_ms
                }
                for q in sorted(self._slow_queries, key=lambda x: x.total_time_ms, reverse=True)[:5]
            ],
            "low_cache_hit_ratio": [
                {
                    "query_id": q.query_id,
                    "cache_hit_ratio": q.cache_hit_ratio,
                    "mean_time_ms": q.mean_time_ms
                }
                for q in self._slow_queries
                if q.cache_hit_ratio < 0.9
            ]
        }
        
        return patterns
        
    async def generate_optimization_suggestions(self) -> List[OptimizationSuggestion]:
        if not self._slow_queries:
            await self.collect_slow_queries()
            
        suggestions = []
        
        for query in self._slow_queries:
            if query.cache_hit_ratio < 0.8:
                suggestions.append(OptimizationSuggestion(
                    query_id=query.query_id,
                    optimization_type=OptimizationType.ADD_INDEX,
                    description=f"低缓存命中率 ({query.cache_hit_ratio:.2%})，建议检查索引或增加shared_buffers",
                    sql_command="-- 检查查询涉及的表索引",
                    estimated_improvement=(1 - query.cache_hit_ratio) * 50,
                    priority=1
                ))
                
            if query.mean_time_ms > 1000:
                plan = await self.explain_query(query.query_text)
                if plan:
                    seq_scan_nodes = [n for n in plan.nodes if "Seq Scan" in n.get("type", "")]
                    if seq_scan_nodes:
                        suggestions.append(OptimizationSuggestion(
                            query_id=query.query_id,
                            optimization_type=OptimizationType.ADD_INDEX,
                            description=f"检测到顺序扫描，建议添加索引",
                            sql_command="-- 分析查询并创建适当索引",
                            estimated_improvement=70,
                            priority=1
                        ))
                        
            if query.rows_affected > 10000 and query.query_type == QueryType.SELECT:
                suggestions.append(OptimizationSuggestion(
                    query_id=query.query_id,
                    optimization_type=OptimizationType.REWRITE_QUERY,
                    description="返回大量行，建议添加LIMIT或分页",
                    sql_command="-- 添加LIMIT子句或实现分页",
                    estimated_improvement=60,
                    priority=2
                ))
                
        self._suggestions = suggestions
        return suggestions
        
    async def get_table_statistics(self) -> List[Dict[str, Any]]:
        async with self.pool.acquire() as conn:
            rows = await conn.fetch("""
                SELECT 
                    schemaname,
                    relname as table_name,
                    seq_scan,
                    seq_tup_read,
                    idx_scan,
                    idx_tup_fetch,
                    n_tup_ins,
                    n_tup_upd,
                    n_tup_del,
                    n_tup_hot_upd,
                    n_live_tup,
                    n_dead_tup,
                    vacuum_count,
                    autovacuum_count,
                    analyze_count,
                    autoanalyze_count
                FROM pg_stat_user_tables
                ORDER BY seq_scan DESC
            """)
            
        return [dict(r) for r in rows]
        
    async def get_index_usage_stats(self) -> List[Dict[str, Any]]:
        async with self.pool.acquire() as conn:
            rows = await conn.fetch("""
                SELECT 
                    schemaname,
                    relname as table_name,
                    indexrelname as index_name,
                    idx_scan,
                    idx_tup_read,
                    idx_tup_fetch,
                    pg_relation_size(indexrelid) as index_size
                FROM pg_stat_user_indexes
                ORDER BY idx_scan DESC
            """)
            
        return [dict(r) for r in rows]
        
    async def reset_stats(self):
        async with self.pool.acquire() as conn:
            await conn.execute("SELECT pg_stat_statements_reset();")
        logger.info("pg_stat_statements reset")


class QueryPerformanceAnalyzer:
    def __init__(self, monitor: PgStatStatementsMonitor):
        self.monitor = monitor
        self._history: List[Dict[str, Any]] = []
        
    async def run_analysis(self) -> Dict[str, Any]:
        slow_queries = await self.monitor.collect_slow_queries()
        patterns = await self.monitor.analyze_query_patterns()
        suggestions = await self.monitor.generate_optimization_suggestions()
        table_stats = await self.monitor.get_table_statistics()
        index_stats = await self.monitor.get_index_usage_stats()
        
        analysis = {
            "timestamp": datetime.now().isoformat(),
            "slow_queries_count": len(slow_queries),
            "patterns": patterns,
            "suggestions": [
                {
                    "query_id": s.query_id,
                    "type": s.optimization_type.value,
                    "description": s.description,
                    "priority": s.priority,
                    "estimated_improvement": f"{s.estimated_improvement}%"
                }
                for s in suggestions
            ],
            "table_statistics": table_stats[:10],
            "index_statistics": index_stats[:10],
            "recommendations": self._generate_recommendations(slow_queries, table_stats)
        }
        
        self._history.append(analysis)
        
        return analysis
        
    def _generate_recommendations(
        self,
        slow_queries: List[SlowQuery],
        table_stats: List[Dict[str, Any]]
    ) -> List[str]:
        recommendations = []
        
        high_seq_scan_tables = [
            t for t in table_stats
            if t["seq_scan"] > 1000 and t["idx_scan"] < t["seq_scan"]
        ]
        if high_seq_scan_tables:
            recommendations.append(
                f"发现 {len(high_seq_scan_tables)} 个表顺序扫描过多，建议检查索引策略"
            )
            
        high_dead_tuples = [
            t for t in table_stats
            if t["n_dead_tup"] > 10000
        ]
        if high_dead_tuples:
            recommendations.append(
                f"发现 {len(high_dead_tuples)} 个表有大量死元组，建议执行VACUUM"
            )
            
        very_slow_queries = [q for q in slow_queries if q.mean_time_ms > 5000]
        if very_slow_queries:
            recommendations.append(
                f"发现 {len(very_slow_queries)} 个极慢查询(>5s)，需要紧急优化"
            )
            
        return recommendations
        
    def get_trend_analysis(self, days: int = 7) -> Dict[str, Any]:
        cutoff = datetime.now() - timedelta(days=days)
        
        recent_history = [
            h for h in self._history
            if datetime.fromisoformat(h["timestamp"]) >= cutoff
        ]
        
        if len(recent_history) < 2:
            return {"status": "insufficient_data"}
            
        first = recent_history[0]
        last = recent_history[-1]
        
        slow_query_trend = (
            last["slow_queries_count"] - first["slow_queries_count"]
        ) / max(first["slow_queries_count"], 1) * 100
        
        return {
            "period_days": days,
            "data_points": len(recent_history),
            "slow_query_trend_percent": round(slow_query_trend, 2),
            "improving": slow_query_trend < 0,
            "first_snapshot": first["timestamp"],
            "last_snapshot": last["timestamp"]
        }


class AutoOptimizer:
    def __init__(self, monitor: PgStatStatementsMonitor):
        self.monitor = monitor
        self._auto_vacuum_enabled = True
        self._auto_analyze_enabled = True
        self._vacuum_threshold = 10000
        self._analyze_threshold = 1000
        
    async def run_auto_optimization(self) -> Dict[str, Any]:
        results = {
            "vacuum_tables": [],
            "analyze_tables": [],
            "errors": []
        }
        
        table_stats = await self.monitor.get_table_statistics()
        
        for table in table_stats:
            table_name = f"{table['schemaname']}.{table['relname']}"
            
            if self._auto_vacuum_enabled and table["n_dead_tup"] > self._vacuum_threshold:
                try:
                    async with self.monitor.pool.acquire() as conn:
                        await conn.execute(f"VACUUM {table_name};")
                    results["vacuum_tables"].append(table_name)
                    logger.info(f"Auto-vacuumed: {table_name}")
                except Exception as e:
                    results["errors"].append(f"Vacuum failed for {table_name}: {e}")
                    
            if self._auto_analyze_enabled and table["n_tup_ins"] + table["n_tup_upd"] + table["n_tup_del"] > self._analyze_threshold:
                try:
                    async with self.monitor.pool.acquire() as conn:
                        await conn.execute(f"ANALYZE {table_name};")
                    results["analyze_tables"].append(table_name)
                    logger.info(f"Auto-analyzed: {table_name}")
                except Exception as e:
                    results["errors"].append(f"Analyze failed for {table_name}: {e}")
                    
        return results


async def create_query_monitor(pool: asyncpg.Pool) -> PgStatStatementsMonitor:
    monitor = PgStatStatementsMonitor(pool)
    await monitor.enable_pg_stat_statements()
    return monitor
