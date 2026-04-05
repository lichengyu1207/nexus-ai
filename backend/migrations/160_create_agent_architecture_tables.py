# -*- coding: utf-8 -*-
"""
Migration: 创建智能体架构核心表
包括: agents, agent_logs, task_queue, ministry_coordinator
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
-- 智能体表
CREATE TABLE IF NOT EXISTS agents (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id VARCHAR(36) REFERENCES users(id) ON DELETE CASCADE,
    name VARCHAR(100) NOT NULL,
    role VARCHAR(20) NOT NULL CHECK (role IN ('li', 'hu', 'li_guan', 'bing', 'xing', 'gong', 'zhongshu', 'menxia', 'shangshu')),
    level INTEGER DEFAULT 1 CHECK (level BETWEEN 1 AND 10),
    energy FLOAT DEFAULT 100.0 CHECK (energy BETWEEN 0 AND 100),
    max_energy FLOAT DEFAULT 100.0,
    status VARCHAR(20) DEFAULT 'idle' CHECK (status IN ('idle', 'working', 'learning', 'resting', 'reproducing', 'dying', 'dead')),
    capabilities JSONB DEFAULT '[]',
    gene_pool JSONB DEFAULT '{}',
    experience INTEGER DEFAULT 0,
    total_tasks_completed INTEGER DEFAULT 0,
    success_rate FLOAT DEFAULT 0.0,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_agents_user_id ON agents(user_id);
CREATE INDEX IF NOT EXISTS idx_agents_role ON agents(role);
CREATE INDEX IF NOT EXISTS idx_agents_status ON agents(status);

-- 智能体日志表
CREATE TABLE IF NOT EXISTS agent_logs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    agent_id UUID REFERENCES agents(id) ON DELETE SET NULL,
    task_id VARCHAR(36) REFERENCES tasks(id) ON DELETE SET NULL,
    action VARCHAR(50) NOT NULL,
    input_data JSONB,
    output_data JSONB,
    energy_consumed FLOAT DEFAULT 0.0,
    duration_ms INTEGER,
    success BOOLEAN DEFAULT true,
    error_message TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_agent_logs_agent_id ON agent_logs(agent_id);
CREATE INDEX IF NOT EXISTS idx_agent_logs_task_id ON agent_logs(task_id);
CREATE INDEX IF NOT EXISTS idx_agent_logs_created_at ON agent_logs(created_at DESC);

-- 任务队列表
CREATE TABLE IF NOT EXISTS task_queue (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    task_id VARCHAR(36) REFERENCES tasks(id) ON DELETE CASCADE,
    priority INTEGER DEFAULT 0,
    status VARCHAR(20) DEFAULT 'pending' CHECK (status IN ('pending', 'processing', 'completed', 'failed', 'cancelled')),
    assigned_agent_id UUID REFERENCES agents(id) ON DELETE SET NULL,
    retry_count INTEGER DEFAULT 0,
    max_retries INTEGER DEFAULT 3,
    scheduled_at TIMESTAMP WITH TIME ZONE,
    started_at TIMESTAMP WITH TIME ZONE,
    completed_at TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_task_queue_status ON task_queue(status);
CREATE INDEX IF NOT EXISTS idx_task_queue_priority ON task_queue(priority DESC);
CREATE INDEX IF NOT EXISTS idx_task_queue_scheduled ON task_queue(scheduled_at);

-- 六部协调器状态表
CREATE TABLE IF NOT EXISTS ministry_coordinator_state (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    task_id VARCHAR(36) REFERENCES tasks(id) ON DELETE CASCADE UNIQUE,
    phase VARCHAR(50) DEFAULT 'init',
    li_bu_status VARCHAR(20) DEFAULT 'pending',
    hu_bu_status VARCHAR(20) DEFAULT 'pending',
    li_guan_status VARCHAR(20) DEFAULT 'pending',
    bing_bu_status VARCHAR(20) DEFAULT 'pending',
    xing_bu_status VARCHAR(20) DEFAULT 'pending',
    gong_bu_status VARCHAR(20) DEFAULT 'pending',
    li_bu_result JSONB,
    hu_bu_result JSONB,
    li_guan_result JSONB,
    bing_bu_result JSONB,
    xing_bu_result JSONB,
    gong_bu_result JSONB,
    final_result JSONB,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_ministry_coordinator_task_id ON ministry_coordinator_state(task_id);

-- 三省决策记录表
-- ⚠️ 注意：此表定义已迁移至 170_create_three_provinces_tables.py（更完整的版本）
-- 此处保留是为了向后兼容，实际以170号迁移为准
CREATE TABLE IF NOT EXISTS three_provinces_log (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    task_id VARCHAR(36) REFERENCES tasks(id) ON DELETE CASCADE,
    province VARCHAR(20) NOT NULL CHECK (province IN ('zhongshu', 'menxia', 'shangshu')),
    action VARCHAR(50) NOT NULL,
    input_data JSONB,
    output_data JSONB,
    approved BOOLEAN,
    rejection_reason TEXT,
    duration_ms INTEGER,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_three_provinces_log_task_id ON three_provinces_log(task_id);
CREATE INDEX IF NOT EXISTS idx_three_provinces_log_province ON three_provinces_log(province);

-- 用户默认智能体配置表
CREATE TABLE IF NOT EXISTS user_default_agents (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id VARCHAR(36) REFERENCES users(id) ON DELETE CASCADE UNIQUE,
    default_agent_ids JSONB DEFAULT '{}',
    auto_spawn BOOLEAN DEFAULT true,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_user_default_agents_user_id ON user_default_agents(user_id);

-- 智能体能量消耗记录表
CREATE TABLE IF NOT EXISTS agent_energy_log (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    agent_id UUID REFERENCES agents(id) ON DELETE CASCADE,
    energy_before FLOAT,
    energy_after FLOAT,
    energy_delta FLOAT,
    reason VARCHAR(100),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_agent_energy_log_agent_id ON agent_energy_log(agent_id);
CREATE INDEX IF NOT EXISTS idx_agent_energy_log_created_at ON agent_energy_log(created_at DESC);

-- 创建更新时间触发器函数
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ language 'plpgsql';

-- 为需要的表添加触发器
DROP TRIGGER IF EXISTS update_agents_updated_at ON agents;
CREATE TRIGGER update_agents_updated_at
    BEFORE UPDATE ON agents
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

DROP TRIGGER IF EXISTS update_ministry_coordinator_updated_at ON ministry_coordinator_state;
CREATE TRIGGER update_ministry_coordinator_updated_at
    BEFORE UPDATE ON ministry_coordinator_state
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

DROP TRIGGER IF EXISTS update_user_default_agents_updated_at ON user_default_agents;
CREATE TRIGGER update_user_default_agents_updated_at
    BEFORE UPDATE ON user_default_agents
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();
"""

async def run_migration():
    """执行迁移"""
    logger.info("Starting agent architecture tables migration...")
    
    try:
        conn = await asyncpg.connect(DATABASE_URL)
        
        try:
            await conn.execute(MIGRATION_SQL)
            logger.info("Migration completed successfully!")
            
            result = await conn.fetch("""
                SELECT table_name 
                FROM information_schema.tables 
                WHERE table_schema = 'public' 
                AND table_name IN ('agents', 'agent_logs', 'task_queue', 'ministry_coordinator_state', 'three_provinces_log', 'user_default_agents', 'agent_energy_log')
            """)
            logger.info(f"Created tables: {[r['table_name'] for r in result]}")
            
        finally:
            await conn.close()
            
    except Exception as e:
        logger.error(f"Migration failed: {e}")
        raise

if __name__ == "__main__":
    asyncio.run(run_migration())
