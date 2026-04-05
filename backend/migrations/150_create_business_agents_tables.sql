-- 业务层活体智能体数据库迁移
-- Migration: 150_create_business_agents_tables.sql
-- Description: 创建业务层活体智能体相关表

-- 1. 业务智能体表
CREATE TABLE business_agents (
    id VARCHAR(50) PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    role VARCHAR(50) NOT NULL,
    species VARCHAR(50) NOT NULL,
    energy FLOAT DEFAULT 100.0,
    max_energy FLOAT DEFAULT 300.0,
    age INT DEFAULT 0,
    generation INT DEFAULT 0,
    status VARCHAR(50) DEFAULT 'idle',
    parent_ids TEXT[],
    children_ids TEXT[],
    gene_pool JSONB,
    stats JSONB,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_business_agents_role ON business_agents(role);
CREATE INDEX idx_business_agents_species ON business_agents(species);
CREATE INDEX idx_business_agents_status ON business_agents(status);
CREATE INDEX idx_business_agents_energy ON business_agents(energy);

-- 2. 业务任务表
CREATE TABLE business_tasks (
    id VARCHAR(50) PRIMARY KEY,
    task_type VARCHAR(50) NOT NULL,
    title VARCHAR(200) NOT NULL,
    description TEXT,
    complexity FLOAT DEFAULT 1.0,
    required_skills JSONB,
    required_roles JSONB,
    reward_energy FLOAT DEFAULT 10.0,
    deadline TIMESTAMP,
    priority INT DEFAULT 2,
    user_id VARCHAR(50),
    status VARCHAR(50) DEFAULT 'pending',
    assigned_agents JSONB,
    team_id VARCHAR(50),
    result JSONB,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    started_at TIMESTAMP,
    completed_at Timestamp
);
CREATE INDEX idx_business_tasks_status ON business_tasks(status);
CREATE INDEX idx_business_tasks_user ON business_tasks(user_id);

-- 3. 任务竞标表
CREATE TABLE task_bids (
    id VARCHAR(50) PRIMARY KEY,
    task_id VARCHAR(50) NOT NULL,
    agent_id VARCHAR(50) NOT NULL,
    promised_completion_time FLOAT,
    success_rate_estimate FLOAT,
    energy_offer FLOAT DEFAULT 0,
    proposed_reward FLOAT,
    capabilities JSONB,
    message TEXT,
    status VARCHAR(50) DEFAULT 'pending',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX idx_task_bids_task ON task_bids(task_id);
CREATE INDEX idx_task_bids_agent ON task_bids(agent_id);

-- 4. 协作消息表
CREATE TABLE collaboration_messages (
    id VARCHAR(50) PRIMARY KEY,
    from_agent VARCHAR(50) NOT NULL,
    to_agent VARCHAR(50) NOT NULL,
    message_type VARCHAR(50) NOT NULL,
    payload JSONB,
    energy_offer FLOAT DEFAULT 0,
    task_id VARCHAR(50),
    team_id VARCHAR(50),
    priority INT DEFAULT 1,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    expires_at Timestamp
);
CREATE INDEX idx_collaboration_messages_from ON collaboration_messages(from_agent);
CREATE INDEX idx_collaboration_messages_to ON collaboration_messages(to_agent);

-- 5. 协作记录表
CREATE TABLE collaboration_records (
    id VARCHAR(50) PRIMARY KEY,
    task_id VARCHAR(50),
    requester_id VARCHAR(50),
    helper_id VARCHAR(50),
    message_type VARCHAR(50),
    energy_offered FLOAT,
    energy_transferred FLOAT,
    success BOOLEAN,
    started_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    completed_at Timestamp
);
CREATE INDEX idx_collaboration_records_requester ON collaboration_records(requester_id);
CREATE INDEX idx_collaboration_records_helper ON collaboration_records(helper_id);

-- 6. 局部规则表
CREATE TABLE local_rules (
    id VARCHAR(50) PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    description TEXT,
    department VARCHAR(50),
    trigger_type VARCHAR(50),
    conditions JSONB,
    actions JSONB,
    priority INT DEFAULT 2,
    status VARCHAR(50) DEFAULT 'active',
    cooldown FLOAT DEFAULT 60,
    max_executions INT DEFAULT 100,
    execution_count INT DEFAULT 0,
    success_count INT DEFAULT 0,
    failure_count INT DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at Timestamp DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX idx_local_rules_department ON local_rules(department);
CREATE INDEX idx_local_rules_status ON local_rules(status);

-- 7. 涌现模式表
CREATE TABLE emergence_patterns (
    id VARCHAR(50) PRIMARY KEY,
    pattern_type VARCHAR(50),
    name VARCHAR(100),
    description TEXT,
    agents_involved JSONB,
    sequence JSONB,
    frequency INT DEFAULT 1,
    first_observed TIMESTAMP,
    last_observed TIMESTAMP,
    effectiveness VARCHAR(50),
    impact_score FLOAT DEFAULT 0,
    conditions JSONB,
    outcomes JSONB,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX idx_emergence_patterns_type ON emergence_patterns(pattern_type);

-- 8. 学习会话表
CREATE TABLE learning_sessions (
    id VARCHAR(50) PRIMARY KEY,
    agent_id VARCHAR(50),
    trigger VARCHAR(50),
    samples_used INT,
    epochs_completed INT,
    initial_loss FLOAT,
    final_loss FLOAT,
    validation_score FLOAT,
    improvement FLOAT,
    deployed BOOLEAN DEFAULT FALSE,
    rolled_back BOOLEAN DEFAULT FALSE,
    started_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    completed_at Timestamp
    error TEXT
);
CREATE INDEX idx_learning_sessions_agent ON learning_sessions(agent_id);

-- 9. 技能传承会话表
CREATE TABLE skill_transfer_sessions (
    id VARCHAR(50) PRIMARY KEY,
    pair_id VARCHAR(50),
    teacher_id VARCHAR(50),
    student_id VARCHAR(50),
    transfer_type VARCHAR(50),
    knowledge_modules JSONB,
    energy_cost FLOAT,
    energy_paid FLOAT,
    status VARCHAR(50),
    started_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    completed_at Timestamp,
    test_results JSONB,
    success_score FLOAT DEFAULT 0,
    error TEXT
);
CREATE INDEX idx_skill_transfer_teacher ON skill_transfer_sessions(teacher_id);
CREATE INDEX idx_skill_transfer_student ON skill_transfer_sessions(student_id);

-- 10. 繁殖记录表
CREATE TABLE reproduction_records (
    id VARCHAR(50) PRIMARY KEY,
    parent_ids JSONB,
    reproduction_type VARCHAR(50),
    generation INT,
    initial_energy FLOAT,
    gene_pool JSONB,
    status VARCHAR(50),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    activated_at Timestamp,
    terminated_at Timestamp,
    validation_result JSONB,
    performance JSONB
);
CREATE INDEX idx_reproduction_generation ON reproduction_records(generation);

-- 11. 虚拟团队表
CREATE TABLE virtual_teams (
    id VARCHAR(50) PRIMARY KEY,
    task_id VARCHAR(50),
    leader_id VARCHAR(50),
    member_ids JSONB,
    strategy VARCHAR(50),
    formed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    status VARCHAR(50) DEFAULT 'active',
    performance JSONB,
    completed_at Timestamp
);
CREATE INDEX idx_virtual_teams_task ON virtual_teams(task_id);

-- 12. 用户反馈表
CREATE TABLE user_feedbacks (
    id VARCHAR(50) PRIMARY KEY,
    user_id VARCHAR(50) NOT NULL,
    agent_id VARCHAR(50) NOT NULL,
    task_id VARCHAR(50),
    feedback_type VARCHAR(50),
    severity VARCHAR(50),
    content TEXT,
    rating FLOAT,
    metadata JSONB,
    processed BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX idx_user_feedbacks_user ON user_feedbacks(user_id);
CREATE INDEX idx_user_feedbacks_agent ON user_feedbacks(agent_id);

-- 13. 用户偏好模型表
CREATE TABLE user_preferences (
    id VARCHAR(50) PRIMARY KEY,
    user_id VARCHAR(50) UNIQUE NOT NULL,
    preferences JSONB,
    interaction_history JSONB,
    feedback_summary JSONB,
    preferred_agents JSONB,
    preferred_styles JSONB,
    last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 14. 目标对齐规则表
CREATE TABLE alignment_rules (
    id VARCHAR(50) PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    description TEXT,
    metric VARCHAR(50),
    threshold FLOAT,
    weight FLOAT DEFAULT 1.0,
    active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX idx_alignment_rules_metric ON alignment_rules(metric);

-- 15. 干预记录表
CREATE TABLE intervention_records (
    id VARCHAR(50) PRIMARY KEY,
    operator_id VARCHAR(50),
    intervention_type VARCHAR(50),
    target_agent_id VARCHAR(50),
    parameters JSONB,
    reason TEXT,
    executed BOOLEAN DEFAULT FALSE,
    result JSONB,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX idx_intervention_operator ON intervention_records(operator_id);

-- 16. 生命指数评估表
CREATE TABLE life_index_evaluations (
    id VARCHAR(50) PRIMARY KEY,
    agent_id VARCHAR(50),
    adaptability FLOAT,
    learning_efficiency FLOAT,
    collaboration_degree FLOAT,
    emergent_intelligence FLOAT,
    reproduction_health FLOAT,
    overall_score FLOAT,
    grade VARCHAR(50),
    evaluated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    details JSONB
);
CREATE INDEX idx_life_index_agent ON life_index_evaluations(agent_id);
CREATE INDEX idx_life_index_evaluated ON life_index_evaluations(evaluated_at);

-- 17. 环境快照表
CREATE TABLE environment_snapshots (
    id VARCHAR(50) PRIMARY KEY,
    kpis JSONB,
    market_data JSONB,
    internal_state JSONB,
    events JSONB,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX idx_environment_snapshots_created ON environment_snapshots(created_at);

-- 视图：活跃威胁视图
CREATE VIEW active_threats_view AS
SELECT 
    ba.agent_id,
    ba.name,
    ba.role,
    ba.species,
    ba.energy,
    ba.status,
    ba.stats->'tasks_completed' as completed_tasks,
    ba.stats->'tasks_failed' as failed_tasks,
    ba.stats->'tasks_success_rate' as success_rate,
    ba.updated_at
FROM business_agents ba
WHERE ba.status IN ('working', 'learning')
AND ba.energy < 50;

ORDER BY ba.energy ASC;

LIMIT 10;

-- 视图: 团队效果视图
CREATE VIEW team_effectiveness_view AS
SELECT 
    vt.id,
    vt.task_id,
    vt.leader_id,
    vt.member_ids,
    vt.strategy,
    vt.formed_at,
    vt.completed_at,
    vt.performance->'success' as success,
    COUNT(*) as member_count
FROM virtual_teams vt
WHERE vt.status = 'completed'
ORDER BY vt.completed_at DESC
LIMIT 10;

-- 授权
GRANT SELECT, INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA public TO fangdudu_user;
GRANT USAGE, SELECT ON ALL SEQUENCES IN SCHEMA public TO fangdudu_user;
GRANT EXECUTE ON ALL FUNCTIONS IN SCHEMA public TO fangdudu_user;
