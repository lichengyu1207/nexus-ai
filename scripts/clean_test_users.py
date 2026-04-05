"""
清理测试数据脚本
删除测试用户及其关联数据
"""
import sqlite3
import os
import argparse

DB_PATH = os.path.join(os.path.dirname(__file__), '..', 'data', 'property-ai.db')


def get_db():
    conn = sqlite3.connect(DB_PATH, timeout=30.0)
    conn.row_factory = sqlite3.Row
    return conn


def clean_test_users(email_prefix: str = 'test_', dry_run: bool = False):
    """清理测试用户"""
    conn = get_db()
    cursor = conn.cursor()
    
    cursor.execute("SELECT COUNT(*) FROM users WHERE email LIKE ?", (f'{email_prefix}%',))
    user_count = cursor.fetchone()[0]
    
    if user_count == 0:
        print(f"没有找到邮箱前缀为 '{email_prefix}' 的用户")
        conn.close()
        return
    
    print(f"找到 {user_count} 个测试用户")
    
    if dry_run:
        print("\n[DRY RUN] 以下数据将被删除:")
        
        cursor.execute("SELECT COUNT(*) FROM integral_logs WHERE user_id IN (SELECT id FROM users WHERE email LIKE ?)", (f'{email_prefix}%',))
        log_count = cursor.fetchone()[0]
        print(f"  - 积分日志: {log_count} 条")
        
        cursor.execute("SELECT COUNT(*) FROM analysis_tasks WHERE user_id IN (SELECT id FROM users WHERE email LIKE ?)", (f'{email_prefix}%',))
        task_count = cursor.fetchone()[0]
        print(f"  - 任务记录: {task_count} 条")
        
        cursor.execute("SELECT COUNT(*) FROM signin_records WHERE user_id IN (SELECT id FROM users WHERE email LIKE ?)", (f'{email_prefix}%',))
        signin_count = cursor.fetchone()[0]
        print(f"  - 签到记录: {signin_count} 条")
        
        cursor.execute("SELECT COUNT(*) FROM user_behavior_stats WHERE user_id IN (SELECT id FROM users WHERE email LIKE ?)", (f'{email_prefix}%',))
        behavior_count = cursor.fetchone()[0]
        print(f"  - 行为统计: {behavior_count} 条")
        
        conn.close()
        return
    
    confirm = input(f"\n确认删除 {user_count} 个测试用户及其所有关联数据? (yes/no): ")
    if confirm.lower() != 'yes':
        print("操作已取消")
        conn.close()
        return
    
    print("\n开始清理...")
    
    cursor.execute("DELETE FROM integral_logs WHERE user_id IN (SELECT id FROM users WHERE email LIKE ?)", (f'{email_prefix}%',))
    log_deleted = cursor.rowcount
    print(f"  删除积分日志: {log_deleted} 条")
    
    cursor.execute("DELETE FROM analysis_tasks WHERE user_id IN (SELECT id FROM users WHERE email LIKE ?)", (f'{email_prefix}%',))
    task_deleted = cursor.rowcount
    print(f"  删除任务记录: {task_deleted} 条")
    
    cursor.execute("DELETE FROM signin_records WHERE user_id IN (SELECT id FROM users WHERE email LIKE ?)", (f'{email_prefix}%',))
    signin_deleted = cursor.rowcount
    print(f"  删除签到记录: {signin_deleted} 条")
    
    cursor.execute("DELETE FROM user_behavior_stats WHERE user_id IN (SELECT id FROM users WHERE email LIKE ?)", (f'{email_prefix}%',))
    behavior_deleted = cursor.rowcount
    print(f"  删除行为统计: {behavior_deleted} 条")
    
    cursor.execute("DELETE FROM user_signin_stats WHERE user_id IN (SELECT id FROM users WHERE email LIKE ?)", (f'{email_prefix}%',))
    
    cursor.execute("DELETE FROM users WHERE email LIKE ?", (f'{email_prefix}%',))
    user_deleted = cursor.rowcount
    print(f"  删除用户: {user_deleted} 个")
    
    print("\n重建统计表...")
    
    cursor.execute("DELETE FROM user_source_stats")
    cursor.execute('''
        INSERT INTO user_source_stats (source, user_count, updated_at)
        SELECT COALESCE(source, 'unknown'), COUNT(*), CURRENT_TIMESTAMP
        FROM users GROUP BY COALESCE(source, 'unknown')
    ''')
    
    cursor.execute("DELETE FROM user_city_stats")
    cursor.execute('''
        INSERT INTO user_city_stats (city, user_count, updated_at)
        SELECT city, COUNT(*), CURRENT_TIMESTAMP
        FROM users WHERE city IS NOT NULL AND city != '' GROUP BY city
    ''')
    
    cursor.execute("DELETE FROM user_district_stats")
    cursor.execute('''
        INSERT INTO user_district_stats (id, city, district, user_count, updated_at)
        SELECT city || '_' || district, city, district, COUNT(*), CURRENT_TIMESTAMP
        FROM users WHERE city IS NOT NULL AND city != '' AND district IS NOT NULL AND district != ''
        GROUP BY city, district
    ''')
    
    conn.commit()
    conn.close()
    
    print("\n" + "=" * 60)
    print("✅ 测试数据清理完成!")
    print("=" * 60)


def main():
    parser = argparse.ArgumentParser(description='清理测试用户数据')
    parser.add_argument('--prefix', type=str, default='test_', help='邮箱前缀筛选')
    parser.add_argument('--dry-run', action='store_true', help='仅预览，不实际删除')
    args = parser.parse_args()
    
    print("=" * 60)
    print("清理测试数据")
    print("=" * 60)
    
    clean_test_users(args.prefix, args.dry_run)


if __name__ == '__main__':
    main()
