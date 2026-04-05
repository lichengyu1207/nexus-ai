import sqlite3

db_path = 'c:/Users/Administrator/Desktop/測試2/data/app.db'
conn = sqlite3.connect(db_path)
cursor = conn.cursor()

# Check current structure
print("=== Current audit_logs structure ===")
cursor.execute("PRAGMA table_info(audit_logs)")
columns = cursor.fetchall()
for col in columns:
    print(f"  {col[1]}: {col[2]}")

# Drop and recreate with correct structure
print("\nRecreating audit_logs table with correct structure...")
cursor.execute("DROP TABLE IF EXISTS audit_logs")
cursor.execute("""
    CREATE TABLE audit_logs (
        id TEXT PRIMARY KEY,
        timestamp TEXT NOT NULL,
        user_id TEXT,
        username TEXT,
        user_role TEXT,
        ip_address TEXT,
        user_agent TEXT,
        action_type TEXT NOT NULL,
        resource_type TEXT,
        resource_id TEXT,
        old_value TEXT,
        new_value TEXT,
        status TEXT DEFAULT 'success',
        error_message TEXT,
        created_at TEXT DEFAULT CURRENT_TIMESTAMP
    )
""")
conn.commit()

# Verify
print("\n=== New audit_logs structure ===")
cursor.execute("PRAGMA table_info(audit_logs)")
columns = cursor.fetchall()
for col in columns:
    print(f"  {col[1]}: {col[2]}")

conn.close()
print("\nDone!")
