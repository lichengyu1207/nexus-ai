-- 刑部智能体自博弈对抗训练内核数据库表 (PostgreSQL)
-- Ministry of Justice Self-Play Adversarial Training Kernel Tables

-- 高级训练内核配置表
CREATE TABLE IF NOT EXISTS training_kernel_configs (
    id SERIAL PRIMARY KEY,
    config_id VARCHAR(50) NOT NULL UNIQUE,
    
    n_attackers INTEGER DEFAULT 8,
    n_defenders INTEGER DEFAULT 8,
    
    state_dim INTEGER DEFAULT 13,
    attack_action_dim INTEGER DEFAULT 8,
    defense_action_dim INTEGER DEFAULT 8,
    
    hidden_dim INTEGER DEFAULT 256,
    latent_dim INTEGER DEFAULT 32,
    
    learning_rate REAL DEFAULT 0.0003,
    gamma REAL DEFAULT 0.99,
    clip_epsilon REAL DEFAULT 0.2,
    
    is_active BOOLEAN DEFAULT TRUE,
    
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 高级智能体状态表
CREATE TABLE IF NOT EXISTS advanced_agents (
    id SERIAL PRIMARY KEY,
    agent_id VARCHAR(50) NOT NULL UNIQUE,
    
    role VARCHAR(20) NOT NULL,
    version INTEGER DEFAULT 1,
    
    total_games INTEGER DEFAULT 0,
    wins INTEGER DEFAULT 0,
    win_rate REAL DEFAULT 0.0,
    avg_reward REAL DEFAULT 0.0,
    
    tpr REAL DEFAULT 0.0,
    fpr REAL DEFAULT 0.0,
    
    model_path TEXT,
    is_champion BOOLEAN DEFAULT FALSE,
    
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_advanced_agents_role ON advanced_agents(role);
CREATE INDEX IF NOT EXISTS idx_advanced_agents_champion ON advanced_agents(is_champion);

-- 对抗样本记录表
CREATE TABLE IF NOT EXISTS adversarial_samples (
    id SERIAL PRIMARY KEY,
    sample_id VARCHAR(50) NOT NULL UNIQUE,
    
    original_state JSONB NOT NULL,
    perturbed_state JSONB NOT NULL,
    perturbation_type VARCHAR(50) NOT NULL,
    
    epsilon REAL DEFAULT 0.1,
    pgd_steps INTEGER DEFAULT 5,
    
    original_action INTEGER,
    perturbed_action INTEGER,
    
    defense_success BOOLEAN DEFAULT FALSE,
    
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_adversarial_samples_type ON adversarial_samples(perturbation_type);

-- 鲁棒训练指标表
CREATE TABLE IF NOT EXISTS robust_training_metrics (
    id SERIAL PRIMARY KEY,
    training_id VARCHAR(50) NOT NULL UNIQUE,
    
    total_steps INTEGER DEFAULT 0,
    avg_reward REAL DEFAULT 0.0,
    avg_adv_reward REAL DEFAULT 0.0,
    
    buffer_size INTEGER DEFAULT 0,
    
    epsilon REAL DEFAULT 0.1,
    adv_ratio REAL DEFAULT 0.3,
    
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_robust_training_steps ON robust_training_metrics(total_steps);

-- 鲁棒性评估结果表
CREATE TABLE IF NOT EXISTS robustness_evaluations (
    id SERIAL PRIMARY KEY,
    evaluation_id VARCHAR(50) NOT NULL UNIQUE,
    
    epsilon REAL NOT NULL,
    avg_reward REAL DEFAULT 0.0,
    avg_tpr REAL DEFAULT 0.0,
    avg_fpr REAL DEFAULT 0.0,
    
    n_episodes INTEGER DEFAULT 10,
    
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_robustness_evaluations_epsilon ON robustness_evaluations(epsilon);

-- 部署模型表
CREATE TABLE IF NOT EXISTS deployed_models (
    id SERIAL PRIMARY KEY,
    deployment_id VARCHAR(50) NOT NULL UNIQUE,
    
    model_path TEXT NOT NULL,
    quantization VARCHAR(20) DEFAULT 'dynamic',
    precision VARCHAR(10) DEFAULT 'fp16',
    
    original_size_mb REAL,
    quantized_size_mb REAL,
    compression_ratio REAL,
    
    onnx_path TEXT,
    torchscript_path TEXT,
    
    is_active BOOLEAN DEFAULT TRUE,
    
    deployed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_deployed_models_active ON deployed_models(is_active);

-- 推理服务状态表
CREATE TABLE IF NOT EXISTS inference_service_stats (
    id SERIAL PRIMARY KEY,
    service_id VARCHAR(50) NOT NULL UNIQUE,
    
    total_requests INTEGER DEFAULT 0,
    cache_hits INTEGER DEFAULT 0,
    cache_hit_rate REAL DEFAULT 0.0,
    
    avg_latency_ms REAL DEFAULT 0.0,
    max_latency_ms REAL DEFAULT 0.0,
    p99_latency_ms REAL DEFAULT 0.0,
    
    queue_size INTEGER DEFAULT 0,
    is_running BOOLEAN DEFAULT FALSE,
    
    recorded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 基准测试结果表
CREATE TABLE IF NOT EXISTS benchmark_results (
    id SERIAL PRIMARY KEY,
    benchmark_id VARCHAR(50) NOT NULL UNIQUE,
    
    batch_size INTEGER NOT NULL,
    n_requests INTEGER DEFAULT 100,
    
    mean_latency_ms REAL,
    std_latency_ms REAL,
    p50_latency_ms REAL,
    p95_latency_ms REAL,
    p99_latency_ms REAL,
    max_latency_ms REAL,
    
    throughput_qps REAL,
    
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_benchmark_results_batch ON benchmark_results(batch_size);

-- 防御评估指标表
CREATE TABLE IF NOT EXISTS defense_evaluation_metrics (
    id SERIAL PRIMARY KEY,
    evaluation_id VARCHAR(50) NOT NULL UNIQUE,
    
    tpr REAL DEFAULT 0.0,
    fpr REAL DEFAULT 0.0,
    precision REAL DEFAULT 0.0,
    f1_score REAL DEFAULT 0.0,
    accuracy REAL DEFAULT 0.0,
    
    block_rate REAL DEFAULT 0.0,
    service_availability REAL DEFAULT 1.0,
    
    avg_response_time_ms REAL DEFAULT 0.0,
    p99_response_time_ms REAL DEFAULT 0.0,
    avg_error_rate REAL DEFAULT 0.0,
    
    total_attacks INTEGER DEFAULT 0,
    blocked_attacks INTEGER DEFAULT 0,
    missed_attacks INTEGER DEFAULT 0,
    false_positives INTEGER DEFAULT 0,
    
    n_episodes INTEGER DEFAULT 100,
    
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_defense_eval_created ON defense_evaluation_metrics(created_at);

-- 按攻击类型评估表
CREATE TABLE IF NOT EXISTS attack_type_evaluations (
    id SERIAL PRIMARY KEY,
    evaluation_id VARCHAR(50) NOT NULL,
    
    attack_type VARCHAR(50) NOT NULL,
    
    tpr REAL DEFAULT 0.0,
    fpr REAL DEFAULT 0.0,
    block_rate REAL DEFAULT 0.0,
    service_availability REAL DEFAULT 1.0,
    
    n_episodes INTEGER DEFAULT 20,
    
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    UNIQUE(evaluation_id, attack_type)
);

CREATE INDEX IF NOT EXISTS idx_attack_type_eval_type ON attack_type_evaluations(attack_type);

-- 博弈论指标表
CREATE TABLE IF NOT EXISTS game_theory_metrics (
    id SERIAL PRIMARY KEY,
    metric_id VARCHAR(50) NOT NULL UNIQUE,
    
    nash_distance REAL DEFAULT 0.0,
    exploitability REAL DEFAULT 0.0,
    
    attacker_entropy REAL DEFAULT 0.0,
    defender_entropy REAL DEFAULT 0.0,
    
    strategy_diversity REAL DEFAULT 0.0,
    
    avg_attacker_payoff REAL DEFAULT 0.0,
    avg_defender_payoff REAL DEFAULT 0.0,
    
    avg_attacker_strategy JSONB,
    avg_defender_strategy JSONB,
    
    n_samples INTEGER DEFAULT 100,
    
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_game_theory_created ON game_theory_metrics(created_at);

-- 训练收敛指标表
CREATE TABLE IF NOT EXISTS training_convergence_metrics (
    id SERIAL PRIMARY KEY,
    training_session_id VARCHAR(50) NOT NULL,
    
    episode_number INTEGER NOT NULL,
    
    avg_reward REAL,
    reward_std REAL,
    best_reward REAL,
    
    avg_episode_length REAL,
    avg_policy_loss REAL,
    avg_value_loss REAL,
    
    is_converged BOOLEAN DEFAULT FALSE,
    convergence_threshold REAL DEFAULT 0.01,
    
    recorded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_training_convergence_session ON training_convergence_metrics(training_session_id);

-- 目标达成状态表
CREATE TABLE IF NOT EXISTS target_compliance (
    id SERIAL PRIMARY KEY,
    compliance_id VARCHAR(50) NOT NULL UNIQUE,
    
    tpr_target REAL DEFAULT 0.98,
    tpr_actual REAL DEFAULT 0.0,
    tpr_met BOOLEAN DEFAULT FALSE,
    
    fpr_target REAL DEFAULT 0.01,
    fpr_actual REAL DEFAULT 0.0,
    fpr_met BOOLEAN DEFAULT FALSE,
    
    latency_target_ms REAL DEFAULT 5.0,
    latency_actual_ms REAL DEFAULT 0.0,
    latency_met BOOLEAN DEFAULT FALSE,
    
    availability_target REAL DEFAULT 0.999,
    availability_actual REAL DEFAULT 1.0,
    availability_met BOOLEAN DEFAULT FALSE,
    
    all_targets_met BOOLEAN DEFAULT FALSE,
    
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_target_compliance_all_met ON target_compliance(all_targets_met);

-- 评估报告表
CREATE TABLE IF NOT EXISTS evaluation_reports (
    id SERIAL PRIMARY KEY,
    report_id VARCHAR(50) NOT NULL UNIQUE,
    
    summary JSONB NOT NULL,
    defense_metrics JSONB,
    realtime_metrics JSONB,
    training_metrics JSONB,
    game_theory_metrics JSONB,
    target_compliance JSONB,
    
    best_tpr REAL DEFAULT 0.0,
    best_model_path TEXT,
    
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_evaluation_reports_created ON evaluation_reports(created_at);

-- QMIX多智能体协同表
CREATE TABLE IF NOT EXISTS qmix_coordination_metrics (
    id SERIAL PRIMARY KEY,
    coordination_id VARCHAR(50) NOT NULL UNIQUE,
    
    n_agents INTEGER DEFAULT 8,
    
    global_q_value REAL,
    individual_q_values JSONB,
    
    mixing_loss REAL,
    
    coordination_success_rate REAL DEFAULT 0.0,
    
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- VAE特征提取器状态表
CREATE TABLE IF NOT EXISTS vae_feature_extractor_stats (
    id SERIAL PRIMARY KEY,
    vae_id VARCHAR(50) NOT NULL UNIQUE,
    
    input_dim INTEGER DEFAULT 13,
    latent_dim INTEGER DEFAULT 32,
    hidden_dim INTEGER DEFAULT 64,
    
    reconstruction_loss REAL,
    kl_loss REAL,
    total_vae_loss REAL,
    
    vae_weight REAL DEFAULT 0.1,
    
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 插入默认配置
INSERT INTO training_kernel_configs (config_id, n_attackers, n_defenders)
SELECT 'default_config', 8, 8
WHERE NOT EXISTS (SELECT 1 FROM training_kernel_configs WHERE config_id = 'default_config');

-- 创建更新时间触发器函数
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ language 'plpgsql';

-- 为需要的表添加触发器
DROP TRIGGER IF EXISTS update_training_kernel_configs_updated_at ON training_kernel_configs;
CREATE TRIGGER update_training_kernel_configs_updated_at
    BEFORE UPDATE ON training_kernel_configs
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

DROP TRIGGER IF EXISTS update_advanced_agents_updated_at ON advanced_agents;
CREATE TRIGGER update_advanced_agents_updated_at
    BEFORE UPDATE ON advanced_agents
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

DROP TRIGGER IF EXISTS update_vae_feature_extractor_stats_updated_at ON vae_feature_extractor_stats;
CREATE TRIGGER update_vae_feature_extractor_stats_updated_at
    BEFORE UPDATE ON vae_feature_extractor_stats
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();
