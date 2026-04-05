# -*- coding: utf-8 -*-
"""
产业园区数据库迁移
创建产业园区相关表
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
    print("Creating Industrial Park Tables")
    print("=" * 60)
    
    conn = await asyncpg.connect(DATABASE_URL.replace("postgresql+asyncpg://", "postgresql://"))
    
    try:
        # 1. 创建产业园区表
        print("\n[1] Creating industrial_parks table...")
        await conn.execute("""
            CREATE TABLE IF NOT EXISTS industrial_parks (
                id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                name VARCHAR(200) NOT NULL,
                city VARCHAR(50) NOT NULL,
                district VARCHAR(50),
                industry_type VARCHAR(100),
                industry_tags JSONB DEFAULT '[]',
                description TEXT,
                development_goal TEXT,
                latitude FLOAT,
                longitude FLOAT,
                status VARCHAR(20) DEFAULT 'planning',
                investment_amount FLOAT,
                employment_estimate INT,
                area_size FLOAT,
                nearby_property_price_min FLOAT,
                nearby_property_price_max FLOAT,
                policy_support JSONB DEFAULT '{}',
                created_at TIMESTAMP DEFAULT NOW(),
                updated_at TIMESTAMP DEFAULT NOW()
            );
        """)
        print("   [OK] Created industrial_parks table")
        
        # 2. 创建产城融合指数表
        print("\n[2] Creating city_integration_index table...")
        await conn.execute("""
            CREATE TABLE IF NOT EXISTS city_integration_index (
                id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                city VARCHAR(50) NOT NULL,
                district VARCHAR(50),
                overall_score FLOAT DEFAULT 0,
                industry_score FLOAT DEFAULT 0,
                infrastructure_score FLOAT DEFAULT 0,
                policy_score FLOAT DEFAULT 0,
                talent_score FLOAT DEFAULT 0,
                investment_potential VARCHAR(20),
                key_industries JSONB DEFAULT '[]',
                growth_rate FLOAT,
                data_source VARCHAR(100),
                calculated_at TIMESTAMP DEFAULT NOW(),
                UNIQUE(city, district)
            );
        """)
        print("   [OK] Created city_integration_index table")
        
        # 3. 创建产业-房产关联表
        print("\n[3] Creating industry_property_correlation table...")
        await conn.execute("""
            CREATE TABLE IF NOT EXISTS industry_property_correlation (
                id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                park_id UUID REFERENCES industrial_parks(id),
                property_id UUID,
                distance_km FLOAT,
                price_impact_factor FLOAT DEFAULT 1.0,
                investment_recommendation TEXT,
                created_at TIMESTAMP DEFAULT NOW()
            );
        """)
        print("   [OK] Created industry_property_correlation table")
        
        # 4. 创建索引
        print("\n[4] Creating indexes...")
        await conn.execute("""
            CREATE INDEX IF NOT EXISTS idx_park_city ON industrial_parks(city);
            CREATE INDEX IF NOT EXISTS idx_park_industry ON industrial_parks(industry_type);
            CREATE INDEX IF NOT EXISTS idx_park_status ON industrial_parks(status);
            CREATE INDEX IF NOT EXISTS idx_park_location ON industrial_parks(latitude, longitude);
            
            CREATE INDEX IF NOT EXISTS idx_index_city ON city_integration_index(city);
            CREATE INDEX IF NOT EXISTS idx_index_score ON city_integration_index(overall_score DESC);
        """)
        print("   [OK] Created indexes")
        
        # 5. 插入湖南省产业园区数据
        print("\n[5] Inserting Hunan industrial parks data...")
        parks_data = [
            {
                "name": "长沙宁乡圣钘科技新一代锂电池项目",
                "city": "长沙市",
                "district": "宁乡市",
                "industry_type": "锂电池",
                "industry_tags": ["新能源", "锂电池", "储能"],
                "description": "新一代锂电池研发生产基地",
                "development_goal": "推进项目建设，培育壮大新动能",
                "latitude": 28.25,
                "longitude": 112.55,
                "status": "construction",
                "nearby_property_price_min": 6500,
                "nearby_property_price_max": 9500
            },
            {
                "name": "浏阳蓝思科技3D玻璃研发生产项目",
                "city": "长沙市",
                "district": "浏阳市",
                "industry_type": "3D玻璃研发生产",
                "industry_tags": ["智能制造", "新材料", "高科技"],
                "description": "3D玻璃研发生产基地",
                "development_goal": "推进项目建设，培育壮大新动能",
                "latitude": 28.16,
                "longitude": 113.63,
                "status": "construction",
                "nearby_property_price_min": 5500,
                "nearby_property_price_max": 8000
            },
            {
                "name": "郴州新能源动力和储能项目",
                "city": "郴州市",
                "district": None,
                "industry_type": "新能源动力和储能",
                "industry_tags": ["新能源", "储能", "绿色能源"],
                "description": "新能源动力和储能产业基地",
                "development_goal": "推进项目建设，培育壮大新动能",
                "latitude": 25.78,
                "longitude": 113.02,
                "status": "construction",
                "nearby_property_price_min": 4500,
                "nearby_property_price_max": 7000
            },
            {
                "name": "娄底高性能软磁和钛材料项目",
                "city": "娄底市",
                "district": None,
                "industry_type": "高性能软磁和钛材料",
                "industry_tags": ["新材料", "高端制造"],
                "description": "高性能软磁和钛材料生产基地",
                "development_goal": "推进项目建设，培育壮大新动能",
                "latitude": 27.70,
                "longitude": 111.99,
                "status": "construction",
                "nearby_property_price_min": 4000,
                "nearby_property_price_max": 6000
            },
            {
                "name": "长岳临空经济示范区",
                "city": "长沙市",
                "district": "长沙县",
                "industry_type": "临空经济",
                "industry_tags": ["临空经济", "跨境电商", "物流"],
                "description": "临空经济示范区和航空货运枢纽",
                "development_goal": "打造临空经济示范区和航空货运枢纽，推动外贸外资高质量发展",
                "latitude": 28.22,
                "longitude": 113.22,
                "status": "planning",
                "nearby_property_price_min": 7000,
                "nearby_property_price_max": 10000
            }
        ]
        
        for park in parks_data:
            await conn.execute("""
                INSERT INTO industrial_parks 
                (name, city, district, industry_type, industry_tags, description, 
                 development_goal, latitude, longitude, status, 
                 nearby_property_price_min, nearby_property_price_max)
                VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12)
                ON CONFLICT DO NOTHING
            """, park["name"], park["city"], park["district"], park["industry_type"],
                json.dumps(park["industry_tags"]), park["description"],
                park["development_goal"], park["latitude"], park["longitude"],
                park["status"], park["nearby_property_price_min"], park["nearby_property_price_max"])
        
        print(f"   [OK] Inserted {len(parks_data)} industrial parks")
        
        # 6. 插入产城融合指数数据
        print("\n[6] Inserting city integration index data...")
        index_data = [
            {
                "city": "长沙市",
                "overall_score": 4.8,
                "industry_score": 4.9,
                "infrastructure_score": 4.7,
                "policy_score": 4.8,
                "talent_score": 4.6,
                "investment_potential": "极高",
                "key_industries": ["锂电池", "3D玻璃", "临空经济"],
                "growth_rate": 12.5
            },
            {
                "city": "郴州市",
                "overall_score": 4.2,
                "industry_score": 4.5,
                "infrastructure_score": 4.0,
                "policy_score": 4.3,
                "talent_score": 3.8,
                "investment_potential": "高",
                "key_industries": ["新能源", "储能"],
                "growth_rate": 10.2
            },
            {
                "city": "娄底市",
                "overall_score": 3.8,
                "industry_score": 4.0,
                "infrastructure_score": 3.5,
                "policy_score": 4.0,
                "talent_score": 3.5,
                "investment_potential": "中高",
                "key_industries": ["新材料", "高端制造"],
                "growth_rate": 8.5
            }
        ]
        
        for idx in index_data:
            await conn.execute("""
                INSERT INTO city_integration_index 
                (city, overall_score, industry_score, infrastructure_score, 
                 policy_score, talent_score, investment_potential, key_industries, growth_rate)
                VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9)
                ON CONFLICT (city, district) WHERE district IS NULL DO NOTHING
            """, idx["city"], idx["overall_score"], idx["industry_score"],
                idx["infrastructure_score"], idx["policy_score"], idx["talent_score"],
                idx["investment_potential"], json.dumps(idx["key_industries"]), idx["growth_rate"])
        
        print(f"   [OK] Inserted {len(index_data)} city integration indices")
        
        print("\n" + "=" * 60)
        print("Migration completed successfully!")
        print("=" * 60)
        print("\nCreated tables:")
        print("  - industrial_parks (产业园区)")
        print("  - city_integration_index (产城融合指数)")
        print("  - industry_property_correlation (产业-房产关联)")
        
    finally:
        await conn.close()


if __name__ == "__main__":
    asyncio.run(create_tables())
