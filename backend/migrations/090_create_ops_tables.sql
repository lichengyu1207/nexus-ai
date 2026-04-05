-- 生产部署与智能运维系统数据库表 (PostgreSQL)
-- Production Deployment and Intelligent Ops System Tables

-- 任务执行日志表
CREATE TABLE IF NOT EXISTS task_execution_log (
    id SERIAL PRIMARY KEY,
    task_id VARCHAR(50) NOT NULL UNIQUE,
    task_name VARCHAR(200) NOT NULL,
    status VARCHAR(20) NOT NULL DEFAULT 'pending',
    
    started_at TIMESTAMP,
    completed_at TIMESTAMP,
    duration_seconds REAL,
    
    args JSONB,
    kwargs JSONB,
    result JSONB,
    
    error_message TEXT,
    error_traceback TEXT,
    
    retry_count INTEGER DEFAULT 0,
    worker_name VARCHAR(100),
    
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_task_execution_status ON task_execution_log(status);
CREATE INDEX IF NOT EXISTS idx_task_execution_name ON task_execution_log(task_name);
CREATE INDEX IF NOT EXISTS idx_task_execution_created ON task_execution_log(created_at);

-- 训练会话表
CREATE TABLE IF NOT EXISTS training_sessions (
    id SERIAL PRIMARY KEY,
    session_id VARCHAR(50) NOT NULL UNIQUE,
    
    start_time TIMESTAMP NOT NULL,
    end_time TIMESTAMP,
    num_episodes INTEGER DEFAULT 0,
    
    best_defender_id VARCHAR(50),
    best_win_rate REAL,
    model_path TEXT,
    
    status VARCHAR(20) DEFAULT 'running',
    error_message TEXT,
    
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_training_sessions_status ON training_sessions(status);

-- 模型版本表
CREATE TABLE IF NOT EXISTS model_versions (
    id SERIAL PRIMARY KEY,
    model_type VARCHAR(50) NOT NULL,
    version INTEGER NOT NULL,
    path TEXT NOT NULL,
    
    win_rate REAL,
    tpr REAL,
    fpr REAL,
    
    is_active BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    UNIQUE(model_type, version)
);

CREATE INDEX IF NOT EXISTS idx_model_versions_active ON model_versions(is_active);

-- 生产模型历史表
CREATE TABLE IF NOT EXISTS production_model_history (
    id SERIAL PRIMARY KEY,
    model_path TEXT NOT NULL,
    deployed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    deployed_by VARCHAR(100),
    
    previous_model_path TEXT,
    rollback_available BOOLEAN DEFAULT TRUE
);

-- 防御统计小时表
CREATE TABLE IF NOT EXISTS defense_stats_hourly (
    id SERIAL PRIMARY KEY,
    stat_id VARCHAR(50) NOT NULL UNIQUE,
    
    stat_date DATE NOT NULL,
    stat_hour TIMESTAMP NOT NULL,
    
    total_attacks INTEGER DEFAULT 0,
    blocked_attacks INTEGER DEFAULT 0,
    missed_attacks INTEGER DEFAULT 0,
    false_positives INTEGER DEFAULT 0,
    normal_requests INTEGER DEFAULT 0,
    service_down_events INTEGER DEFAULT 0,
    
    attack_type_distribution JSONB,
    attack_success_rate REAL,
    avg_response_time_ms REAL,
    
    high_latency_events INTEGER DEFAULT 0,
    critical_latency_events INTEGER DEFAULT 0,
    service_unavailable_events INTEGER DEFAULT 0,
    
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    UNIQUE(stat_date, stat_hour)
);

CREATE INDEX IF NOT EXISTS idx_defense_stats_hourly_date ON defense_stats_hourly(stat_date);

-- 防御统计日表
CREATE TABLE IF NOT EXISTS defense_stats_daily (
    id SERIAL PRIMARY KEY,
    stat_date DATE NOT NULL UNIQUE,
    
    total_episodes INTEGER DEFAULT 0,
    total_games INTEGER DEFAULT 0,
    
    total_attacks INTEGER DEFAULT 0,
    blocked_attacks INTEGER DEFAULT 0,
    missed_attacks INTEGER DEFAULT 0,
    false_positives INTEGER DEFAULT 0,
    normal_requests INTEGER DEFAULT 0,
    service_down_events INTEGER DEFAULT 0,
    
    avg_attacker_reward REAL,
    avg_defender_reward REAL,
    
    best_attacker_id VARCHAR(50),
    best_attacker_win_rate REAL,
    
    best_defender_tpr REAL,
    best_defender_fpr REAL,
    best_defender_version INTEGER,
    
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_defense_stats_daily_date ON defense_stats_daily(stat_date);

-- 攻击类型分布表
CREATE TABLE IF NOT EXISTS attack_type_distribution (
    id SERIAL PRIMARY KEY,
    distribution_id VARCHAR(50) NOT NULL UNIQUE,
    
    stat_date DATE NOT NULL,
    stat_hour TIMESTAMP,
    
    attack_type VARCHAR(50) NOT NULL,
    attack_counts INTEGER DEFAULT 0,
    percentage REAL DEFAULT 0.0,
    
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_attack_type_distribution_date ON attack_type_distribution(stat_date);
CREATE INDEX IF NOT EXISTS idx_attack_type_distribution_type ON attack_type_distribution(attack_type);

-- 攻击趋势日表
CREATE TABLE IF NOT EXISTS attack_trend_daily (
    id SERIAL PRIMARY KEY,
    stat_date DATE NOT NULL UNIQUE,
    
    attack_counts JSONB,
    attack_type_distribution JSONB,
    
    total_attacks INTEGER DEFAULT 0,
    unique_attackers INTEGER DEFAULT 0,
    
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 攻击趋势周表
CREATE TABLE IF NOT EXISTS attack_trend_weekly (
    id SERIAL PRIMARY KEY,
    week_start DATE NOT NULL,
    week_end DATE NOT NULL,
    
    attack_counts JSONB,
    attack_type_distribution JSONB,
    
    total_attacks INTEGER DEFAULT 0,
    avg_daily_attacks REAL,
    
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    UNIQUE(week_start, week_end)
);

-- 攻击趋势月表
CREATE TABLE IF NOT EXISTS attack_trend_monthly (
    id SERIAL PRIMARY KEY,
    month_start DATE NOT NULL,
    month_end DATE NOT NULL,
    
    attack_counts JSONB,
    attack_type_distribution JSONB,
    
    total_attacks INTEGER DEFAULT 0,
    avg_daily_attacks REAL,
    
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    UNIQUE(month_start, month_end)
);

-- 响应时间统计日表
CREATE TABLE IF NOT EXISTS response_time_daily (
    id SERIAL PRIMARY KEY,
    stat_date DATE NOT NULL UNIQUE,
    
    avg_response_time_ms REAL,
    p50_response_time_ms REAL,
    p95_response_time_ms REAL,
    p99_response_time_ms REAL,
    max_response_time_ms REAL,
    
    total_requests INTEGER DEFAULT 0,
    
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 服务可用性日表
CREATE TABLE IF NOT EXISTS service_availability_daily (
    id SERIAL PRIMARY KEY,
    stat_date DATE NOT NULL UNIQUE,
    
    availability_rate REAL DEFAULT 1.0,
    downtime_seconds INTEGER DEFAULT 0,
    incident_count INTEGER DEFAULT 0,
    
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 训练进度日表
CREATE TABLE IF NOT EXISTS training_progress_daily (
    id SERIAL PRIMARY KEY,
    stat_date DATE NOT NULL UNIQUE,
    
    total_episodes INTEGER DEFAULT 0,
    best_win_rate REAL,
    avg_reward REAL,
    model_version INTEGER,
    
    training_time_seconds INTEGER DEFAULT 0,
    
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 资源使用日表
CREATE TABLE IF NOT EXISTS resource_usage_daily (
    id SERIAL PRIMARY KEY,
    stat_date DATE NOT NULL UNIQUE,
    
    avg_cpu_percent REAL,
    max_cpu_percent REAL,
    avg_memory_percent REAL,
    max_memory_percent REAL,
    disk_usage_percent REAL,
    
    network_in_mbps REAL,
    network_out_mbps REAL,
    
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 模型性能日表
CREATE TABLE IF NOT EXISTS model_performance_daily (
    id SERIAL PRIMARY KEY,
    stat_date DATE NOT NULL UNIQUE,
    
    model_version INTEGER,
    tpr REAL,
    fpr REAL,
    f1_score REAL,
    avg_latency_ms REAL,
    
    total_inferences INTEGER DEFAULT 0,
    
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 防御统计小时汇总表
CREATE TABLE IF NOT EXISTS defense_stats_hourly_summary (
    id SERIAL PRIMARY KEY,
    stat_hour TIMESTAMP NOT NULL UNIQUE,
    
    total_attacks INTEGER DEFAULT 0,
    blocked_attacks INTEGER DEFAULT 0,
    missed_attacks INTEGER DEFAULT 0,
    false_positives INTEGER DEFAULT 0,
    normal_requests INTEGER DEFAULT 0,
    service_down_events INTEGER DEFAULT 0,
    
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 系统告警表
CREATE TABLE IF NOT EXISTS system_alerts (
    id SERIAL PRIMARY KEY,
    alert_type VARCHAR(50) NOT NULL,
    severity VARCHAR(20) NOT NULL,
    
    title VARCHAR(200) NOT NULL,
    message TEXT,
    
    source VARCHAR(100),
    metric_name VARCHAR(100),
    metric_value REAL,
    threshold REAL,
    
    is_resolved BOOLEAN DEFAULT FALSE,
    resolved_at TIMESTAMP,
    resolved_by VARCHAR(100),
    
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_system_alerts_resolved ON system_alerts(is_resolved);
CREATE INDEX IF NOT EXISTS idx_system_alerts_severity ON system_alerts(severity);
CREATE INDEX IF NOT EXISTS idx_system_alerts_created ON system_alerts(created_at);

-- 备份记录表
CREATE TABLE IF NOT EXISTS backup_records (
    id SERIAL PRIMARY KEY,
    backup_id VARCHAR(50) NOT NULL UNIQUE,
    
    backup_name VARCHAR(200) NOT NULL,
    backup_type VARCHAR(50) NOT NULL,
    backup_path TEXT NOT NULL,
    
    size_bytes BIGINT,
    duration_seconds REAL,
    
    includes_database BOOLEAN DEFAULT TRUE,
    includes_logs BOOLEAN DEFAULT FALSE,
    includes_config BOOLEAN DEFAULT FALSE,
    is_compressed BOOLEAN DEFAULT FALSE,
    
    status VARCHAR(20) DEFAULT 'pending',
    error_message TEXT,
    
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_backup_records_status ON backup_records(status);
CREATE INDEX IF NOT EXISTS idx_backup_records_created ON backup_records(created_at);

-- 迁移记录表
CREATE TABLE IF NOT EXISTS migration_records (
    id SERIAL PRIMARY KEY,
    migration_id VARCHAR(50) NOT NULL UNIQUE,
    
    source_type VARCHAR(50) NOT NULL,
    target_type VARCHAR(50) NOT NULL,
    
    tables_created INTEGER DEFAULT 0,
    tables_migrated INTEGER DEFAULT 0,
    rows_migrated INTEGER DEFAULT 0,
    indexes_created INTEGER DEFAULT 0,
    
    duration_seconds REAL,
    
    status VARCHAR(20) DEFAULT 'pending',
    errors JSONB,
    
    rollback_available BOOLEAN DEFAULT FALSE,
    
    started_at TIMESTAMP,
    completed_at TIMESTAMP,
    
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 系统配置表
CREATE TABLE IF NOT EXISTS system_config (
    id SERIAL PRIMARY KEY,
    config_key VARCHAR(100) NOT NULL UNIQUE,
    config_value JSONB NOT NULL,
    
    description TEXT,
    is_active BOOLEAN DEFAULT TRUE,
    
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 插入默认系统配置
INSERT INTO system_config (config_key, config_value, description)
SELECT 'backup_config', '{"retention_days": 30, "schedule_hour": 3, "compress": true}', '备份配置'
WHERE NOT EXISTS (SELECT 1 FROM system_config WHERE config_key = 'backup_config');

INSERT INTO system_config (config_key, config_value, description)
SELECT 'training_config', '{"episodes_per_hour": 100, "update_interval": 10}', '训练配置'
WHERE NOT EXISTS (SELECT 1 FROM system_config WHERE config_key = 'training_config');

INSERT INTO system_config (config_key, config_value, description)
SELECT 'alert_thresholds', '{"tpr_min": 0.98, "fpr_max": 0.01, "latency_max_ms": 5.0}', '告警阈值配置'
WHERE NOT EXISTS (SELECT 1 FROM system_config WHERE config_key = 'alert_thresholds');

-- 创建更新时间触发器
DROP TRIGGER IF EXISTS update_system_config_updated_at ON system_config;
CREATE TRIGGER update_system_config_updated_at
    BEFORE UPDATE ON system_config
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

-- 创建物化视图用于快速查询
CREATE MATERIALIZED VIEW IF NOT EXISTS defense_summary_view AS
SELECT 
    stat_date,
    SUM(total_attacks) as total_attacks,
    SUM(blocked_attacks) as blocked_attacks,
    SUM(missed_attacks) as missed_attacks,
    SUM(false_positives) as false_positives,
    AVG(best_defender_tpr) as avg_tpr,
    AVG(best_defender_fpr) as avg_fpr
FROM defense_stats_daily
GROUP BY stat_date
ORDER BY stat_date DESC;

-- 创建刷新物化视图的索引
CREATE UNIQUE INDEX IF NOT EXISTS idx_defense_summary_view_date ON defense_summary_view(stat_date);
