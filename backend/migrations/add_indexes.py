"""
数据库索引优化迁移脚本
添加必要的索引以提升查询性能
"""
import asyncio
import aiosqlite
import logging
from pathlib import Path

logger = logging.getLogger(__name__)

DB_PATH = Path(__file__).parent.parent / "data" / "app.db"

INDEXES = [
    ("idx_tasks_user_status", "analysis_tasks(user_id, status)"),
    ("idx_tasks_created_at", "analysis_tasks(created_at DESC)"),
    ("idx_tasks_status", "analysis_tasks(status)"),
    ("idx_reports_user_id", "reports(user_id)"),
    ("idx_reports_task_id", "reports(task_id)"),
    ("idx_reports_status", "reports(status)"),
    ("idx_reports_created_at", "reports(created_at DESC)"),
    ("idx_comments_report_id", "comments(report_id)"),
    ("idx_comments_user_id", "comments(user_id)"),
    ("idx_comments_created_at", "comments(created_at DESC)"),
    ("idx_team_members_team_user", "team_members(team_id, user_id)"),
    ("idx_team_members_user_id", "team_members(user_id)"),
    ("idx_notifications_user_read", "notifications(user_id, is_read)"),
    ("idx_notifications_created_at", "notifications(created_at DESC)"),
    ("idx_agent_messages_task_id", "agent_messages(task_id)"),
    ("idx_agent_messages_created_at", "agent_messages(created_at)"),
]


async def create_indexes():
    """创建所有索引"""
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        
        existing_indexes = set()
        cursor = await db.execute(
            "SELECT name FROM sqlite_master WHERE type='index'"
        )
        rows = await cursor.fetchall()
        existing_indexes = {row["name"] for row in rows}
        
        created = 0
        skipped = 0
        
        for index_name, index_def in INDEXES:
            if index_name in existing_indexes:
                logger.info(f"Index already exists: {index_name}")
                skipped += 1
                continue
            
            try:
                await db.execute(f"CREATE INDEX IF NOT EXISTS {index_name} ON {index_def}")
                logger.info(f"Created index: {index_name}")
                created += 1
            except Exception as e:
                logger.error(f"Failed to create index {index_name}: {e}")
        
        await db.commit()
        
        logger.info(f"Index migration complete: {created} created, {skipped} skipped")
        return {"created": created, "skipped": skipped}


async def analyze_tables():
    """分析表统计信息"""
    async with aiosqlite.connect(DB_PATH) as db:
        tables = ["users", "analysis_tasks", "reports", "comments", "notifications", "team_members"]
        
        stats = {}
        for table in tables:
            cursor = await db.execute(f"SELECT COUNT(*) as count FROM {table}")
            row = await cursor.fetchone()
            stats[table] = row[0]
        
        return stats


async def get_query_plan(query: str, params: tuple = None):
    """获取查询计划"""
    async with aiosqlite.connect(DB_PATH) as db:
        cursor = await db.execute(f"EXPLAIN QUERY PLAN {query}", params or ())
        rows = await cursor.fetchall()
        return [dict(row) for row in rows]


async def main():
    """主函数"""
    logging.basicConfig(level=logging.INFO)
    
    print("Creating indexes...")
    result = await create_indexes()
    print(f"Result: {result}")
    
    print("\nTable statistics:")
    stats = await analyze_tables()
    for table, count in stats.items():
        print(f"  {table}: {count} rows")


if __name__ == "__main__":
    asyncio.run(main())
