-- 活体智能体生态系统数据库迁移
-- Migration: 130_create_ecosystem_tables.sql
-- Description: 创建活体智能体生态系统相关表

-- 1. 活体智能体注册表
CREATE TABLE IF NOT EXISTS living_agents_registry (
    id SERIAL PRIMARY KEY,
    agent_id VARCHAR(100) UNIQUE NOT NULL,
    agent_type VARCHAR(20) NOT NULL,
    species VARCHAR(50) DEFAULT 'default',
    generation INTEGER DEFAULT 0,
    parent_ids TEXT[],
    children_ids TEXT[],
    energy DECIMAL(10, 4) DEFAULT 100.0,
    max_energy DECIMAL(10, 4) DEFAULT 300.0,
    age INTEGER DEFAULT 0,
    max_age INTEGER DEFAULT 1000,
    status VARCHAR(20) DEFAULT 'idle',
    gene_pool JSONB DEFAULT '{}',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    died_at TIMESTAMP WITH TIME ZONE,
    
    CONSTRAINT chk_agent_type CHECK (agent_type IN ('attack', 'defense', 'memory', 'observer')),
    CONSTRAINT chk_agent_status CHECK (status IN ('idle', 'working', 'resting', 'reproducing', 'dying', 'dead'))
);

CREATE INDEX idx_living_agents_type ON living_agents_registry(agent_type);
CREATE INDEX idx_living_agents_status ON living_agents_registry(status);
CREATE INDEX idx_living_agents_energy ON living_agents_registry(energy DESC);
CREATE INDEX idx_living_agents_generation ON living_agents_registry(generation);
CREATE INDEX idx_living_agents_created ON living_agents_registry(created_at DESC);

COMMENT ON TABLE living_agents_registry IS '活体智能体注册表';

-- 2. 智能体统计表
CREATE TABLE IF NOT EXISTS agent_statistics (
    id SERIAL PRIMARY KEY,
    agent_id VARCHAR(100) NOT NULL,
    tasks_completed INTEGER DEFAULT 0,
    tasks_failed INTEGER DEFAULT 0,
    success_count INTEGER DEFAULT 0,
    failure_count INTEGER DEFAULT 0,
    energy_earned DECIMAL(10, 4) DEFAULT 0,
    energy_spent DECIMAL(10, 4) DEFAULT 0,
    reproductions INTEGER DEFAULT 0,
    mutations INTEGER DEFAULT 0,
    last_updated TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    
    CONSTRAINT uk_agent_stats UNIQUE (agent_id)
);

CREATE INDEX idx_agent_stats_agent ON agent_statistics(agent_id);

COMMENT ON TABLE agent_statistics IS '智能体统计表';

