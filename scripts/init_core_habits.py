"""
初始化核心功能习惯培养系统数据库表
"""
import asyncio
import sys
sys.path.insert(0, 'c:\\Users\\Administrator\\Desktop\\測試2')

from backend.database import get_db_connection


async def create_core_habits_tables():
    """创建核心功能习惯培养系统表"""
    conn = await get_db_connection()
    try:
        await conn.execute('''
            CREATE TABLE IF NOT EXISTS core_function_usage (
                id TEXT PRIMARY KEY,
                user_id TEXT NOT NULL,
                function_type TEXT NOT NULL,
                usage_date DATE NOT NULL,
                count INTEGER DEFAULT 0,
                last_used_at TIMESTAMP,
                consecutive_days INTEGER DEFAULT 0,
                total_days INTEGER DEFAULT 0,
                total_count INTEGER DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users(id),
                UNIQUE(user_id, function_type, usage_date)
            )
        ''')
        await conn.execute('CREATE INDEX IF NOT EXISTS idx_core_usage_user ON core_function_usage(user_id)')
        await conn.execute('CREATE INDEX IF NOT EXISTS idx_core_usage_date ON core_function_usage(usage_date)')
        await conn.execute('CREATE INDEX IF NOT EXISTS idx_core_usage_type ON core_function_usage(function_type)')
        
        await conn.execute('''
            CREATE TABLE IF NOT EXISTS user_function_goals (
                id TEXT PRIMARY KEY,
                user_id TEXT NOT NULL,
                function_type TEXT NOT NULL,
                period TEXT NOT NULL,
                target_count INTEGER NOT NULL,
                progress INTEGER DEFAULT 0,
                achieved INTEGER DEFAULT 0,
                goal_date DATE,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users(id)
            )
        ''')
        await conn.execute('CREATE INDEX IF NOT EXISTS idx_func_goals_user ON user_function_goals(user_id)')
        await conn.execute('CREATE INDEX IF NOT EXISTS idx_func_goals_date ON user_function_goals(goal_date)')
        
        await conn.execute('''
            CREATE TABLE IF NOT EXISTS user_preferences (
                user_id TEXT PRIMARY KEY,
                reminder_enabled INTEGER DEFAULT 1,
                reminder_time TEXT DEFAULT '20:00',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users(id)
            )
        ''')
        
        await conn.commit()
        print("核心功能习惯培养系统表创建成功")
        
        cursor = await conn.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name IN ('core_function_usage', 'user_function_goals', 'user_preferences')"
        )
        tables = [row["name"] for row in await cursor.fetchall()]
        print(f"已创建的表: {tables}")
    finally:
        await conn.close()


async def main():
    await create_core_habits_tables()
    print("\n核心功能习惯培养系统初始化完成！")


if __name__ == "__main__":
    asyncio.run(main())
