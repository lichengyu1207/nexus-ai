"""
数据库种子数据脚本
创建默认管理员用户
"""

import asyncio
import sys
import os

# 添加项目根目录到路径
project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, project_root)

from backend.auth import get_password_hash
import uuid
from datetime import datetime


async def create_admin_users():
    """创建默认管理员用户"""
    from backend.database_pg import get_db
    
    async with get_db() as conn:
        # 检查是否已存在super_admin (使用原邮箱)
        existing_super = await conn.fetchrow(
            "SELECT * FROM users WHERE email = $1",
            "1558691995@qq.com"
        )
        
        if existing_super:
            print("超级管理员已存在:", existing_super["email"])
        else:
            # 创建超级管理员 (使用原账号信息)
            super_admin_id = str(uuid.uuid4())
            now = datetime.utcnow().isoformat()
            await conn.execute(
                """
                INSERT INTO users (id, username, email, hashed_password, full_name, role, integral, is_active, created_at, updated_at)
                VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10)
                """,
                super_admin_id, "superadmin", "1558691995@qq.com", 
                get_password_hash("147258@Zxcvbnm"), "超级管理员", 
                "super_admin", 100000, True, now, now
            )
            print("✅ 超级管理员创建成功!")
            print("   邮箱: 1558691995@qq.com")
            print("   密码: 147258@Zxcvbnm")
            print("   角色: super_admin")
        
        # 检查是否已存在admin
        existing_admin = await conn.fetchrow(
            "SELECT * FROM users WHERE username = $1",
            "admin"
        )
        
        if existing_admin:
            print("管理员已存在:", existing_admin["username"])
        else:
            # 创建普通管理员
            admin_id = str(uuid.uuid4())
            now = datetime.utcnow().isoformat()
            await conn.execute(
                """
                INSERT INTO users (id, username, email, hashed_password, full_name, role, integral, is_active, created_at, updated_at)
                VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10)
                """,
                admin_id, "admin", "admin@fangdu.ai", 
                get_password_hash("Admin@2026"), "管理员", 
                "admin", 10000, True, now, now
            )
            print("✅ 管理员创建成功!")
            print("   用户名: admin")
            print("   密码: Admin@2026")
            print("   角色: admin")
        
        # 检查测试用户
        existing_test = await conn.fetchrow(
            "SELECT * FROM users WHERE username = $1",
            "test"
        )
        
        if existing_test:
            print("测试用户已存在:", existing_test["username"])
        else:
            # 创建测试用户
            test_id = str(uuid.uuid4())
            now = datetime.utcnow().isoformat()
            await conn.execute(
                """
                INSERT INTO users (id, username, email, hashed_password, full_name, role, integral, is_active, created_at, updated_at)
                VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10)
                """,
                test_id, "test", "test@fangdu.ai", 
                get_password_hash("Test@2026"), "测试用户", 
                "user", 1000, True, now, now
            )
            print("✅ 测试用户创建成功!")
            print("   用户名: test")
            print("   密码: Test@2026")
            print("   角色: user")


async def main():
    print("=" * 50)
    print("房都督AI - 数据库种子数据初始化")
    print("=" * 50)
    print()
    
    try:
        await create_admin_users()
        print()
        print("=" * 50)
        print("种子数据初始化完成!")
        print("=" * 50)
    except Exception as e:
        print(f"❌ 错误: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())