-- 3. 攻击智能体状态表
CREATE TABLE IF NOT EXISTS attack_agents_state (
    id SERIAL PRIMARY KEY,
    agent_id VARCHAR(100) UNIQUE NOT NULL,
    attack_capability DECIMAL(5, 4) DEFAULT 0.5,
    stealth_level DECIMAL(5, 4) DEFAULT 0.5,
    strategy_library JSONB DEFAULT '{}',
    active_attacks JSONB DEFAULT '{}',
    alliance_ids TEXT[],
    alliance_leader VARCHAR(100),
    alliance_role VARCHAR(20),
    target_preferences JSONB DEFAULT '{}',
    defense_knowledge JSONB DEFAULT '{}',
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_attack_agents_alliance ON attack_agents_state(alliance_leader);

COMMENT ON TABLE attack_agents_state IS '攻击智能体状态表';

-- 4. 防御智能体状态表
CREATE TABLE IF NOT EXISTS defense_agents_state (
    id SERIAL PRIMARY KEY,
    agent_id VARCHAR(100) UNIQUE NOT NULL,
    defense_capability DECIMAL(5, 4) DEFAULT 0.5,
    detection_accuracy DECIMAL(5, 4) DEFAULT 0.5,
    defense_strategies JSONB DEFAULT '{}',
    active_defenses JSONB DEFAULT '{}',
    team_ids TEXT[],
    team_leader VARCHAR(100),
    team_role VARCHAR(20),
    responsibility_zone VARCHAR(100),
    known_attack_patterns JSONB DEFAULT '{}',
    attack_predictions JSONB DEFAULT '[]',
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_defense_agents_team ON defense_agents_state(team_leader);

COMMENT ON TABLE defense_agents_state IS '防御智能体状态表';

-- 5. 记忆智能体状态表
CREATE TABLE IF NOT EXISTS memory_agents_state (
    id SERIAL PRIMARY KEY,
    agent_id VARCHAR(100) UNIQUE NOT NULL,
    memory_capacity INTEGER DEFAULT 10000,
    memory_count INTEGER DEFAULT 0,
    retrieval_accuracy DECIMAL(5, 4) DEFAULT 0.8,
    memory_index JSONB DEFAULT '{}',
    tag_index JSONB DEFAULT '{}',
    association_count INTEGER DEFAULT 0,
    predictions JSONB DEFAULT '[]',
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

COMMENT ON TABLE memory_agents_state IS '记忆智能体状态表';

-- 6. 记忆存储表
CREATE TABLE IF NOT EXISTS memory_entries (
    id SERIAL PRIMARY KEY,
    memory_id VARCHAR(100) UNIQUE NOT NULL,
    agent_id VARCHAR(100) NOT NULL,
    memory_type VARCHAR(20) NOT NULL,
    content JSONB NOT NULL,
    importance DECIMAL(5, 4) DEFAULT 0.5,
    access_count INTEGER DEFAULT 0,
    last_accessed TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    expires_at TIMESTAMP WITH TIME ZONE,
    tags TEXT[],
    associations TEXT[],
    
    CONSTRAINT chk_memory_type CHECK (memory_type IN ('episodic', 'semantic', 'procedural', 'collective'))
);

CREATE INDEX idx_memory_entries_agent ON memory_entries(agent_id);
CREATE INDEX idx_memory_entries_type ON memory_entries(memory_type);
CREATE INDEX idx_memory_entries_importance ON memory_entries(importance DESC);
CREATE INDEX idx_memory_entries_created ON memory_entries(created_at DESC);
CREATE INDEX idx_memory_entries_expires ON memory_entries(expires_at);

COMMENT ON TABLE memory_entries IS '记忆存储表';

-- 7. 记忆关联图
CREATE TABLE IF NOT EXISTS memory_associations (
    id SERIAL PRIMARY KEY,
    memory_id_1 VARCHAR(100) NOT NULL,
    memory_id_2 VARCHAR(100) NOT NULL,
    association_strength DECIMAL(5, 4) DEFAULT 0.5,
    association_type VARCHAR(50),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    
    CONSTRAINT uk_memory_association UNIQUE (memory_id_1, memory_id_2)
);

CREATE INDEX idx_memory_assoc_m1 ON memory_associations(memory_id_1);
CREATE INDEX idx_memory_assoc_m2 ON memory_associations(memory_id_2);

COMMENT ON TABLE memory_associations IS '记忆关联图表';

-- 8. 攻击历史表
CREATE TABLE IF NOT EXISTS attack_history (
    id SERIAL PRIMARY KEY,
    attack_id VARCHAR(100) UNIQUE NOT NULL,
    agent_id VARCHAR(100) NOT NULL,
    target_id VARCHAR(100),
    strategy VARCHAR(50),
    success BOOLEAN DEFAULT FALSE,
    detected BOOLEAN DEFAULT FALSE,
    energy_cost DECIMAL(10, 4),
    success_rate DECIMAL(5, 4),
    timestamp TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_attack_history_agent ON attack_history(agent_id);
CREATE INDEX idx_attack_history_target ON attack_history(target_id);
CREATE INDEX idx_attack_history_timestamp ON attack_history(timestamp DESC);

COMMENT ON TABLE attack_history IS '攻击历史表';

-- 9. 防御历史表
CREATE TABLE IF NOT EXISTS defense_history (
    id SERIAL PRIMARY KEY,
    defense_id VARCHAR(100) UNIQUE NOT NULL,
    agent_id VARCHAR(100) NOT NULL,
    threat_id VARCHAR(100),
    strategy VARCHAR(50),
    success BOOLEAN DEFAULT FALSE,
    false_positive BOOLEAN DEFAULT FALSE,
    energy_cost DECIMAL(10, 4),
    effectiveness DECIMAL(5, 4),
    response_time DECIMAL(10, 4),
    timestamp TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_defense_history_agent ON defense_history(agent_id);
CREATE INDEX idx_defense_history_threat ON defense_history(threat_id);
CREATE INDEX idx_defense_history_timestamp ON defense_history(timestamp DESC);

COMMENT ON TABLE defense_history IS '防御历史表';

-- 10. 智能体联盟表
CREATE TABLE IF NOT EXISTS agent_alliances (
    id SERIAL PRIMARY KEY,
    alliance_id VARCHAR(100) UNIQUE NOT NULL,
    leader_id VARCHAR(100) NOT NULL,
    member_ids TEXT[] NOT NULL,
    target_id VARCHAR(100),
    status VARCHAR(20) DEFAULT 'active',
    total_energy DECIMAL(10, 4) DEFAULT 0,
    success_count INTEGER DEFAULT 0,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    dissolved_at TIMESTAMP WITH TIME ZONE,
    
    CONSTRAINT chk_alliance_status CHECK (status IN ('forming', 'active', 'dissolved'))
);

CREATE INDEX idx_agent_alliances_leader ON agent_alliances(leader_id);
CREATE INDEX idx_agent_alliances_status ON agent_alliances(status);

COMMENT ON TABLE agent_alliances IS '智能体联盟表';

-- 11. 防御团队表
CREATE TABLE IF NOT EXISTS defense_teams (
    id SERIAL PRIMARY KEY,
    team_id VARCHAR(100) UNIQUE NOT NULL,
    leader_id VARCHAR(100) NOT NULL,
    member_ids TEXT[] NOT NULL,
    threat_type VARCHAR(50),
    status VARCHAR(20) DEFAULT 'active',
    total_defense_power DECIMAL(10, 4) DEFAULT 0,
    success_count INTEGER DEFAULT 0,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    dissolved_at TIMESTAMP WITH TIME ZONE,
    
    CONSTRAINT chk_team_status CHECK (status IN ('forming', 'active', 'dissolved'))
);

CREATE INDEX idx_defense_teams_leader ON defense_teams(leader_id);
CREATE INDEX idx_defense_teams_status ON defense_teams(status);

COMMENT ON TABLE defense_teams IS '防御团队表';

-- 12. 进化事件表
CREATE TABLE IF NOT EXISTS evolution_events (
    id SERIAL PRIMARY KEY,
    event_type VARCHAR(50) NOT NULL,
    subject VARCHAR(100),
    category VARCHAR(20),
    generation INTEGER,
    details JSONB DEFAULT '{}',
    timestamp TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    
    CONSTRAINT chk_evolution_category CHECK (category IN ('attack', 'defense', 'memory', 'system'))
);

CREATE INDEX idx_evolution_events_type ON evolution_events(event_type);
CREATE INDEX idx_evolution_events_category ON evolution_events(category);
CREATE INDEX idx_evolution_events_timestamp ON evolution_events(timestamp DESC);

COMMENT ON TABLE evolution_events IS '进化事件表';

-- 13. 涌现模式表
CREATE TABLE IF NOT EXISTS emergence_patterns (
    id SERIAL PRIMARY KEY,
    pattern_id VARCHAR(100) UNIQUE NOT NULL,
    pattern_type VARCHAR(50) NOT NULL,
    pattern_data JSONB NOT NULL,
    first_detected TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    last_detected TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    occurrence_count INTEGER DEFAULT 1,
    significance_score DECIMAL(5, 4) DEFAULT 0.5
);

CREATE INDEX idx_emergence_patterns_type ON emergence_patterns(pattern_type);
CREATE INDEX idx_emergence_patterns_occurrence ON emergence_patterns(occurrence_count DESC);

COMMENT ON TABLE emergence_patterns IS '涌现模式表';

-- 14. 生态系统指标历史表
CREATE TABLE IF NOT EXISTS ecosystem_metrics_history (
    id SERIAL PRIMARY KEY,
    total_agents INTEGER DEFAULT 0,
    attack_agents INTEGER DEFAULT 0,
    defense_agents INTEGER DEFAULT 0,
    memory_agents INTEGER DEFAULT 0,
    total_energy DECIMAL(10, 4) DEFAULT 0,
    avg_energy DECIMAL(10, 4) DEFAULT 0,
    attack_success_rate DECIMAL(5, 4) DEFAULT 0,
    defense_success_rate DECIMAL(5, 4) DEFAULT 0,
    reproduction_rate DECIMAL(5, 4) DEFAULT 0,
    death_rate DECIMAL(5, 4) DEFAULT 0,
    diversity_index DECIMAL(5, 4) DEFAULT 0,
    emergence_events INTEGER DEFAULT 0,
    ecosystem_state VARCHAR(20) DEFAULT 'stable',
    timestamp TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    
    CONSTRAINT chk_ecosystem_state CHECK (ecosystem_state IN ('stable', 'stressed', 'under_attack', 'recovering', 'evolving'))
);

CREATE INDEX idx_ecosystem_metrics_timestamp ON ecosystem_metrics_history(timestamp DESC);

COMMENT ON TABLE ecosystem_metrics_history IS '生态系统指标历史表';

-- 15. 智能体经验回放缓冲区
CREATE TABLE IF NOT EXISTS agent_experience_buffer (
    id SERIAL PRIMARY KEY,
    agent_id VARCHAR(100) NOT NULL,
    experience_type VARCHAR(50) NOT NULL,
    experience_data JSONB NOT NULL,
    energy DECIMAL(10, 4),
    age INTEGER,
    timestamp TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_experience_buffer_agent ON agent_experience_buffer(agent_id);
CREATE INDEX idx_experience_buffer_timestamp ON agent_experience_buffer(timestamp DESC);

COMMENT ON TABLE agent_experience_buffer IS '智能体经验回放缓冲区';

-- 16. 基因库表
CREATE TABLE IF NOT EXISTS gene_pool_history (
    id SERIAL PRIMARY KEY,
    agent_id VARCHAR(100) NOT NULL,
    generation INTEGER,
    gene_name VARCHAR(50) NOT NULL,
    gene_value DECIMAL(10, 6),
    mutation_rate DECIMAL(5, 4),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_gene_pool_agent ON gene_pool_history(agent_id);
CREATE INDEX idx_gene_pool_gene ON gene_pool_history(gene_name);

COMMENT ON TABLE gene_pool_history IS '基因库历史表';

-- 17. 攻防交互表
CREATE TABLE IF NOT EXISTS attack_defense_interactions (
    id SERIAL PRIMARY KEY,
    interaction_id VARCHAR(100) UNIQUE NOT NULL,
    attack_agent_id VARCHAR(100) NOT NULL,
    defense_agent_id VARCHAR(100) NOT NULL,
    attack_strategy VARCHAR(50),
    defense_strategy VARCHAR(50),
    attack_success BOOLEAN,
    defense_success BOOLEAN,
    energy_transferred DECIMAL(10, 4) DEFAULT 0,
    timestamp TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_interactions_attack ON attack_defense_interactions(attack_agent_id);
CREATE INDEX idx_interactions_defense ON attack_defense_interactions(defense_agent_id);
CREATE INDEX idx_interactions_timestamp ON attack_defense_interactions(timestamp DESC);

COMMENT ON TABLE attack_defense_interactions IS '攻防交互表';

-- 18. 智能体族谱表
CREATE TABLE IF NOT EXISTS agent_family_tree (
    id SERIAL PRIMARY KEY,
    agent_id VARCHAR(100) NOT NULL,
    parent_id VARCHAR(100),
    grandparent_ids TEXT[],
    generation INTEGER DEFAULT 0,
    species VARCHAR(50),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_family_tree_agent ON agent_family_tree(agent_id);
CREATE INDEX idx_family_tree_parent ON agent_family_tree(parent_id);

COMMENT ON TABLE agent_family_tree IS '智能体族谱表';

-- 创建视图：活跃智能体概览
CREATE OR REPLACE VIEW v_active_agents_overview AS
SELECT 
    r.agent_id,
    r.agent_type,
    r.species,
    r.generation,
    r.energy,
    r.age,
    r.status,
    s.tasks_completed,
    s.tasks_failed,
    s.success_count,
    s.failure_count,
    r.created_at
FROM living_agents_registry r
LEFT JOIN agent_statistics s ON r.agent_id = s.agent_id
WHERE r.status != 'dead'
ORDER BY r.energy DESC;

COMMENT ON VIEW v_active_agents_overview IS '活跃智能体概览视图';

-- 创建视图：生态系统健康状态
CREATE OR REPLACE VIEW v_ecosystem_health AS
SELECT 
    timestamp,
    ecosystem_state,
    total_agents,
    avg_energy,
    attack_success_rate,
    defense_success_rate,
    diversity_index,
    (attack_success_rate + defense_success_rate) / 2 as balance_score
FROM ecosystem_metrics_history
ORDER BY timestamp DESC
LIMIT 100;

COMMENT ON VIEW v_ecosystem_health IS '生态系统健康状态视图';

-- 创建函数：计算智能体适应度
CREATE OR REPLACE FUNCTION calculate_agent_fitness(p_agent_id VARCHAR(100))
RETURNS DECIMAL(10, 6) AS $$
DECLARE
    v_success_rate DECIMAL(5, 4);
    v_energy_factor DECIMAL(5, 4);
    v_age_factor DECIMAL(5, 4);
    v_reproduction_factor DECIMAL(5, 4);
    v_fitness DECIMAL(10, 6);
BEGIN
    SELECT 
        CASE WHEN (success_count + failure_count) > 0 
            THEN success_count::DECIMAL / (success_count + failure_count)
            ELSE 0.5 END,
        energy / 100.0,
        1 - (age::DECIMAL / max_age),
        LEAST(1.0, jsonb_array_length(children_ids)::DECIMAL / 5)
    INTO v_success_rate, v_energy_factor, v_age_factor, v_reproduction_factor
    FROM living_agents_registry r
    LEFT JOIN agent_statistics s ON r.agent_id = s.agent_id
    WHERE r.agent_id = p_agent_id;
    
    v_fitness := COALESCE(v_success_rate, 0.5) * 0.4 +
                 COALESCE(v_energy_factor, 0.5) * 0.2 +
                 COALESCE(v_age_factor, 0.5) * 0.2 +
                 COALESCE(v_reproduction_factor, 0) * 0.2;
    
    RETURN v_fitness;
END;
$$ LANGUAGE plpgsql;

COMMENT ON FUNCTION calculate_agent_fitness IS '计算智能体适应度函数';

-- 创建函数：清理死亡智能体
CREATE OR REPLACE FUNCTION cleanup_dead_agents()
RETURNS INTEGER AS $$
DECLARE
    deleted_count INTEGER;
BEGIN
    DELETE FROM living_agents_registry
    WHERE status = 'dead'
    AND died_at < CURRENT_TIMESTAMP - INTERVAL '7 days';
    
    GET DIAGNOSTICS deleted_count = ROW_COUNT;
    
    RETURN deleted_count;
END;
$$ LANGUAGE plpgsql;

COMMENT ON FUNCTION cleanup_dead_agents IS '清理死亡智能体函数';

-- 创建函数：记录进化事件
CREATE OR REPLACE FUNCTION record_evolution_event(
    p_event_type VARCHAR(50),
    p_subject VARCHAR(100),
    p_category VARCHAR(20),
    p_generation INTEGER,
    p_details JSONB
)
RETURNS VOID AS $$
BEGIN
    INSERT INTO evolution_events (event_type, subject, category, generation, details)
    VALUES (p_event_type, p_subject, p_category, p_generation, p_details);
END;
$$ LANGUAGE plpgsql;

COMMENT ON FUNCTION record_evolution_event IS '记录进化事件函数';

-- 创建触发器：自动更新统计时间
CREATE OR REPLACE FUNCTION update_agent_stats_timestamp()
RETURNS TRIGGER AS $$
BEGIN
    NEW.last_updated = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER tr_agent_stats_timestamp
BEFORE UPDATE ON agent_statistics
FOR EACH ROW EXECUTE FUNCTION update_agent_stats_timestamp();

-- 插入初始生态系统状态
INSERT INTO ecosystem_metrics_history (
    total_agents, attack_agents, defense_agents, memory_agents,
    ecosystem_state
)
VALUES (0, 0, 0, 0, 'stable')
ON CONFLICT DO NOTHING;

-- 授权
GRANT SELECT, INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA public TO fangdudu_user;
GRANT USAGE, SELECT ON ALL SEQUENCES IN SCHEMA public TO fangdudu_user;
GRANT EXECUTE ON ALL FUNCTIONS IN SCHEMA public TO fangdudu_user;
