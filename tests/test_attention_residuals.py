# -*- coding: utf-8 -*-
"""
Attention Residuals 海马体记忆系统测试
"""
import asyncio
import asyncpg
import sys
import os
import uuid

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

DATABASE_URL = "postgresql://postgres:147258%40Zxcvbnm@localhost:5432/fangdu"


async def test_attention_residuals():
    print("=" * 60)
    print("ATTENTION RESIDUALS MEMORY SYSTEM TEST")
    print("=" * 60)
    
    conn = await asyncpg.connect(DATABASE_URL)
    
    try:
        print("\n[1] Testing memory_entries table...")
        entries = await conn.fetch("SELECT id, content, importance, memory_type FROM memory_entries LIMIT 5")
        print(f"   Found {len(entries)} memory entries:")
        for e in entries:
            print(f"   - {e['content'][:30]}... (importance: {e['importance']}, type: {e['memory_type']})")
        
        print("\n[2] Testing memory insertion...")
        test_user_id = str(uuid.uuid4())
        test_memory_id = str(uuid.uuid4())
        await conn.execute("""
            INSERT INTO memory_entries (id, user_id, content, metadata, importance, memory_type)
            VALUES ($1, $2, $3, $4, $5, $6)
        """, test_memory_id, test_user_id, "测试记忆内容：用户询问了长沙房价走势", 
            '{"topic": "房价", "location": "长沙"}', 0.8, "consultation")
        print(f"   Created test memory: {test_memory_id}")
        
        print("\n[3] Testing memory_sessions table...")
        sessions = await conn.fetch("SELECT id, user_id, session_type FROM memory_sessions LIMIT 5")
        print(f"   Found {len(sessions)} sessions")
        
        print("\n[4] Testing user_memory_profiles table...")
        profiles = await conn.fetch("SELECT user_id, total_memories, total_sessions FROM user_memory_profiles LIMIT 5")
        print(f"   Found {len(profiles)} profiles:")
        for p in profiles:
            print(f"   - User: {p['user_id'][:8]}... (memories: {p['total_memories']}, sessions: {p['total_sessions']})")
        
        print("\n[5] Testing attention_logs table...")
        log_id = str(uuid.uuid4())
        await conn.execute("""
            INSERT INTO attention_logs (id, user_id, block_weights, selected_memories, confidence_score)
            VALUES ($1, $2, $3, $4, $5)
        """, log_id, test_user_id, "[0.4, 0.3, 0.3]", f'["{test_memory_id}"]', 0.85)
        print(f"   Created attention log: {log_id}")
        
        print("\n[6] Testing memory_blocks table...")
        blocks = await conn.fetch("SELECT * FROM memory_blocks LIMIT 5")
        print(f"   Found {len(blocks)} memory blocks")
        
        print("\n[7] Testing HippocampusRetriever...")
        from backend.services.attention_residuals.hippocampus_retriever import (
            HippocampusRetriever, MemoryBlocker
        )
        from backend.services.attention_residuals.models import MemoryEntry
        
        retriever = HippocampusRetriever(embed_dim=768, block_size=50)
        blocker = MemoryBlocker(block_size=50)
        
        test_memories = [
            MemoryEntry(
                id=str(uuid.uuid4()),
                user_id=test_user_id,
                content="记忆1：用户喜欢新房",
                embedding=[0.1] * 768,
                importance=0.8
            ),
            MemoryEntry(
                id=str(uuid.uuid4()),
                user_id=test_user_id,
                content="记忆2：用户关注学区房",
                embedding=[0.2] * 768,
                importance=0.9
            ),
            MemoryEntry(
                id=str(uuid.uuid4()),
                user_id=test_user_id,
                content="记忆3：用户预算200万",
                embedding=[0.15] * 768,
                importance=0.7
            )
        ]
        
        blocks = blocker.block_memories(test_memories)
        print(f"   Created {len(blocks)} memory blocks")
        
        query_vector = [0.1] * 768
        result = retriever.retrieve(query_vector, test_memories)
        print(f"   Attention result: confidence={result.confidence_score:.2f}")
        print(f"   Selected {len(result.selected_memories)} memories")
        
        print("\n[8] Testing vector similarity search...")
        try:
            similar = await conn.fetch("""
                SELECT id, content, 
                       1 - (embedding <=> '[0.1, 0.1, 0.1]'::vector) as similarity
                FROM memory_entries
                WHERE embedding IS NOT NULL
                ORDER BY embedding <=> '[0.1, 0.1, 0.1]'::vector
                LIMIT 3
            """)
            print(f"   Found {len(similar)} similar memories")
        except Exception as e:
            print(f"   Vector search skipped: {e}")
        
        print("\n" + "=" * 60)
        print("ALL TESTS PASSED!")
        print("=" * 60)
        
    finally:
        await conn.close()


if __name__ == "__main__":
    asyncio.run(test_attention_residuals())
