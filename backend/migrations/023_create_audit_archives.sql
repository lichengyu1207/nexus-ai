-- 审计日志归档表
CREATE TABLE IF NOT EXISTS audit_archives (
    id TEXT PRIMARY KEY,
    filename TEXT NOT NULL,
    file_path TEXT NOT NULL,
    file_size INTEGER NOT NULL DEFAULT 0,
    compressed_size INTEGER NOT NULL DEFAULT 0,
    start_timestamp TIMESTAMP NOT NULL,
    end_timestamp TIMESTAMP NOT NULL,
    log_count INTEGER NOT NULL DEFAULT 0,
    first_log_id TEXT,
    last_log_id TEXT,
    first_hash TEXT,
    last_hash TEXT,
    checksum TEXT,
    storage_type TEXT NOT NULL DEFAULT 'local',
    storage_location TEXT,
    retention_days INTEGER NOT NULL DEFAULT 180,
    archived_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    archived_by TEXT,
    status TEXT NOT NULL DEFAULT 'completed',
    error_message TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_audit_archives_start ON audit_archives(start_timestamp DESC);
CREATE INDEX IF NOT EXISTS idx_audit_archives_end ON audit_archives(end_timestamp DESC);
CREATE INDEX IF NOT EXISTS idx_audit_archives_status ON audit_archives(status);
CREATE INDEX IF NOT EXISTS idx_audit_archives_archived_at ON audit_archives(archived_at DESC);

-- 归档配置表
CREATE TABLE IF NOT EXISTS audit_archive_config (
    id TEXT PRIMARY KEY DEFAULT 'default',
    enabled INTEGER NOT NULL DEFAULT 1,
    retention_days INTEGER NOT NULL DEFAULT 180,
    archive_after_days INTEGER NOT NULL DEFAULT 150,
    schedule_cron TEXT DEFAULT '0 2 * * 0',
    storage_type TEXT NOT NULL DEFAULT 'local',
    storage_path TEXT DEFAULT './archives/audit',
    compress_format TEXT DEFAULT 'gzip',
    max_archive_size_mb INTEGER DEFAULT 100,
    last_run_at TIMESTAMP,
    next_run_at TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_by TEXT
);

INSERT OR IGNORE INTO audit_archive_config (id, enabled, retention_days, archive_after_days)
VALUES ('default', 1, 180, 150);

-- 归档恢复记录表
CREATE TABLE IF NOT EXISTS audit_archive_restores (
    id TEXT PRIMARY KEY,
    archive_id TEXT NOT NULL,
    restored_by TEXT,
    restored_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    log_count INTEGER DEFAULT 0,
    status TEXT NOT NULL DEFAULT 'completed',
    error_message TEXT,
    FOREIGN KEY (archive_id) REFERENCES audit_archives(id)
);

CREATE INDEX IF NOT EXISTS idx_archive_restores_archive ON audit_archive_restores(archive_id);
CREATE INDEX IF NOT EXISTS idx_archive_restores_time ON audit_archive_restores(restored_at DESC);
