import sqlite3
from passlib.context import CryptContext

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

db_path = 'c:/Users/Administrator/Desktop/測試2/data/property-ai.db'
conn = sqlite3.connect(db_path)
cursor = conn.cursor()

# 生成密码哈希
password = 'test123456'
hashed = pwd_context.hash(password)

print(f"密码: {password}")
print(f"哈希: {hashed}")

# 更新测试用户密码
users_to_update = [
    'xiaowang@test.com',
    'xiaoli@test.com',
    'laozhang@test.com',
    'chenjie@test.com',
]

for email in users_to_update:
    cursor.execute("UPDATE users SET hashed_password = ? WHERE email = ?", (hashed, email))
    print(f"已更新: {email}")

# 更新管理员密码
admin_password = 'admin123'
admin_hashed = pwd_context.hash(admin_password)
cursor.execute("UPDATE users SET hashed_password = ? WHERE email = 'admin@test.com'", (admin_hashed,))
print(f"已更新管理员密码: admin123")

conn.commit()
conn.close()

print("\n密码重置完成!")
