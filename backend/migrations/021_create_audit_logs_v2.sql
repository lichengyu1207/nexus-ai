-- 合规审计系统迁移
-- 创建审计日志表
CREATE TABLE IF NOT EXISTS audit_logs (
    id TEXT PRIMARY KEY,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    user_id TEXT,
    username TEXT,
    user_role TEXT,
    ip_address TEXT,
    user_agent TEXT,
    action_type TEXT NOT NULL,
    resource_type TEXT,
    resource_id TEXT,
    old_value TEXT,
    new_value TEXT,
    status TEXT DEFAULT 'success',
    error_message TEXT,
    hash TEXT,
    prev_hash TEXT,
    signature TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 创建索引
CREATE INDEX IF NOT EXISTS idx_audit_logs_timestamp ON audit_logs(timestamp DESC);
CREATE INDEX IF NOT EXISTS idx_audit_logs_user_id ON audit_logs(user_id);
CREATE INDEX IF NOT EXISTS idx_audit_logs_action_type ON audit_logs(action_type);
CREATE INDEX IF NOT EXISTS idx_audit_logs_resource_type ON audit_logs(resource_type);
CREATE INDEX IF NOT EXISTS idx_audit_logs_status ON audit_logs(status);
CREATE INDEX IF NOT EXISTS idx_audit_logs_resource_id ON audit_logs(resource_id);

-- 创建审计日志归档表
CREATE TABLE IF NOT EXISTS audit_logs_archive (
    id TEXT PRIMARY KEY,
    timestamp TIMESTAMP,
    user_id TEXT,
    username TEXT,
    user_role TEXT,
    ip_address TEXT,
    user_agent TEXT,
    action_type TEXT NOT NULL,
    resource_type TEXT,
    resource_id TEXT,
    old_value TEXT,
    new_value TEXT,
    status TEXT,
    error_message TEXT,
    hash TEXT,
    prev_hash TEXT,
    signature TEXT,
    archived_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    archive_batch TEXT
);

-- 创建审计统计表
CREATE TABLE IF NOT EXISTS audit_stats (
    id TEXT PRIMARY KEY,
    date TEXT NOT NULL UNIQUE,
    total_logs INTEGER DEFAULT 0,
    login_count INTEGER DEFAULT 0,
    logout_count INTEGER DEFAULT 0,
    task_create_count INTEGER DEFAULT 0,
    task_delete_count INTEGER DEFAULT 0,
    report_export_count INTEGER DEFAULT 0,
    admin_action_count INTEGER DEFAULT 0,
    failure_count INTEGER DEFAULT 0,
    unique_users INTEGER DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 创建异常行为记录表
CREATE TABLE IF NOT EXISTS audit_anomalies (
    id TEXT PRIMARY KEY,
    user_id TEXT,
    username TEXT,
    anomaly_type TEXT NOT NULL,
    severity TEXT DEFAULT 'medium',
    description TEXT,
    related_logs TEXT,
    is_resolved BOOLEAN DEFAULT FALSE,
    resolved_by TEXT,
    resolved_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 创建索引
CREATE INDEX IF NOT EXISTS idx_audit_anomalies_user ON audit_anomalies(user_id);
CREATE INDEX IF NOT EXISTS idx_audit_anomalies_type ON audit_anomalies(anomaly_type);
CREATE INDEX IF NOT EXISTS idx_audit_anomalies_resolved ON audit_anomalies(is_resolved);
CREATE INDEX IF NOT EXISTS idx_audit_anomalies_created ON audit_anomalies(created_at DESC);
