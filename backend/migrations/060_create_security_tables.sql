-- 自进化安全防护内核数据库表 (PostgreSQL)
-- Self-Evolving Security Protection Kernel Tables

-- 安全事件表
CREATE TABLE IF NOT EXISTS security_events (
    id SERIAL PRIMARY KEY,
    event_id VARCHAR(50) NOT NULL UNIQUE,
    
    event_type VARCHAR(30) NOT NULL,
    threat_level VARCHAR(20) NOT NULL,
    attack_type VARCHAR(30),
    
    source_ips JSONB DEFAULT '[]',
    target_urls JSONB DEFAULT '[]',
    
    feature_vector JSONB,
    feature_summary JSONB,
    
    confidence REAL DEFAULT 0.0,
    detected_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    resolved_at TIMESTAMP,
    
    status VARCHAR(20) DEFAULT 'detected',
    metadata JSONB
);

CREATE INDEX IF NOT EXISTS idx_security_events_type ON security_events(event_type);
CREATE INDEX IF NOT EXISTS idx_security_events_threat ON security_events(threat_level);
CREATE INDEX IF NOT EXISTS idx_security_events_detected ON security_events(detected_at);
CREATE INDEX IF NOT EXISTS idx_security_events_status ON security_events(status);

-- 安全决策表
CREATE TABLE IF NOT EXISTS security_decisions (
    id SERIAL PRIMARY KEY,
    decision_id VARCHAR(50) NOT NULL UNIQUE,
    event_id VARCHAR(50),
    
    action VARCHAR(30) NOT NULL,
    confidence REAL DEFAULT 0.0,
    
    target_ips JSONB DEFAULT '[]',
    target_devices JSONB DEFAULT '[]',
    rate_limit INTEGER DEFAULT 0,
    
    reason TEXT,
    similar_attacks JSONB DEFAULT '[]',
    
    model_confidence REAL DEFAULT 0.0,
    history_confidence REAL DEFAULT 0.0,
    
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    executed_at TIMESTAMP,
    execution_success BOOLEAN DEFAULT FALSE
);

CREATE INDEX IF NOT EXISTS idx_security_decisions_event ON security_decisions(event_id);
CREATE INDEX IF NOT EXISTS idx_security_decisions_action ON security_decisions(action);
CREATE INDEX IF NOT EXISTS idx_security_decisions_created ON security_decisions(created_at);

