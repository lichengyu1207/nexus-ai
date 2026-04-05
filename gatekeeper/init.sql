-- 审计日志表
CREATE TABLE IF NOT EXISTS agent_restart_logs (
    id SERIAL PRIMARY KEY,
    agent_id VARCHAR(100) NOT NULL,
    trigger_type VARCHAR(10) NOT NULL,
    last_heartbeat TIMESTAMPTZ,
    operator VARCHAR(100),
    result VARCHAR(20),
    error_message TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- 索引
CREATE INDEX IF NOT EXISTS idx_agent_restart_logs_agent_id ON agent_restart_logs(agent_id);
CREATE INDEX IF NOT EXISTS idx_agent_restart_logs_created_at ON agent_restart_logs(created_at);
CREATE INDEX IF NOT EXISTS idx_agent_restart_logs_trigger_type ON agent_restart_logs(trigger_type);
