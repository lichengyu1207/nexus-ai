import sqlite3
import uuid
from datetime import datetime

db_path = 'c:/Users/Administrator/Desktop/測試2/data/property-ai.db'
conn = sqlite3.connect(db_path)
cursor = conn.cursor()

cursor.execute("""
    CREATE TABLE IF NOT EXISTS manual_recharge_orders (
        id TEXT PRIMARY KEY,
        user_id TEXT NOT NULL,
        plan_id TEXT,
        amount REAL,
        credits INTEGER,
        membership_type TEXT,
        membership_days INTEGER,
        status TEXT DEFAULT 'pending',
        admin_notes TEXT,
        transaction_proof TEXT,
        user_notes TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        completed_at TIMESTAMP,
        completed_by TEXT,
        FOREIGN KEY (user_id) REFERENCES users(id),
        FOREIGN KEY (plan_id) REFERENCES plans(id)
    )
""")

cursor.execute("CREATE INDEX IF NOT EXISTS idx_manual_orders_user ON manual_recharge_orders(user_id)")
cursor.execute("CREATE INDEX IF NOT EXISTS idx_manual_orders_status ON manual_recharge_orders(status)")

conn.commit()
print("manual_recharge_orders 表创建成功!")

cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='manual_recharge_orders'")
print(f"验证: {cursor.fetchone()}")

conn.close()
