-- 公告系统迁移
-- 创建公告表
CREATE TABLE IF NOT EXISTS announcements (
    id TEXT PRIMARY KEY,
    title TEXT NOT NULL,
    content TEXT NOT NULL,
    type TEXT DEFAULT 'info',
    is_published BOOLEAN DEFAULT FALSE,
    is_pinned BOOLEAN DEFAULT FALSE,
    published_at TIMESTAMP,
    expires_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    created_by TEXT REFERENCES users(id)
);

-- 创建用户已读公告表
CREATE TABLE IF NOT EXISTS user_read_announcements (
    id TEXT PRIMARY KEY,
    user_id TEXT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    announcement_id TEXT NOT NULL REFERENCES announcements(id) ON DELETE CASCADE,
    read_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(user_id, announcement_id)
);

-- 创建索引
CREATE INDEX IF NOT EXISTS idx_announcements_published ON announcements(is_published, published_at DESC);
CREATE INDEX IF NOT EXISTS idx_announcements_pinned ON announcements(is_pinned, published_at DESC);
CREATE INDEX IF NOT EXISTS idx_user_read_announcements_user ON user_read_announcements(user_id);
CREATE INDEX IF NOT EXISTS idx_user_read_announcements_announcement ON user_read_announcements(announcement_id);

-- 插入示例公告
INSERT INTO announcements (id, title, content, type, is_published, is_pinned, published_at, created_by)
VALUES 
    ('ann-001', '欢迎使用房都督AI', '房都督AI智能房产分析平台正式上线，为您提供专业的房产分析服务。', 'info', true, true, NOW(), 'admin'),
    ('ann-002', '新功能上线：多智能体协同分析', '我们推出了多智能体协同分析功能，可以从不同维度综合分析房产价值。', 'feature', true, false, NOW(), 'admin')
ON CONFLICT (id) DO NOTHING;
