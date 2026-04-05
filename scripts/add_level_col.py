import sqlite3
conn = sqlite3.connect('data/property-ai.db')
cursor = conn.cursor()
try:
    cursor.execute('ALTER TABLE ip_partners ADD COLUMN level TEXT DEFAULT "bronze"')
    conn.commit()
    print('Added level column')
except Exception as e:
    print(f'Error: {e}')
conn.close()
