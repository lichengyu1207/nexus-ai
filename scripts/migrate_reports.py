#!/usr/bin/env python3
"""
报告系统数据库迁移脚本
执行报告相关表的创建和升级
"""
import asyncio
import aiosqlite
from pathlib import Path
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

DB_PATH = Path(__file__).parent.parent / "data" / "property-ai.db"


async def migrate_reports():
    """执行报告表迁移"""
    logger.info("开始报告系统数据库迁移...")
    
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    
    conn = await aiosqlite.connect(str(DB_PATH))
    conn.row_factory = aiosqlite.Row
    
    try:
        # 创建报告表
        logger.info("创建 reports 表...")
        await conn.execute("""
            CREATE TABLE IF NOT EXISTS reports (
                id TEXT PRIMARY KEY,
                task_id TEXT UNIQUE NOT NULL,
                user_id TEXT NOT NULL,
                status TEXT NOT NULL DEFAULT 'pending',
                content TEXT,
                summary TEXT,
                version INTEGER DEFAULT 1,
                progress INTEGER DEFAULT 0,
                current_section TEXT,
                error_message TEXT,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                completed_at DATETIME,
                FOREIGN KEY (task_id) REFERENCES analysis_tasks(id),
                FOREIGN KEY (user_id) REFERENCES users(id)
            )
        """)
        
        # 创建索引
        logger.info("创建 reports 索引...")
        await conn.execute("CREATE INDEX IF NOT EXISTS idx_reports_task_id ON reports(task_id)")
        await conn.execute("CREATE INDEX IF NOT EXISTS idx_reports_user_id ON reports(user_id)")
        await conn.execute("CREATE INDEX IF NOT EXISTS idx_reports_status ON reports(status)")
        
        # 创建报告版本历史表
        logger.info("创建 report_versions 表...")
        await conn.execute("""
            CREATE TABLE IF NOT EXISTS report_versions (
                id TEXT PRIMARY KEY,
                report_id TEXT NOT NULL,
                version INTEGER NOT NULL,
                content TEXT NOT NULL,
                change_summary TEXT,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (report_id) REFERENCES reports(id),
                UNIQUE(report_id, version)
            )
        """)
        
        await conn.execute("CREATE INDEX IF NOT EXISTS idx_report_versions_report_id ON report_versions(report_id)")
        
        # 创建报告交互表
        logger.info("创建 report_interactions 表...")
        await conn.execute("""
            CREATE TABLE IF NOT EXISTS report_interactions (
                id TEXT PRIMARY KEY,
                report_id TEXT NOT NULL,
                user_id TEXT NOT NULL,
                interaction_type TEXT NOT NULL,
                content TEXT,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (report_id) REFERENCES reports(id),
                FOREIGN KEY (user_id) REFERENCES users(id),
                UNIQUE(report_id, user_id, interaction_type)
            )
        """)
        
        await conn.execute("CREATE INDEX IF NOT EXISTS idx_report_interactions_report_id ON report_interactions(report_id)")
        await conn.execute("CREATE INDEX IF NOT EXISTS idx_report_interactions_user_id ON report_interactions(user_id)")
        
        await conn.commit()
        logger.info("报告系统数据库迁移完成！")
        
        # 验证表结构
        logger.info("验证表结构...")
        cursor = await conn.execute("SELECT name FROM sqlite_master WHERE type='table' AND name LIKE 'report%'")
        tables = await cursor.fetchall()
        logger.info(f"已创建的表: {[t['name'] for t in tables]}")
        
    except Exception as e:
        logger.error(f"迁移失败: {e}")
        raise
    finally:
        await conn.close()


async def migrate_analysis_reports():
    """迁移旧的 analysis_reports 数据到新的 reports 表"""
    logger.info("检查是否需要迁移旧数据...")
    
    conn = await aiosqlite.connect(str(DB_PATH))
    conn.row_factory = aiosqlite.Row
    
    try:
        # 检查旧表是否存在
        cursor = await conn.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name='analysis_reports'"
        )
        if not await cursor.fetchone():
            logger.info("旧表不存在，跳过数据迁移")
            return
        
        # 检查旧表是否有数据
        cursor = await conn.execute("SELECT COUNT(*) as count FROM analysis_reports")
        row = await cursor.fetchone()
        old_count = row['count']
        
        if old_count == 0:
            logger.info("旧表无数据，跳过数据迁移")
            return
        
        logger.info(f"发现 {old_count} 条旧数据，开始迁移...")
        
        # 迁移数据
        cursor = await conn.execute("""
            SELECT 
                id, task_id, user_id, query, style,
                executive_summary, core_findings, detailed_analysis,
                investment_advice, risk_warnings, data_sources,
                confidence_score, created_at
            FROM analysis_reports
        """)
        
        old_reports = await cursor.fetchall()
        
        for old in old_reports:
            import json
            import uuid
            
            # 构建新格式内容
            content = {
                "executive_summary": old["executive_summary"],
                "core_findings": json.loads(old["core_findings"]) if old["core_findings"] else None,
                "detailed_analysis": json.loads(old["detailed_analysis"]) if old["detailed_analysis"] else None,
                "investment_advice": json.loads(old["investment_advice"]) if old["investment_advice"] else None,
                "risk_warnings": json.loads(old["risk_warnings"]) if old["risk_warnings"] else None,
                "data_sources": json.loads(old["data_sources"]) if old["data_sources"] else None,
                "confidence_score": old["confidence_score"],
                "style": old["style"],
                "query": old["query"]
            }
            
            summary = old["executive_summary"][:200] if old["executive_summary"] else None
            
            # 插入新表
            try:
                await conn.execute("""
                    INSERT OR IGNORE INTO reports 
                    (id, task_id, user_id, status, content, summary, progress, created_at, completed_at)
                    VALUES (?, ?, ?, 'completed', ?, ?, 100, ?, ?)
                """, (
                    str(uuid.uuid4()),
                    old["task_id"],
                    old["user_id"],
                    json.dumps(content, ensure_ascii=False),
                    summary,
                    old["created_at"],
                    old["created_at"]
                ))
            except Exception as e:
                logger.warning(f"迁移记录 {old['id']} 失败: {e}")
        
        await conn.commit()
        logger.info("旧数据迁移完成！")
        
    except Exception as e:
        logger.error(f"数据迁移失败: {e}")
    finally:
        await conn.close()


async def main():
    """主函数"""
    print("=" * 50)
    print("报告系统数据库迁移脚本")
    print("=" * 50)
    print()
    
    await migrate_reports()
    await migrate_analysis_reports()
    
    print()
    print("=" * 50)
    print("迁移完成！")
    print("=" * 50)


if __name__ == "__main__":
    asyncio.run(main())
