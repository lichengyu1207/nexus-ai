-- 活体智能体系统数据库迁移
-- Migration: 120_create_living_system_tables.sql
-- Description: 创建活体智能体系统相关表

-- 1. 智能体基因组表
CREATE TABLE IF NOT EXISTS agent_genomes (
    id SERIAL PRIMARY KEY,
    genome_id VARCHAR(100) UNIQUE NOT NULL,
    agent_id VARCHAR(100) NOT NULL,
    parent_ids TEXT[],
    generation INTEGER DEFAULT 0,
    architecture JSONB DEFAULT '{}',
    weights_hash VARCHAR(64),
    fitness_score DECIMAL(10, 6) DEFAULT 0,
    mutation_history JSONB DEFAULT '[]',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    
    CONSTRAINT uk_agent_genome UNIQUE (agent_id)
);

CREATE INDEX idx_agent_genomes_agent_id ON agent_genomes(agent_id);
CREATE INDEX idx_agent_genomes_fitness ON agent_genomes(fitness_score DESC);
CREATE INDEX idx_agent_genomes_generation ON agent_genomes(generation);
CREATE INDEX idx_agent_genomes_created_at ON agent_genomes(created_at DESC);

COMMENT ON TABLE agent_genomes IS '智能体基因组表';

-- 2. 繁殖记录表
CREATE TABLE IF NOT EXISTS reproduction_records (
    id SERIAL PRIMARY KEY,
    reproduction_id VARCHAR(100) UNIQUE NOT NULL,
    parent_id VARCHAR(100) NOT NULL,
    offspring_id VARCHAR(100) NOT NULL,
    reproduction_type VARCHAR(20) NOT NULL,
    energy_transferred DECIMAL(10, 4) DEFAULT 0,
    mutations JSONB DEFAULT '[]',
    timestamp TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    
    CONSTRAINT chk_reproduction_type CHECK (reproduction_type IN ('asexual', 'sexual'))
);

CREATE INDEX idx_reproduction_records_parent ON reproduction_records(parent_id);
CREATE INDEX idx_reproduction_records_offspring ON reproduction_records(offspring_id);
CREATE INDEX idx_reproduction_records_timestamp ON reproduction_records(timestamp DESC);

COMMENT ON TABLE reproduction_records IS '繁殖记录表';

-- 3. 任务表
CREATE TABLE IF NOT EXISTS living_tasks (
    id SERIAL PRIMARY KEY,
    task_id VARCHAR(100) UNIQUE NOT NULL,
    task_type VARCHAR(50) NOT NULL,
    description TEXT,
    required_skills JSONB DEFAULT '[]',
    priority INTEGER DEFAULT 2,
    reward DECIMAL(10, 4) DEFAULT 0,
    deadline TIMESTAMP WITH TIME ZONE,
    max_team_size INTEGER DEFAULT 5,
    min_team_size INTEGER DEFAULT 1,
    status VARCHAR(20) DEFAULT 'pending',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    created_by VARCHAR(100),
    assigned_agents TEXT[],
    completed_at TIMESTAMP WITH TIME ZONE,
    result JSONB,
    
    CONSTRAINT chk_task_status CHECK (status IN ('pending', 'bidding', 'assigned', 'in_progress', 'completed', 'failed', 'cancelled'))
);

CREATE INDEX idx_living_tasks_status ON living_tasks(status);
CREATE INDEX idx_living_tasks_type ON living_tasks(task_type);
CREATE INDEX idx_living_tasks_created_at ON living_tasks(created_at DESC);
CREATE INDEX idx_living_tasks_priority ON living_tasks(priority DESC);

COMMENT ON TABLE living_tasks IS '活体系统任务表';

-- 4. 竞标表
CREATE TABLE IF NOT EXISTS task_bids (
    id SERIAL PRIMARY KEY,
    bid_id VARCHAR(100) UNIQUE NOT NULL,
    task_id VARCHAR(100) NOT NULL,
    agent_id VARCHAR(100) NOT NULL,
    estimated_completion_time DECIMAL(10, 2),
    success_probability DECIMAL(5, 4) DEFAULT 0.8,
    proposed_reward DECIMAL(10, 4),
    capabilities JSONB DEFAULT '{}',
    message TEXT,
    status VARCHAR(20) DEFAULT 'pending',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    
    CONSTRAINT chk_bid_status CHECK (status IN ('pending', 'accepted', 'rejected'))
);

