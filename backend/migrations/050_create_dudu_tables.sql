-- 吉祥物嘟嘟系统数据库表 (PostgreSQL)
-- Dudu Mascot System Database Tables

-- 嘟嘟状态表
CREATE TABLE IF NOT EXISTS dudu_state (
    id SERIAL PRIMARY KEY,
    user_id VARCHAR(50) NOT NULL UNIQUE,
    
    emotion_state JSONB DEFAULT '{"pleasure": 50, "activity": 50, "intimacy": 0}',
    level_info JSONB DEFAULT '{"level": 1, "exp": 0, "total_interactions": 0}',
    
    current_emotion VARCHAR(20) DEFAULT 'idle',
    current_action VARCHAR(20) DEFAULT 'idle',
    current_message TEXT DEFAULT '',
    
    equipped_costumes JSONB DEFAULT '{}',
    
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_dudu_state_user_id ON dudu_state(user_id);
CREATE INDEX IF NOT EXISTS idx_dudu_state_updated_at ON dudu_state(updated_at);

-- 用户拥有的装扮表
CREATE TABLE IF NOT EXISTS dudu_user_costumes (
    id SERIAL PRIMARY KEY,
    user_id VARCHAR(50) NOT NULL,
    costume_id VARCHAR(50) NOT NULL,
    
    purchased_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    equipped BOOLEAN DEFAULT FALSE,
    
    UNIQUE(user_id, costume_id)
);

CREATE INDEX IF NOT EXISTS idx_dudu_user_costumes_user_id ON dudu_user_costumes(user_id);

-- 嘟嘟互动记录表
CREATE TABLE IF NOT EXISTS dudu_interactions (
    id SERIAL PRIMARY KEY,
    user_id VARCHAR(50) NOT NULL,
    
    interaction_type VARCHAR(30) NOT NULL,
    event_data JSONB,
    
    intimacy_change INTEGER DEFAULT 0,
    exp_change INTEGER DEFAULT 0,
    integral_change INTEGER DEFAULT 0,
    
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_dudu_interactions_user_id ON dudu_interactions(user_id);
CREATE INDEX IF NOT EXISTS idx_dudu_interactions_type ON dudu_interactions(interaction_type);
CREATE INDEX IF NOT EXISTS idx_dudu_interactions_created_at ON dudu_interactions(created_at);

-- 嘟嘟语录库表
CREATE TABLE IF NOT EXISTS dudu_quotes (
    id SERIAL PRIMARY KEY,
    category VARCHAR(30) NOT NULL,
    content TEXT NOT NULL,
    
    is_active BOOLEAN DEFAULT TRUE,
    priority INTEGER DEFAULT 0,
    
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_dudu_quotes_category ON dudu_quotes(category);
CREATE INDEX IF NOT EXISTS idx_dudu_quotes_active ON dudu_quotes(is_active);

-- 装扮商城表
CREATE TABLE IF NOT EXISTS dudu_costume_shop (
    id SERIAL PRIMARY KEY,
    costume_id VARCHAR(50) NOT NULL UNIQUE,
    name VARCHAR(100) NOT NULL,
    description TEXT,
    category VARCHAR(30) NOT NULL,
    rarity VARCHAR(20) DEFAULT 'common',
    
    price INTEGER DEFAULT 0,
    unlock_level INTEGER DEFAULT 1,
    
    preview_url TEXT,
    animation_data JSONB,
    
    is_active BOOLEAN DEFAULT TRUE,
    is_limited BOOLEAN DEFAULT FALSE,
    limited_count INTEGER DEFAULT 0,
    sold_count INTEGER DEFAULT 0,
    
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_dudu_costume_shop_category ON dudu_costume_shop(category);
CREATE INDEX IF NOT EXISTS idx_dudu_costume_shop_rarity ON dudu_costume_shop(rarity);
CREATE INDEX IF NOT EXISTS idx_dudu_costume_shop_active ON dudu_costume_shop(is_active);

-- 嘟嘟成就表
CREATE TABLE IF NOT EXISTS dudu_achievements (
    id SERIAL PRIMARY KEY,
    user_id VARCHAR(50) NOT NULL,
    achievement_id VARCHAR(50) NOT NULL,
    
    unlocked_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    UNIQUE(user_id, achievement_id)
);

CREATE INDEX IF NOT EXISTS idx_dudu_achievements_user_id ON dudu_achievements(user_id);

-- 喂食记录表
CREATE TABLE IF NOT EXISTS dudu_feed_log (
    id SERIAL PRIMARY KEY,
    user_id VARCHAR(50) NOT NULL,
    
    food_type VARCHAR(30) NOT NULL,
    food_value INTEGER DEFAULT 10,
    integral_cost INTEGER DEFAULT 0,
    
    intimacy_before INTEGER,
    intimacy_after INTEGER,
    
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_dudu_feed_log_user_id ON dudu_feed_log(user_id);
CREATE INDEX IF NOT EXISTS idx_dudu_feed_log_created_at ON dudu_feed_log(created_at);

-- 插入默认语录
INSERT INTO dudu_quotes (category, content, priority) VALUES
('welcome', '欢迎回来！今天也要加油哦~', 10),
('welcome', '嘟嘟等你好久啦！', 8),
('welcome', '主人来啦！今天想看什么？', 9),
('welcome', '又见面啦，开心！', 7),
('task_complete', '太棒啦！任务完成！', 10),
('task_complete', '厉害厉害！嘟嘟为你骄傲！', 9),
('task_complete', '完美！又完成一个任务~', 8),
('task_complete', '干得漂亮！', 7),
('task_fail', '没关系，下次一定行！', 10),
('task_fail', '嘟嘟相信你可以的！', 9),
('task_fail', '别灰心，再试一次吧~', 8),
('task_fail', '失败是成功之母嘛！', 7),
('integral_gained', '积分+1！继续加油！', 10),
('integral_gained', '哇，积分增加了！', 8),
('integral_gained', '攒积分换装扮咯~', 7),
('risk_alert', '注意！有风险预警！', 10),
('risk_alert', '嘟嘟发现异常了！', 9),
('risk_alert', '小心小心！', 8),
('idle', '嘟嘟在等你哦~', 5),
('idle', '有什么可以帮你的吗？', 5),
('idle', '今天天气真好~', 3),
('idle', '想看看新装扮吗？', 4),
('idle', '嘟嘟想你了~', 6),
('click', '嘿嘿，被发现了！', 8),
('click', '戳我干嘛~', 7),
('click', '嘟嘟在这里！', 9),
('click', '想我了吗？', 6),
('click', '点击有惊喜哦~', 5),
('feed', '好吃好吃！谢谢主人！', 10),
('feed', '嘟嘟吃饱啦~', 8),
('feed', '最喜欢主人了！', 9),
('feed', '再来再来！', 7),
('level_up', '升级啦！嘟嘟变强了！', 10),
('level_up', '等级提升！新技能解锁！', 9),
('level_up', '成长快乐！', 8),
('sign_in', '签到成功！积分到手！', 10),
('sign_in', '今天也签到啦~', 8),
('sign_in', '连续签到奖励更多哦！', 9),
('new_feature', '新功能上线啦！快去看看！', 10),
('new_feature', '有新东西哦，嘟嘟带你去看！', 9),
('goodbye', '下次见！嘟嘟会想你的！', 10),
('goodbye', '拜拜~记得回来哦！', 8),
('goodbye', '期待下次见面！', 9)
ON CONFLICT DO NOTHING;

-- 插入默认装扮
INSERT INTO dudu_costume_shop (costume_id, name, description, category, rarity, price, unlock_level) VALUES
('default', '默认汉服', '嘟嘟的默认装扮，可爱的迷你汉服', 'outfit', 'common', 0, 1),
('zhouyu_hat', '周瑜纶巾', '模仿周瑜都督的头巾，充满智慧气息', 'hat', 'rare', 100, 5),
('luxun_hat', '陆逊武弁', '模仿陆逊都督的武弁，英气逼人', 'hat', 'rare', 100, 5),
('spring', '春日和服', '樱花粉色的和服，春意盎然', 'outfit', 'epic', 300, 10),
('summer', '夏日清凉装', '清爽的夏日装扮，清凉一夏', 'outfit', 'rare', 150, 8),
('autumn', '秋日枫叶装', '枫叶色的秋装，温暖如秋', 'outfit', 'rare', 150, 8),
('winter', '冬日暖绒装', '毛茸茸的冬装，温暖过冬', 'outfit', 'epic', 300, 10),
('glasses', '小眼镜', '可爱的小眼镜，知识渊博的样子', 'accessory', 'common', 50, 3),
('bowtie', '小领结', '正式的小领结，绅士风度', 'accessory', 'common', 50, 3),
('crown', '小皇冠', '闪闪发光的小皇冠，王者风范', 'hat', 'legendary', 500, 20),
('santa_hat', '圣诞帽', '红白相间的圣诞帽，节日气氛', 'hat', 'rare', 80, 5),
('lantern', '小灯笼', '元宵节特供，提着小灯笼', 'accessory', 'rare', 80, 5),
('spring_festival', '春节红装', '大红色的春节装扮，喜庆吉祥', 'outfit', 'epic', 200, 5)
ON CONFLICT (costume_id) DO NOTHING;
