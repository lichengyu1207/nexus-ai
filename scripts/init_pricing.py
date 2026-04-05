import sqlite3
from datetime import datetime

db_path = 'c:/Users/Administrator/Desktop/測試2/data/property-ai.db'
conn = sqlite3.connect(db_path)
cursor = conn.cursor()

# Create plans table
cursor.execute("""
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
        sort_order INTEGER DEFAULT 0,
        is_active INTEGER DEFAULT 1,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
""")

# Create orders table
cursor.execute("""
    CREATE TABLE IF NOT EXISTS orders (
        id TEXT PRIMARY KEY,
        user_id TEXT NOT NULL,
        plan_id TEXT NOT NULL,
        amount INTEGER NOT NULL,
        original_amount INTEGER,
        discount_reason TEXT,
        status TEXT DEFAULT 'pending',
        payment_method TEXT,
        transaction_id TEXT,
        paid_at TIMESTAMP,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (user_id) REFERENCES users(id),
        FOREIGN KEY (plan_id) REFERENCES plans(id)
    )
""")

# Add has_used_first_order column to users if not exists
try:
    cursor.execute("ALTER TABLE users ADD COLUMN has_used_first_order INTEGER DEFAULT 0")
except:
    pass

# Insert default plans
plans_data = [
    ('plan_free', '免费版', 'free', 0, None, None, None, 3, 0, '["3次免费分析","基础报告查看","7天历史记录"]', 1, 1),
    ('plan_integral_10', '积分10次', 'integral', 1990, 1790, 1490, 990, 10, 0, '["10次分析","永久有效","基础报告"]', 2, 1),
    ('plan_integral_30', '积分30次', 'integral', 4990, 4490, 3990, 2990, 30, 0, '["30次分析","永久有效","PDF导出"]', 3, 1),
    ('plan_integral_100', '积分100次', 'integral', 14990, 12990, 9990, 7990, 100, 0, '["100次分析","永久有效","PDF导出","批量分析"]', 4, 1),
    ('plan_professional', '专业版', 'professional', 19900, 19900, 15900, None, None, 30, '["无限次分析","PDF导出","批量分析","房源对比","优先客服"]', 5, 1),
    ('plan_enterprise', '企业版', 'enterprise', 99900, 99900, 79900, None, None, 30, '["所有专业版功能","API接口","团队协作(5人)","定制报告","专属客服","SLA保障"]', 6, 1),
]

for plan in plans_data:
    cursor.execute("""
        INSERT OR REPLACE INTO plans 
        (id, name, type, price_regular, price_member, price_laohai, price_new_user, credits, duration_days, features, sort_order, is_active)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, plan)

conn.commit()

# Verify
cursor.execute("SELECT id, name, type, price_regular, price_laohai FROM plans")
print("=== Plans Created ===")
for row in cursor.fetchall():
    print(f"  {row}")

cursor.execute("SELECT COUNT(*) FROM orders")
print(f"\nOrders table ready: {cursor.fetchone()[0]} rows")

conn.close()
print("\nDone!")
