"""
初始化习惯培养系统数据库表
"""
import asyncio
import sys
sys.path.insert(0, 'c:\\Users\\Administrator\\Desktop\\測試2')

from backend.database import get_db_connection


async def create_habit_tables():
    """创建习惯培养系统表"""
    conn = await get_db_connection()
    try:
        await conn.execute('''
            CREATE TABLE IF NOT EXISTS signin_records (
                id TEXT PRIMARY KEY,
                user_id TEXT NOT NULL,
                sign_date DATE NOT NULL,
                reward_integral DECIMAL(10,2) NOT NULL,
                consecutive_days INTEGER,
                is_repent INTEGER DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users(id),
                UNIQUE(user_id, sign_date)
            )
        ''')
        await conn.execute('CREATE INDEX IF NOT EXISTS idx_signin_user_date ON signin_records(user_id, sign_date)')
        
        await conn.execute('''
            CREATE TABLE IF NOT EXISTS repent_cards (
                id TEXT PRIMARY KEY,
                user_id TEXT NOT NULL,
                quantity INTEGER DEFAULT 0,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users(id),
                UNIQUE(user_id)
            )
        ''')
        
        await conn.execute('''
            CREATE TABLE IF NOT EXISTS tasks (
                id TEXT PRIMARY KEY,
                name TEXT NOT NULL,
                description TEXT,
                type TEXT NOT NULL,
                target_action TEXT NOT NULL,
                target_count INTEGER NOT NULL,
                reward_integral DECIMAL(10,2) NOT NULL,
                extra_reward TEXT,
                frequency INTEGER,
                enabled INTEGER DEFAULT 1,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        await conn.execute('CREATE INDEX IF NOT EXISTS idx_tasks_type ON tasks(type)')
        await conn.execute('CREATE INDEX IF NOT EXISTS idx_tasks_enabled ON tasks(enabled)')
        
        await conn.execute('''
            CREATE TABLE IF NOT EXISTS user_task_progress (
                id TEXT PRIMARY KEY,
                user_id TEXT NOT NULL,
                task_id TEXT NOT NULL,
                progress INTEGER DEFAULT 0,
                status TEXT DEFAULT 'active',
                completed_at TIMESTAMP,
                last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users(id),
                FOREIGN KEY (task_id) REFERENCES tasks(id),
                UNIQUE(user_id, task_id)
            )
        ''')
        await conn.execute('CREATE INDEX IF NOT EXISTS idx_user_task_user ON user_task_progress(user_id)')
        await conn.execute('CREATE INDEX IF NOT EXISTS idx_user_task_status ON user_task_progress(status)')
        
        await conn.execute('''
            CREATE TABLE IF NOT EXISTS user_behavior_points (
                user_id TEXT PRIMARY KEY,
                total_points INTEGER DEFAULT 0,
                level INTEGER DEFAULT 1,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users(id)
            )
        ''')
        
        await conn.execute('''
            CREATE TABLE IF NOT EXISTS level_benefits (
                level INTEGER PRIMARY KEY,
                required_points INTEGER NOT NULL,
                benefits TEXT,
                icon TEXT
            )
        ''')
        
        await conn.commit()
        print("习惯培养系统表创建成功")
        
        cursor = await conn.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name IN ('signin_records', 'repent_cards', 'tasks', 'user_task_progress', 'user_behavior_points', 'level_benefits')"
        )
        tables = [row["name"] for row in await cursor.fetchall()]
        print(f"已创建的表: {tables}")
    finally:
        await conn.close()


async def init_default_data():
    """初始化默认数据"""
    import uuid
    conn = await get_db_connection()
    try:
        cursor = await conn.execute("SELECT COUNT(*) as cnt FROM tasks")
        row = await cursor.fetchone()
        
        if row["cnt"] > 0:
            print("任务数据已存在，跳过初始化")
            return
        
        default_tasks = [
            ("daily_analysis", "每日分析", "每天完成一次房产分析", "daily", "create_task", 1, 10, None, 1),
            ("daily_consult", "咨询达人", "每天咨询3次", "daily", "consult_query", 3, 15, None, 1),
            ("daily_upload", "数据贡献者", "每天上传一条数据", "daily", "upload_data", 1, 20, None, 1),
            ("weekly_active", "周活跃", "一周完成7次分析", "weekly", "create_task", 7, 100, None, 7),
            ("weekly_invite", "邀请好友", "邀请一位新用户注册", "weekly", "invite_user", 1, 200, None, 7),
            ("achievement_signin7", "连续签到7天", "连续签到7天", "achievement", "signin_consecutive", 7, 500, '{"badge": "signin_master_7"}', 0),
            ("achievement_first_upload", "首次上传", "首次上传数据", "achievement", "upload_data", 1, 50, '{"badge": "first_contributor"}', 0),
        ]
        
        for task in default_tasks:
            task_id = str(uuid.uuid4())
            await conn.execute(
                "INSERT INTO tasks (id, name, description, type, target_action, target_count, reward_integral, extra_reward, frequency) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
                (task_id, task[1], task[2], task[3], task[4], task[5], task[6], task[7], task[8])
            )
        
        default_levels = [
            (1, 0, '{"title": "新手", "benefits": ["基础功能"]}', "/icons/level1.png"),
            (2, 1000, '{"title": "入门", "benefits": ["基础功能", "每日任务奖励+5%"]}', "/icons/level2.png"),
            (3, 2000, '{"title": "熟练", "benefits": ["基础功能", "每日任务奖励+10%", "专属客服"]}', "/icons/level3.png"),
            (4, 5000, '{"title": "专家", "benefits": ["基础功能", "每日任务奖励+15%", "专属客服", "报告去水印"]}', "/icons/level4.png"),
            (5, 10000, '{"title": "大师", "benefits": ["基础功能", "每日任务奖励+20%", "专属客服", "报告去水印", "优先支持"]}', "/icons/level5.png"),
        ]
        
        for level in default_levels:
            await conn.execute(
                "INSERT INTO level_benefits (level, required_points, benefits, icon) VALUES (?, ?, ?, ?)",
                level
            )
        
        await conn.commit()
        print("默认任务和等级数据初始化完成")
        
        cursor = await conn.execute("SELECT id, name, type, reward_integral FROM tasks")
        tasks = await cursor.fetchall()
        for task in tasks:
            print(f"  - {task['name']} ({task['type']}): {task['reward_integral']}积分")
    finally:
        await conn.close()


async def main():
    await create_habit_tables()
    await init_default_data()
    print("\n习惯培养系统初始化完成！")


if __name__ == "__main__":
    asyncio.run(main())
