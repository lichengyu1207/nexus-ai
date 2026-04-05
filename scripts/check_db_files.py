import sqlite3
import os

# Check both possible database locations
db_paths = [
    'c:/Users/Administrator/Desktop/測試2/data/property-ai.db',
    'c:/Users/Administrator/Desktop/測試2/data/app.db'
]

for db_path in db_paths:
    print(f"\n=== {db_path} ===")
    print(f"Exists: {os.path.exists(db_path)}")
    
    if os.path.exists(db_path):
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = cursor.fetchall()
        print(f"Tables: {[t[0] for t in tables]}")
        
        if 'audit_logs' in [t[0] for t in tables]:
            cursor.execute("PRAGMA table_info(audit_logs)")
            columns = cursor.fetchall()
            print(f"audit_logs columns: {[col[1] for col in columns]}")
            
            cursor.execute("SELECT COUNT(*) FROM audit_logs")
            count = cursor.fetchone()[0]
            print(f"audit_logs rows: {count}")
        
        conn.close()
