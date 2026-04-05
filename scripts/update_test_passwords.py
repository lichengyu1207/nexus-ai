import sqlite3
import sys
sys.path.insert(0, 'c:/Users/Administrator/Desktop/測試2')

from passlib.context import CryptContext

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

db_path = 'c:/Users/Administrator/Desktop/測試2/data/property-ai.db'
conn = sqlite3.connect(db_path)
cursor = conn.cursor()

password = 'test123456'
hashed = pwd_context.hash(password)

# 更新测试用户密码
users_to_update = [
    'xiaowang@test.com',
    'xiaoli@test.com',
    'laozhang@test.com',
    'chenjie@test.com',
]

for email in users_to_update:
    cursor.execute("UPDATE users SET hashed_password = ? WHERE email = ?", (hashed, email))
    print(f"已更新密码: {email}")

conn.commit()
conn.close()

print(f"\n所有测试用户密码已更新为: {password}")
