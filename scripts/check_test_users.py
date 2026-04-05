import sqlite3

db_path = 'c:/Users/Administrator/Desktop/測試2/data/property-ai.db'
conn = sqlite3.connect(db_path)
cursor = conn.cursor()

print("=== 测试用户列表 ===")
cursor.execute("""
    SELECT id, email, username, full_name, source, integral, membership_level, has_used_first_order 
    FROM users 
    WHERE email IN ('xiaowang@test.com', 'xiaoli@test.com', 'laozhang@test.com', 'chenjie@test.com')
""")
for row in cursor.fetchall():
    print(f"  ID: {row[0][:8]}...")
    print(f"  邮箱: {row[1]}")
    print(f"  用户名: {row[2]}")
    print(f"  姓名: {row[3]}")
    print(f"  来源: {row[4]}")
    print(f"  积分: {row[5]}")
    print(f"  会员等级: {row[6]}")
    print(f"  已用首单: {row[7]}")
    print()

print("=== 管理员账户 ===")
cursor.execute("SELECT id, email, username, role, is_admin FROM users WHERE is_admin = 1")
for row in cursor.fetchall():
    print(f"  邮箱: {row[1]}, 角色: {row[3]}")

conn.close()
