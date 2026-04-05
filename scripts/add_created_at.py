import sqlite3

db_path = 'c:/Users/Administrator/Desktop/測試2/data/app.db'
conn = sqlite3.connect(db_path)
cursor = conn.cursor()

# Check if created_at column exists
cursor.execute("PRAGMA table_info(audit_logs)")
columns = cursor.fetchall()
column_names = [col[1] for col in columns]
print(f"Current columns: {column_names}")

if 'created_at' not in column_names:
    print("\nAdding created_at column to existing audit_logs table...")
    try:
        cursor.execute("ALTER TABLE audit_logs ADD COLUMN created_at DATETIME DEFAULT CURRENT_TIMESTAMP")
        conn.commit()
        print("Column added successfully!")
    except Exception as e:
        print(f"Error: {e}")
else:
    print("\ncreated_at column already exists!")

# Verify
cursor.execute("PRAGMA table_info(audit_logs)")
columns = cursor.fetchall()
print("\nFinal columns:")
for col in columns:
    print(f"  {col[1]}: {col[2]}")

conn.close()