-- 执行记录表
CREATE TABLE IF NOT EXISTS security_execution_logs (
    id SERIAL PRIMARY KEY,
    record_id VARCHAR(50) NOT NULL UNIQUE,
    decision_id VARCHAR(50),
    
    action VARCHAR(30) NOT NULL,
    target VARCHAR(100) NOT NULL,
    duration INTEGER DEFAULT 0,
    
    success BOOLEAN DEFAULT FALSE,
    error TEXT,
    metadata JSONB,
    
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_security_execution_decision ON security_execution_logs(decision_id);
CREATE INDEX IF NOT EXISTS idx_security_execution_action ON security_execution_logs(action);
CREATE INDEX IF NOT EXISTS idx_security_execution_created ON security_execution_logs(created_at);

-- IP封禁表
CREATE TABLE IF NOT EXISTS security_ip_bans (
    id SERIAL PRIMARY KEY,
    ip VARCHAR(45) NOT NULL,
    
    ban_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    duration INTEGER NOT NULL,
    unban_time TIMESTAMP,
    
    reason TEXT,
    attack_type VARCHAR(30),
    
    is_active BOOLEAN DEFAULT TRUE,
    manual_unban BOOLEAN DEFAULT FALSE,
    
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    UNIQUE(ip, ban_time)
);

CREATE INDEX IF NOT EXISTS idx_security_ip_bans_ip ON security_ip_bans(ip);
CREATE INDEX IF NOT EXISTS idx_security_ip_bans_active ON security_ip_bans(is_active);
CREATE INDEX IF NOT EXISTS idx_security_ip_bans_time ON security_ip_bans(ban_time);

-- 强化学习经验表
CREATE TABLE IF NOT EXISTS security_rl_experiences (
    id SERIAL PRIMARY KEY,
    experience_id VARCHAR(50) NOT NULL UNIQUE,
    
    state JSONB NOT NULL,
    action INTEGER NOT NULL,
    reward REAL NOT NULL,
    next_state JSONB,
    done BOOLEAN DEFAULT FALSE,
    
    info JSONB,
    
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_security_rl_experiences_created ON security_rl_experiences(created_at);

-- 攻击模式表
CREATE TABLE IF NOT EXISTS security_attack_patterns (
    id SERIAL PRIMARY KEY,
    pattern_id VARCHAR(50) NOT NULL UNIQUE,
    
    attack_type VARCHAR(30) NOT NULL,
    feature_signature JSONB,
    
    common_ips JSONB DEFAULT '[]',
    common_urls JSONB DEFAULT '[]',
    
    typical_duration REAL,
    severity_range JSONB,
    
    occurrence_count INTEGER DEFAULT 1,
    last_seen TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_security_attack_patterns_type ON security_attack_patterns(attack_type);
CREATE INDEX IF NOT EXISTS idx_security_attack_patterns_seen ON security_attack_patterns(last_seen);

-- 攻击报告表
CREATE TABLE IF NOT EXISTS security_attack_reports (
    id SERIAL PRIMARY KEY,
    report_id VARCHAR(50) NOT NULL UNIQUE,
    
    attack_type VARCHAR(30) NOT NULL,
    start_time TIMESTAMP NOT NULL,
    end_time TIMESTAMP NOT NULL,
    duration REAL,
    
    source_ips JSONB DEFAULT '[]',
    target_urls JSONB DEFAULT '[]',
    
    feature_summary JSONB,
    actions_taken JSONB DEFAULT '[]',
    
    effectiveness_score REAL DEFAULT 0.0,
    damage_assessment JSONB,
    recommendations JSONB DEFAULT '[]',
    
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_security_attack_reports_type ON security_attack_reports(attack_type);
CREATE INDEX IF NOT EXISTS idx_security_attack_reports_created ON security_attack_reports(created_at);

-- 联邦学习聚合表
CREATE TABLE IF NOT EXISTS federated_aggregations (
    id SERIAL PRIMARY KEY,
    model_version INTEGER NOT NULL,
    
    aggregated_samples INTEGER DEFAULT 0,
    participating_nodes INTEGER DEFAULT 0,
    
    result JSONB,
    
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_federated_aggregations_version ON federated_aggregations(model_version);

-- 联邦学习节点表
CREATE TABLE IF NOT EXISTS federated_nodes (
    id SERIAL PRIMARY KEY,
    node_id VARCHAR(50) NOT NULL UNIQUE,
    
    registered_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_update TIMESTAMP,
    
    total_samples INTEGER DEFAULT 0,
    status VARCHAR(20) DEFAULT 'active',
    
    node_info JSONB
);

CREATE INDEX IF NOT EXISTS idx_federated_nodes_status ON federated_nodes(status);

-- 用户行为基线表
CREATE TABLE IF NOT EXISTS user_behavior_baselines (
    id SERIAL PRIMARY KEY,
    user_id VARCHAR(50) NOT NULL,
    
    avg_request_rate REAL DEFAULT 0.0,
    avg_session_duration REAL DEFAULT 0.0,
    common_urls JSONB DEFAULT '[]',
    common_times JSONB DEFAULT '[]',
    
    feature_vector JSONB,
    
    sample_count INTEGER DEFAULT 0,
    last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    UNIQUE(user_id)
);

CREATE INDEX IF NOT EXISTS idx_user_behavior_baselines_user ON user_behavior_baselines(user_id);

-- 安全统计表
CREATE TABLE IF NOT EXISTS security_statistics (
    id SERIAL PRIMARY KEY,
    stat_date DATE NOT NULL UNIQUE,
    
    total_requests BIGINT DEFAULT 0,
    blocked_requests BIGINT DEFAULT 0,
    captcha_challenges BIGINT DEFAULT 0,
    rate_limited BIGINT DEFAULT 0,
    
    attacks_detected INTEGER DEFAULT 0,
    attacks_blocked INTEGER DEFAULT 0,
    false_positives INTEGER DEFAULT 0,
    
    avg_response_time REAL DEFAULT 0.0,
    uptime_percentage REAL DEFAULT 100.0,
    
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_security_statistics_date ON security_statistics(stat_date);

-- 插入默认统计记录
INSERT INTO security_statistics (stat_date, total_requests, blocked_requests)
SELECT CURRENT_DATE, 0, 0
WHERE NOT EXISTS (SELECT 1 FROM security_statistics WHERE stat_date = CURRENT_DATE);
