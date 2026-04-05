import sqlite3
conn = sqlite3.connect('c:/Users/Administrator/Desktop/測試2/data/app.db')
cursor = conn.cursor()
cursor.execute('SELECT id, email, full_name, role, is_admin FROM users')
for row in cursor.fetchall():
    print(row)
