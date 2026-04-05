"""
数据库迁移：添加性能指标表
"""
import sqlite3
import os

MIGRATION_SQL = """
-- 性能指标表
CREATE TABLE IF NOT EXISTS performance_metrics (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    metric_name TEXT NOT NULL,
    value REAL NOT NULL,
    rating TEXT NOT NULL,
    delta REAL,
    metric_id TEXT,
    navigation_type TEXT,
    timestamp DATETIME NOT NULL,
    url TEXT,
    user_agent TEXT,
    connection_type TEXT,
    memory_usage REAL,
    session_id TEXT,
    user_id TEXT,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- 索引
CREATE INDEX IF NOT EXISTS idx_perf_metrics_name ON performance_metrics(metric_name);
CREATE INDEX IF NOT EXISTS idx_perf_metrics_timestamp ON performance_metrics(timestamp);
CREATE INDEX IF NOT EXISTS idx_perf_metrics_session ON performance_metrics(session_id);
CREATE INDEX IF NOT EXISTS idx_perf_metrics_rating ON performance_metrics(rating);
CREATE INDEX IF NOT EXISTS idx_perf_metrics_name_timestamp ON performance_metrics(metric_name, timestamp);

-- 慢查询日志表
CREATE TABLE IF NOT EXISTS slow_queries (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    endpoint TEXT NOT NULL,
    method TEXT NOT NULL,
    duration_ms REAL NOT NULL,
    request_id TEXT,
    user_id TEXT,
    params TEXT,
    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_slow_queries_endpoint ON slow_queries(endpoint);
CREATE INDEX IF NOT EXISTS idx_slow_queries_timestamp ON slow_queries(timestamp);

-- API性能统计表
CREATE TABLE IF NOT EXISTS api_performance (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    endpoint TEXT NOT NULL,
    method TEXT NOT NULL,
    total_requests INTEGER DEFAULT 0,
    total_duration_ms REAL DEFAULT 0,
    avg_duration_ms REAL DEFAULT 0,
    min_duration_ms REAL,
    max_duration_ms REAL,
    error_count INTEGER DEFAULT 0,
    date DATE NOT NULL,
    UNIQUE(endpoint, method, date)
);

CREATE INDEX IF NOT EXISTS idx_api_perf_endpoint ON api_performance(endpoint);
CREATE INDEX IF NOT EXISTS idx_api_perf_date ON api_performance(date);
"""


def run_migration(db_path: str = "data/property-ai.db"):
    """执行迁移"""
    os.makedirs(os.path.dirname(db_path), exist_ok=True)
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    try:
        cursor.executescript(MIGRATION_SQL)
        conn.commit()
        print("✅ Performance metrics migration completed successfully")
    except Exception as e:
        conn.rollback()
        print(f"❌ Migration failed: {e}")
        raise
    finally:
        conn.close()


if __name__ == "__main__":
    run_migration()
