# -*- coding: utf-8 -*-
"""
Attention Residuals 海马体记忆系统 - 数据库迁移
创建记忆相关表（使用JSONB存储向量）
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
    print("Creating Attention Residuals Memory Tables")
    print("=" * 60)
    
    conn = await asyncpg.connect(DATABASE_URL.replace("postgresql+asyncpg://", "postgresql://"))
    
    try:
        # 1. 检查pgvector扩展
        print("\n[1] Checking pgvector extension...")
        has_vector = False
        try:
            await conn.execute("CREATE EXTENSION IF NOT EXISTS vector;")
            has_vector = True
            print("   [OK] pgvector extension enabled")
        except Exception as e:
            print("   [WARN] pgvector not available, using JSONB for vectors")
            has_vector = False
        
        # 2. 创建记忆条目表
        print("\n[2] Creating memory_entries table...")
        if has_vector:
            await conn.execute("""
                CREATE TABLE IF NOT EXISTS memory_entries (
                    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                    user_id UUID NOT NULL,
                    session_id UUID,
                    content TEXT NOT NULL,
                    embedding vector(768),
                    metadata JSONB DEFAULT '{}',
                    importance FLOAT DEFAULT 0.5,
                    memory_type VARCHAR(20) DEFAULT 'general',
                    created_at TIMESTAMP DEFAULT NOW(),
                    last_accessed TIMESTAMP DEFAULT NOW(),
                    access_count INT DEFAULT 0
                );
            """)
        else:
            await conn.execute("""
                CREATE TABLE IF NOT EXISTS memory_entries (
                    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                    user_id UUID NOT NULL,
                    session_id UUID,
                    content TEXT NOT NULL,
                    embedding JSONB,
                    metadata JSONB DEFAULT '{}',
                    importance FLOAT DEFAULT 0.5,
                    memory_type VARCHAR(20) DEFAULT 'general',
                    created_at TIMESTAMP DEFAULT NOW(),
                    last_accessed TIMESTAMP DEFAULT NOW(),
                    access_count INT DEFAULT 0
                );
            """)
        print("   [OK] Created memory_entries table")
        
        # 3. 创建记忆分块表
        print("\n[3] Creating memory_blocks table...")
        if has_vector:
            await conn.execute("""
                CREATE TABLE IF NOT EXISTS memory_blocks (
                    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                    user_id UUID NOT NULL,
                    block_index INT NOT NULL,
                    memory_ids JSONB DEFAULT '[]',
                    block_vector vector(768),
                    memory_count INT DEFAULT 0,
                    avg_importance FLOAT DEFAULT 0.5,
                    created_at TIMESTAMP DEFAULT NOW(),
                    updated_at TIMESTAMP DEFAULT NOW(),
                    UNIQUE(user_id, block_index)
                );
            """)
        else:
            await conn.execute("""
                CREATE TABLE IF NOT EXISTS memory_blocks (
                    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                    user_id UUID NOT NULL,
                    block_index INT NOT NULL,
                    memory_ids JSONB DEFAULT '[]',
                    block_vector JSONB,
                    memory_count INT DEFAULT 0,
                    avg_importance FLOAT DEFAULT 0.5,
                    created_at TIMESTAMP DEFAULT NOW(),
                    updated_at TIMESTAMP DEFAULT NOW(),
                    UNIQUE(user_id, block_index)
                );
            """)
        print("   [OK] Created memory_blocks table")
        
        # 4. 创建会话记忆表
        print("\n[4] Creating memory_sessions table...")
        await conn.execute("""
            CREATE TABLE IF NOT EXISTS memory_sessions (
                id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                user_id UUID NOT NULL,
                summary TEXT,
                key_topics JSONB DEFAULT '[]',
                turn_count INT DEFAULT 0,
                started_at TIMESTAMP DEFAULT NOW(),
                ended_at TIMESTAMP,
                session_type VARCHAR(20) DEFAULT 'consultation'
            );
        """)
        print("   [OK] Created memory_sessions table")
        
        # 5. 创建注意力日志表
        print("\n[5] Creating attention_logs table...")
        await conn.execute("""
            CREATE TABLE IF NOT EXISTS attention_logs (
                id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                user_id UUID NOT NULL,
                query_id UUID,
                query_text TEXT,
                block_weights JSONB DEFAULT '[]',
                selected_memories JSONB DEFAULT '[]',
                confidence_score FLOAT DEFAULT 0.0,
                aggregation_method VARCHAR(20) DEFAULT 'attention_residual',
                created_at TIMESTAMP DEFAULT NOW()
            );
        """)
        print("   [OK] Created attention_logs table")
        
        # 6. 创建用户记忆画像表
        print("\n[6] Creating user_memory_profiles table...")
        if has_vector:
            await conn.execute("""
                CREATE TABLE IF NOT EXISTS user_memory_profiles (
                    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                    user_id UUID UNIQUE NOT NULL,
                    preference_vector vector(768),
                    topic_weights JSONB DEFAULT '{}',
                    total_memories INT DEFAULT 0,
                    total_sessions INT DEFAULT 0,
                    last_active TIMESTAMP DEFAULT NOW(),
                    created_at TIMESTAMP DEFAULT NOW(),
                    last_updated TIMESTAMP DEFAULT NOW()
                );
            """)
        else:
            await conn.execute("""
                CREATE TABLE IF NOT EXISTS user_memory_profiles (
                    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                    user_id UUID UNIQUE NOT NULL,
                    preference_vector JSONB,
                    topic_weights JSONB DEFAULT '{}',
                    total_memories INT DEFAULT 0,
                    total_sessions INT DEFAULT 0,
                    last_active TIMESTAMP DEFAULT NOW(),
                    created_at TIMESTAMP DEFAULT NOW(),
                    last_updated TIMESTAMP DEFAULT NOW()
                );
            """)
        print("   [OK] Created user_memory_profiles table")
        
        # 7. 创建索引
        print("\n[7] Creating indexes...")
        await conn.execute("""
            CREATE INDEX IF NOT EXISTS idx_memory_user ON memory_entries(user_id);
            CREATE INDEX IF NOT EXISTS idx_memory_session ON memory_entries(session_id);
            CREATE INDEX IF NOT EXISTS idx_memory_importance ON memory_entries(importance DESC);
            CREATE INDEX IF NOT EXISTS idx_memory_created ON memory_entries(created_at DESC);
            CREATE INDEX IF NOT EXISTS idx_memory_type ON memory_entries(memory_type);
            
            CREATE INDEX IF NOT EXISTS idx_block_user ON memory_blocks(user_id);
            CREATE INDEX IF NOT EXISTS idx_block_index ON memory_blocks(block_index);
            
            CREATE INDEX IF NOT EXISTS idx_session_user ON memory_sessions(user_id);
            CREATE INDEX IF NOT EXISTS idx_session_time ON memory_sessions(started_at DESC);
            
            CREATE INDEX IF NOT EXISTS idx_attention_user ON attention_logs(user_id);
            CREATE INDEX IF NOT EXISTS idx_attention_time ON attention_logs(created_at DESC);
        """)
        print("   [OK] Created indexes")
        
        # 8. 插入示例数据
        print("\n[8] Inserting sample data...")
        sample_embedding = json.dumps([0.1] * 768)
        
        await conn.execute("""
            INSERT INTO memory_entries (id, user_id, content, embedding, metadata, importance, memory_type)
            VALUES 
                (gen_random_uuid(), '00000000-0000-0000-0000-000000000001', 
                 '用户询问了长沙岳麓区的房价走势', 
                 $1::jsonb, 
                 '{"topic": "房价", "location": "长沙岳麓区"}'::jsonb, 
                 0.8, 'consultation'),
                (gen_random_uuid(), '00000000-0000-0000-0000-000000000001', 
                 '用户关注学区房投资', 
                 $2::jsonb,
                 '{"topic": "学区房", "intent": "投资"}'::jsonb, 
                 0.9, 'preference'),
                (gen_random_uuid(), '00000000-0000-0000-0000-000000000001', 
                 '用户偏好新房而非二手房', 
                 $3::jsonb,
                 '{"topic": "房型偏好", "type": "新房"}'::jsonb, 
                 0.7, 'preference')
            ON CONFLICT DO NOTHING;
        """, sample_embedding, sample_embedding, sample_embedding)
        print("   [OK] Inserted sample memory entries")
        
        await conn.execute("""
            INSERT INTO user_memory_profiles (user_id, topic_weights, total_memories)
            VALUES ('00000000-0000-0000-0000-000000000001', 
                    '{"房价": 0.3, "学区房": 0.4, "新房": 0.3}'::jsonb, 
                    3)
            ON CONFLICT (user_id) DO NOTHING;
        """)
        print("   [OK] Inserted sample user profile")
        
        print("\n" + "=" * 60)
        print("Migration completed successfully!")
        print("=" * 60)
        print("\nCreated tables:")
        print("  - memory_entries (记忆条目)")
        print("  - memory_blocks (记忆分块)")
        print("  - memory_sessions (会话记忆)")
        print("  - attention_logs (注意力日志)")
        print("  - user_memory_profiles (用户画像)")
        
    finally:
        await conn.close()


if __name__ == "__main__":
    asyncio.run(create_tables())
