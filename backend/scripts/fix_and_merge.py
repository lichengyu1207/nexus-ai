"""
修复用户密码并合并数据库
"""
import asyncio
import aiosqlite
from pathlib import Path
import bcrypt

# 数据库路径
MAIN_DB = Path(r"c:\Users\Administrator\Desktop\測試2\data\property-ai.db")
OTHER_DBS = [
    Path(r"c:\Users\Administrator\Desktop\測試2\app.db"),
    Path(r"c:\Users\Administrator\Desktop\測試2\backend\data\property-ai.db"),
    Path(r"c:\Users\Administrator\Desktop\測試2\data\app.db"),
]

TARGET_EMAIL = "1558691995@qq.com"
NEW_PASSWORD = "147258@Zxcvbnm"

async def fix_password_and_merge():
    print("=" * 60)
    print("修复用户密码并合并数据库")
    print("=" * 60)
    
    # 1. 修改密码
    print(f"\n1. 修改用户 {TARGET_EMAIL} 的密码...")
    
    # 生成新的密码哈希
    salt = bcrypt.gensalt()
    hashed_password = bcrypt.hashpw(NEW_PASSWORD.encode('utf-8'), salt).decode('utf-8')
    
    conn = await aiosqlite.connect(str(MAIN_DB))
    
    # 更新密码
    await conn.execute(
        "UPDATE users SET hashed_password = ? WHERE email = ?",
        (hashed_password, TARGET_EMAIL)
    )
    await conn.commit()
    
    # 验证更新
    cursor = await conn.execute(
        "SELECT email, username, role FROM users WHERE email = ?",
        (TARGET_EMAIL,)
    )
    user = await cursor.fetchone()
    
    if user:
        print(f"   ✅ 密码已更新")
        print(f"   用户: {user[1]} ({user[0]})")
        print(f"   角色: {user[2]}")
    else:
        print(f"   ❌ 用户不存在")
    
    # 2. 检查其他数据库中的数据
    print(f"\n2. 检查其他数据库...")
    
    for db_path in OTHER_DBS:
        if not db_path.exists():
            print(f"   ❌ 不存在: {db_path.name}")
            continue
        
        print(f"   📁 检查: {db_path.name}")
        try:
            other_conn = await aiosqlite.connect(str(db_path))
            other_conn.row_factory = aiosqlite.Row
            
            # 获取所有表
            cursor = await other_conn.execute(
                "SELECT name FROM sqlite_master WHERE type='table'"
            )
            tables = [t['name'] for t in await cursor.fetchall()]
            
            for table in tables:
                cursor = await other_conn.execute(f"SELECT COUNT(*) FROM {table}")
                count = (await cursor.fetchone())[0]
                if count > 0:
                    print(f"      - {table}: {count} 条记录")
            
            await other_conn.close()
        except Exception as e:
            print(f"      错误: {e}")
    
    # 3. 合并 articles 表数据
    print(f"\n3. 合并 articles 数据...")
    
    backend_db = Path(r"c:\Users\Administrator\Desktop\測試2\backend\data\property-ai.db")
    if backend_db.exists():
        try:
            other_conn = await aiosqlite.connect(str(backend_db))
            other_conn.row_factory = aiosqlite.Row
            
            cursor = await other_conn.execute("SELECT * FROM articles")
            articles = await cursor.fetchall()
            
            for article in articles:
                # 检查是否已存在
                cursor = await conn.execute(
                    "SELECT id FROM articles WHERE id = ? OR slug = ?",
                    (article['id'], article['slug'])
                )
                existing = await cursor.fetchone()
                
                if not existing:
                    # 插入文章
                    await conn.execute("""
                        INSERT INTO articles (id, title, slug, content, summary, cover_image, 
                                             category, tags, author_id, status, is_featured, 
                                             view_count, like_count, comment_count, published_at, 
                                             created_at, updated_at)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """, (
                        article['id'], article['title'], article['slug'], article['content'],
                        article['summary'], article['cover_image'], article['category'],
                        article['tags'], article['author_id'], article['status'],
                        article['is_featured'], article['view_count'], article['like_count'],
                        article['comment_count'], article['published_at'],
                        article['created_at'], article['updated_at']
                    ))
                    print(f"      ✅ 已合并文章: {article['title']}")
            
            await conn.commit()
            await other_conn.close()
        except Exception as e:
            print(f"      错误: {e}")
    
    # 4. 合并 plans 表数据
    print(f"\n4. 合并 plans 数据...")
    
    if backend_db.exists():
        try:
            other_conn = await aiosqlite.connect(str(backend_db))
            other_conn.row_factory = aiosqlite.Row
            
            cursor = await other_conn.execute("SELECT * FROM plans")
            plans = await cursor.fetchall()
            
            for plan in plans:
                # 检查是否已存在
                cursor = await conn.execute(
                    "SELECT id FROM plans WHERE id = ?",
                    (plan['id'],)
                )
                existing = await cursor.fetchone()
                
                if not existing:
                    # 插入套餐
                    await conn.execute("""
                        INSERT INTO plans (id, name, type, price_regular, price_member, 
                                          price_laohai, price_new_user, credits, duration_days, 
                                          features, is_active, sort_order, created_at, updated_at)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """, (
                        plan['id'], plan['name'], plan['type'], plan['price_regular'],
                        plan['price_member'], plan['price_laohai'], plan['price_new_user'],
                        plan['credits'], plan['duration_days'], plan['features'],
                        plan['is_active'], plan['sort_order'], plan['created_at'], plan['updated_at']
                    ))
                    print(f"      ✅ 已合并套餐: {plan['name']}")
            
            await conn.commit()
            await other_conn.close()
        except Exception as e:
            print(f"      错误: {e}")
    
    await conn.close()
    
    print("\n" + "=" * 60)
    print("✅ 完成！")
    print("=" * 60)
    print(f"\n用户: {TARGET_EMAIL}")
    print(f"新密码: {NEW_PASSWORD}")
    print("\n请使用新密码登录测试！")

if __name__ == "__main__":
    asyncio.run(fix_password_and_merge())
