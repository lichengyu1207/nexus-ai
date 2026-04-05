# -*- coding: utf-8 -*-
"""
Agent Swarm 可扩展多智能体协作系统 - 数据库迁移
创建智能体协作相关表
"""
import asyncio
import asyncpg
import os
import sys
import json

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://postgres:147258%40Zxcvbnm@localhost:5432/fangdu")


async def create_tables():
    print("=" * 60)
    print("Creating Agent Swarm Tables")
    print("=" * 60)
    
    conn = await asyncpg.connect(DATABASE_URL.replace("postgresql+asyncpg://", "postgresql://"))
    
    try:
        print("\n[1] Creating swarm_agents table...")
        await conn.execute("""
            CREATE TABLE IF NOT EXISTS swarm_agents (
                id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                name VARCHAR(100) NOT NULL UNIQUE,
                agent_type VARCHAR(50) NOT NULL,
                department VARCHAR(50),
                capabilities JSONB DEFAULT '[]',
                skill_scores JSONB DEFAULT '{}',
                current_load FLOAT DEFAULT 0.0,
                max_concurrent_tasks INT DEFAULT 3,
                neighbors JSONB DEFAULT '[]',
                status VARCHAR(20) DEFAULT 'idle',
                last_heartbeat TIMESTAMP,
                metadata JSONB DEFAULT '{}',
                created_at TIMESTAMP DEFAULT NOW(),
                updated_at TIMESTAMP DEFAULT NOW()
            );
        """)
        print("   [OK] Created swarm_agents table")
        
        print("\n[2] Creating swarm_tasks table...")
        await conn.execute("""
            CREATE TABLE IF NOT EXISTS swarm_tasks (
                id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                parent_task_id UUID REFERENCES swarm_tasks(id) ON DELETE CASCADE,
                session_id UUID,
                task_type VARCHAR(50) NOT NULL,
                required_capabilities JSONB DEFAULT '[]',
                priority INT DEFAULT 5,
                status VARCHAR(20) DEFAULT 'pending',
                payload JSONB DEFAULT '{}',
                result JSONB DEFAULT '{}',
                collaboration_mode VARCHAR(20) DEFAULT 'parallel',
                decomposition_level INT DEFAULT 0,
                assigned_agent_id UUID REFERENCES swarm_agents(id),
                deadline TIMESTAMP,
                created_at TIMESTAMP DEFAULT NOW(),
                started_at TIMESTAMP,
                completed_at TIMESTAMP
            );
        """)
        print("   [OK] Created swarm_tasks table")
        
        print("\n[3] Creating swarm_bids table...")
        await conn.execute("""
            CREATE TABLE IF NOT EXISTS swarm_bids (
                id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                task_id UUID NOT NULL REFERENCES swarm_tasks(id) ON DELETE CASCADE,
                agent_id UUID NOT NULL REFERENCES swarm_agents(id) ON DELETE CASCADE,
                score FLOAT NOT NULL,
                estimated_time FLOAT DEFAULT 0.0,
                confidence FLOAT DEFAULT 0.5,
                proposal JSONB DEFAULT '{}',
                is_winner BOOLEAN DEFAULT FALSE,
                created_at TIMESTAMP DEFAULT NOW(),
                UNIQUE(task_id, agent_id)
            );
        """)
        print("   [OK] Created swarm_bids table")
        
        print("\n[4] Creating swarm_sessions table...")
        await conn.execute("""
            CREATE TABLE IF NOT EXISTS swarm_sessions (
                id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                user_id UUID,
                collaboration_mode VARCHAR(20) DEFAULT 'parallel',
                total_tasks INT DEFAULT 0,
                completed_tasks INT DEFAULT 0,
                failed_tasks INT DEFAULT 0,
                total_latency_ms FLOAT DEFAULT 0.0,
                metadata JSONB DEFAULT '{}',
                started_at TIMESTAMP DEFAULT NOW(),
                ended_at TIMESTAMP
            );
        """)
        print("   [OK] Created swarm_sessions table")
        
        print("\n[5] Creating swarm_task_logs table...")
        await conn.execute("""
            CREATE TABLE IF NOT EXISTS swarm_task_logs (
                id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                task_id UUID NOT NULL REFERENCES swarm_tasks(id) ON DELETE CASCADE,
                agent_id UUID REFERENCES swarm_agents(id) ON DELETE SET NULL,
                event_type VARCHAR(50) NOT NULL,
                event_data JSONB DEFAULT '{}',
                created_at TIMESTAMP DEFAULT NOW()
            );
        """)
        print("   [OK] Created swarm_task_logs table")
        
        print("\n[6] Creating swarm_heartbeats table...")
        await conn.execute("""
            CREATE TABLE IF NOT EXISTS swarm_heartbeats (
                id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                agent_id UUID NOT NULL REFERENCES swarm_agents(id) ON DELETE CASCADE,
                load FLOAT DEFAULT 0.0,
                active_tasks INT DEFAULT 0,
                status_info JSONB DEFAULT '{}',
                recorded_at TIMESTAMP DEFAULT NOW()
            );
        """)
        print("   [OK] Created swarm_heartbeats table")
        
        print("\n[7] Creating indexes...")
        await conn.execute("""
            CREATE INDEX IF NOT EXISTS idx_agent_type ON swarm_agents(agent_type);
            CREATE INDEX IF NOT EXISTS idx_agent_department ON swarm_agents(department);
            CREATE INDEX IF NOT EXISTS idx_agent_status ON swarm_agents(status);
            CREATE INDEX IF NOT EXISTS idx_agent_heartbeat ON swarm_agents(last_heartbeat DESC);
            
            CREATE INDEX IF NOT EXISTS idx_task_session ON swarm_tasks(session_id);
            CREATE INDEX IF NOT EXISTS idx_task_parent ON swarm_tasks(parent_task_id);
            CREATE INDEX IF NOT EXISTS idx_task_status ON swarm_tasks(status);
            CREATE INDEX IF NOT EXISTS idx_task_type ON swarm_tasks(task_type);
            CREATE INDEX IF NOT EXISTS idx_task_priority ON swarm_tasks(priority DESC);
            CREATE INDEX IF NOT EXISTS idx_task_assigned ON swarm_tasks(assigned_agent_id);
            CREATE INDEX IF NOT EXISTS idx_task_created ON swarm_tasks(created_at DESC);
            
            CREATE INDEX IF NOT EXISTS idx_bid_task ON swarm_bids(task_id);
            CREATE INDEX IF NOT EXISTS idx_bid_agent ON swarm_bids(agent_id);
            CREATE INDEX IF NOT EXISTS idx_bid_winner ON swarm_bids(is_winner);
            CREATE INDEX IF NOT EXISTS idx_bid_score ON swarm_bids(score);
            
            CREATE INDEX IF NOT EXISTS idx_session_user ON swarm_sessions(user_id);
            CREATE INDEX IF NOT EXISTS idx_session_time ON swarm_sessions(started_at DESC);
            
            CREATE INDEX IF NOT EXISTS idx_log_task ON swarm_task_logs(task_id);
            CREATE INDEX IF NOT EXISTS idx_log_agent ON swarm_task_logs(agent_id);
            CREATE INDEX IF NOT EXISTS idx_log_type ON swarm_task_logs(event_type);
            CREATE INDEX IF NOT EXISTS idx_log_time ON swarm_task_logs(created_at DESC);
            
            CREATE INDEX IF NOT EXISTS idx_hb_agent ON swarm_heartbeats(agent_id);
            CREATE INDEX IF NOT EXISTS idx_hb_time ON swarm_heartbeats(recorded_at DESC);
        """)
        print("   [OK] Created indexes")
        
        print("\n[8] Inserting default agents...")
        agents = [
            {"name": "zhongshu_sheng", "agent_type": "province", "department": "decision",
             "capabilities": ["planning", "decision_making", "task_decomposition", "coordination"],
             "skill_scores": {"planning": 0.95, "coordination": 0.90}, "max_concurrent_tasks": 5},
            {"name": "menxia_sheng", "agent_type": "province", "department": "review",
             "capabilities": ["review", "validation", "quality_check", "audit"],
             "skill_scores": {"review": 0.95, "validation": 0.90}, "max_concurrent_tasks": 4},
            {"name": "shangshu_sheng", "agent_type": "province", "department": "execution",
             "capabilities": ["execution", "coordination", "resource_management", "aggregation"],
             "skill_scores": {"execution": 0.90, "aggregation": 0.95}, "max_concurrent_tasks": 6},
            {"name": "li_bu", "agent_type": "ministry", "department": "consultation",
             "capabilities": ["chat", "sentiment_analysis", "advice", "consultation", "interaction"],
             "skill_scores": {"chat": 0.95, "consultation": 0.90}, "max_concurrent_tasks": 8},
            {"name": "hu_bu", "agent_type": "ministry", "department": "data",
             "capabilities": ["data_collection", "price_query", "market_analysis", "statistics"],
             "skill_scores": {"data_collection": 0.90, "analysis": 0.85}, "max_concurrent_tasks": 6},
            {"name": "bing_bu", "agent_type": "ministry", "department": "risk",
             "capabilities": ["risk_assessment", "warning", "monitoring", "alert"],
             "skill_scores": {"risk_assessment": 0.95, "monitoring": 0.90}, "max_concurrent_tasks": 5},
            {"name": "xing_bu", "agent_type": "ministry", "department": "compliance",
             "capabilities": ["compliance_check", "legal_review", "audit", "verification"],
             "skill_scores": {"compliance_check": 0.95, "audit": 0.90}, "max_concurrent_tasks": 4},
            {"name": "gong_bu", "agent_type": "ministry", "department": "report",
             "capabilities": ["report_generation", "chart_creation", "visualization", "formatting"],
             "skill_scores": {"report_generation": 0.95, "visualization": 0.85}, "max_concurrent_tasks": 4},
            {"name": "li_bu2", "agent_type": "ministry", "department": "management",
             "capabilities": ["management", "scheduling", "allocation", "optimization"],
             "skill_scores": {"scheduling": 0.90, "optimization": 0.85}, "max_concurrent_tasks": 6}
        ]
        
        for agent in agents:
            await conn.execute("""
                INSERT INTO swarm_agents (name, agent_type, department, capabilities, skill_scores, max_concurrent_tasks)
                VALUES ($1, $2, $3, $4, $5, $6)
                ON CONFLICT (name) DO UPDATE SET
                    agent_type = $2, department = $3, capabilities = $4,
                    skill_scores = $5, max_concurrent_tasks = $6, updated_at = NOW()
            """, agent["name"], agent["agent_type"], agent["department"],
                json.dumps(agent["capabilities"]), json.dumps(agent["skill_scores"]), agent["max_concurrent_tasks"])
        
        print(f"   [OK] Inserted {len(agents)} agents")
        
        print("\n" + "=" * 60)
        print("Migration completed successfully!")
        print("=" * 60)
        print("\nCreated tables:")
        print("  - swarm_agents (智能体注册表)")
        print("  - swarm_tasks (任务管理)")
        print("  - swarm_bids (竞标记录)")
        print("  - swarm_sessions (会话管理)")
        print("  - swarm_task_logs (任务日志)")
        print("  - swarm_heartbeats (心跳记录)")
        
    finally:
        await conn.close()


if __name__ == "__main__":
    asyncio.run(create_tables())
