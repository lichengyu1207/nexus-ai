-- 三省六部制智能体自我进化系统数据库迁移
-- Migration: 110_create_evolution_tables.sql
-- Description: 创建智能体进化系统相关表

-- 1. 智能体版本管理表
CREATE TABLE IF NOT EXISTS agent_versions (
    id SERIAL PRIMARY KEY,
    version_id VARCHAR(100) UNIQUE NOT NULL,
    agent_type VARCHAR(50) NOT NULL,
    version VARCHAR(50) NOT NULL,
    model_path VARCHAR(500) NOT NULL,
    metrics JSONB DEFAULT '{}',
    checksum VARCHAR(64),
    is_active BOOLEAN DEFAULT FALSE,
    is_staging BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    deployed_at TIMESTAMP WITH TIME ZONE,
    
    CONSTRAINT uk_agent_version UNIQUE (agent_type, version)
);

CREATE INDEX idx_agent_versions_agent_type ON agent_versions(agent_type);
CREATE INDEX idx_agent_versions_is_active ON agent_versions(is_active);
CREATE INDEX idx_agent_versions_created_at ON agent_versions(created_at DESC);

COMMENT ON TABLE agent_versions IS '智能体版本管理表';

-- 2. 进化建议表
CREATE TABLE IF NOT EXISTS evolution_suggestions (
    id SERIAL PRIMARY KEY,
    suggestion_id VARCHAR(100) UNIQUE NOT NULL,
    agent_id VARCHAR(100) NOT NULL,
    agent_type VARCHAR(50) NOT NULL,
    category VARCHAR(50) NOT NULL,
    suggestion_text TEXT NOT NULL,
    anomaly_score DECIMAL(10, 4) DEFAULT 0,
    metrics JSONB DEFAULT '{}',
    status VARCHAR(20) DEFAULT 'pending',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    processed_at TIMESTAMP WITH TIME ZONE,
    processed_by VARCHAR(100),
    rejection_reason TEXT,
    
    CONSTRAINT chk_suggestion_status CHECK (status IN ('pending', 'accepted', 'rejected', 'applied'))
);

CREATE INDEX idx_evolution_suggestions_status ON evolution_suggestions(status);
CREATE INDEX idx_evolution_suggestions_agent_id ON evolution_suggestions(agent_id);
CREATE INDEX idx_evolution_suggestions_agent_type ON evolution_suggestions(agent_type);
CREATE INDEX idx_evolution_suggestions_created_at ON evolution_suggestions(created_at DESC);
CREATE INDEX idx_evolution_suggestions_category ON evolution_suggestions(category);

COMMENT ON TABLE evolution_suggestions IS '进化建议表';

-- 3. 诊断历史表
CREATE TABLE IF NOT EXISTS diagnosis_history (
    id SERIAL PRIMARY KEY,
    agent_id VARCHAR(100) NOT NULL,
    agent_type VARCHAR(50) NOT NULL,
    is_anomaly BOOLEAN DEFAULT FALSE,
    anomaly_score DECIMAL(10, 4) DEFAULT 0,
    attribution VARCHAR(50),
    suggestion TEXT,
    metrics JSONB DEFAULT '{}',
    trajectory_size INTEGER DEFAULT 0,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    
    CONSTRAINT chk_attribution CHECK (attribution IN ('data_drift', 'model_decay', 'env_change', 'other') OR attribution IS NULL)
);

CREATE INDEX idx_diagnosis_history_agent_id ON diagnosis_history(agent_id);
CREATE INDEX idx_diagnosis_history_is_anomaly ON diagnosis_history(is_anomaly);
CREATE INDEX idx_diagnosis_history_created_at ON diagnosis_history(created_at DESC);
CREATE INDEX idx_diagnosis_history_attribution ON diagnosis_history(attribution);

COMMENT ON TABLE diagnosis_history IS '诊断历史表';

