"""
数据库索引优化迁移脚本
添加必要的索引以提升查询性能
"""
import sqlite3
import os
import time
from datetime import datetime

INDEXES = [
    ("idx_users_email", "users", "email", True),
    ("idx_users_role", "users", "role", False),
    ("idx_users_created_at", "users", "created_at", False),
    ("idx_users_is_active", "users", "is_active", False),
    
    ("idx_tasks_user_id", "tasks", "user_id", False),
    ("idx_tasks_status", "tasks", "status", False),
    ("idx_tasks_created_at", "tasks", "created_at", False),
    ("idx_tasks_updated_at", "tasks", "updated_at", False),
    ("idx_tasks_user_status", "tasks", "user_id, status", False),
    ("idx_tasks_user_created", "tasks", "user_id, created_at DESC", False),
    
    ("idx_reports_task_id", "reports", "task_id", False),
    ("idx_reports_user_id", "reports", "user_id", False),
    ("idx_reports_status", "reports", "status", False),
    ("idx_reports_created_at", "reports", "created_at", False),
    ("idx_reports_task_status", "reports", "task_id, status", False),
    
    ("idx_audit_logs_user_id", "audit_logs", "user_id", False),
    ("idx_audit_logs_action", "audit_logs", "action", False),
    ("idx_audit_logs_timestamp", "audit_logs", "timestamp", False),
    ("idx_audit_logs_user_time", "audit_logs", "user_id, timestamp DESC", False),
    ("idx_audit_logs_action_time", "audit_logs", "action, timestamp DESC", False),
    
    ("idx_notifications_user_id", "notifications", "user_id", False),
    ("idx_notifications_is_read", "notifications", "is_read", False),
    ("idx_notifications_created_at", "notifications", "created_at", False),
    ("idx_notifications_user_read", "notifications", "user_id, is_read", False),
    
    ("idx_feedback_user_id", "feedback", "user_id", False),
    ("idx_feedback_status", "feedback", "status", False),
    ("idx_feedback_created_at", "feedback", "created_at", False),
    ("idx_feedback_type", "feedback", "feedback_type", False),
    
    ("idx_comments_task_id", "comments", "task_id", False),
    ("idx_comments_user_id", "comments", "user_id", False),
    ("idx_comments_created_at", "comments", "created_at", False),
    
    ("idx_teams_owner_id", "teams", "owner_id", False),
    ("idx_teams_created_at", "teams", "created_at", False),
    
    ("idx_team_members_team_id", "team_members", "team_id", False),
    ("idx_team_members_user_id", "team_members", "user_id", False),
    ("idx_team_members_unique", "team_members", "team_id, user_id", True),
    
    ("idx_announcements_is_active", "announcements", "is_active", False),
    ("idx_announcements_created_at", "announcements", "created_at", False),
    ("idx_announcements_type", "announcements", "type", False),
    
    ("idx_user_locations_user_id", "user_locations", "user_id", False),
    ("idx_user_locations_location_id", "user_locations", "location_id", False),
    
    ("idx_settings_key", "settings", "key", True),
    ("idx_settings_category", "settings", "category", False),
    
    ("idx_knowledge_base_category", "knowledge_base", "category", False),
    ("idx_knowledge_base_is_active", "knowledge_base", "is_active", False),
    ("idx_knowledge_base_created_at", "knowledge_base", "created_at", False),
    
    ("idx_ab_tests_name", "ab_tests", "name", True),
    ("idx_ab_tests_is_active", "ab_tests", "is_active", False),
    
    ("idx_ab_test_events_test_id", "ab_test_events", "test_id", False),
    ("idx_ab_test_events_user_id", "ab_test_events", "user_id", False),
    ("idx_ab_test_events_variant", "ab_test_events", "variant", False),
    ("idx_ab_test_events_created_at", "ab_test_events", "created_at", False),
    
    ("idx_alerts_type", "alerts", "type", False),
    ("idx_alerts_severity", "alerts", "severity", False),
    ("idx_alerts_is_resolved", "alerts", "is_resolved", False),
    ("idx_alerts_created_at", "alerts", "created_at", False),
    
    ("idx_mascot_stats_date", "mascot_stats", "date", False),
    ("idx_mascot_stats_emotion", "mascot_stats", "emotion", False),
    
    ("idx_mascot_quotes_emotion", "mascot_quotes", "emotion", False),
    ("idx_mascot_quotes_is_active", "mascot_quotes", "is_active", False),
]

