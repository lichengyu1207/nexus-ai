-- 攻击与防御智能体集群战时协作系统数据库表 (PostgreSQL)
-- Attack-Defense Agent Cluster Wartime Collaboration System Tables

-- 双模式智能体状态表
CREATE TABLE IF NOT EXISTS dual_mode_agents (
    id SERIAL PRIMARY KEY,
    agent_id VARCHAR(50) NOT NULL UNIQUE,
    
    agent_type VARCHAR(20) NOT NULL,
    current_mode VARCHAR(20) NOT NULL DEFAULT 'attack',
    
    total_games INTEGER DEFAULT 0,
    wins INTEGER DEFAULT 0,
    losses INTEGER DEFAULT 0,
    
    contribution_score REAL DEFAULT 1.0,
    trust_score REAL DEFAULT 1.0,
    
    advise_given_count INTEGER DEFAULT 0,
    advise_accepted_count INTEGER DEFAULT 0,
    advise_rejected_count INTEGER DEFAULT 0,
    
    model_version INTEGER DEFAULT 1,
    model_path TEXT,
    
    is_active BOOLEAN DEFAULT TRUE,
    is_malicious BOOLEAN DEFAULT FALSE,
    
    last_heartbeat TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_dual_mode_agents_type ON dual_mode_agents(agent_type);
CREATE INDEX IF NOT EXISTS idx_dual_mode_agents_mode ON dual_mode_agents(current_mode);
CREATE INDEX IF NOT EXISTS idx_dual_mode_agents_active ON dual_mode_agents(is_active);

-- 战时指挥中心状态表
CREATE TABLE IF NOT EXISTS war_center_state (
    id SERIAL PRIMARY KEY,
    state_id VARCHAR(50) NOT NULL UNIQUE,
    
    system_state VARCHAR(20) NOT NULL DEFAULT 'peacetime',
    
    wartime_start_time TIMESTAMP,
    peacetime_start_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    total_wartime_activations INTEGER DEFAULT 0,
    total_collaborations INTEGER DEFAULT 0,
    
    active_attackers INTEGER DEFAULT 0,
    active_defenders INTEGER DEFAULT 0,
    
    last_attack_detected TIMESTAMP,
    last_mode_switch TIMESTAMP,
    
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 攻击检测记录表
CREATE TABLE IF NOT EXISTS attack_detections (
    id SERIAL PRIMARY KEY,
    detection_id VARCHAR(50) NOT NULL UNIQUE,
    
    attack_type VARCHAR(50) NOT NULL,
    attack_intensity REAL,
    confidence REAL,
    
    source_ip VARCHAR(50),
    target_port INTEGER,
    
    pattern_signature JSONB,
    anomaly_score REAL,
    
    detected_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    resolved_at TIMESTAMP,
    
    is_external BOOLEAN DEFAULT TRUE,
    is_false_positive BOOLEAN DEFAULT FALSE
);

CREATE INDEX IF NOT EXISTS idx_attack_detections_type ON attack_detections(attack_type);
CREATE INDEX IF NOT EXISTS idx_attack_detections_detected ON attack_detections(detected_at);

-- 模式切换记录表
CREATE TABLE IF NOT EXISTS mode_switches (
    id SERIAL PRIMARY KEY,
    switch_id VARCHAR(50) NOT NULL UNIQUE,
    
    from_mode VARCHAR(20) NOT NULL,
    to_mode VARCHAR(20) NOT NULL,
    
    trigger_reason VARCHAR(200),
    trigger_score REAL,
    
    switch_duration_ms REAL,
    success BOOLEAN DEFAULT TRUE,
    
    agents_affected INTEGER DEFAULT 0,
    
    switched_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_mode_switches_time ON mode_switches(switched_at);

-- 防御建议表
CREATE TABLE IF NOT EXISTS defense_advices (
    id SERIAL PRIMARY KEY,
    advice_id VARCHAR(50) NOT NULL UNIQUE,
    
    agent_id VARCHAR(50) NOT NULL,
    session_id VARCHAR(50),
    
    state_snapshot JSONB NOT NULL,
    advised_action INTEGER NOT NULL,
    confidence REAL,
    
    reasoning TEXT,
    contribution_score REAL DEFAULT 1.0,
    
    is_validated BOOLEAN,
    validation_reason TEXT,
    
    is_malicious BOOLEAN DEFAULT FALSE,
    malicious_score REAL DEFAULT 0.0,
    
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_defense_advices_agent ON defense_advices(agent_id);
CREATE INDEX IF NOT EXISTS idx_defense_advices_session ON defense_advices(session_id);

-- 建议融合记录表
CREATE TABLE IF NOT EXISTS advice_fusions (
    id SERIAL PRIMARY KEY,
    fusion_id VARCHAR(50) NOT NULL UNIQUE,
    session_id VARCHAR(50),
    
    input_advices JSONB NOT NULL,
    fusion_method VARCHAR(50) NOT NULL,
    
    final_action INTEGER NOT NULL,
    final_confidence REAL,
    
    consensus_achieved BOOLEAN DEFAULT FALSE,
    consensus_ratio REAL,
    
    redundancy_sufficient BOOLEAN DEFAULT TRUE,
    
    fusion_time_ms REAL,
    
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_advice_fusions_session ON advice_fusions(session_id);

-- 协作训练记录表
CREATE TABLE IF NOT EXISTS collaboration_training (
    id SERIAL PRIMARY KEY,
    training_id VARCHAR(50) NOT NULL UNIQUE,
    
    stage INTEGER NOT NULL,
    stage_name VARCHAR(50),
    
    episodes_completed INTEGER DEFAULT 0,
    epochs_completed INTEGER DEFAULT 0,
    
    avg_reward REAL,
    best_reward REAL,
    
    collaboration_score REAL,
    defense_success_rate REAL,
    
    model_saved BOOLEAN DEFAULT FALSE,
    model_path TEXT,
    
    started_at TIMESTAMP,
    completed_at TIMESTAMP,
    
    status VARCHAR(20) DEFAULT 'running',
    error_message TEXT,
    
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_collaboration_training_stage ON collaboration_training(stage);
CREATE INDEX IF NOT EXISTS idx_collaboration_training_status ON collaboration_training(status);

-- 协作奖励记录表
CREATE TABLE IF NOT EXISTS collaboration_rewards (
    id SERIAL PRIMARY KEY,
    reward_id VARCHAR(50) NOT NULL UNIQUE,
    episode_id VARCHAR(50),
    
    attacker_rewards JSONB,
    defender_rewards JSONB,
    
    collaboration_bonus REAL,
    advice_quality_score REAL,
    
    defense_successful BOOLEAN,
    attack_successful BOOLEAN,
    
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 安全事件日志表
CREATE TABLE IF NOT EXISTS security_events (
    id SERIAL PRIMARY KEY,
    event_id VARCHAR(50) NOT NULL UNIQUE,
    
    event_type VARCHAR(50) NOT NULL,
    severity VARCHAR(20) NOT NULL,
    
    agent_id VARCHAR(50),
    details JSONB,
    
    is_resolved BOOLEAN DEFAULT FALSE,
    resolved_at TIMESTAMP,
    resolved_by VARCHAR(100),
    
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_security_events_type ON security_events(event_type);
CREATE INDEX IF NOT EXISTS idx_security_events_severity ON security_events(severity);
CREATE INDEX IF NOT EXISTS idx_security_events_resolved ON security_events(is_resolved);

-- 智能体健康状态表
CREATE TABLE IF NOT EXISTS agent_health (
    id SERIAL PRIMARY KEY,
    agent_id VARCHAR(50) NOT NULL,
    
    is_healthy BOOLEAN DEFAULT TRUE,
    last_response_time_ms REAL,
    
    consecutive_failures INTEGER DEFAULT 0,
    total_failures INTEGER DEFAULT 0,
    
    last_check_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    UNIQUE(agent_id, last_check_time)
);

CREATE INDEX IF NOT EXISTS idx_agent_health_agent ON agent_health(agent_id);

-- 冗余状态表
CREATE TABLE IF NOT EXISTS redundancy_status (
    id SERIAL PRIMARY KEY,
    check_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    active_attackers INTEGER DEFAULT 0,
    active_defenders INTEGER DEFAULT 0,
    
    min_attackers_met BOOLEAN DEFAULT FALSE,
    min_defenders_met BOOLEAN DEFAULT FALSE,
    
    redundancy_sufficient BOOLEAN DEFAULT FALSE,
    
    failed_agents JSONB,
    
    UNIQUE(check_time)
);

-- 共识状态表
CREATE TABLE IF NOT EXISTS consensus_state (
    id SERIAL PRIMARY KEY,
    consensus_id VARCHAR(50) NOT NULL UNIQUE,
    
    total_advices INTEGER DEFAULT 0,
    unique_actions INTEGER DEFAULT 0,
    
    majority_action INTEGER,
    majority_count INTEGER,
    majority_ratio REAL,
    
    consensus_achieved BOOLEAN DEFAULT FALSE,
    
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 外部攻击环境状态表
CREATE TABLE IF NOT EXISTS external_attack_env (
    id SERIAL PRIMARY KEY,
    env_id VARCHAR(50) NOT NULL UNIQUE,
    
    time_step INTEGER DEFAULT 0,
    attack_active BOOLEAN DEFAULT FALSE,
    attack_type INTEGER DEFAULT 0,
    attack_intensity REAL DEFAULT 0.0,
    
    request_rate REAL,
    error_rate REAL,
    unique_ips REAL,
    cpu_usage REAL,
    memory_usage REAL,
    response_time REAL,
    
    service_down BOOLEAN DEFAULT FALSE,
    
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_external_attack_env_time ON external_attack_env(time_step);

-- 插入默认配置
INSERT INTO war_center_state (state_id, system_state)
SELECT 'default', 'peacetime'
WHERE NOT EXISTS (SELECT 1 FROM war_center_state WHERE state_id = 'default');

-- 创建更新时间触发器
DROP TRIGGER IF EXISTS update_dual_mode_agents_updated_at ON dual_mode_agents;
CREATE TRIGGER update_dual_mode_agents_updated_at
    BEFORE UPDATE ON dual_mode_agents
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

DROP TRIGGER IF EXISTS update_war_center_state_updated_at ON war_center_state;
CREATE TRIGGER update_war_center_state_updated_at
    BEFORE UPDATE ON war_center_state
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();