-- 4. 进化事件日志表
CREATE TABLE IF NOT EXISTS evolution_events (
    id SERIAL PRIMARY KEY,
    event_type VARCHAR(50) NOT NULL,
    event_data JSONB DEFAULT '{}',
    agent_id VARCHAR(100),
    version_id VARCHAR(100),
    user_id VARCHAR(100),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_evolution_events_event_type ON evolution_events(event_type);
CREATE INDEX idx_evolution_events_agent_id ON evolution_events(agent_id);
CREATE INDEX idx_evolution_events_created_at ON evolution_events(created_at DESC);

COMMENT ON TABLE evolution_events IS '进化事件日志表';

-- 5. 智能体轨迹记录表
CREATE TABLE IF NOT EXISTS agent_trajectories (
    id SERIAL PRIMARY KEY,
    agent_id VARCHAR(100) NOT NULL,
    agent_type VARCHAR(50) NOT NULL,
    state JSONB NOT NULL,
    action INTEGER NOT NULL,
    reward DECIMAL(10, 6) DEFAULT 0,
    next_state JSONB,
    metadata JSONB DEFAULT '{}',
    session_id VARCHAR(100),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_agent_trajectories_agent_id ON agent_trajectories(agent_id);
CREATE INDEX idx_agent_trajectories_agent_type ON agent_trajectories(agent_type);
CREATE INDEX idx_agent_trajectories_created_at ON agent_trajectories(created_at DESC);
CREATE INDEX idx_agent_trajectories_session_id ON agent_trajectories(session_id);

COMMENT ON TABLE agent_trajectories IS '智能体轨迹记录表';

-- 6. 情景记忆表
CREATE TABLE IF NOT EXISTS episodic_memories (
    id SERIAL PRIMARY KEY,
    memory_id VARCHAR(100) UNIQUE NOT NULL,
    user_id VARCHAR(100) NOT NULL,
    session_id VARCHAR(100),
    interaction_type VARCHAR(50) NOT NULL,
    content JSONB NOT NULL,
    embedding VECTOR(64),
    importance_score DECIMAL(5, 4) DEFAULT 0.5,
    access_count INTEGER DEFAULT 0,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    last_accessed TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_episodic_memories_user_id ON episodic_memories(user_id);
CREATE INDEX idx_episodic_memories_session_id ON episodic_memories(session_id);
CREATE INDEX idx_episodic_memories_interaction_type ON episodic_memories(interaction_type);
CREATE INDEX idx_episodic_memories_created_at ON episodic_memories(created_at DESC);

COMMENT ON TABLE episodic_memories IS '情景记忆表';

-- 7. 语义记忆表（知识图谱）
CREATE TABLE IF NOT EXISTS semantic_memories (
    id SERIAL PRIMARY KEY,
    memory_id VARCHAR(100) UNIQUE NOT NULL,
    entity_type VARCHAR(50) NOT NULL,
    entity_id VARCHAR(100) NOT NULL,
    knowledge JSONB NOT NULL,
    embedding VECTOR(64),
    relations JSONB DEFAULT '[]',
    importance_score DECIMAL(5, 4) DEFAULT 0.5,
    access_count INTEGER DEFAULT 0,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    last_accessed TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    last_updated TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    
    CONSTRAINT uk_entity UNIQUE (entity_type, entity_id)
);

CREATE INDEX idx_semantic_memories_entity_type ON semantic_memories(entity_type);
CREATE INDEX idx_semantic_memories_entity_id ON semantic_memories(entity_id);
CREATE INDEX idx_semantic_memories_created_at ON semantic_memories(created_at DESC);
CREATE INDEX idx_semantic_memories_last_updated ON semantic_memories(last_updated DESC);

COMMENT ON TABLE semantic_memories IS '语义记忆表';

-- 8. 程序性记忆表（技能库）
CREATE TABLE IF NOT EXISTS procedural_memories (
    id SERIAL PRIMARY KEY,
    memory_id VARCHAR(100) UNIQUE NOT NULL,
    skill_name VARCHAR(100) NOT NULL,
    skill_type VARCHAR(50) NOT NULL,
    parameters JSONB DEFAULT '{}',
    success_conditions JSONB DEFAULT '[]',
    execution_steps JSONB DEFAULT '[]',
    embedding VECTOR(64),
    success_rate DECIMAL(5, 4) DEFAULT 0,
    execution_count INTEGER DEFAULT 0,
    importance_score DECIMAL(5, 4) DEFAULT 0.5,
    access_count INTEGER DEFAULT 0,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    last_accessed TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    
    CONSTRAINT uk_skill_name UNIQUE (skill_name)
);

CREATE INDEX idx_procedural_memories_skill_type ON procedural_memories(skill_type);
CREATE INDEX idx_procedural_memories_success_rate ON procedural_memories(success_rate);
CREATE INDEX idx_procedural_memories_created_at ON procedural_memories(created_at DESC);

COMMENT ON TABLE procedural_memories IS '程序性记忆表';

-- 9. 技能执行历史表
CREATE TABLE IF NOT EXISTS skill_execution_history (
    id SERIAL PRIMARY KEY,
    skill_name VARCHAR(100) NOT NULL,
    success BOOLEAN NOT NULL,
    duration_ms DECIMAL(10, 2),
    context JSONB DEFAULT '{}',
    error_message TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_skill_execution_history_skill_name ON skill_execution_history(skill_name);
CREATE INDEX idx_skill_execution_history_success ON skill_execution_history(success);
CREATE INDEX idx_skill_execution_history_created_at ON skill_execution_history(created_at DESC);

COMMENT ON TABLE skill_execution_history IS '技能执行历史表';

-- 10. A/B测试记录表
CREATE TABLE IF NOT EXISTS ab_tests (
    id SERIAL PRIMARY KEY,
    test_id VARCHAR(100) UNIQUE NOT NULL,
    agent_id VARCHAR(100) NOT NULL,
    control_version_id VARCHAR(100) NOT NULL,
    treatment_version_id VARCHAR(100) NOT NULL,
    test_ratio DECIMAL(5, 4) DEFAULT 0.01,
    status VARCHAR(20) DEFAULT 'running',
    control_samples INTEGER DEFAULT 0,
    treatment_samples INTEGER DEFAULT 0,
    control_mean DECIMAL(10, 6),
    control_std DECIMAL(10, 6),
    treatment_mean DECIMAL(10, 6),
    treatment_std DECIMAL(10, 6),
    t_statistic DECIMAL(10, 6),
    is_significant BOOLEAN DEFAULT FALSE,
    treatment_better BOOLEAN DEFAULT FALSE,
    should_switch BOOLEAN DEFAULT FALSE,
    started_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    completed_at TIMESTAMP WITH TIME ZONE,
    
    CONSTRAINT chk_ab_test_status CHECK (status IN ('running', 'completed', 'stopped'))
);

CREATE INDEX idx_ab_tests_agent_id ON ab_tests(agent_id);
CREATE INDEX idx_ab_tests_status ON ab_tests(status);
CREATE INDEX idx_ab_tests_started_at ON ab_tests(started_at DESC);

COMMENT ON TABLE ab_tests IS 'A/B测试记录表';

-- 11. 热更新状态表
CREATE TABLE IF NOT EXISTS hot_update_status (
    id SERIAL PRIMARY KEY,
    agent_id VARCHAR(100) UNIQUE NOT NULL,
    active_version_id VARCHAR(100),
    staging_version_id VARCHAR(100),
    has_staging BOOLEAN DEFAULT FALSE,
    health_metrics JSONB DEFAULT '[]',
    avg_health_metric DECIMAL(10, 6) DEFAULT 0,
    last_switch_at TIMESTAMP WITH TIME ZONE,
    last_rollback_at TIMESTAMP WITH TIME ZONE,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_hot_update_status_agent_id ON hot_update_status(agent_id);
CREATE INDEX idx_hot_update_status_has_staging ON hot_update_status(has_staging);

COMMENT ON TABLE hot_update_status IS '热更新状态表';

-- 12. 元认知状态表
CREATE TABLE IF NOT EXISTS meta_cognition_status (
    id SERIAL PRIMARY KEY,
    agent_id VARCHAR(100) UNIQUE NOT NULL,
    agent_name VARCHAR(100),
    trajectory_size INTEGER DEFAULT 0,
    reward_mean DECIMAL(10, 6) DEFAULT 0,
    reward_std DECIMAL(10, 6) DEFAULT 0,
    success_rate DECIMAL(5, 4) DEFAULT 0,
    avg_response_time DECIMAL(10, 2) DEFAULT 0,
    action_counts JSONB DEFAULT '{}',
    last_diagnosis_at TIMESTAMP WITH TIME ZONE,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_meta_cognition_status_agent_id ON meta_cognition_status(agent_id);
CREATE INDEX idx_meta_cognition_status_updated_at ON meta_cognition_status(updated_at DESC);

COMMENT ON TABLE meta_cognition_status IS '元认知状态表';

-- 13. 用户兴趣追踪表
CREATE TABLE IF NOT EXISTS user_interest_tracking (
    id SERIAL PRIMARY KEY,
    user_id VARCHAR(100) NOT NULL,
    interaction_type VARCHAR(50) NOT NULL,
    interaction_count INTEGER DEFAULT 0,
    last_interaction_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    
    CONSTRAINT uk_user_interest UNIQUE (user_id, interaction_type)
);

CREATE INDEX idx_user_interest_tracking_user_id ON user_interest_tracking(user_id);
CREATE INDEX idx_user_interest_tracking_interaction_type ON user_interest_tracking(interaction_type);

COMMENT ON TABLE user_interest_tracking IS '用户兴趣追踪表';

-- 14. 训练任务表
CREATE TABLE IF NOT EXISTS training_tasks (
    id SERIAL PRIMARY KEY,
    task_id VARCHAR(100) UNIQUE NOT NULL,
    agent_type VARCHAR(50) NOT NULL,
    status VARCHAR(20) DEFAULT 'pending',
    config JSONB DEFAULT '{}',
    training_samples INTEGER DEFAULT 0,
    validation_samples INTEGER DEFAULT 0,
    epochs_trained INTEGER DEFAULT 0,
    final_loss DECIMAL(10, 6),
    final_accuracy DECIMAL(5, 4),
    final_reward DECIMAL(10, 6),
    should_update BOOLEAN DEFAULT FALSE,
    started_at TIMESTAMP WITH TIME ZONE,
    completed_at TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    
    CONSTRAINT chk_training_status CHECK (status IN ('pending', 'running', 'completed', 'failed'))
);

CREATE INDEX idx_training_tasks_agent_type ON training_tasks(agent_type);
CREATE INDEX idx_training_tasks_status ON training_tasks(status);
CREATE INDEX idx_training_tasks_created_at ON training_tasks(created_at DESC);

COMMENT ON TABLE training_tasks IS '训练任务表';

-- 15. 训练历史表
CREATE TABLE IF NOT EXISTS training_history (
    id SERIAL PRIMARY KEY,
    task_id VARCHAR(100) NOT NULL,
    epoch INTEGER NOT NULL,
    train_loss DECIMAL(10, 6),
    train_accuracy DECIMAL(5, 4),
    val_loss DECIMAL(10, 6),
    val_accuracy DECIMAL(5, 4),
    val_reward DECIMAL(10, 6),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_training_history_task_id ON training_history(task_id);
CREATE INDEX idx_training_history_created_at ON training_history(created_at DESC);

COMMENT ON TABLE training_history IS '训练历史表';

-- 插入初始版本记录
INSERT INTO agent_versions (version_id, agent_type, version, model_path, metrics, is_active)
VALUES 
    ('attack_v1.0.0_init', 'attack', 'v1.0.0', 'models/attack_v1.0.0.pt', '{"accuracy": 0.75, "reward": 0.65}', TRUE),
    ('defense_v1.0.0_init', 'defense', 'v1.0.0', 'models/defense_v1.0.0.pt', '{"accuracy": 0.80, "reward": 0.70}', TRUE),
    ('valuation_v1.0.0_init', 'valuation', 'v1.0.0', 'models/valuation_v1.0.0.pt', '{"accuracy": 0.85, "reward": 0.75}', TRUE)
ON CONFLICT (version_id) DO NOTHING;

-- 创建视图：活跃版本概览
CREATE OR REPLACE VIEW v_active_versions AS
SELECT 
    agent_type,
    version_id,
    version,
    model_path,
    metrics,
    deployed_at,
    created_at
FROM agent_versions
WHERE is_active = TRUE
ORDER BY agent_type;

COMMENT ON VIEW v_active_versions IS '活跃版本概览视图';

-- 创建视图：待处理建议概览
CREATE OR REPLACE VIEW v_pending_suggestions AS
SELECT 
    suggestion_id,
    agent_id,
    agent_type,
    category,
    suggestion_text,
    anomaly_score,
    created_at
FROM evolution_suggestions
WHERE status = 'pending'
ORDER BY anomaly_score DESC, created_at DESC;

COMMENT ON VIEW v_pending_suggestions IS '待处理建议概览视图';

-- 创建视图：智能体健康状态
CREATE OR REPLACE VIEW v_agent_health AS
SELECT 
    m.agent_id,
    m.agent_name,
    m.trajectory_size,
    m.reward_mean,
    m.reward_std,
    m.success_rate,
    m.avg_response_time,
    m.updated_at,
    COUNT(d.id) as diagnosis_count,
    SUM(CASE WHEN d.is_anomaly THEN 1 ELSE 0 END) as anomaly_count
FROM meta_cognition_status m
LEFT JOIN diagnosis_history d ON m.agent_id = d.agent_id
GROUP BY m.agent_id, m.agent_name, m.trajectory_size, m.reward_mean, m.reward_std, 
         m.success_rate, m.avg_response_time, m.updated_at;

COMMENT ON VIEW v_agent_health IS '智能体健康状态视图';

-- 创建函数：清理过期轨迹
CREATE OR REPLACE FUNCTION cleanup_old_trajectories(days_to_keep INTEGER DEFAULT 30)
RETURNS INTEGER AS $$
DECLARE
    deleted_count INTEGER;
BEGIN
    DELETE FROM agent_trajectories
    WHERE created_at < CURRENT_TIMESTAMP - (days_to_keep || ' days')::INTERVAL;
    
    GET DIAGNOSTICS deleted_count = ROW_COUNT;
    
    RETURN deleted_count;
END;
$$ LANGUAGE plpgsql;

COMMENT ON FUNCTION cleanup_old_trajectories IS '清理过期轨迹函数';

-- 创建函数：更新智能体健康指标
CREATE OR REPLACE FUNCTION update_agent_health_metric(
    p_agent_id VARCHAR(100),
    p_reward DECIMAL(10, 6),
    p_success BOOLEAN
)
RETURNS VOID AS $$
BEGIN
    INSERT INTO meta_cognition_status (agent_id, reward_mean, success_rate, updated_at)
    VALUES (p_agent_id, p_reward, CASE WHEN p_success THEN 1 ELSE 0 END, CURRENT_TIMESTAMP)
    ON CONFLICT (agent_id) DO UPDATE SET
        reward_mean = (meta_cognition_status.reward_mean * 0.99 + p_reward * 0.01),
        success_rate = (meta_cognition_status.success_rate * 0.99 + CASE WHEN p_success THEN 0.01 ELSE 0 END),
        trajectory_size = meta_cognition_status.trajectory_size + 1,
        updated_at = CURRENT_TIMESTAMP;
END;
$$ LANGUAGE plpgsql;

COMMENT ON FUNCTION update_agent_health_metric IS '更新智能体健康指标函数';

-- 创建触发器：记录进化事件
CREATE OR REPLACE FUNCTION log_evolution_event()
RETURNS TRIGGER AS $$
BEGIN
    INSERT INTO evolution_events (event_type, event_data, agent_id, version_id, created_at)
    VALUES (
        TG_OP,
        to_jsonb(NEW),
        COALESCE(NEW.agent_id, NEW.version_id),
        NEW.version_id,
        CURRENT_TIMESTAMP
    );
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER tr_agent_versions_log
AFTER INSERT OR UPDATE ON agent_versions
FOR EACH ROW EXECUTE FUNCTION log_evolution_event();

-- 创建触发器：更新建议处理时间
CREATE OR REPLACE FUNCTION update_suggestion_processed_at()
RETURNS TRIGGER AS $$
BEGIN
    IF NEW.status != OLD.status AND NEW.status IN ('accepted', 'rejected', 'applied') THEN
        NEW.processed_at = CURRENT_TIMESTAMP;
    END IF;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER tr_evolution_suggestions_processed
BEFORE UPDATE ON evolution_suggestions
FOR EACH ROW EXECUTE FUNCTION update_suggestion_processed_at();

-- 授权
GRANT SELECT, INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA public TO fangdudu_user;
GRANT USAGE, SELECT ON ALL SEQUENCES IN SCHEMA public TO fangdudu_user;
GRANT EXECUTE ON ALL FUNCTIONS IN SCHEMA public TO fangdudu_user;
