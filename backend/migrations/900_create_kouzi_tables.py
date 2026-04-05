# -*- coding: utf-8 -*-
"""
扣子数据接收系统 - 数据库迁移
创建扣子信息流、爬虫数据、转化记录相关表
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
    print("Creating Kouzi Data Reception Tables")
    print("=" * 60)
    
    conn = await asyncpg.connect(DATABASE_URL.replace("postgresql+asyncpg://", "postgresql://"))
    
    try:
        print("\n[1] Creating kouzi_info_streams table...")
        await conn.execute("""
            CREATE TABLE IF NOT EXISTS kouzi_info_streams (
                id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                stream_id VARCHAR(100) NOT NULL,
                source_type VARCHAR(50) NOT NULL,
                source_name VARCHAR(200),
                content_type VARCHAR(50) DEFAULT 'text',
                raw_content JSONB DEFAULT '{}',
                processed_content JSONB DEFAULT '{}',
                metadata JSONB DEFAULT '{}',
                status VARCHAR(20) DEFAULT 'pending',
                priority INT DEFAULT 5,
                received_at TIMESTAMP DEFAULT NOW(),
                processed_at TIMESTAMP,
                error_message TEXT
            );
        """)
        print("   [OK] Created kouzi_info_streams table")
        
        print("\n[2] Creating kouzi_crawler_data table...")
        await conn.execute("""
            CREATE TABLE IF NOT EXISTS kouzi_crawler_data (
                id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                crawler_id VARCHAR(100) NOT NULL,
                crawler_type VARCHAR(50) NOT NULL,
                target_url TEXT,
                crawl_status VARCHAR(20) DEFAULT 'pending',
                raw_data JSONB DEFAULT '{}',
                parsed_data JSONB DEFAULT '{}',
                images JSONB DEFAULT '[]',
                documents JSONB DEFAULT '[]',
                crawl_metadata JSONB DEFAULT '{}',
                started_at TIMESTAMP,
                completed_at TIMESTAMP,
                created_at TIMESTAMP DEFAULT NOW(),
                error_message TEXT,
                retry_count INT DEFAULT 0
            );
        """)
        print("   [OK] Created kouzi_crawler_data table")
        
        print("\n[3] Creating kouzi_transform_logs table...")
        await conn.execute("""
            CREATE TABLE IF NOT EXISTS kouzi_transform_logs (
                id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                source_table VARCHAR(100) NOT NULL,
                source_id UUID NOT NULL,
                target_table VARCHAR(100) NOT NULL,
                target_id UUID,
                transform_type VARCHAR(50) NOT NULL,
                transform_status VARCHAR(20) DEFAULT 'pending',
                source_data JSONB DEFAULT '{}',
                transformed_data JSONB DEFAULT '{}',
                mapping_rules JSONB DEFAULT '{}',
                created_at TIMESTAMP DEFAULT NOW(),
                completed_at TIMESTAMP,
                error_message TEXT
            );
        """)
        print("   [OK] Created kouzi_transform_logs table")
        
        print("\n[4] Creating pssq_properties table...")
        await conn.execute("""
            CREATE TABLE IF NOT EXISTS pssq_properties (
                id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                property_id VARCHAR(100) UNIQUE,
                property_name VARCHAR(500),
                property_type VARCHAR(50),
                address TEXT,
                city VARCHAR(100),
                district VARCHAR(100),
                area_size FLOAT,
                price FLOAT,
                price_unit VARCHAR(20),
                build_year INT,
                floor_info VARCHAR(100),
                orientation VARCHAR(50),
                decoration VARCHAR(50),
                property_rights VARCHAR(50),
                source_platform VARCHAR(100),
                source_url TEXT,
                source_id VARCHAR(200),
                raw_data JSONB DEFAULT '{}',
                images JSONB DEFAULT '[]',
                contact_info JSONB DEFAULT '{}',
                status VARCHAR(20) DEFAULT 'active',
                created_at TIMESTAMP DEFAULT NOW(),
                updated_at TIMESTAMP DEFAULT NOW(),
                kouzi_stream_id UUID REFERENCES kouzi_info_streams(id)
            );
        """)
        print("   [OK] Created pssq_properties table")
        
        print("\n[5] Creating pssq_market_data table...")
        await conn.execute("""
            CREATE TABLE IF NOT EXISTS pssq_market_data (
                id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                data_type VARCHAR(50) NOT NULL,
                region VARCHAR(100),
                region_code VARCHAR(50),
                avg_price FLOAT,
                price_change_rate FLOAT,
                transaction_count INT,
                listing_count INT,
                data_date DATE,
                data_month VARCHAR(20),
                data_year INT,
                source VARCHAR(100),
                raw_data JSONB DEFAULT '{}',
                created_at TIMESTAMP DEFAULT NOW(),
                kouzi_stream_id UUID REFERENCES kouzi_info_streams(id)
            );
        """)
        print("   [OK] Created pssq_market_data table")
        
        print("\n[6] Creating kouzi_webhooks table...")
        await conn.execute("""
            CREATE TABLE IF NOT EXISTS kouzi_webhooks (
                id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                webhook_id VARCHAR(100) UNIQUE NOT NULL,
                webhook_name VARCHAR(200),
                webhook_type VARCHAR(50) NOT NULL,
                endpoint_url TEXT,
                secret_key VARCHAR(200),
                is_active BOOLEAN DEFAULT TRUE,
                last_triggered TIMESTAMP,
                trigger_count INT DEFAULT 0,
                created_at TIMESTAMP DEFAULT NOW(),
                updated_at TIMESTAMP DEFAULT NOW()
            );
        """)
        print("   [OK] Created kouzi_webhooks table")
        
        print("\n[7] Creating indexes...")
        await conn.execute("""
            CREATE INDEX IF NOT EXISTS idx_stream_id ON kouzi_info_streams(stream_id);
            CREATE INDEX IF NOT EXISTS idx_stream_source ON kouzi_info_streams(source_type);
            CREATE INDEX IF NOT EXISTS idx_stream_status ON kouzi_info_streams(status);
            CREATE INDEX IF NOT EXISTS idx_stream_received ON kouzi_info_streams(received_at DESC);
            
            CREATE INDEX IF NOT EXISTS idx_crawler_id ON kouzi_crawler_data(crawler_id);
            CREATE INDEX IF NOT EXISTS idx_crawler_type ON kouzi_crawler_data(crawler_type);
            CREATE INDEX IF NOT EXISTS idx_crawler_status ON kouzi_crawler_data(crawl_status);
            CREATE INDEX IF NOT EXISTS idx_crawler_created ON kouzi_crawler_data(created_at DESC);
            
            CREATE INDEX IF NOT EXISTS idx_transform_source ON kouzi_transform_logs(source_table, source_id);
            CREATE INDEX IF NOT EXISTS idx_transform_target ON kouzi_transform_logs(target_table, target_id);
            CREATE INDEX IF NOT EXISTS idx_transform_status ON kouzi_transform_logs(transform_status);
            CREATE INDEX IF NOT EXISTS idx_transform_type ON kouzi_transform_logs(transform_type);
            
            CREATE INDEX IF NOT EXISTS idx_pssq_property_id ON pssq_properties(property_id);
            CREATE INDEX IF NOT EXISTS idx_pssq_city ON pssq_properties(city);
            CREATE INDEX IF NOT EXISTS idx_pssq_district ON pssq_properties(district);
            CREATE INDEX IF NOT EXISTS idx_pssq_status ON pssq_properties(status);
            CREATE INDEX IF NOT EXISTS idx_pssq_source ON pssq_properties(source_platform);
            
            CREATE INDEX IF NOT EXISTS idx_market_type ON pssq_market_data(data_type);
            CREATE INDEX IF NOT EXISTS idx_market_region ON pssq_market_data(region);
            CREATE INDEX IF NOT EXISTS idx_market_date ON pssq_market_data(data_date DESC);
            
            CREATE INDEX IF NOT EXISTS idx_webhook_type ON kouzi_webhooks(webhook_type);
            CREATE INDEX IF NOT EXISTS idx_webhook_active ON kouzi_webhooks(is_active);
        """)
        print("   [OK] Created indexes")
        
        print("\n[8] Inserting default webhooks...")
        webhooks = [
            {
                "webhook_id": "kouzi_property_stream",
                "webhook_name": "房产信息流接收",
                "webhook_type": "property_stream",
                "endpoint_url": "/api/kouzi/property/stream"
            },
            {
                "webhook_id": "kouzi_crawler_task",
                "webhook_name": "爬虫任务回调",
                "webhook_type": "crawler_callback",
                "endpoint_url": "/api/kouzi/crawler/callback"
            },
            {
                "webhook_id": "kouzi_market_data",
                "webhook_name": "市场数据接收",
                "webhook_type": "market_data",
                "endpoint_url": "/api/kouzi/market/data"
            }
        ]
        
        for wh in webhooks:
            await conn.execute("""
                INSERT INTO kouzi_webhooks (webhook_id, webhook_name, webhook_type, endpoint_url)
                VALUES ($1, $2, $3, $4)
                ON CONFLICT (webhook_id) DO UPDATE SET
                    webhook_name = $2, webhook_type = $3, endpoint_url = $4, updated_at = NOW()
            """, wh["webhook_id"], wh["webhook_name"], wh["webhook_type"], wh["endpoint_url"])
        
        print(f"   [OK] Inserted {len(webhooks)} webhooks")
        
        print("\n" + "=" * 60)
        print("Migration completed successfully!")
        print("=" * 60)
        print("\nCreated tables:")
        print("  - kouzi_info_streams (信息流)")
        print("  - kouzi_crawler_data (爬虫数据)")
        print("  - kouzi_transform_logs (转化日志)")
        print("  - pssq_properties (房产数据)")
        print("  - pssq_market_data (市场数据)")
        print("  - kouzi_webhooks (Webhook配置)")
        
    finally:
        await conn.close()


if __name__ == "__main__":
    asyncio.run(create_tables())
