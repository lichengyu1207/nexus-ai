-- 反击系统数据库迁移
-- Migration: 140_create_counterstrike_tables.sql
-- Description: 创建反击系统相关表

-- 1. 攻击者画像表
CREATE TABLE IF NOT EXISTS attacker_profiles (
    profile_id SERIAL PRIMARY KEY,
    attacker_id VARCHAR(100) UNIQUE NOT NULL,
    primary_ip VARCHAR(45),
    associated_ips TEXT[],
    first_seen TIMESTAMP WITH TIME ZONE,
    last_seen TIMESTAMP WITH TIME ZONE,
    actor_type VARCHAR(50) DEFAULT 'unknown',
    confidence INTEGER DEFAULT 1,
    geo_location JSONB DEFAULT '{}',
    organization VARCHAR(255),
    motivation TEXT[],
    capabilities TEXT[],
    threat_score DECIMAL(5,4) DEFAULT 0.0,
    reputation_score DECIMAL(5,4) DEFAULT 0.0,
    tags TEXT[],
    is_known_attacker BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_attacker_profiles_primary_ip ON attacker_profiles(primary_ip);
CREATE INDEX idx_attacker_profiles_actor_type ON attacker_profiles(actor_type);
CREATE INDEX idx_attacker_profiles_threat_score ON attacker_profiles(threat_score DESC);

-- 2. 侦察报告表
CREATE TABLE IF NOT EXISTS recon_reports (
    report_id SERIAL PRIMARY KEY,
    external_report_id VARCHAR(100) UNIQUE NOT NULL,
    attacker_id VARCHAR(100),
    source_ip VARCHAR(45),
    detected_attack_types TEXT[],
    threat_level INTEGER DEFAULT 1,
    confidence DECIMAL(5,4) DEFAULT 0.0,
    indicators JSONB DEFAULT '[]',
    recommended_actions TEXT[],
    raw_traffic_samples JSONB DEFAULT '[]',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    
    FOREIGN KEY (attacker_id) REFERENCES attacker_profiles(attacker_id) ON DELETE SET NULL
);

CREATE INDEX idx_recon_reports_attacker_id ON recon_reports(attacker_id);
CREATE INDEX idx_recon_reports_source_ip ON recon_reports(source_ip);
CREATE INDEX idx_recon_reports_created_at ON recon_reports(created_at DESC);

-- 3. 攻击链表
CREATE TABLE IF NOT EXISTS attack_chains (
    chain_id SERIAL PRIMARY KEY,
    external_chain_id VARCHAR(100) UNIQUE NOT NULL,
    attacker_id VARCHAR(100),
    current_phase VARCHAR(50),
    predicted_next_phase VARCHAR(50),
    target_assets TEXT[],
    total_duration_ms BIGINT DEFAULT 0,
    success_count INTEGER DEFAULT 0,
    detected_count INTEGER DEFAULT 0,
    status VARCHAR(50) DEFAULT 'active',
    start_time TIMESTAMP WITH TIME ZONE,
    last_update TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    
    FOREIGN KEY (attacker_id) REFERENCES attacker_profiles(attacker_id) ON DELETE SET NULL
);

CREATE INDEX idx_attack_chains_attacker_id ON attack_chains(attacker_id);
CREATE INDEX idx_attack_chains_status ON attack_chains(status);

-- 4. 攻击节点表
CREATE TABLE IF NOT EXISTS attack_nodes (
    node_id SERIAL PRIMARY KEY,
    external_node_id VARCHAR(100) UNIQUE NOT NULL,
    chain_id INTEGER NOT NULL,
    tactic VARCHAR(100),
    technique VARCHAR(100),
    timestamp TIMESTAMP WITH TIME ZONE,
    source_ip VARCHAR(45),
    target_asset VARCHAR(255),
    payload_hash VARCHAR(64),
    success BOOLEAN DEFAULT FALSE,
    detected BOOLEAN DEFAULT TRUE,
    details JSONB DEFAULT '{}',
    indicators JSONB DEFAULT '[]',
    duration_ms BIGINT DEFAULT 0,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    
    FOREIGN KEY (chain_id) REFERENCES attack_chains(chain_id) ON DELETE CASCADE
);

CREATE INDEX idx_attack_nodes_chain_id ON attack_nodes(chain_id);
CREATE INDEX idx_attack_nodes_tactic ON attack_nodes(tactic);
CREATE INDEX idx_attack_nodes_timestamp ON attack_nodes(timestamp DESC);

-- 5. 蜜罐实例表
CREATE TABLE IF NOT EXISTS honeypot_instances (
    honeypot_id SERIAL PRIMARY KEY,
    external_honeypot_id VARCHAR(100) UNIQUE NOT NULL,
    honeypot_type VARCHAR(50) NOT NULL,
    port INTEGER,
    bind_address VARCHAR(45) DEFAULT '0.0.0.0',
    service_version VARCHAR(100),
    state VARCHAR(50) DEFAULT 'initializing',
    attacker_profile_id VARCHAR(100),
    interaction_count INTEGER DEFAULT 0,
    credentials_captured INTEGER DEFAULT 0,
    payloads_captured INTEGER DEFAULT 0,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    expires_at TIMESTAMP WITH TIME ZONE,
    
    FOREIGN KEY (attacker_profile_id) REFERENCES attacker_profiles(attacker_id) ON DELETE SET NULL
);

CREATE INDEX idx_honeypot_instances_type ON honeypot_instances(honeypot_type);
CREATE INDEX idx_honeypot_instances_state ON honeypot_instances(state);

-- 6. 蜜罐交互日志表
CREATE TABLE IF NOT EXISTS honeypot_interactions (
    interaction_id SERIAL PRIMARY KEY,
    external_interaction_id VARCHAR(100) UNIQUE NOT NULL,
    honeypot_id INTEGER NOT NULL,
    source_ip VARCHAR(45) NOT NULL,
    start_time TIMESTAMP WITH TIME ZONE,
    end_time TIMESTAMP WITH TIME ZONE,
    duration_seconds DECIMAL(10,2),
    commands JSONB DEFAULT '[]',
    responses JSONB DEFAULT '[]',
    files_accessed TEXT[],
    credentials_tried JSONB DEFAULT '[]',
    payloads TEXT[],
    attacker_behavior TEXT[],
    session_data JSONB DEFAULT '{}',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    
    FOREIGN KEY (honeypot_id) REFERENCES honeypot_instances(honeypot_id) ON DELETE CASCADE
);

CREATE INDEX idx_honeypot_interactions_honeypot_id ON honeypot_interactions(honeypot_id);
CREATE INDEX idx_honeypot_interactions_source_ip ON honeypot_interactions(source_ip);
CREATE INDEX idx_honeypot_interactions_start_time ON honeypot_interactions(start_time DESC);

-- 7. 反击行动表
CREATE TABLE IF NOT EXISTS counter_strike_actions (
    action_id SERIAL PRIMARY KEY,
    external_action_id VARCHAR(100) UNIQUE NOT NULL,
    action_type VARCHAR(50) NOT NULL,
    target_identity VARCHAR(100),
    target_ip VARCHAR(45),
    status VARCHAR(50) DEFAULT 'pending',
    severity INTEGER DEFAULT 2,
    parameters JSONB DEFAULT '{}',
    results JSONB DEFAULT '{}',
    requires_approval BOOLEAN DEFAULT FALSE,
    approved_by VARCHAR(100),
    effectiveness_score DECIMAL(5,4) DEFAULT 0.0,
    side_effects TEXT[],
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    approved_at TIMESTAMP WITH TIME ZONE,
    executed_at TIMESTAMP WITH TIME ZONE,
    expires_at TIMESTAMP WITH TIME ZONE,
    
    FOREIGN KEY (target_identity) REFERENCES attacker_profiles(attacker_id) ON DELETE SET NULL
);

CREATE INDEX idx_counter_strike_actions_target_ip ON counter_strike_actions(target_ip);
CREATE INDEX idx_counter_strike_actions_status ON counter_strike_actions(status);
CREATE INDEX idx_counter_strike_actions_created_at ON counter_strike_actions(created_at DESC);

-- 8. 围剿策略表
CREATE TABLE IF NOT EXISTS pursuit_strategies (
    strategy_id SERIAL PRIMARY KEY,
    external_strategy_id VARCHAR(100) UNIQUE NOT NULL,
    formation VARCHAR(50) NOT NULL,
    target_identity VARCHAR(100),
    target_ips TEXT[],
    current_phase VARCHAR(50) DEFAULT 'reconnaissance',
    priority INTEGER DEFAULT 1,
    assigned_agents JSONB DEFAULT '{}',
    estimated_duration INTEGER DEFAULT 3600,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    completed_at TIMESTAMP WITH TIME ZONE,
    
    FOREIGN KEY (target_identity) REFERENCES attacker_profiles(attacker_id) ON DELETE SET NULL
);

CREATE INDEX idx_pursuit_strategies_target_identity ON pursuit_strategies(target_identity);
CREATE INDEX idx_pursuit_strategies_current_phase ON pursuit_strategies(current_phase);

-- 9. 作战记忆表
CREATE TABLE IF NOT EXISTS war_memories (
    memory_id SERIAL PRIMARY KEY,
    external_memory_id VARCHAR(100) UNIQUE NOT NULL,
    memory_type VARCHAR(50) NOT NULL,
    content JSONB NOT NULL,
    tags TEXT[],
    priority INTEGER DEFAULT 2,
    access_count INTEGER DEFAULT 0,
    related_memories TEXT[],
    distilled BOOLEAN DEFAULT FALSE,
    source VARCHAR(100),
    confidence DECIMAL(5,4) DEFAULT 1.0,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    last_accessed TIMESTAMP WITH TIME ZONE
);

CREATE INDEX idx_war_memories_type ON war_memories(memory_type);
CREATE INDEX idx_war_memories_created_at ON war_memories(created_at DESC);
CREATE INDEX idx_war_memories_tags ON war_memories USING GIN(tags);

-- 10. 战术库表
CREATE TABLE IF NOT EXISTS tactics (
    tactic_id SERIAL PRIMARY KEY,
    external_tactic_id VARCHAR(100) UNIQUE NOT NULL,
    name VARCHAR(255) NOT NULL,
    category VARCHAR(50) NOT NULL,
    description TEXT,
    conditions JSONB DEFAULT '{}',
    parameters JSONB DEFAULT '{}',
    required_agents JSONB DEFAULT '{}',
    expected_effectiveness DECIMAL(5,4) DEFAULT 0.7,
    success_rate DECIMAL(5,4) DEFAULT 0.7,
    risk_level DECIMAL(5,4) DEFAULT 0.3,
    use_count INTEGER DEFAULT 0,
    success_count INTEGER DEFAULT 0,
    failure_count INTEGER DEFAULT 0,
    tags TEXT[],
    status VARCHAR(50) DEFAULT 'available',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    last_used TIMESTAMP WITH TIME ZONE
);

CREATE INDEX idx_tactics_category ON tactics(category);
CREATE INDEX idx_tactics_status ON tactics(status);

-- 11. 战术执行记录表
CREATE TABLE IF NOT EXISTS tactic_executions (
    execution_id SERIAL PRIMARY KEY,
    external_execution_id VARCHAR(100) UNIQUE NOT NULL,
    tactic_id INTEGER NOT NULL,
    target_identity VARCHAR(100),
    status VARCHAR(50) DEFAULT 'pending',
    agents_involved TEXT[],
    actions_taken JSONB DEFAULT '[]',
    effectiveness_score DECIMAL(5,4) DEFAULT 0.0,
    resource_usage JSONB DEFAULT '{}',
    errors TEXT[],
    metrics JSONB DEFAULT '{}',
    started_at TIMESTAMP WITH TIME ZONE,
    completed_at TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    
    FOREIGN KEY (tactic_id) REFERENCES tactics(tactic_id) ON DELETE CASCADE,
    FOREIGN KEY (target_identity) REFERENCES attacker_profiles(attacker_id) ON DELETE SET NULL
);

CREATE INDEX idx_tactic_executions_tactic_id ON tactic_executions(tactic_id);
CREATE INDEX idx_tactic_executions_status ON tactic_executions(status);

-- 12. 复盘报告表
CREATE TABLE IF NOT EXISTS after_action_reviews (
    review_id SERIAL PRIMARY KEY,
    external_review_id VARCHAR(100) UNIQUE NOT NULL,
    operation_id VARCHAR(100),
    status VARCHAR(50) DEFAULT 'pending',
    outcome VARCHAR(50) DEFAULT 'inconclusive',
    timeline JSONB DEFAULT '[]',
    key_decisions JSONB DEFAULT '[]',
    effectiveness_metrics JSONB DEFAULT '{}',
    resource_usage JSONB DEFAULT '{}',
    success_factors TEXT[],
    failure_factors TEXT[],
    lessons_learned TEXT[],
    recommendations TEXT[],
    follow_up_actions JSONB DEFAULT '[]',
    participants TEXT[],
    overall_score DECIMAL(5,4) DEFAULT 0.0,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    completed_at TIMESTAMP WITH TIME ZONE
);

CREATE INDEX idx_after_action_reviews_operation_id ON after_action_reviews(operation_id);
CREATE INDEX idx_after_action_reviews_outcome ON after_action_reviews(outcome);

-- 13. 边界规则表
CREATE TABLE IF NOT EXISTS boundary_rules (
    rule_id SERIAL PRIMARY KEY,
    external_rule_id VARCHAR(100) UNIQUE NOT NULL,
    rule_type VARCHAR(50) NOT NULL,
    name VARCHAR(255) NOT NULL,
    description TEXT,
    conditions JSONB DEFAULT '{}',
    actions TEXT[],
    active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_boundary_rules_type ON boundary_rules(rule_type);
CREATE INDEX idx_boundary_rules_active ON boundary_rules(active);

-- 14. 边界违规记录表
CREATE TABLE IF NOT EXISTS boundary_violations (
    violation_id SERIAL PRIMARY KEY,
    external_violation_id VARCHAR(100) UNIQUE NOT NULL,
    action JSONB NOT NULL,
    rule JSONB NOT NULL,
    severity INTEGER DEFAULT 2,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_boundary_violations_severity ON boundary_violations(severity);
CREATE INDEX idx_boundary_violations_created_at ON boundary_violations(created_at DESC);

-- 15. 审批请求表
CREATE TABLE IF NOT EXISTS approval_requests (
    request_id SERIAL PRIMARY KEY,
    external_request_id VARCHAR(100) UNIQUE NOT NULL,
    action_id VARCHAR(100),
    action_type VARCHAR(50),
    target VARCHAR(255),
    reason TEXT,
    urgency VARCHAR(50) DEFAULT 'normal',
    timeout_seconds INTEGER DEFAULT 300,
    status VARCHAR(50) DEFAULT 'pending',
    approver VARCHAR(100),
    notes TEXT,
    rejection_reason TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    expires_at TIMESTAMP WITH TIME ZONE,
    processed_at TIMESTAMP WITH TIME ZONE
);

CREATE INDEX idx_approval_requests_status ON approval_requests(status);
CREATE INDEX idx_approval_requests_created_at ON approval_requests(created_at DESC);

-- 16. 信息素沉积记录表
CREATE TABLE IF NOT EXISTS pheromone_deposits (
    deposit_id SERIAL PRIMARY KEY,
    pheromone_id VARCHAR(100) UNIQUE NOT NULL,
    pheromone_type VARCHAR(50) NOT NULL,
    position_x DECIMAL(10,6),
    position_y DECIMAL(10,6),
    strength DECIMAL(5,4),
    deposited_by VARCHAR(100),
    decay_rate DECIMAL(5,4) DEFAULT 0.05,
    diffusion_radius DECIMAL(10,6) DEFAULT 0.1,
    metadata JSONB DEFAULT '{}',
    deposited_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_pheromone_deposits_type ON pheromone_deposits(pheromone_type);
CREATE INDEX idx_pheromone_deposits_position ON pheromone_deposits(position_x, position_y);

-- 17. 网络变换记录表
CREATE TABLE IF NOT EXISTS network_transforms (
    transform_id SERIAL PRIMARY KEY,
    external_transform_id VARCHAR(100) UNIQUE NOT NULL,
    transform_type VARCHAR(50) NOT NULL,
    trigger VARCHAR(50),
    source_config JSONB DEFAULT '{}',
    target_config JSONB DEFAULT '{}',
    affected_services TEXT[],
    duration_seconds DECIMAL(10,2),
    success BOOLEAN DEFAULT TRUE,
    rollback_data JSONB DEFAULT '{}',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_network_transforms_type ON network_transforms(transform_type);
CREATE INDEX idx_network_transforms_created_at ON network_transforms(created_at DESC);

-- 18. 伪造响应记录表
CREATE TABLE IF NOT EXISTS forged_responses (
    response_id SERIAL PRIMARY KEY,
    external_response_id VARCHAR(100) UNIQUE NOT NULL,
    response_type VARCHAR(50) NOT NULL,
    request_data JSONB DEFAULT '{}',
    response_data JSONB DEFAULT '{}',
    delay_ms DECIMAL(10,2) DEFAULT 0,
    attacker_ip VARCHAR(45),
    success BOOLEAN DEFAULT TRUE,
    deception_score DECIMAL(5,4) DEFAULT 0.0,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_forged_responses_type ON forged_responses(response_type);
CREATE INDEX idx_forged_responses_attacker_ip ON forged_responses(attacker_ip);

-- 19. 智能体注册表
CREATE TABLE IF NOT EXISTS agent_registry (
    agent_id SERIAL PRIMARY KEY,
    external_agent_id VARCHAR(100) UNIQUE NOT NULL,
    agent_type VARCHAR(50) NOT NULL,
    capabilities TEXT[],
    status VARCHAR(50) DEFAULT 'registered',
    position_x DECIMAL(10,6),
    position_y DECIMAL(10,6),
    current_role VARCHAR(50),
    effectiveness_score DECIMAL(5,4) DEFAULT 0.5,
    registered_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    last_active TIMESTAMP WITH TIME ZONE
);

CREATE INDEX idx_agent_registry_type ON agent_registry(agent_type);
CREATE INDEX idx_agent_registry_status ON agent_registry(status);

-- 20. 系统事件日志表
CREATE TABLE IF NOT EXISTS system_event_log (
    event_id SERIAL PRIMARY KEY,
    event_type VARCHAR(100) NOT NULL,
    source VARCHAR(100),
    target VARCHAR(100),
    data JSONB DEFAULT '{}',
    severity INTEGER DEFAULT 2,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_system_event_log_type ON system_event_log(event_type);
CREATE INDEX idx_system_event_log_created_at ON system_event_log(created_at DESC);

-- 创建视图：活跃威胁视图
CREATE OR REPLACE VIEW active_threats_view AS
SELECT 
    ap.attacker_id,
    ap.primary_ip,
    ap.actor_type,
    ap.threat_score,
    ap.last_seen,
    COUNT(DISTINCT rr.report_id) as report_count,
    COUNT(DISTINCT ac.chain_id) as chain_count,
    COUNT(DISTINCT cs.action_id) as counter_strike_count
FROM attacker_profiles ap
LEFT JOIN recon_reports rr ON ap.attacker_id = rr.attacker_id
LEFT JOIN attack_chains ac ON ap.attacker_id = ac.attacker_id AND ac.status = 'active'
LEFT JOIN counter_strike_actions cs ON ap.attacker_id = cs.target_identity AND cs.status = 'active'
WHERE ap.last_seen > CURRENT_TIMESTAMP - INTERVAL '24 hours'
GROUP BY ap.attacker_id, ap.primary_ip, ap.actor_type, ap.threat_score, ap.last_seen
ORDER BY ap.threat_score DESC;

-- 创建视图：蜜罐效果统计
CREATE OR REPLACE VIEW honeypot_effectiveness_view AS
SELECT 
    hi.honeypot_type,
    COUNT(DISTINCT hi.honeypot_id) as total_honeypots,
    COUNT(DISTINCT hpi.interaction_id) as total_interactions,
    SUM(hpi.credentials_captured) as total_credentials,
    SUM(hpi.payloads_captured) as total_payloads,
    AVG(EXTRACT(EPOCH FROM (hpi.end_time - hpi.start_time))) as avg_interaction_duration
FROM honeypot_instances hi
LEFT JOIN honeypot_interactions hpi ON hi.honeypot_id = hpi.honeypot_id
GROUP BY hi.honeypot_type;

-- 创建函数：更新时间戳
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ language 'plpgsql';

-- 创建触发器
CREATE TRIGGER update_attacker_profiles_updated_at
    BEFORE UPDATE ON attacker_profiles
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

-- 授权
GRANT SELECT, INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA public TO fangdudu_user;
GRANT USAGE, SELECT ON ALL SEQUENCES IN SCHEMA public TO fangdudu_user;
GRANT EXECUTE ON ALL FUNCTIONS IN SCHEMA public TO fangdudu_user;
