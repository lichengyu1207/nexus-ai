# -*- coding: utf-8 -*-
"""
Migration: 创建三省系统日志表
"""
import asyncio
import asyncpg
import logging
from pathlib import Path
from dotenv import load_dotenv
import os

logger = logging.getLogger(__name__)

env_path = Path(__file__).parent.parent.parent / ".env"
load_dotenv(env_path)

DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://postgres:147258%40Zxcvbnm@localhost:5432/fangdu")
DATABASE_URL = DATABASE_URL.replace("postgresql+asyncpg://", "postgresql://")

MIGRATION_SQL = """
-- 创建更新时间触发器函数（如果不存在）
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ language 'plpgsql';

-- 三省系统日志表
CREATE TABLE IF NOT EXISTS three_provinces_log (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    task_id UUID NOT NULL,
    province VARCHAR(20) NOT NULL CHECK (province IN ('zhongshu', 'menxia', 'shangshu')),
    action VARCHAR(50) NOT NULL,
    input_data JSONB,
    output_data JSONB,
    duration_ms INTEGER,
    approved BOOLEAN DEFAULT true,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_three_provinces_log_task_id ON three_provinces_log(task_id);
CREATE INDEX IF NOT EXISTS idx_three_provinces_log_province ON three_provinces_log(province);
CREATE INDEX IF NOT EXISTS idx_three_provinces_log_created_at ON three_provinces_log(created_at DESC);

-- 六部协调器状态表
CREATE TABLE IF NOT EXISTS ministry_coordinator_state (
    task_id UUID PRIMARY KEY,
    phase VARCHAR(50) DEFAULT 'init',
    li_status VARCHAR(20) DEFAULT 'pending',
    hu_status VARCHAR(20) DEFAULT 'pending',
    li_guan_status VARCHAR(20) DEFAULT 'pending',
    bing_status VARCHAR(20) DEFAULT 'pending',
    xing_status VARCHAR(20) DEFAULT 'pending',
    gong_status VARCHAR(20) DEFAULT 'pending',
    li_result JSONB,
    hu_result JSONB,
    li_guan_result JSONB,
    bing_result JSONB,
    xing_result JSONB,
    gong_result JSONB,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_ministry_coordinator_phase ON ministry_coordinator_state(phase);

-- 添加更新时间触发器
DROP TRIGGER IF EXISTS update_ministry_coordinator_state_updated_at ON ministry_coordinator_state;
CREATE TRIGGER update_ministry_coordinator_state_updated_at
    BEFORE UPDATE ON ministry_coordinator_state
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();
"""

async def run_migration():
    logger.info("Starting three provinces log tables migration...")
    
    try:
        conn = await asyncpg.connect(DATABASE_URL)
        
        try:
            await conn.execute(MIGRATION_SQL)
            logger.info("Migration completed successfully!")
            
            result = await conn.fetch("""
                SELECT table_name 
                FROM information_schema.tables 
                WHERE table_schema = 'public' 
                AND table_name IN ('three_provinces_log', 'ministry_coordinator_state')
            """)
            logger.info(f"Created tables: {[r['table_name'] for r in result]}")
            
        finally:
            await conn.close()
            
    except Exception as e:
        logger.error(f"Migration failed: {e}")
        raise

if __name__ == "__main__":
    asyncio.run(run_migration())
