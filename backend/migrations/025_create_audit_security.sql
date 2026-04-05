-- 审计日志备份表
CREATE TABLE IF NOT EXISTS audit_backups (
    id TEXT PRIMARY KEY,
    filename TEXT NOT NULL,
    file_path TEXT NOT NULL,
    file_size INTEGER NOT NULL DEFAULT 0,
    log_count INTEGER NOT NULL DEFAULT 0,
    start_timestamp TIMESTAMP,
    end_timestamp TIMESTAMP,
    encrypted INTEGER NOT NULL DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_audit_backups_created ON audit_backups(created_at DESC);

-- 审计日志访问记录表
CREATE TABLE IF NOT EXISTS audit_access_logs (
    id TEXT PRIMARY KEY,
    user_id TEXT NOT NULL,
    username TEXT,
    ip_address TEXT,
    user_agent TEXT,
    action TEXT NOT NULL,
    resource_type TEXT,
    resource_id TEXT,
    details TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_audit_access_logs_user ON audit_access_logs(user_id);
CREATE INDEX IF NOT EXISTS idx_audit_access_logs_time ON audit_access_logs(created_at DESC);
