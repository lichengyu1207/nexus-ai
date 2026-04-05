"""
用户角色和权限迁移脚本
为现有用户设置默认角色，添加permissions字段
"""
import asyncio
import aiosqlite
import json
import argparse
from pathlib import Path

DB_PATH = Path(__file__).parent.parent / "data" / "app.db"

DEFAULT_ROLE_PERMISSIONS = {
    "user": [],
    "admin": [
        "can_manage_users",
        "can_view_logs",
        "can_manage_teams",
        "can_export_data",
    ],
    "super_admin": [
        "can_manage_users",
        "can_view_logs",
        "can_manage_system",
        "can_manage_teams",
        "can_export_data",
        "can_view_all_reports",
    ],
}


async def migrate(super_admin_email: str = None):
    """
    执行迁移
    
    Args:
        super_admin_email: 指定为超级管理员的用户邮箱
    """
    print("开始迁移...")
    
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        
        # 检查permissions列是否存在
        cursor = await db.execute("PRAGMA table_info(users)")
        columns = [row["name"] for row in await cursor.fetchall()]
        
        if "permissions" not in columns:
            print("添加permissions列...")
            await db.execute("ALTER TABLE users ADD COLUMN permissions TEXT DEFAULT '{}'")
            await db.commit()
            print("permissions列添加成功")
        else:
            print("permissions列已存在")
        
        # 获取所有用户
        cursor = await db.execute("SELECT id, email, role, is_admin, permissions FROM users")
        users = await cursor.fetchall()
        
        print(f"找到 {len(users)} 个用户")
        
        updated_count = 0
        
        for user in users:
            user_id = user["id"]
            email = user["email"]
            current_role = user["role"] or "user"
            is_admin = bool(user["is_admin"])
            permissions = user["permissions"]
            
            # 确定角色
            if super_admin_email and email == super_admin_email:
                new_role = "super_admin"
                new_is_admin = True
            elif is_admin:
                new_role = "admin"
                new_is_admin = True
            else:
                new_role = "user"
                new_is_admin = False
            
            # 设置默认权限
            if not permissions or permissions == "{}":
                default_perms = DEFAULT_ROLE_PERMISSIONS.get(new_role, [])
                new_permissions = json.dumps({perm: True for perm in default_perms})
            else:
                new_permissions = permissions
            
            # 更新用户
            await db.execute(
                """
                UPDATE users 
                SET role = ?, is_admin = ?, permissions = ?
                WHERE id = ?
                """,
                (new_role, new_is_admin, new_permissions, user_id)
            )
            
            updated_count += 1
            print(f"  用户 {email}: role={new_role}, is_admin={new_is_admin}")
        
        await db.commit()
        
        print(f"\n迁移完成！更新了 {updated_count} 个用户")
        
        # 显示统计
        cursor = await db.execute(
            "SELECT role, COUNT(*) as count FROM users GROUP BY role"
        )
        stats = await cursor.fetchall()
        
        print("\n角色统计:")
        for row in stats:
            print(f"  {row['role']}: {row['count']} 个用户")


async def create_super_admin(email: str):
    """
    创建或设置超级管理员
    
    Args:
        email: 超级管理员邮箱
    """
    async with aiosqlite.connect(DB_PATH) as db:
        cursor = await db.execute(
            "SELECT id FROM users WHERE email = ?",
            (email,)
        )
        user = await cursor.fetchone()
        
        if not user:
            print(f"用户 {email} 不存在")
            return
        
        permissions = json.dumps({perm: True for perm in DEFAULT_ROLE_PERMISSIONS["super_admin"]})
        
        await db.execute(
            """
            UPDATE users 
            SET role = 'super_admin', is_admin = 1, permissions = ?
            WHERE email = ?
            """,
            (permissions, email)
        )
        await db.commit()
        
        print(f"用户 {email} 已设置为超级管理员")


def main():
    parser = argparse.ArgumentParser(description="用户角色和权限迁移")
    parser.add_argument(
        "--super-admin",
        type=str,
        help="指定超级管理员邮箱"
    )
    parser.add_argument(
        "--set-super-admin",
        type=str,
        help="设置指定用户为超级管理员"
    )
    
    args = parser.parse_args()
    
    if args.set_super_admin:
        asyncio.run(create_super_admin(args.set_super_admin))
    else:
        asyncio.run(migrate(args.super_admin))


if __name__ == "__main__":
    main()
