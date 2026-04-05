import sqlite3
from datetime import datetime

db_path = 'c:/Users/Administrator/Desktop/測試2/data/property-ai.db'
conn = sqlite3.connect(db_path)
cursor = conn.cursor()

# Check current structure
cursor.execute("PRAGMA table_info(audit_logs)")
columns = cursor.fetchall()
column_names = [col[1] for col in columns]
print(f"Current columns: {column_names}")

if 'created_at' not in column_names:
    print("\nAdding created_at column (without default)...")
    cursor.execute("ALTER TABLE audit_logs ADD COLUMN created_at TEXT")
    
    # Update existing records with timestamp value
    print("Updating existing records...")
    cursor.execute("UPDATE audit_logs SET created_at = timestamp WHERE created_at IS NULL")
    conn.commit()
    print("Column added and records updated!")
else:
    print("\ncreated_at column already exists!")

# Verify
cursor.execute("PRAGMA table_info(audit_logs)")
columns = cursor.fetchall()
print(f"\nFinal columns: {[col[1] for col in columns]}")

cursor.execute("SELECT COUNT(*) FROM audit_logs")
count = cursor.fetchone()[0]
print(f"Total audit logs: {count}")

cursor.execute("SELECT id, timestamp, created_at FROM audit_logs LIMIT 3")
print("\nSample records:")
for row in cursor.fetchall():
    print(f"  {row}")

conn.close()
