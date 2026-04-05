"""
创建 plans 表并插入初始套餐数据
"""
import asyncio
import aiosqlite
import json
from pathlib import Path
from datetime import datetime

DB_PATH = Path(__file__).parent.parent / "data" / "property-ai.db"

async def migrate_plans():
    """创建 plans 表并插入初始数据"""
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    conn = await aiosqlite.connect(str(DB_PATH))
    conn.row_factory = aiosqlite.Row
    
    try:
        # 创建 plans 表
        await conn.executescript("""
            CREATE TABLE IF NOT EXISTS plans (
                id TEXT PRIMARY KEY,
                name TEXT NOT NULL,
                type TEXT NOT NULL,
                price_regular INTEGER NOT NULL,
                price_member INTEGER,
                price_laohai INTEGER,
                price_new_user INTEGER,
                credits INTEGER,
                duration_days INTEGER DEFAULT 0,
                features TEXT,
                is_active INTEGER DEFAULT 1,
                sort_order INTEGER DEFAULT 0,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
            );
            
            CREATE INDEX IF NOT EXISTS idx_plans_type ON plans(type);
            CREATE INDEX IF NOT EXISTS idx_plans_is_active ON plans(is_active);
        """)
        
        # 检查是否已有数据
        cursor = await conn.execute("SELECT COUNT(*) FROM plans")
        count = (await cursor.fetchone())[0]
        
        if count > 0:
            print(f"plans 表已有 {count} 条数据，跳过初始化")
            return
        
        # 插入初始套餐数据
        plans_data = [
            {
                "id": "plan_basic",
                "name": "基础版",
                "type": "basic",
                "price_regular": 9900,
                "price_member": 7900,
                "price_laohai": 6900,
                "price_new_user": 100,
                "credits": 10,
                "duration_days": 30,
                "features": json.dumps(["10次分析额度", "基础报告", "7天有效期"], ensure_ascii=False),
                "is_active": 1,
                "sort_order": 1
            },
            {
                "id": "plan_professional",
                "name": "专业版",
                "type": "professional",
                "price_regular": 29900,
                "price_member": 23900,
                "price_laohai": 19900,
                "price_new_user": 9900,
                "credits": 50,
                "duration_days": 30,
                "features": json.dumps(["50次分析额度", "专业报告", "批量分析", "数据导出", "30天有效期"], ensure_ascii=False),
                "is_active": 1,
                "sort_order": 2
            },
            {
                "id": "plan_enterprise",
                "name": "企业版",
                "type": "enterprise",
                "price_regular": 99900,
                "price_member": 79900,
                "price_laohai": 69900,
                "price_new_user": 49900,
                "credits": 200,
                "duration_days": 90,
                "features": json.dumps(["200次分析额度", "企业级报告", "批量分析", "数据导出", "API接口", "专属客服", "90天有效期"], ensure_ascii=False),
                "is_active": 1,
                "sort_order": 3
            }
        ]
        
        for plan in plans_data:
            await conn.execute("""
                INSERT INTO plans (id, name, type, price_regular, price_member, price_laohai, 
                                   price_new_user, credits, duration_days, features, is_active, sort_order)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                plan["id"], plan["name"], plan["type"], plan["price_regular"], plan["price_member"],
                plan["price_laohai"], plan["price_new_user"], plan["credits"], plan["duration_days"],
                plan["features"], plan["is_active"], plan["sort_order"]
            ))
        
        await conn.commit()
        print("✅ plans 表创建成功，已插入 3 个初始套餐")
        
    finally:
        await conn.close()


if __name__ == "__main__":
    asyncio.run(migrate_plans())
