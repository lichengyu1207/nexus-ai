"""
模块数据协同 - 数据库结构优化迁移脚本
添加用户城市字段、来源统计表、城市统计表
支持数据一致性保障
"""
import sqlite3
import os
from datetime import datetime

DB_PATH = os.path.join(os.path.dirname(__file__), '..', 'data', 'property-ai.db')

def table_exists(cursor, table_name):
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name=?", (table_name,))
    return cursor.fetchone() is not None

def column_exists(cursor, table_name, column_name):
    cursor.execute(f"PRAGMA table_info({table_name})")
    columns = [col[1] for col in cursor.fetchall()]
    return column_name in columns

def migrate():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    print("=" * 60)
    print("模块数据协同 - 数据库结构优化迁移")
    print("=" * 60)
    
    print("\n1. 检查用户表字段...")
    
    if not column_exists(cursor, 'users', 'city'):
        print("   添加 users.city 字段...")
        cursor.execute('ALTER TABLE users ADD COLUMN city TEXT')
        print("   ✅ 添加成功")
    else:
        print("   ✅ users.city 字段已存在")
    
    if not column_exists(cursor, 'users', 'district'):
        print("   添加 users.district 字段...")
        cursor.execute('ALTER TABLE users ADD COLUMN district TEXT')
        print("   ✅ 添加成功")
    else:
        print("   ✅ users.district 字段已存在")
    
    print("\n2. 创建用户来源统计表...")
    if not table_exists(cursor, 'user_source_stats'):
        cursor.execute('''
            CREATE TABLE user_source_stats (
                source TEXT PRIMARY KEY,
                user_count INTEGER DEFAULT 0,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        print("   ✅ user_source_stats 表创建成功")
    else:
        print("   ✅ user_source_stats 表已存在")
    
    print("\n3. 创建用户城市统计表...")
    if not table_exists(cursor, 'user_city_stats'):
        cursor.execute('''
            CREATE TABLE user_city_stats (
                city TEXT PRIMARY KEY,
                user_count INTEGER DEFAULT 0,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        print("   ✅ user_city_stats 表创建成功")
    else:
        print("   ✅ user_city_stats 表已存在")
    
    print("\n4. 创建用户区域统计表...")
    if not table_exists(cursor, 'user_district_stats'):
        cursor.execute('''
            CREATE TABLE user_district_stats (
                id TEXT PRIMARY KEY,
                city TEXT NOT NULL,
                district TEXT NOT NULL,
                user_count INTEGER DEFAULT 0,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(city, district)
            )
        ''')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_user_district_stats_city ON user_district_stats(city)')
        print("   ✅ user_district_stats 表创建成功")
    else:
        print("   ✅ user_district_stats 表已存在")
    
    print("\n5. 创建用户行为统计表...")
    if not table_exists(cursor, 'user_behavior_stats'):
        cursor.execute('''
            CREATE TABLE user_behavior_stats (
                user_id TEXT PRIMARY KEY,
                total_tasks INTEGER DEFAULT 0,
                completed_tasks INTEGER DEFAULT 0,
                total_integral_earned REAL DEFAULT 0,
                total_integral_spent REAL DEFAULT 0,
                signin_days INTEGER DEFAULT 0,
                last_active_at TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users(id)
            )
        ''')
        print("   ✅ user_behavior_stats 表创建成功")
    else:
        print("   ✅ user_behavior_stats 表已存在")
    
    print("\n6. 创建数据一致性日志表...")
    if not table_exists(cursor, 'consistency_logs'):
        cursor.execute('''
            CREATE TABLE consistency_logs (
                id TEXT PRIMARY KEY,
                check_type TEXT NOT NULL,
                expected_value INTEGER,
                actual_value INTEGER,
                is_consistent INTEGER DEFAULT 1,
                details TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_consistency_logs_type ON consistency_logs(check_type)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_consistency_logs_created ON consistency_logs(created_at)')
        print("   ✅ consistency_logs 表创建成功")
    else:
        print("   ✅ consistency_logs 表已存在")
    
    print("\n7. 重建统计数据...")
    
    cursor.execute("DELETE FROM user_source_stats")
    cursor.execute('''
        INSERT INTO user_source_stats (source, user_count, updated_at)
        SELECT 
            COALESCE(source, 'unknown') as source,
            COUNT(*) as user_count,
            CURRENT_TIMESTAMP
        FROM users
        GROUP BY COALESCE(source, 'unknown')
    ''')
    cursor.execute("SELECT COUNT(*) FROM user_source_stats")
    source_count = cursor.fetchone()[0]
    print(f"   ✅ 来源统计重建完成: {source_count} 个来源")
    
    cursor.execute("DELETE FROM user_city_stats")
    cursor.execute('''
        INSERT INTO user_city_stats (city, user_count, updated_at)
        SELECT 
            COALESCE(city, 'unknown') as city,
            COUNT(*) as user_count,
            CURRENT_TIMESTAMP
        FROM users
        WHERE city IS NOT NULL AND city != ''
        GROUP BY city
    ''')
    cursor.execute("SELECT COUNT(*) FROM user_city_stats")
    city_count = cursor.fetchone()[0]
    print(f"   ✅ 城市统计重建完成: {city_count} 个城市")
    
    cursor.execute("DELETE FROM user_district_stats")
    cursor.execute('''
        INSERT INTO user_district_stats (id, city, district, user_count, updated_at)
        SELECT 
            city || '_' || district as id,
            city,
            district,
            COUNT(*) as user_count,
            CURRENT_TIMESTAMP
        FROM users
        WHERE city IS NOT NULL AND city != '' AND district IS NOT NULL AND district != ''
        GROUP BY city, district
    ''')
    cursor.execute("SELECT COUNT(*) FROM user_district_stats")
    district_count = cursor.fetchone()[0]
    print(f"   ✅ 区域统计重建完成: {district_count} 个区域")
    
    print("\n8. 初始化用户行为统计...")
    cursor.execute('''
        INSERT OR IGNORE INTO user_behavior_stats (user_id, total_tasks, completed_tasks, updated_at)
        SELECT 
            u.id as user_id,
            COALESCE(t.total_tasks, 0) as total_tasks,
            COALESCE(t.completed_tasks, 0) as completed_tasks,
            CURRENT_TIMESTAMP
        FROM users u
        LEFT JOIN (
            SELECT user_id, COUNT(*) as total_tasks, 
                   SUM(CASE WHEN status = 'completed' THEN 1 ELSE 0 END) as completed_tasks
            FROM analysis_tasks
            GROUP BY user_id
        ) t ON u.id = t.user_id
    ''')
    cursor.execute("SELECT COUNT(*) FROM user_behavior_stats")
    behavior_count = cursor.fetchone()[0]
    print(f"   ✅ 用户行为统计初始化: {behavior_count} 条记录")
    
    conn.commit()
    conn.close()
    
    print("\n" + "=" * 60)
    print("✅ 数据库结构优化迁移完成!")
    print("=" * 60)

if __name__ == '__main__':
    migrate()
