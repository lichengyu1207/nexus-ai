import sqlite3
import os

db_path = 'c:/Users/Administrator/Desktop/測試2/data/property-ai.db'
conn = sqlite3.connect(db_path)
cursor = conn.cursor()

# Check all tables
cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
tables = cursor.fetchall()
print("=== All Tables ===")
for t in tables:
    print(f"  {t[0]}")

# Check if plans table exists
table_names = [t[0] for t in tables]
if 'plans' in table_names:
    cursor.execute("PRAGMA table_info(plans)")
    columns = cursor.fetchall()
    print("\n=== plans table structure ===")
    for col in columns:
        print(f"  {col[1]}: {col[2]}")
    
    cursor.execute("SELECT * FROM plans")
    rows = cursor.fetchall()
    print(f"\n=== plans data ({len(rows)} rows) ===")
    for row in rows:
        print(f"  {row}")
else:
    print("\nplans table does NOT exist!")

# Check integral_logs table
if 'integral_logs' in table_names:
    cursor.execute("PRAGMA table_info(integral_logs)")
    columns = cursor.fetchall()
    print("\n=== integral_logs table structure ===")
    for col in columns:
        print(f"  {col[1]}: {col[2]}")

# Check orders table
if 'orders' in table_names:
    cursor.execute("PRAGMA table_info(orders)")
    columns = cursor.fetchall()
    print("\n=== orders table structure ===")
    for col in columns:
        print(f"  {col[1]}: {col[2]}")
else:
    print("\norders table does NOT exist!")

conn.close()
