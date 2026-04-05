"""
数据库优化脚本
- 添加缺失的索引
- 清理冗余数据
- 分析查询性能
"""
import sqlite3
import os

DB_PATH = 'c:/Users/Administrator/Desktop/測試2/data/property-ai.db'

def optimize_database():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    print("=" * 60)
    print("数据库优化脚本")
    print("=" * 60)
    
    # 1. 分析表大小
    print("\n📊 表大小统计:")
    cursor.execute("""
        SELECT name FROM sqlite_master WHERE type='table'
    """)
    tables = cursor.fetchall()
    
    for (table_name,) in tables:
        cursor.execute(f"SELECT COUNT(*) FROM {table_name}")
        count = cursor.fetchone()[0]
        if count > 0:
            print(f"  {table_name}: {count} 条记录")
    
    # 2. 检查索引
    print("\n📋 现有索引:")
    cursor.execute("""
        SELECT name, tbl_name FROM sqlite_master WHERE type='index' AND name NOT LIKE 'sqlite_%'
    """)
    indexes = cursor.fetchall()
    for name, table in indexes:
        print(f"  {table}.{name}")
    
    # 3. 添加优化索引
    print("\n🔧 添加优化索引...")
    
    optimization_indexes = [
        "CREATE INDEX IF NOT EXISTS idx_users_role ON users(role)",
        "CREATE INDEX IF NOT EXISTS idx_users_created_at ON users(created_at)",
        "CREATE INDEX IF NOT EXISTS idx_tasks_status ON analysis_tasks(status)",
        "CREATE INDEX IF NOT EXISTS idx_tasks_created_at ON analysis_tasks(created_at)",
        "CREATE INDEX IF NOT EXISTS idx_audit_logs_user_id ON audit_logs(user_id)",
        "CREATE INDEX IF NOT EXISTS idx_audit_logs_action ON audit_logs(action)",
    ]
    
    for sql in optimization_indexes:
        try:
            cursor.execute(sql)
            print(f"  ✅ {sql.split('idx_')[1].split(' ')[0]}")
        except Exception as e:
            print(f"  ⚠️ {e}")
    
    # 4. VACUUM优化
    print("\n🧹 执行VACUUM优化...")
    cursor.execute("VACUUM")
    print("  ✅ VACUUM完成")
    
    # 5. 分析统计
    print("\n📈 执行ANALYZE...")
    cursor.execute("ANALYZE")
    print("  ✅ ANALYZE完成")
    
    conn.commit()
    conn.close()
    
    print("\n" + "=" * 60)
    print("数据库优化完成!")
    print("=" * 60)

if __name__ == "__main__":
    optimize_database()
