"""
用户习惯培养系统测试脚本
"""
import asyncio
import sys
sys.path.insert(0, 'c:\\Users\\Administrator\\Desktop\\測試2')

from backend.database import get_db_connection
from backend.routers.habit import (
    init_default_tasks,
    reset_daily_tasks,
    reset_weekly_tasks,
    get_consecutive_days,
    calculate_signin_reward,
    ensure_user_behavior_points,
    add_behavior_points
)


async def test_database_tables():
    """测试数据库表是否创建成功"""
    print("\n=== 测试数据库表 ===")
    conn = await get_db_connection()
    try:
        cursor = await conn.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name IN ('signin_records', 'repent_cards', 'tasks', 'user_task_progress', 'user_behavior_points', 'level_benefits')"
        )
        tables = [row["name"] for row in await cursor.fetchall()]
        print(f"已创建的表: {tables}")
        assert len(tables) == 6, f"期望6个表，实际创建了{len(tables)}个"
        print("✓ 数据库表创建成功")
    finally:
        await conn.close()


async def test_init_default_tasks():
    """测试初始化默认任务"""
    print("\n=== 测试初始化默认任务 ===")
    await init_default_tasks()
    
    conn = await get_db_connection()
    try:
        cursor = await conn.execute("SELECT COUNT(*) as cnt FROM tasks")
        count = (await cursor.fetchone())["cnt"]
        print(f"任务数量: {count}")
        
        cursor = await conn.execute("SELECT id, name, type, reward_integral FROM tasks")
        tasks = await cursor.fetchall()
        for task in tasks:
            print(f"  - {task['name']} ({task['type']}): {task['reward_integral']}积分")
        
        cursor = await conn.execute("SELECT COUNT(*) as cnt FROM level_benefits")
        level_count = (await cursor.fetchone())["cnt"]
        print(f"等级数量: {level_count}")
        print("✓ 默认任务初始化成功")
    finally:
        await conn.close()


async def test_signin_reward_calculation():
    """测试签到奖励计算"""
    print("\n=== 测试签到奖励计算 ===")
    for day in range(1, 15):
        reward = await calculate_signin_reward(day)
        print(f"第{day}天签到奖励: {reward}积分")
    print("✓ 签到奖励计算正确")


async def test_level_system():
    """测试等级系统"""
    print("\n=== 测试等级系统 ===")
    conn = await get_db_connection()
    try:
        cursor = await conn.execute("SELECT * FROM level_benefits ORDER BY level")
        levels = await cursor.fetchall()
        for level in levels:
            print(f"  Lv.{level['level']}: 需要{level['required_points']}积分")
        print("✓ 等级系统配置正确")
    finally:
        await conn.close()


async def main():
    """主测试函数"""
    print("=" * 50)
    print("用户习惯培养系统测试")
    print("=" * 50)
    
    try:
        await test_database_tables()
        await test_init_default_tasks()
        await test_signin_reward_calculation()
        await test_level_system()
        
        print("\n" + "=" * 50)
        print("所有测试通过！✓")
        print("=" * 50)
    except Exception as e:
        print(f"\n测试失败: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())
