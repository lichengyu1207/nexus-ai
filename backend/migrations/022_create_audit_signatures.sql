-- 审计日志签名批处理表
CREATE TABLE IF NOT EXISTS audit_signature_batches (
    id TEXT PRIMARY KEY,
    start_log_id TEXT NOT NULL,
    end_log_id TEXT NOT NULL,
    start_timestamp TIMESTAMP NOT NULL,
    end_timestamp TIMESTAMP NOT NULL,
    log_count INTEGER NOT NULL,
    batch_hash TEXT NOT NULL,
    signature TEXT,
    signed_at TIMESTAMP,
    public_key_fingerprint TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 创建索引
CREATE INDEX IF NOT EXISTS idx_signature_batches_start ON audit_signature_batches(start_timestamp);
CREATE INDEX IF NOT EXISTS idx_signature_batches_end ON audit_signature_batches(end_timestamp);
CREATE INDEX IF NOT EXISTS idx_signature_batches_fingerprint ON audit_signature_batches(public_key_fingerprint);

-- 验证历史记录表
CREATE TABLE IF NOT EXISTS audit_verifications (
    id TEXT PRIMARY KEY,
    verification_time TIMESTAMP NOT NULL,
    total_logs INTEGER NOT NULL,
    verified_logs INTEGER NOT NULL,
    hash_errors INTEGER DEFAULT 0,
    chain_errors INTEGER DEFAULT 0,
    signature_errors INTEGER DEFAULT 0,
    status TEXT NOT NULL,
    integrity_score REAL,
    duration_ms REAL,
    report TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_audit_verifications_time ON audit_verifications(verification_time DESC);
