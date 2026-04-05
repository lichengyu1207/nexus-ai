-- 异常告警表
CREATE TABLE IF NOT EXISTS anomaly_alerts (
    id TEXT PRIMARY KEY,
    alert_type TEXT NOT NULL,
    severity TEXT NOT NULL DEFAULT 'medium',
    title TEXT NOT NULL,
    description TEXT,
    user_id TEXT,
    username TEXT,
    ip_address TEXT,
    user_agent TEXT,
    rule_name TEXT NOT NULL,
    rule_config TEXT,
    matched_logs TEXT,
    matched_count INTEGER DEFAULT 0,
    time_window_start TIMESTAMP,
    time_window_end TIMESTAMP,
    status TEXT NOT NULL DEFAULT 'open',
    acknowledged_by TEXT,
    acknowledged_at TIMESTAMP,
    resolved_by TEXT,
    resolved_at TIMESTAMP,
    resolution_note TEXT,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_anomaly_alerts_type ON anomaly_alerts(alert_type);
CREATE INDEX IF NOT EXISTS idx_anomaly_alerts_severity ON anomaly_alerts(severity);
CREATE INDEX IF NOT EXISTS idx_anomaly_alerts_status ON anomaly_alerts(status);
CREATE INDEX IF NOT EXISTS idx_anomaly_alerts_user ON anomaly_alerts(user_id);
CREATE INDEX IF NOT EXISTS idx_anomaly_alerts_ip ON anomaly_alerts(ip_address);
CREATE INDEX IF NOT EXISTS idx_anomaly_alerts_created ON anomaly_alerts(created_at DESC);

-- 异常检测规则配置表
CREATE TABLE IF NOT EXISTS anomaly_rules (
    id TEXT PRIMARY KEY,
    name TEXT NOT NULL UNIQUE,
    display_name TEXT NOT NULL,
    description TEXT,
    category TEXT NOT NULL,
    severity TEXT NOT NULL DEFAULT 'medium',
    enabled INTEGER NOT NULL DEFAULT 1,
    config TEXT NOT NULL,
    cooldown_minutes INTEGER DEFAULT 60,
    notify_admins INTEGER DEFAULT 1,
    last_triggered_at TIMESTAMP,
    trigger_count INTEGER DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_anomaly_rules_category ON anomaly_rules(category);
CREATE INDEX IF NOT EXISTS idx_anomaly_rules_enabled ON anomaly_rules(enabled);

-- 插入默认规则
INSERT OR IGNORE INTO anomaly_rules (id, name, display_name, description, category, severity, config) VALUES
('brute_force_login', 'brute_force_login', '暴力破解登录', '短时间内多次登录失败，可能存在暴力破解攻击', 'security', 'high', '{"action_type": "LOGIN_FAILED", "time_window_minutes": 5, "threshold": 5, "group_by": "ip_address"}'),
('bulk_delete', 'bulk_delete', '批量删除操作', '短时间内大量删除操作，可能存在恶意删除风险', 'data_loss', 'high', '{"action_type": "TASK_DELETE,REPORT_DELETE", "time_window_minutes": 10, "threshold": 10, "group_by": "user_id"}'),
('unusual_time_access', 'unusual_time_access', '非常规时间访问', '在非常规时间段（如凌晨）大量操作', 'suspicious', 'medium', '{"start_hour": 0, "end_hour": 6, "threshold": 20, "time_window_minutes": 60}'),
('permission_escalation', 'permission_escalation', '权限提升尝试', '普通用户尝试访问管理员API或执行特权操作', 'security', 'critical', '{"action_types": ["ADMIN_USER_CREATE", "ADMIN_USER_UPDATE", "ADMIN_USER_DELETE", "ADMIN_SETTING_CHANGE"], "check_role": true}'),
('mass_export', 'mass_export', '批量数据导出', '短时间内大量数据导出操作', 'data_exfiltration', 'high', '{"action_type": "REPORT_EXPORT,DATA_EXPORT", "time_window_minutes": 30, "threshold": 20, "group_by": "user_id"}'),
('multiple_ip_login', 'multiple_ip_login', '多IP登录', '同一账号在短时间内从不同IP登录', 'account_compromise', 'high', '{"action_type": "LOGIN", "time_window_minutes": 30, "ip_threshold": 3, "group_by": "user_id"}'),
('failed_permission_access', 'failed_permission_access', '权限访问失败', '频繁尝试访问无权限资源', 'security', 'medium', '{"status": "failure", "time_window_minutes": 10, "threshold": 10, "group_by": "user_id"}'),
('suspicious_api_pattern', 'suspicious_api_pattern', '可疑API调用模式', '异常的API调用模式，可能是自动化攻击', 'security', 'medium', '{"request_threshold": 100, "time_window_minutes": 1, "unique_paths_threshold": 5}');

-- 告警统计表
CREATE TABLE IF NOT EXISTS anomaly_alert_stats (
    id TEXT PRIMARY KEY,
    date TEXT NOT NULL UNIQUE,
    total_alerts INTEGER DEFAULT 0,
    open_alerts INTEGER DEFAULT 0,
    acknowledged_alerts INTEGER DEFAULT 0,
    resolved_alerts INTEGER DEFAULT 0,
    by_severity TEXT,
    by_type TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_anomaly_alert_stats_date ON anomaly_alert_stats(date);