def analyze_table(db_path: str, table_name: str):
    """分析表统计信息"""
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    cursor.execute(f"SELECT COUNT(*) FROM {table_name}")
    count = cursor.fetchone()[0]
    
    cursor.execute(f"PRAGMA table_info({table_name})")
    columns = cursor.fetchall()
    
    cursor.execute(f"PRAGMA index_list({table_name})")
    indexes = cursor.fetchall()
    
    conn.close()
    
    return {
        "table": table_name,
        "row_count": count,
        "columns": len(columns),
        "indexes": len(indexes),
    }

def check_index_exists(cursor, index_name: str) -> bool:
    """检查索引是否已存在"""
    cursor.execute("SELECT name FROM sqlite_master WHERE type='index' AND name=?", (index_name,))
    return cursor.fetchone() is not None

def create_index(db_path: str, index_name: str, table: str, columns: str, unique: bool) -> dict:
    """创建索引"""
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    result = {
        "index": index_name,
        "table": table,
        "columns": columns,
        "status": "skipped",
        "time_ms": 0,
    }
    
    if check_index_exists(cursor, index_name):
        conn.close()
        return result
    
    unique_str = "UNIQUE" if unique else ""
    sql = f"CREATE {unique_str} INDEX IF NOT EXISTS {index_name} ON {table} ({columns})"
    
    try:
        start_time = time.time()
        cursor.execute(sql)
        conn.commit()
        elapsed = (time.time() - start_time) * 1000
        
        result["status"] = "created"
        result["time_ms"] = round(elapsed, 2)
        print(f"✅ Created index: {index_name} on {table}({columns}) [{elapsed:.2f}ms]")
    except Exception as e:
        result["status"] = "error"
        result["error"] = str(e)
        print(f"❌ Failed to create index {index_name}: {e}")
    finally:
        conn.close()
    
    return result

def run_migration(db_path: str = "data/property-ai.db"):
    """执行索引迁移"""
    print("=" * 60)
    print("数据库索引优化迁移")
    print(f"数据库路径: {db_path}")
    print(f"开始时间: {datetime.now().isoformat()}")
    print("=" * 60)
    
    if not os.path.exists(db_path):
        print(f"❌ 数据库文件不存在: {db_path}")
        return
    
    results = {
        "created": 0,
        "skipped": 0,
        "errors": 0,
        "total_time_ms": 0,
        "details": [],
    }
    
    for index_name, table, columns, unique in INDEXES:
        result = create_index(db_path, index_name, table, columns, unique)
        results["details"].append(result)
        
        if result["status"] == "created":
            results["created"] += 1
            results["total_time_ms"] += result.get("time_ms", 0)
        elif result["status"] == "skipped":
            results["skipped"] += 1
        else:
            results["errors"] += 1
    
    print("\n" + "=" * 60)
    print("迁移完成!")
    print(f"创建索引: {results['created']}")
    print(f"跳过索引: {results['skipped']}")
    print(f"错误数量: {results['errors']}")
    print(f"总耗时: {results['total_time_ms']:.2f}ms")
    print("=" * 60)
    
    return results

def analyze_query_performance(db_path: str, query: str) -> dict:
    """分析查询性能"""
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    try:
        cursor.execute(f"EXPLAIN QUERY PLAN {query}")
        plan = cursor.fetchall()
        
        start_time = time.time()
        cursor.execute(query)
        results = cursor.fetchall()
        elapsed = (time.time() - start_time) * 1000
        
        return {
            "query": query[:100] + "..." if len(query) > 100 else query,
            "plan": plan,
            "rows": len(results),
            "time_ms": round(elapsed, 2),
        }
    except Exception as e:
        return {
            "query": query,
            "error": str(e),
        }
    finally:
        conn.close()

def vacuum_database(db_path: str):
    """执行VACUUM优化数据库"""
    print("正在执行VACUUM优化...")
    
    original_size = os.path.getsize(db_path)
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute("VACUUM")
    conn.commit()
    conn.close()
    
    new_size = os.path.getsize(db_path)
    saved = original_size - new_size
    saved_percent = (saved / original_size) * 100 if original_size > 0 else 0
    
    print(f"✅ VACUUM完成")
    print(f"   原始大小: {original_size / 1024 / 1024:.2f} MB")
    print(f"   优化后: {new_size / 1024 / 1024:.2f} MB")
    print(f"   节省空间: {saved / 1024 / 1024:.2f} MB ({saved_percent:.1f}%)")

if __name__ == "__main__":
    import sys
    
    db_path = sys.argv[1] if len(sys.argv) > 1 else "data/property-ai.db"
    
    run_migration(db_path)
    
    print("\n")
    vacuum_database(db_path)
