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

# 只恢复真正的管理员密码
cursor.execute("UPDATE users SET hashed_password = ? WHERE email = '1558691995@qq.com'", (hashed,))
print(f"已恢复管理员密码: 1558691995@qq.com")

conn.commit()
conn.close()

print(f"\n密码已恢复为: {password}")
