import sqlite3

db_path = 'c:/Users/Administrator/Desktop/測試2/data/property-ai.db'
conn = sqlite3.connect(db_path)
cursor = conn.cursor()

print("=== Plans in Database ===")
cursor.execute("SELECT id, name, type, price_regular, price_laohai, price_new_user FROM plans")
for row in cursor.fetchall():
    print(row)

print("\n=== Orders Table ===")
cursor.execute("SELECT COUNT(*) FROM orders")
print(f"Orders count: {cursor.fetchone()[0]}")

print("\n=== Users with source ===")
cursor.execute("SELECT id, email, source, integral, membership_level FROM users LIMIT 5")
for row in cursor.fetchall():
    print(row)

conn.close()
