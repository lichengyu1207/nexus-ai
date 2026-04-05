-- 迁移脚本：新增表 agent_messages
-- 用于存储代理间的消息历史记录

CREATE TABLE IF NOT EXISTS agent_messages (
    id TEXT PRIMARY KEY,
    task_id TEXT NOT NULL,
    sender TEXT NOT NULL,
    recipient TEXT,
    type TEXT NOT NULL,
    content TEXT,  -- JSON字符串
    in_reply_to TEXT,
    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_agent_messages_task_id ON agent_messages(task_id);
CREATE INDEX IF NOT EXISTS idx_agent_messages_sender ON agent_messages(sender);
CREATE INDEX IF NOT EXISTS idx_agent_messages_recipient ON agent_messages(recipient);
CREATE INDEX IF NOT EXISTS idx_agent_messages_timestamp ON agent_messages(timestamp);

-- 任务状态表
CREATE TABLE IF NOT EXISTS agent_tasks (
    task_id TEXT PRIMARY KEY,
    status TEXT NOT NULL DEFAULT 'pending',  -- pending, running, completed, failed
    query TEXT,
    result TEXT,  -- JSON字符串
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    completed_at DATETIME
);

CREATE INDEX IF NOT EXISTS idx_agent_tasks_status ON agent_tasks(status);
CREATE INDEX IF NOT EXISTS idx_agent_tasks_created_at ON agent_tasks(created_at);
