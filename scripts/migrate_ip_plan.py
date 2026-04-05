"""
IP扶持计划数据库迁移脚本
创建IP合作伙伴、推广链接、推广记录、佣金记录、提现申请、内容草稿等表
"""
import sqlite3
import os

DB_PATH = os.path.join(os.path.dirname(__file__), '..', 'data', 'property-ai.db')

def table_exists(cursor, table_name):
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name=?", (table_name,))
    return cursor.fetchone() is not None

def column_exists(cursor, table_name, column_name):
    cursor.execute(f"PRAGMA table_info({table_name})")
    columns = [col[1] for col in cursor.fetchall()]
    return column_name in columns

def migrate():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    print("开始IP扶持计划数据库迁移...")
    
    # 1. IP主表
    if not table_exists(cursor, 'ip_partners'):
        print("创建 ip_partners 表...")
        cursor.execute('''
            CREATE TABLE ip_partners (
                id TEXT PRIMARY KEY,
                user_id TEXT UNIQUE,
                name TEXT NOT NULL,
                contact TEXT,
                email TEXT,
                avatar TEXT,
                platform_type TEXT,
                platform_id TEXT,
                platform_name TEXT,
                followers INTEGER DEFAULT 0,
                introduction TEXT,
                status TEXT DEFAULT 'pending',
                level TEXT DEFAULT 'bronze',
                base_commission REAL DEFAULT 5.0,
                total_earned REAL DEFAULT 0.0,
                balance REAL DEFAULT 0.0,
                frozen_balance REAL DEFAULT 0.0,
                total_referrals INTEGER DEFAULT 0,
                total_orders INTEGER DEFAULT 0,
                referral_config TEXT,
                contract_signed INTEGER DEFAULT 0,
                signed_at TIMESTAMP,
                notes TEXT,
                admin_notes TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users(id)
            )
        ''')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_ip_status ON ip_partners(status)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_ip_level ON ip_partners(level)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_ip_balance ON ip_partners(balance)')
    else:
        print("ip_partners 表已存在，检查并添加缺失列...")
        for col, col_type in [
            ('avatar', 'TEXT'),
            ('platform_name', 'TEXT'),
            ('frozen_balance', 'REAL DEFAULT 0.0'),
            ('total_orders', 'INTEGER DEFAULT 0'),
            ('admin_notes', 'TEXT'),
        ]:
            if not column_exists(cursor, 'ip_partners', col):
                try:
                    cursor.execute(f'ALTER TABLE ip_partners ADD COLUMN {col} {col_type}')
                    print(f"  添加列: {col}")
                except Exception as e:
                    print(f"  添加列 {col} 失败: {e}")
    
    # 2. 推广链接表
    if not table_exists(cursor, 'ip_links'):
        print("创建 ip_links 表...")
        cursor.execute('''
            CREATE TABLE ip_links (
                id TEXT PRIMARY KEY,
                ip_id TEXT NOT NULL,
                link_type TEXT NOT NULL,
                url TEXT NOT NULL,
                code TEXT UNIQUE NOT NULL,
                channel TEXT,
                description TEXT,
                click_count INTEGER DEFAULT 0,
                register_count INTEGER DEFAULT 0,
                is_active INTEGER DEFAULT 1,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (ip_id) REFERENCES ip_partners(id)
            )
        ''')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_ip_links_code ON ip_links(code)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_ip_links_ip ON ip_links(ip_id)')
    else:
        print("ip_links 表已存在")
    
    # 3. 推广记录表
    if not table_exists(cursor, 'ip_referrals'):
        print("创建 ip_referrals 表...")
        cursor.execute('''
            CREATE TABLE ip_referrals (
                id TEXT PRIMARY KEY,
                ip_id TEXT NOT NULL,
                user_id TEXT NOT NULL,
                link_id TEXT,
                ref_code TEXT,
                clicked_at TIMESTAMP,
                registered_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                first_order_at TIMESTAMP,
                first_order_amount REAL,
                total_orders INTEGER DEFAULT 0,
                total_amount REAL DEFAULT 0.0,
                status TEXT DEFAULT 'active',
                risk_level TEXT DEFAULT 'low',
                risk_tags TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (ip_id) REFERENCES ip_partners(id),
                FOREIGN KEY (user_id) REFERENCES users(id),
                FOREIGN KEY (link_id) REFERENCES ip_links(id)
            )
        ''')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_ip_ref_ip ON ip_referrals(ip_id)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_ip_ref_user ON ip_referrals(user_id)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_ip_ref_status ON ip_referrals(status)')
    else:
        print("ip_referrals 表已存在")
    
    # 4. 佣金记录表
    if not table_exists(cursor, 'ip_commissions'):
        print("创建 ip_commissions 表...")
        cursor.execute('''
            CREATE TABLE ip_commissions (
                id TEXT PRIMARY KEY,
                ip_id TEXT NOT NULL,
                referral_id TEXT,
                order_id TEXT,
                order_type TEXT,
                order_amount REAL NOT NULL,
                commission_rate REAL NOT NULL,
                commission_amount REAL NOT NULL,
                bonus_amount REAL DEFAULT 0.0,
                total_amount REAL NOT NULL,
                status TEXT DEFAULT 'pending',
                settled_at TIMESTAMP,
                notes TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (ip_id) REFERENCES ip_partners(id),
                FOREIGN KEY (referral_id) REFERENCES ip_referrals(id),
                FOREIGN KEY (order_id) REFERENCES recharge_orders(id)
            )
        ''')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_ip_comm_ip ON ip_commissions(ip_id)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_ip_comm_status ON ip_commissions(status)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_ip_comm_order ON ip_commissions(order_id)')
    else:
        print("ip_commissions 表已存在")
    
    # 5. 提现申请表
    if not table_exists(cursor, 'ip_withdrawals'):
        print("创建 ip_withdrawals 表...")
        cursor.execute('''
            CREATE TABLE ip_withdrawals (
                id TEXT PRIMARY KEY,
                ip_id TEXT NOT NULL,
                amount REAL NOT NULL,
                fee REAL DEFAULT 0.0,
                actual_amount REAL NOT NULL,
                account_type TEXT NOT NULL,
                account_name TEXT,
                account_info TEXT,
                status TEXT DEFAULT 'pending',
                admin_notes TEXT,
                processed_at TIMESTAMP,
                processed_by TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (ip_id) REFERENCES ip_partners(id),
                FOREIGN KEY (processed_by) REFERENCES users(id)
            )
        ''')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_ip_wd_ip ON ip_withdrawals(ip_id)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_ip_wd_status ON ip_withdrawals(status)')
    else:
        print("ip_withdrawals 表已存在")
    
    # 6. 内容草稿表
    if not table_exists(cursor, 'ip_content_drafts'):
        print("创建 ip_content_drafts 表...")
        cursor.execute('''
            CREATE TABLE ip_content_drafts (
                id TEXT PRIMARY KEY,
                ip_id TEXT NOT NULL,
                title TEXT,
                content TEXT,
                content_type TEXT DEFAULT 'article',
                status TEXT DEFAULT 'draft',
                published_url TEXT,
                view_count INTEGER DEFAULT 0,
                tags TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (ip_id) REFERENCES ip_partners(id)
            )
        ''')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_ip_draft_ip ON ip_content_drafts(ip_id)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_ip_draft_status ON ip_content_drafts(status)')
    else:
        print("ip_content_drafts 表已存在")
    
    # 7. 佣金规则配置表
    if not table_exists(cursor, 'ip_commission_rules'):
        print("创建 ip_commission_rules 表...")
        cursor.execute('''
            CREATE TABLE ip_commission_rules (
                id TEXT PRIMARY KEY,
                name TEXT NOT NULL,
                rule_type TEXT NOT NULL,
                min_amount REAL DEFAULT 0.0,
                max_amount REAL,
                commission_rate REAL NOT NULL,
                bonus_rate REAL DEFAULT 0.0,
                priority INTEGER DEFAULT 0,
                is_active INTEGER DEFAULT 1,
                start_date TIMESTAMP,
                end_date TIMESTAMP,
                config TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        cursor.execute('''
            INSERT INTO ip_commission_rules (id, name, rule_type, min_amount, commission_rate, priority)
            VALUES 
                ('rule-default', '默认佣金规则', 'base', 0, 5.0, 0),
                ('rule-tier1', '阶梯奖励1', 'tier', 1000, 6.0, 10),
                ('rule-tier2', '阶梯奖励2', 'tier', 5000, 7.0, 20),
                ('rule-tier3', '阶梯奖励3', 'tier', 10000, 8.0, 30)
        ''')
    else:
        print("ip_commission_rules 表已存在")
    
    # 8. IP等级配置表
    if not table_exists(cursor, 'ip_levels'):
        print("创建 ip_levels 表...")
        cursor.execute('''
            CREATE TABLE ip_levels (
                id TEXT PRIMARY KEY,
                level_name TEXT NOT NULL,
                level_code TEXT UNIQUE NOT NULL,
                min_earnings REAL DEFAULT 0.0,
                min_referrals INTEGER DEFAULT 0,
                commission_bonus REAL DEFAULT 0.0,
                benefits TEXT,
                icon TEXT,
                color TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        cursor.execute('''
            INSERT INTO ip_levels (id, level_name, level_code, min_earnings, min_referrals, commission_bonus, color)
            VALUES 
                ('level-bronze', '青铜创作者', 'bronze', 0, 0, 0.0, '#CD7F32'),
                ('level-silver', '白银创作者', 'silver', 1000, 10, 1.0, '#C0C0C0'),
                ('level-gold', '黄金创作者', 'gold', 5000, 50, 2.0, '#FFD700'),
                ('level-platinum', '铂金创作者', 'platinum', 20000, 200, 3.0, '#E5E4E2'),
                ('level-diamond', '钻石创作者', 'diamond', 100000, 500, 5.0, '#B9F2FF')
        ''')
    else:
        print("ip_levels 表已存在")
    
    # 9. IP操作日志表
    if not table_exists(cursor, 'ip_operation_logs'):
        print("创建 ip_operation_logs 表...")
        cursor.execute('''
            CREATE TABLE ip_operation_logs (
                id TEXT PRIMARY KEY,
                ip_id TEXT,
                operator_id TEXT,
                operation_type TEXT NOT NULL,
                target_type TEXT,
                target_id TEXT,
                before_data TEXT,
                after_data TEXT,
                notes TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (ip_id) REFERENCES ip_partners(id),
                FOREIGN KEY (operator_id) REFERENCES users(id)
            )
        ''')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_ip_log_ip ON ip_operation_logs(ip_id)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_ip_log_type ON ip_operation_logs(operation_type)')
    else:
        print("ip_operation_logs 表已存在")
    
    # 10. IP风控黑名单表
    if not table_exists(cursor, 'ip_risk_blacklist'):
        print("创建 ip_risk_blacklist 表...")
        cursor.execute('''
            CREATE TABLE ip_risk_blacklist (
                id TEXT PRIMARY KEY,
                ip_address TEXT,
                device_id TEXT,
                user_id TEXT,
                reason TEXT,
                risk_level TEXT DEFAULT 'high',
                added_by TEXT,
                status TEXT DEFAULT 'active',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (added_by) REFERENCES users(id),
                FOREIGN KEY (user_id) REFERENCES users(id)
            )
        ''')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_risk_blacklist_ip ON ip_risk_blacklist(ip_address)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_risk_blacklist_device ON ip_risk_blacklist(device_id)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_risk_blacklist_status ON ip_risk_blacklist(status)')
    else:
        print("ip_risk_blacklist 表已存在")
    
    # 11. 给users表添加IP相关字段
    print("更新 users 表添加IP字段...")
    for col, col_type in [
        ('referred_by_ip', 'TEXT'),
        ('ref_code', 'TEXT'),
        ('ip_partner_id', 'TEXT'),
    ]:
        if not column_exists(cursor, 'users', col):
            try:
                cursor.execute(f'ALTER TABLE users ADD COLUMN {col} {col_type}')
                print(f"  添加列: {col}")
            except Exception as e:
                print(f"  列 {col} 可能已存在: {e}")
    
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_users_ref_ip ON users(referred_by_ip)')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_users_ref_code ON users(ref_code)')
    
    conn.commit()
    conn.close()
    
    print("\nIP扶持计划数据库迁移完成!")

if __name__ == '__main__':
    migrate()