CREATE INDEX idx_task_bids_task_id ON task_bids(task_id);
CREATE INDEX idx_task_bids_agent_id ON task_bids(agent_id);
CREATE INDEX idx_task_bids_status ON task_bids(status);
CREATE INDEX idx_task_bids_created_at ON task_bids(created_at DESC);

COMMENT ON TABLE task_bids IS '任务竞标表';

-- 5. 团队表
CREATE TABLE IF NOT EXISTS living_teams (
    id SERIAL PRIMARY KEY,
    team_id VARCHAR(100) UNIQUE NOT NULL,
    team_name VARCHAR(100),
    task_id VARCHAR(100),
    members TEXT[] NOT NULL,
    leader_id VARCHAR(100),
    status VARCHAR(20) DEFAULT 'active',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    dissolved_at TIMESTAMP WITH TIME ZONE,
    dissolution_reason TEXT
);

CREATE INDEX idx_living_teams_status ON living_teams(status);
CREATE INDEX idx_living_teams_task_id ON living_teams(task_id);
CREATE INDEX idx_living_teams_created_at ON living_teams(created_at DESC);

COMMENT ON TABLE living_teams IS '活体系统团队表';

-- 6. 智能体能量表
CREATE TABLE IF NOT EXISTS agent_energy (
    id SERIAL PRIMARY KEY,
    agent_id VARCHAR(100) UNIQUE NOT NULL,
    energy DECIMAL(10, 4) DEFAULT 50.0,
    total_earned DECIMAL(10, 4) DEFAULT 0,
    total_spent DECIMAL(10, 4) DEFAULT 0,
    last_updated TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_agent_energy_agent_id ON agent_energy(agent_id);
CREATE INDEX idx_agent_energy_level ON agent_energy(energy DESC);

COMMENT ON TABLE agent_energy IS '智能体能量表';

-- 7. 奖励历史表
CREATE TABLE IF NOT EXISTS reward_history (
    id SERIAL PRIMARY KEY,
    agent_id VARCHAR(100) NOT NULL,
    action VARCHAR(100),
    reward DECIMAL(10, 6),
    outcome JSONB DEFAULT '{}',
    timestamp TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_reward_history_agent_id ON reward_history(agent_id);
CREATE INDEX idx_reward_history_timestamp ON reward_history(timestamp DESC);

COMMENT ON TABLE reward_history IS '奖励历史表';

-- 8. 全局目标表
CREATE TABLE IF NOT EXISTS global_goals (
    id SERIAL PRIMARY KEY,
    goal_name VARCHAR(100) UNIQUE NOT NULL,
    target_value DECIMAL(10, 6) NOT NULL,
    current_value DECIMAL(10, 6),
    weight DECIMAL(5, 4) DEFAULT 1.0,
    description TEXT,
    is_lower_better BOOLEAN DEFAULT FALSE,
    last_updated TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_global_goals_name ON global_goals(goal_name);

COMMENT ON TABLE global_goals IS '全局目标表';

-- 9. 涌现模式表
CREATE TABLE IF NOT EXISTS emergence_patterns (
    id SERIAL PRIMARY KEY,
    pattern_id VARCHAR(100) UNIQUE NOT NULL,
    pattern_type VARCHAR(50) NOT NULL,
    pattern_data JSONB NOT NULL,
    first_detected TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    last_detected TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    occurrence_count INTEGER DEFAULT 1
);

CREATE INDEX idx_emergence_patterns_type ON emergence_patterns(pattern_type);
CREATE INDEX idx_emergence_patterns_occurrence ON emergence_patterns(occurrence_count DESC);

COMMENT ON TABLE emergence_patterns IS '涌现模式表';

-- 10. 交互图边表
CREATE TABLE IF NOT EXISTS interaction_edges (
    id SERIAL PRIMARY KEY,
    from_agent VARCHAR(100) NOT NULL,
    to_agent VARCHAR(100) NOT NULL,
    weight DECIMAL(10, 4) DEFAULT 1.0,
    last_interaction TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    
    CONSTRAINT uk_interaction_edge UNIQUE (from_agent, to_agent)
);

CREATE INDEX idx_interaction_edges_from ON interaction_edges(from_agent);
CREATE INDEX idx_interaction_edges_to ON interaction_edges(to_agent);
CREATE INDEX idx_interaction_edges_weight ON interaction_edges(weight DESC);

COMMENT ON TABLE interaction_edges IS '交互图边表';

-- 11. 通信日志表
CREATE TABLE IF NOT EXISTS communication_logs (
    id SERIAL PRIMARY KEY,
    message_id VARCHAR(100),
    from_agent VARCHAR(100),
    to_agent VARCHAR(100),
    message_type VARCHAR(50),
    payload JSONB DEFAULT '{}',
    timestamp TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_communication_logs_from ON communication_logs(from_agent);
CREATE INDEX idx_communication_logs_to ON communication_logs(to_agent);
CREATE INDEX idx_communication_logs_timestamp ON communication_logs(timestamp DESC);

COMMENT ON TABLE communication_logs IS '通信日志表';

-- 12. 状态变更历史表
CREATE TABLE IF NOT EXISTS state_change_history (
    id SERIAL PRIMARY KEY,
    agent_id VARCHAR(100) NOT NULL,
    old_state VARCHAR(50),
    new_state VARCHAR(50),
    context JSONB DEFAULT '{}',
    timestamp TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_state_change_agent ON state_change_history(agent_id);
CREATE INDEX idx_state_change_timestamp ON state_change_history(timestamp DESC);

COMMENT ON TABLE state_change_history IS '状态变更历史表';

-- 13. 约束违规记录表
CREATE TABLE IF NOT EXISTS constraint_violations (
    id SERIAL PRIMARY KEY,
    violation_id VARCHAR(100) UNIQUE NOT NULL,
    agent_id VARCHAR(100) NOT NULL,
    constraint_id VARCHAR(100) NOT NULL,
    action JSONB DEFAULT '{}',
    context JSONB DEFAULT '{}',
    severity VARCHAR(20) DEFAULT 'medium',
    timestamp TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    resolved BOOLEAN DEFAULT FALSE,
    resolution TEXT
);

CREATE INDEX idx_constraint_violations_agent ON constraint_violations(agent_id);
CREATE INDEX idx_constraint_violations_constraint ON constraint_violations(constraint_id);
CREATE INDEX idx_constraint_violations_severity ON constraint_violations(severity);
CREATE INDEX idx_constraint_violations_timestamp ON constraint_violations(timestamp DESC);

COMMENT ON TABLE constraint_violations IS '约束违规记录表';

-- 14. 安全围栏状态表
CREATE TABLE IF NOT EXISTS safety_fence_status (
    id SERIAL PRIMARY KEY,
    emergency_stop_active BOOLEAN DEFAULT FALSE,
    emergency_stop_reason TEXT,
    emergency_stop_time TIMESTAMP WITH TIME ZONE,
    last_updated TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

COMMENT ON TABLE safety_fence_status IS '安全围栏状态表';

-- 15. 议会成员表
CREATE TABLE IF NOT EXISTS parliament_members (
    id SERIAL PRIMARY KEY,
    agent_id VARCHAR(100) UNIQUE NOT NULL,
    registered_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    is_active BOOLEAN DEFAULT TRUE
);

CREATE INDEX idx_parliament_members_agent ON parliament_members(agent_id);

COMMENT ON TABLE parliament_members IS '议会成员表';

-- 16. 判断请求表
CREATE TABLE IF NOT EXISTS judgment_requests (
    id SERIAL PRIMARY KEY,
    judgment_id VARCHAR(100) UNIQUE NOT NULL,
    agent_id VARCHAR(100) NOT NULL,
    action JSONB DEFAULT '{}',
    context JSONB DEFAULT '{}',
    votes_for INTEGER DEFAULT 0,
    votes_against INTEGER DEFAULT 0,
    status VARCHAR(20) DEFAULT 'pending',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    finalized_at TIMESTAMP WITH TIME ZONE,
    result BOOLEAN
);

CREATE INDEX idx_judgment_requests_status ON judgment_requests(status);
CREATE INDEX idx_judgment_requests_agent ON judgment_requests(agent_id);
CREATE INDEX idx_judgment_requests_created ON judgment_requests(created_at DESC);

COMMENT ON TABLE judgment_requests IS '判断请求表';

-- 17. 环境感知状态表
CREATE TABLE IF NOT EXISTS environment_perception (
    id SERIAL PRIMARY KEY,
    qps DECIMAL(10, 2) DEFAULT 0,
    error_rate DECIMAL(5, 4) DEFAULT 0,
    latency DECIMAL(10, 2) DEFAULT 0,
    active_agents INTEGER DEFAULT 0,
    task_queue_size INTEGER DEFAULT 0,
    memory_usage DECIMAL(5, 2) DEFAULT 0,
    cpu_usage DECIMAL(5, 2) DEFAULT 0,
    timestamp TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_environment_perception_timestamp ON environment_perception(timestamp DESC);

COMMENT ON TABLE environment_perception IS '环境感知状态表';

-- 18. 伦理对齐评分表
CREATE TABLE IF NOT EXISTS ethical_alignment_scores (
    id SERIAL PRIMARY KEY,
    agent_id VARCHAR(100) NOT NULL,
    fairness_score DECIMAL(5, 4) DEFAULT 1.0,
    transparency_score DECIMAL(5, 4) DEFAULT 1.0,
    privacy_score DECIMAL(5, 4) DEFAULT 1.0,
    non_discrimination_score DECIMAL(5, 4) DEFAULT 1.0,
    total_score DECIMAL(5, 4) DEFAULT 1.0,
    timestamp TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_ethical_alignment_agent ON ethical_alignment_scores(agent_id);
CREATE INDEX idx_ethical_alignment_timestamp ON ethical_alignment_scores(timestamp DESC);

COMMENT ON TABLE ethical_alignment_scores IS '伦理对齐评分表';

-- 19. 选择历史表
CREATE TABLE IF NOT EXISTS selection_history (
    id SERIAL PRIMARY KEY,
    selection_id VARCHAR(100) UNIQUE NOT NULL,
    survivors TEXT[],
    eliminated TEXT[],
    elite TEXT[],
    timestamp TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_selection_history_timestamp ON selection_history(timestamp DESC);

COMMENT ON TABLE selection_history IS '选择历史表';

-- 20. 黑板缓存表
CREATE TABLE IF NOT EXISTS blackboard_cache (
    id SERIAL PRIMARY KEY,
    key VARCHAR(255) UNIQUE NOT NULL,
    value JSONB NOT NULL,
    ttl INTEGER DEFAULT 3600,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    expires_at TIMESTAMP WITH TIME ZONE
);

CREATE INDEX idx_blackboard_cache_key ON blackboard_cache(key);
CREATE INDEX idx_blackboard_cache_expires ON blackboard_cache(expires_at);

COMMENT ON TABLE blackboard_cache IS '黑板缓存表';

-- 插入初始全局目标
INSERT INTO global_goals (goal_name, target_value, weight, description, is_lower_better)
VALUES 
    ('defense_success_rate', 0.98, 1.0, '防御成功率应高于98%', FALSE),
    ('response_time', 5.0, 0.8, '平均响应时间应低于5ms', TRUE),
    ('false_positive_rate', 0.01, 0.6, '误报率应低于1%', TRUE),
    ('throughput', 1000.0, 0.7, '吞吐量应高于1000 QPS', FALSE)
ON CONFLICT (goal_name) DO NOTHING;

-- 插入初始安全围栏状态
INSERT INTO safety_fence_status (emergency_stop_active)
VALUES (FALSE)
ON CONFLICT DO NOTHING;

-- 创建视图：活跃智能体概览
CREATE OR REPLACE VIEW v_active_agents AS
SELECT 
    g.agent_id,
    g.generation,
    g.fitness_score,
    e.energy,
    e.total_earned,
    g.created_at
FROM agent_genomes g
LEFT JOIN agent_energy e ON g.agent_id = e.agent_id
ORDER BY g.fitness_score DESC;

COMMENT ON VIEW v_active_agents IS '活跃智能体概览视图';

-- 创建视图：任务统计
CREATE OR REPLACE VIEW v_task_statistics AS
SELECT 
    task_type,
    COUNT(*) as total_tasks,
    SUM(CASE WHEN status = 'completed' THEN 1 ELSE 0 END) as completed_tasks,
    SUM(CASE WHEN status = 'failed' THEN 1 ELSE 0 END) as failed_tasks,
    AVG(reward) as avg_reward,
    AVG(EXTRACT(EPOCH FROM (completed_at - created_at))) as avg_completion_time_seconds
FROM living_tasks
GROUP BY task_type;

COMMENT ON VIEW v_task_statistics IS '任务统计视图';

-- 创建视图：交互网络概览
CREATE OR REPLACE VIEW v_interaction_network AS
SELECT 
    from_agent,
    COUNT(*) as connections,
    SUM(weight) as total_weight
FROM interaction_edges
GROUP BY from_agent
ORDER BY total_weight DESC;

COMMENT ON VIEW v_interaction_network IS '交互网络概览视图';

-- 创建函数：清理过期黑板缓存
CREATE OR REPLACE FUNCTION cleanup_blackboard_cache()
RETURNS INTEGER AS $$
DECLARE
    deleted_count INTEGER;
BEGIN
    DELETE FROM blackboard_cache
    WHERE expires_at < CURRENT_TIMESTAMP;
    
    GET DIAGNOSTICS deleted_count = ROW_COUNT;
    
    RETURN deleted_count;
END;
$$ LANGUAGE plpgsql;

COMMENT ON FUNCTION cleanup_blackboard_cache IS '清理过期黑板缓存函数';

-- 创建函数：更新智能体能量
CREATE OR REPLACE FUNCTION update_agent_energy(
    p_agent_id VARCHAR(100),
    p_delta DECIMAL(10, 4)
)
RETURNS VOID AS $$
BEGIN
    INSERT INTO agent_energy (agent_id, energy, total_earned, total_spent, last_updated)
    VALUES (p_agent_id, 50.0 + p_delta, GREATEST(p_delta, 0), GREATEST(-p_delta, 0), CURRENT_TIMESTAMP)
    ON CONFLICT (agent_id) DO UPDATE SET
        energy = GREATEST(0, agent_energy.energy + p_delta),
        total_earned = agent_energy.total_earned + GREATEST(p_delta, 0),
        total_spent = agent_energy.total_spent + GREATEST(-p_delta, 0),
        last_updated = CURRENT_TIMESTAMP;
END;
$$ LANGUAGE plpgsql;

COMMENT ON FUNCTION update_agent_energy IS '更新智能体能量函数';

-- 创建函数：记录涌现模式
CREATE OR REPLACE FUNCTION record_emergence_pattern(
    p_pattern_id VARCHAR(100),
    p_pattern_type VARCHAR(50),
    p_pattern_data JSONB
)
RETURNS VOID AS $$
BEGIN
    INSERT INTO emergence_patterns (pattern_id, pattern_type, pattern_data, first_detected, last_detected, occurrence_count)
    VALUES (p_pattern_id, p_pattern_type, p_pattern_data, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP, 1)
    ON CONFLICT (pattern_id) DO UPDATE SET
        last_detected = CURRENT_TIMESTAMP,
        occurrence_count = emergence_patterns.occurrence_count + 1;
END;
$$ LANGUAGE plpgsql;

COMMENT ON FUNCTION record_emergence_pattern IS '记录涌现模式函数';

-- 创建触发器：自动设置黑板缓存过期时间
CREATE OR REPLACE FUNCTION set_blackboard_expiry()
RETURNS TRIGGER AS $$
BEGIN
    IF NEW.ttl > 0 AND NEW.expires_at IS NULL THEN
        NEW.expires_at = CURRENT_TIMESTAMP + (NEW.ttl || ' seconds')::INTERVAL;
    END IF;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER tr_blackboard_cache_expiry
BEFORE INSERT OR UPDATE ON blackboard_cache
FOR EACH ROW EXECUTE FUNCTION set_blackboard_expiry();

-- 授权
GRANT SELECT, INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA public TO fangdudu_user;
GRANT USAGE, SELECT ON ALL SEQUENCES IN SCHEMA public TO fangdudu_user;
GRANT EXECUTE ON ALL FUNCTIONS IN SCHEMA public TO fangdudu_user;
