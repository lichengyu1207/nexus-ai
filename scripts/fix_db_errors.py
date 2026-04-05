"""
修复数据库缺失的表和列
"""
import sqlite3

DB_PATH = 'c:/Users/Administrator/Desktop/測試2/data/property-ai.db'
conn = sqlite3.connect(DB_PATH)
cursor = conn.cursor()

print("=" * 60)
print("数据库修复脚本")
print("=" * 60)

# 1. 创建audit_signature_batches表
print("\n1. 检查audit_signature_batches表...")
try:
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS audit_signature_batches (
            id TEXT PRIMARY KEY,
            start_log_id TEXT,
            end_log_id TEXT,
            batch_hash TEXT,
            signature TEXT,
            start_timestamp DATETIME,
            end_timestamp DATETIME,
            log_count INTEGER DEFAULT 0,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    """)
    print("   [OK] audit_signature_batches表已创建")
except Exception as e:
    print(f"   [WARN] {e}")

# 2. 添加archived_at列到audit_logs表
print("\n2. 检查audit_logs表的archived_at列...")
try:
    cursor.execute("PRAGMA table_info(audit_logs)")
    columns = [col[1] for col in cursor.fetchall()]
    if 'archived_at' not in columns:
        cursor.execute("ALTER TABLE audit_logs ADD COLUMN archived_at DATETIME")
        print("   [OK] archived_at列已添加")
    else:
        print("   [OK] archived_at列已存在")
except Exception as e:
    print(f"   [WARN] {e}")

# 3. 检查其他可能缺失的审计相关表
print("\n3. 检查其他审计相关表...")

tables_to_check = [
    ("audit_archives", """
        CREATE TABLE IF NOT EXISTS audit_archives (
            id TEXT PRIMARY KEY,
            start_date DATE NOT NULL,
            end_date DATE NOT NULL,
            log_count INTEGER DEFAULT 0,
            file_path TEXT,
            file_size_bytes INTEGER DEFAULT 0,
            checksum TEXT,
            status TEXT DEFAULT 'completed',
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    """),
    ("audit_archive_config", """
        CREATE TABLE IF NOT EXISTS audit_archive_config (
            id TEXT PRIMARY KEY,
            enabled INTEGER DEFAULT 1,
            archive_after_days INTEGER DEFAULT 150,
            schedule_cron TEXT DEFAULT '0 2 * * 0',
            storage_type TEXT DEFAULT 'local',
            storage_path TEXT DEFAULT './archives/audit',
            compress_format TEXT DEFAULT 'gzip',
            max_archive_size_mb INTEGER DEFAULT 100,
            last_run_at DATETIME,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    """),
]

for table_name, create_sql in tables_to_check:
    try:
        cursor.execute(create_sql)
        print(f"   [OK] {table_name}表已创建/存在")
    except Exception as e:
        print(f"   [WARN] {table_name}: {e}")

# 4. 添加索引
print("\n4. 添加索引...")
indexes = [
    "CREATE INDEX IF NOT EXISTS idx_audit_signature_batches_created ON audit_signature_batches(created_at)",
    "CREATE INDEX IF NOT EXISTS idx_audit_archives_created ON audit_archives(created_at)",
    "CREATE INDEX IF NOT EXISTS idx_audit_logs_archived ON audit_logs(archived_at)",
]

for idx_sql in indexes:
    try:
        cursor.execute(idx_sql)
        print(f"   [OK] 索引已创建")
    except Exception as e:
        print(f"   [WARN] {e}")

# 5. 添加audit_archive_config缺失的列
print("\n5. 检查audit_archive_config表列...")
try:
    cursor.execute("PRAGMA table_info(audit_archive_config)")
    columns = [col[1] for col in cursor.fetchall()]
    
    missing_columns = [
        ("retention_days", "INTEGER DEFAULT 180"),
        ("updated_by", "TEXT"),
    ]
    
    for col_name, col_type in missing_columns:
        if col_name not in columns:
            cursor.execute(f"ALTER TABLE audit_archive_config ADD COLUMN {col_name} {col_type}")
            print(f"   [OK] {col_name}列已添加")
        else:
            print(f"   [OK] {col_name}列已存在")
except Exception as e:
    print(f"   [WARN] {e}")

# 6. 插入默认配置
print("\n6. 检查默认配置...")
try:
    cursor.execute("SELECT COUNT(*) FROM audit_archive_config WHERE id = 'default'")
    count = cursor.fetchone()[0]
    if count == 0:
        cursor.execute("""
            INSERT INTO audit_archive_config (id, enabled, retention_days, archive_after_days)
            VALUES ('default', 1, 180, 150)
        """)
        print("   [OK] 默认配置已插入")
    else:
        print("   [OK] 默认配置已存在")
except Exception as e:
    print(f"   [WARN] {e}")

conn.commit()
conn.close()

print("\n" + "=" * 60)
print("数据库修复完成!")
print("=" * 60)
