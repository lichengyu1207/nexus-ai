# -*- coding: utf-8 -*-
"""
CASK 上下文自适应稀疏KV缓存系统 - 数据库迁移
创建KV缓存管理相关表
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
    print("Creating CASK Context-Adaptive Sparse KV Cache Tables")
    print("=" * 60)
    
    conn = await asyncpg.connect(DATABASE_URL.replace("postgresql+asyncpg://", "postgresql://"))
    
    try:
        print("\n[1] Creating cache_sessions table...")
        await conn.execute("""
            CREATE TABLE IF NOT EXISTS cache_sessions (
                id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                user_id UUID,
                model_name VARCHAR(100) DEFAULT 'default',
                max_context_length INT DEFAULT 8192,
                total_memory_mb FLOAT DEFAULT 0.0,
                total_tokens INT DEFAULT 0,
                cask_enabled BOOLEAN DEFAULT TRUE,
                started_at TIMESTAMP DEFAULT NOW(),
                ended_at TIMESTAMP,
                metadata JSONB DEFAULT '{}'
            );
        """)
        print("   [OK] Created cache_sessions table")
        
        print("\n[2] Creating kv_cache_blocks table...")
        await conn.execute("""
            CREATE TABLE IF NOT EXISTS kv_cache_blocks (
                id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                session_id UUID NOT NULL REFERENCES cache_sessions(id) ON DELETE CASCADE,
                block_index INT NOT NULL,
                start_position INT NOT NULL,
                end_position INT NOT NULL,
                compressed_data JSONB DEFAULT '{}',
                csr_values JSONB DEFAULT '[]',
                csr_col_indices JSONB DEFAULT '[]',
                csr_row_ptr JSONB DEFAULT '[]',
                avg_importance FLOAT DEFAULT 0.0,
                token_count INT DEFAULT 0,
                is_sparse BOOLEAN DEFAULT FALSE,
                sparsity_rate FLOAT DEFAULT 0.0,
                created_at TIMESTAMP DEFAULT NOW(),
                last_accessed TIMESTAMP DEFAULT NOW(),
                access_count INT DEFAULT 0
            );
        """)
        print("   [OK] Created kv_cache_blocks table")
        
        print("\n[3] Creating sparsity_decisions table...")
        await conn.execute("""
            CREATE TABLE IF NOT EXISTS sparsity_decisions (
                id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                session_id UUID NOT NULL REFERENCES cache_sessions(id) ON DELETE CASCADE,
                context_length INT NOT NULL,
                complexity_score FLOAT DEFAULT 0.0,
                complexity_method VARCHAR(50) DEFAULT 'attention_entropy',
                sparsity_rate FLOAT DEFAULT 0.5,
                kv_pairs_total INT DEFAULT 0,
                kv_pairs_retained INT DEFAULT 0,
                memory_before_mb FLOAT DEFAULT 0.0,
                memory_after_mb FLOAT DEFAULT 0.0,
                memory_saved_mb FLOAT DEFAULT 0.0,
                compression_ratio FLOAT DEFAULT 0.0,
                latency_ms FLOAT DEFAULT 0.0,
                stage VARCHAR(20) DEFAULT 'stable',
                created_at TIMESTAMP DEFAULT NOW()
            );
        """)
        print("   [OK] Created sparsity_decisions table")
        
        print("\n[4] Creating performance_metrics table...")
        await conn.execute("""
            CREATE TABLE IF NOT EXISTS performance_metrics (
                id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                session_id UUID REFERENCES cache_sessions(id) ON DELETE CASCADE,
                metric_type VARCHAR(50) NOT NULL,
                metric_name VARCHAR(100) NOT NULL,
                value FLOAT NOT NULL,
                unit VARCHAR(20) DEFAULT '',
                metadata JSONB DEFAULT '{}',
                recorded_at TIMESTAMP DEFAULT NOW()
            );
        """)
        print("   [OK] Created performance_metrics table")
        
        print("\n[5] Creating sparsity_configs table...")
        await conn.execute("""
            CREATE TABLE IF NOT EXISTS sparsity_configs (
                id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                model_name VARCHAR(100) NOT NULL UNIQUE,
                min_sparsity FLOAT DEFAULT 0.3,
                max_sparsity FLOAT DEFAULT 0.7,
                default_sparsity FLOAT DEFAULT 0.5,
                warmup_steps INT DEFAULT 128,
                block_size INT DEFAULT 64,
                decay_lambda FLOAT DEFAULT 0.1,
                window_size INT DEFAULT 512,
                sample_size INT DEFAULT 64,
                complexity_threshold_low FLOAT DEFAULT 0.3,
                complexity_threshold_high FLOAT DEFAULT 0.7,
                enable_adaptive BOOLEAN DEFAULT TRUE,
                enable_position_decay BOOLEAN DEFAULT TRUE,
                is_active BOOLEAN DEFAULT TRUE,
                created_at TIMESTAMP DEFAULT NOW(),
                updated_at TIMESTAMP DEFAULT NOW()
            );
        """)
        print("   [OK] Created sparsity_configs table")
        
        print("\n[6] Creating indexes...")
        await conn.execute("""
            CREATE INDEX IF NOT EXISTS idx_session_user ON cache_sessions(user_id);
            CREATE INDEX IF NOT EXISTS idx_session_model ON cache_sessions(model_name);
            CREATE INDEX IF NOT EXISTS idx_session_active ON cache_sessions(ended_at) WHERE ended_at IS NULL;
            
            CREATE INDEX IF NOT EXISTS idx_block_session ON kv_cache_blocks(session_id);
            CREATE INDEX IF NOT EXISTS idx_block_position ON kv_cache_blocks(start_position, end_position);
            CREATE INDEX IF NOT EXISTS idx_block_importance ON kv_cache_blocks(avg_importance DESC);
            CREATE INDEX IF NOT EXISTS idx_block_sparse ON kv_cache_blocks(is_sparse);
            
            CREATE INDEX IF NOT EXISTS idx_decision_session ON sparsity_decisions(session_id);
            CREATE INDEX IF NOT EXISTS idx_decision_sparsity ON sparsity_decisions(sparsity_rate);
            CREATE INDEX IF NOT EXISTS idx_decision_time ON sparsity_decisions(created_at DESC);
            
            CREATE INDEX IF NOT EXISTS idx_metric_session ON performance_metrics(session_id);
            CREATE INDEX IF NOT EXISTS idx_metric_type ON performance_metrics(metric_type);
            CREATE INDEX IF NOT EXISTS idx_metric_time ON performance_metrics(recorded_at DESC);
            
            CREATE INDEX IF NOT EXISTS idx_config_model ON sparsity_configs(model_name);
            CREATE INDEX IF NOT EXISTS idx_config_active ON sparsity_configs(is_active);
        """)
        print("   [OK] Created indexes")
        
        print("\n[7] Inserting default sparsity configs...")
        configs = [
            {
                "model_name": "default",
                "min_sparsity": 0.3,
                "max_sparsity": 0.7,
                "default_sparsity": 0.5,
                "warmup_steps": 128,
                "block_size": 64,
                "decay_lambda": 0.1,
                "window_size": 512,
                "sample_size": 64
            },
            {
                "model_name": "qwen-7b",
                "min_sparsity": 0.35,
                "max_sparsity": 0.75,
                "default_sparsity": 0.55,
                "warmup_steps": 256,
                "block_size": 64,
                "decay_lambda": 0.08,
                "window_size": 1024,
                "sample_size": 128
            },
            {
                "model_name": "deepseek",
                "min_sparsity": 0.3,
                "max_sparsity": 0.65,
                "default_sparsity": 0.45,
                "warmup_steps": 128,
                "block_size": 64,
                "decay_lambda": 0.12,
                "window_size": 512,
                "sample_size": 64
            },
            {
                "model_name": "long_context",
                "min_sparsity": 0.4,
                "max_sparsity": 0.8,
                "default_sparsity": 0.6,
                "warmup_steps": 512,
                "block_size": 128,
                "decay_lambda": 0.05,
                "window_size": 2048,
                "sample_size": 256
            }
        ]
        
        for cfg in configs:
            await conn.execute("""
                INSERT INTO sparsity_configs 
                (model_name, min_sparsity, max_sparsity, default_sparsity, warmup_steps, block_size, decay_lambda, window_size, sample_size)
                VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9)
                ON CONFLICT (model_name) DO UPDATE SET
                    min_sparsity = $2, max_sparsity = $3, default_sparsity = $4,
                    warmup_steps = $5, block_size = $6, decay_lambda = $7,
                    window_size = $8, sample_size = $9, updated_at = NOW()
            """, cfg["model_name"], cfg["min_sparsity"], cfg["max_sparsity"],
                cfg["default_sparsity"], cfg["warmup_steps"], cfg["block_size"],
                cfg["decay_lambda"], cfg["window_size"], cfg["sample_size"])
        
        print(f"   [OK] Inserted {len(configs)} sparsity configs")
        
        print("\n" + "=" * 60)
        print("Migration completed successfully!")
        print("=" * 60)
        print("\nCreated tables:")
        print("  - cache_sessions (缓存会话)")
        print("  - kv_cache_blocks (KV缓存块)")
        print("  - sparsity_decisions (稀疏决策)")
        print("  - performance_metrics (性能指标)")
        print("  - sparsity_configs (稀疏配置)")
        
    finally:
        await conn.close()


if __name__ == "__main__":
    asyncio.run(create_tables())
