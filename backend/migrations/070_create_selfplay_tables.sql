-- 自博弈对抗训练系统数据库表 (PostgreSQL)
-- Self-Play Adversarial Training System Tables

-- 智能体模型版本表
CREATE TABLE IF NOT EXISTS selfplay_agent_versions (
    id SERIAL PRIMARY KEY,
    agent_id VARCHAR(50) NOT NULL,
    version INTEGER NOT NULL,
    role VARCHAR(20) NOT NULL,
    
    model_path TEXT,
    state_dim INTEGER,
    action_dim INTEGER,
    
    total_games INTEGER DEFAULT 0,
    wins INTEGER DEFAULT 0,
    win_rate REAL DEFAULT 0.0,
    avg_reward REAL DEFAULT 0.0,
    
    is_champion BOOLEAN DEFAULT FALSE,
    is_active BOOLEAN DEFAULT TRUE,
    
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    UNIQUE(agent_id, version)
);

CREATE INDEX IF NOT EXISTS idx_selfplay_agent_versions_role ON selfplay_agent_versions(role);
CREATE INDEX IF NOT EXISTS idx_selfplay_agent_versions_champion ON selfplay_agent_versions(is_champion);
CREATE INDEX IF NOT EXISTS idx_selfplay_agent_versions_created ON selfplay_agent_versions(created_at);

-- 对战记录表
CREATE TABLE IF NOT EXISTS selfplay_episodes (
    id SERIAL PRIMARY KEY,
    episode_id VARCHAR(50) NOT NULL UNIQUE,
    
    attacker_id VARCHAR(50) NOT NULL,
    attacker_version INTEGER DEFAULT 1,
    
    defender_id VARCHAR(50) NOT NULL,
    defender_version INTEGER DEFAULT 1,
    
    attacker_reward REAL DEFAULT 0.0,
    defender_reward REAL DEFAULT 0.0,
    
    attacker_won BOOLEAN DEFAULT FALSE,
    steps INTEGER DEFAULT 0,
    
    duration_ms INTEGER DEFAULT 0,
    
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_selfplay_episodes_attacker ON selfplay_episodes(attacker_id);
CREATE INDEX IF NOT EXISTS idx_selfplay_episodes_defender ON selfplay_episodes(defender_id);
CREATE INDEX IF NOT EXISTS idx_selfplay_episodes_created ON selfplay_episodes(created_at);

-- 经验回放表
CREATE TABLE IF NOT EXISTS selfplay_experiences (
    id SERIAL PRIMARY KEY,
    experience_id VARCHAR(50) NOT NULL UNIQUE,
    
    agent_id VARCHAR(50) NOT NULL,
    agent_version INTEGER DEFAULT 1,
    episode_id VARCHAR(50),
    
    state JSONB NOT NULL,
    action INTEGER NOT NULL,
    reward REAL NOT NULL,
    next_state JSONB,
    done BOOLEAN DEFAULT FALSE,
    
    log_prob REAL,
    value REAL,
    advantage REAL,
    
    priority REAL DEFAULT 1.0,
    
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_selfplay_experiences_agent ON selfplay_experiences(agent_id);
CREATE INDEX IF NOT EXISTS idx_selfplay_experiences_episode ON selfplay_experiences(episode_id);
CREATE INDEX IF NOT EXISTS idx_selfplay_experiences_priority ON selfplay_experiences(priority DESC);

-- 训练指标表
CREATE TABLE IF NOT EXISTS selfplay_training_metrics (
    id SERIAL PRIMARY KEY,
    training_step BIGINT NOT NULL,
    
    agent_id VARCHAR(50) NOT NULL,
    agent_version INTEGER DEFAULT 1,
    
    total_loss REAL,
    policy_loss REAL,
    value_loss REAL,
    entropy REAL,
    
    learning_rate REAL,
    clip_epsilon REAL,
    
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_selfplay_training_metrics_agent ON selfplay_training_metrics(agent_id);
CREATE INDEX IF NOT EXISTS idx_selfplay_training_metrics_step ON selfplay_training_metrics(training_step);

-- 评估结果表
CREATE TABLE IF NOT EXISTS selfplay_evaluations (
    id SERIAL PRIMARY KEY,
    evaluation_id VARCHAR(50) NOT NULL UNIQUE,
    
    attacker_id VARCHAR(50) NOT NULL,
    defender_id VARCHAR(50) NOT NULL,
    
    num_games INTEGER DEFAULT 10,
    
    attacker_wins INTEGER DEFAULT 0,
    defender_wins INTEGER DEFAULT 0,
    attacker_win_rate REAL DEFAULT 0.0,
    defender_win_rate REAL DEFAULT 0.0,
    
    avg_attacker_reward REAL DEFAULT 0.0,
    avg_defender_reward REAL DEFAULT 0.0,
    
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_selfplay_evaluations_created ON selfplay_evaluations(created_at);

-- 对手池表
CREATE TABLE IF NOT EXISTS selfplay_opponent_pool (
    id SERIAL PRIMARY KEY,
    pool_id VARCHAR(50) NOT NULL UNIQUE,
    
    agent_id VARCHAR(50) NOT NULL,
    agent_version INTEGER NOT NULL,
    role VARCHAR(20) NOT NULL,
    
    model_path TEXT,
    
    win_rate REAL DEFAULT 0.0,
    games_played INTEGER DEFAULT 0,
    
    is_active BOOLEAN DEFAULT TRUE,
    
    added_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_used_at TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_selfplay_opponent_pool_role ON selfplay_opponent_pool(role);
CREATE INDEX IF NOT EXISTS idx_selfplay_opponent_pool_active ON selfplay_opponent_pool(is_active);

-- 种群统计表
CREATE TABLE IF NOT EXISTS selfplay_population_stats (
    id SERIAL PRIMARY KEY,
    stat_date DATE NOT NULL UNIQUE,
    
    population_size INTEGER DEFAULT 0,
    total_episodes INTEGER DEFAULT 0,
    
    best_attacker_id VARCHAR(50),
    best_attacker_win_rate REAL DEFAULT 0.0,
    
    best_defender_id VARCHAR(50),
    best_defender_win_rate REAL DEFAULT 0.0,
    
    avg_attacker_reward REAL DEFAULT 0.0,
    avg_defender_reward REAL DEFAULT 0.0,
    
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_selfplay_population_stats_date ON selfplay_population_stats(stat_date);

-- 插入默认统计记录
INSERT INTO selfplay_population_stats (stat_date, population_size, total_episodes)
SELECT CURRENT_DATE, 0, 0
WHERE NOT EXISTS (SELECT 1 FROM selfplay_population_stats WHERE stat_date = CURRENT_DATE);
