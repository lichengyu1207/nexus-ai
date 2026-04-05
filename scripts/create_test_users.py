import sqlite3
import uuid
from datetime import datetime

db_path = 'c:/Users/Administrator/Desktop/測試2/data/property-ai.db'
conn = sqlite3.connect(db_path)
cursor = conn.cursor()

# Create test user with laohai source
user_id = str(uuid.uuid4())
cursor.execute("""
    INSERT OR REPLACE INTO users (id, email, username, hashed_password, full_name, source, integral, membership_level, is_active, created_at)
    VALUES (?, 'test_laohai@example.com', 'test_laohai', ?, '测试粉丝用户', 'laohai', 3, 'free', 1, ?)
""", (user_id, '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/X4.qVh.N9NJ.KQXCK', datetime.utcnow().isoformat()))

# Create another test user for new user price test
user_id2 = str(uuid.uuid4())
cursor.execute("""
    INSERT OR REPLACE INTO users (id, email, username, hashed_password, full_name, source, integral, membership_level, is_active, has_used_first_order, created_at)
    VALUES (?, 'test_newuser@example.com', 'test_newuser', ?, '新用户测试', NULL, 3, 'free', 1, 0, ?)
""", (user_id2, '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/X4.qVh.N9NJ.KQXCK', datetime.utcnow().isoformat()))

conn.commit()

print("=== Test Users Created ===")
cursor.execute("SELECT id, email, source, integral, has_used_first_order FROM users WHERE email LIKE 'test_%'")
for row in cursor.fetchall():
    print(f"  {row}")

conn.close()
print("\nDone! Password for all test users: test123456")
