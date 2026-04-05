import sqlite3
import sys
sys.path.insert(0, 'c:/Users/Administrator/Desktop/測試2')

from passlib.context import CryptContext

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

db_path = 'c:/Users/Administrator/Desktop/測試2/data/property-ai.db'
conn = sqlite3.connect(db_path)
cursor = conn.cursor()

password = '147258@Zxcvbnm'
hashed = pwd_context.hash(password)

users_to_update = [
    'xiaowang@test.com',
    'xiaoli@test.com',
    'laozhang@test.com',
    'chenjie@test.com',
]

for email in users_to_update:
    cursor.execute("UPDATE users SET hashed_password = ? WHERE email = ?", (hashed, email))
    print(f"已恢复: {email}")

cursor.execute("UPDATE users SET hashed_password = ? WHERE email = 'admin@test.com'", (hashed,))
print(f"已恢复管理员密码")

conn.commit()
conn.close()

print(f"\n所有密码已恢复为: {password}")
