"""
创建用户反馈表
"""
import sqlite3

DB_PATH = 'c:/Users/Administrator/Desktop/測試2/data/property-ai.db'
conn = sqlite3.connect(DB_PATH)
cursor = conn.cursor()

print("创建用户反馈表...")

try:
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS user_feedback (
            id TEXT PRIMARY KEY,
            user_id TEXT NOT NULL,
            type TEXT DEFAULT 'general',
            content TEXT NOT NULL,
            rating INTEGER,
            page_url TEXT,
            user_agent TEXT,
            status TEXT DEFAULT 'pending',
            reply TEXT,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(id)
        )
    """)
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_feedback_user ON user_feedback(user_id)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_feedback_status ON user_feedback(status)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_feedback_type ON user_feedback(type)")
    conn.commit()
    print("OK - user_feedback表已创建")
except Exception as e:
    print(f"Error: {e}")

conn.close()
