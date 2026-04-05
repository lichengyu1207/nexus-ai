"""
创建用户引导表
"""
import sqlite3

DB_PATH = 'c:/Users/Administrator/Desktop/測試2/data/property-ai.db'
conn = sqlite3.connect(DB_PATH)
cursor = conn.cursor()

print("创建用户引导表...")

try:
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS user_onboarding (
            id TEXT PRIMARY KEY,
            user_id TEXT NOT NULL UNIQUE,
            welcome_completed INTEGER DEFAULT 0,
            profile_completed INTEGER DEFAULT 0,
            first_analysis_completed INTEGER DEFAULT 0,
            tutorial_completed INTEGER DEFAULT 0,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(id)
        )
    """)
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_onboarding_user ON user_onboarding(user_id)")
    conn.commit()
    print("OK - user_onboarding表已创建")
except Exception as e:
    print(f"Error: {e}")

conn.close()
