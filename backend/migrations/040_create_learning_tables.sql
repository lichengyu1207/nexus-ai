-- 学习系统数据库表 (PostgreSQL)
-- Learning System Database Tables

-- 经验回放表
CREATE TABLE IF NOT EXISTS experience_replay (
    id VARCHAR(36) PRIMARY KEY,
    agent_id VARCHAR(50) NOT NULL,
    task_id VARCHAR(50),
    episode_id VARCHAR(50),
    
    state JSONB,
    action JSONB,
    reward JSONB,
    next_state JSONB,
    
    done INTEGER DEFAULT 0,
    priority REAL DEFAULT 1.0,
    
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    processed_at TIMESTAMP,
    
    metadata JSONB
);

CREATE INDEX IF NOT EXISTS idx_experience_agent_id ON experience_replay(agent_id);
CREATE INDEX IF NOT EXISTS idx_experience_task_id ON experience_replay(task_id);
CREATE INDEX IF NOT EXISTS idx_experience_episode_id ON experience_replay(episode_id);
CREATE INDEX IF NOT EXISTS idx_experience_created_at ON experience_replay(created_at);

-- 反思记录表
CREATE TABLE IF NOT EXISTS reflection_records (
    id VARCHAR(36) PRIMARY KEY,
    agent_id VARCHAR(50) NOT NULL,
    task_id VARCHAR(50),
    
    trigger VARCHAR(30),
    reflection_type VARCHAR(30),
    
    context JSONB,
    analysis TEXT,
    root_cause TEXT,
    suggestions JSONB,
    
    training_samples JSONB,
    metrics JSONB,
    
    applied INTEGER DEFAULT 0,
    effectiveness_score REAL,
    
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    applied_at TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_reflection_agent_id ON reflection_records(agent_id);
CREATE INDEX IF NOT EXISTS idx_reflection_task_id ON reflection_records(task_id);
CREATE INDEX IF NOT EXISTS idx_reflection_created_at ON reflection_records(created_at);

-- 性能记录表
CREATE TABLE IF NOT EXISTS performance_records (
    id VARCHAR(36) PRIMARY KEY,
    agent_id VARCHAR(50) NOT NULL,
    
    metric_type VARCHAR(30) NOT NULL,
    metric_value REAL,
    sample_count INTEGER DEFAULT 1,
    
    period_start TIMESTAMP,
    period_end TIMESTAMP,
    granularity VARCHAR(20),
    
    metadata JSONB,
    
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_performance_agent_id ON performance_records(agent_id);
CREATE INDEX IF NOT EXISTS idx_performance_metric_type ON performance_records(metric_type);
CREATE INDEX IF NOT EXISTS idx_performance_period_start ON performance_records(period_start);

-- 模型版本表
CREATE TABLE IF NOT EXISTS model_versions (
    id VARCHAR(36) PRIMARY KEY,
    version_id VARCHAR(50) NOT NULL,
    agent_id VARCHAR(50) NOT NULL,
    
    model_path TEXT,
    metrics JSONB,
    status VARCHAR(20) DEFAULT 'staging',
    
    parent_version VARCHAR(50),
    description TEXT,
    
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    activated_at TIMESTAMP,
    deprecated_at TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_model_version_agent_id ON model_versions(agent_id);
CREATE INDEX IF NOT EXISTS idx_model_version_version_id ON model_versions(version_id);
CREATE INDEX IF NOT EXISTS idx_model_version_status ON model_versions(status);

-- 训练任务表
CREATE TABLE IF NOT EXISTS training_jobs (
    id VARCHAR(36) PRIMARY KEY,
    job_id VARCHAR(100) NOT NULL UNIQUE,
    agent_id VARCHAR(50) NOT NULL,
    
    status VARCHAR(20) DEFAULT 'pending',
    config JSONB,
    
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    started_at TIMESTAMP,
    completed_at TIMESTAMP,
    
    result JSONB,
    error TEXT,
    model_version VARCHAR(50)
);

CREATE INDEX IF NOT EXISTS idx_training_job_agent_id ON training_jobs(agent_id);
CREATE INDEX IF NOT EXISTS idx_training_job_status ON training_jobs(status);
CREATE INDEX IF NOT EXISTS idx_training_job_created_at ON training_jobs(created_at);

-- A/B测试实验表
CREATE TABLE IF NOT EXISTS ab_experiments (
    id VARCHAR(36) PRIMARY KEY,
    experiment_id VARCHAR(100) NOT NULL UNIQUE,
    agent_id VARCHAR(50) NOT NULL,
    
    version_a VARCHAR(50) NOT NULL,
    version_b VARCHAR(50) NOT NULL,
    traffic_split REAL DEFAULT 0.5,
    
    status VARCHAR(20) DEFAULT 'running',
    
    metrics_a JSONB,
    metrics_b JSONB,
    
    winner VARCHAR(50),
    
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    completed_at TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_ab_experiment_agent_id ON ab_experiments(agent_id);
CREATE INDEX IF NOT EXISTS idx_ab_experiment_status ON ab_experiments(status);
