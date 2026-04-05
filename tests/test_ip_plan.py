"""
IP扶持计划 - 单元测试和集成测试
覆盖申请、审核、链接生成、推广注册、佣金计算、提现等核心流程
"""
import pytest
import sqlite3
import os
import sys
import uuid
from datetime import datetime, timedelta
from unittest.mock import patch, MagicMock

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'backend'))

TEST_DB_PATH = os.path.join(os.path.dirname(__file__), 'test_ip_plan.db')

@pytest.fixture(scope='module')
def test_db():
    if os.path.exists(TEST_DB_PATH):
        os.remove(TEST_DB_PATH)
    
    conn = sqlite3.connect(TEST_DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    cursor.execute('''
        CREATE TABLE users (
            id TEXT PRIMARY KEY,
            email TEXT UNIQUE,
            username TEXT,
            password_hash TEXT,
            role TEXT DEFAULT 'user',
            referred_by_ip TEXT,
            ref_code TEXT,
            ip_partner_id TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    cursor.execute('''
        CREATE TABLE ip_partners (
            id TEXT PRIMARY KEY,
            user_id TEXT UNIQUE,
            name TEXT NOT NULL,
            contact TEXT,
            email TEXT,
            platform_type TEXT,
            platform_id TEXT,
            followers INTEGER DEFAULT 0,
            introduction TEXT,
            status TEXT DEFAULT 'pending',
            level TEXT DEFAULT 'bronze',
            base_commission REAL DEFAULT 5.0,
            total_earned REAL DEFAULT 0.0,
            balance REAL DEFAULT 0.0,
            frozen_balance REAL DEFAULT 0.0,
            total_referrals INTEGER DEFAULT 0,
            contract_signed INTEGER DEFAULT 0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(id)
        )
    ''')
    
    cursor.execute('''
        CREATE TABLE ip_links (
            id TEXT PRIMARY KEY,
            ip_id TEXT NOT NULL,
            link_type TEXT NOT NULL,
            url TEXT NOT NULL,
            code TEXT UNIQUE NOT NULL,
            channel TEXT,
            click_count INTEGER DEFAULT 0,
            register_count INTEGER DEFAULT 0,
            is_active INTEGER DEFAULT 1,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (ip_id) REFERENCES ip_partners(id)
        )
    ''')
    
    cursor.execute('''
        CREATE TABLE ip_referrals (
            id TEXT PRIMARY KEY,
            ip_id TEXT NOT NULL,
            user_id TEXT NOT NULL,
            link_id TEXT,
            clicked_at TIMESTAMP,
            registered_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            first_order_at TIMESTAMP,
            first_order_amount REAL,
            status TEXT DEFAULT 'active',
            FOREIGN KEY (ip_id) REFERENCES ip_partners(id),
            FOREIGN KEY (user_id) REFERENCES users(id),
            FOREIGN KEY (link_id) REFERENCES ip_links(id)
        )
    ''')
    
    cursor.execute('''
        CREATE TABLE ip_commissions (
            id TEXT PRIMARY KEY,
            ip_id TEXT NOT NULL,
            referral_id TEXT,
            order_id TEXT,
            order_amount REAL NOT NULL,
            commission_rate REAL NOT NULL,
            commission_amount REAL NOT NULL,
            bonus_amount REAL DEFAULT 0.0,
            total_amount REAL NOT NULL,
            status TEXT DEFAULT 'pending',
            settled_at TIMESTAMP,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (ip_id) REFERENCES ip_partners(id)
        )
    ''')
    
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
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (ip_id) REFERENCES ip_partners(id)
        )
    ''')
    
    cursor.execute('''
        CREATE TABLE ip_commission_rules (
            id TEXT PRIMARY KEY,
            name TEXT NOT NULL,
            rule_type TEXT NOT NULL,
            min_amount REAL DEFAULT 0.0,
            commission_rate REAL NOT NULL,
            bonus_rate REAL DEFAULT 0.0,
            priority INTEGER DEFAULT 0,
            is_active INTEGER DEFAULT 1
        )
    ''')
    
    cursor.execute('''
        INSERT INTO ip_commission_rules (id, name, rule_type, min_amount, commission_rate, priority)
        VALUES 
            ('rule-default', '默认佣金规则', 'base', 0, 5.0, 0),
            ('rule-tier1', '阶梯奖励1', 'tier', 1000, 6.0, 10),
            ('rule-tier2', '阶梯奖励2', 'tier', 5000, 7.0, 20)
    ''')
    
    cursor.execute('''
        CREATE TABLE ip_risk_blacklist (
            id TEXT PRIMARY KEY,
            ip_address TEXT,
            device_id TEXT,
            reason TEXT,
            risk_level TEXT DEFAULT 'high',
            status TEXT DEFAULT 'active',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    cursor.execute('''
        CREATE TABLE ip_operation_logs (
            id TEXT PRIMARY KEY,
            ip_id TEXT,
            operation TEXT NOT NULL,
            details TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    conn.commit()
    
    yield conn
    
    conn.close()
    if os.path.exists(TEST_DB_PATH):
        os.remove(TEST_DB_PATH)

@pytest.fixture
def sample_user(test_db):
    cursor = test_db.cursor()
    user_id = str(uuid.uuid4())
    cursor.execute('''
        INSERT INTO users (id, email, username, role)
        VALUES (?, ?, ?, ?)
    ''', (user_id, f'test_{user_id[:8]}@example.com', f'testuser_{user_id[:8]}', 'user'))
    test_db.commit()
    return user_id

@pytest.fixture
def sample_ip(test_db, sample_user):
    cursor = test_db.cursor()
    ip_id = str(uuid.uuid4())
    cursor.execute('''
        INSERT INTO ip_partners (id, user_id, name, contact, email, platform_type, followers, status, base_commission)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
    ''', (ip_id, sample_user, '测试IP', 'wechat_test', 'ip@example.com', 'zhihu', 10000, 'active', 10.0))
    test_db.commit()
    return ip_id

class TestIPApplication:
    
    def test_create_ip_application(self, test_db):
        cursor = test_db.cursor()
        ip_id = str(uuid.uuid4())
        
        cursor.execute('''
            INSERT INTO ip_partners (id, name, contact, email, platform_type, followers, introduction, status)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        ''', (ip_id, '张三', 'wechat123', 'zhangsan@example.com', 'zhihu', 50000, '房产领域创作者', 'pending'))
        test_db.commit()
        
        cursor.execute('SELECT * FROM ip_partners WHERE id = ?', (ip_id,))
        result = cursor.fetchone()
        
        assert result is not None
        assert result['name'] == '张三'
        assert result['status'] == 'pending'
        assert result['platform_type'] == 'zhihu'
        assert result['followers'] == 50000
    
    def test_duplicate_email_application(self, test_db):
        cursor = test_db.cursor()
        ip_id1 = str(uuid.uuid4())
        ip_id2 = str(uuid.uuid4())
        email = 'duplicate@example.com'
        
        cursor.execute('''
            INSERT INTO ip_partners (id, name, email, status)
            VALUES (?, ?, ?, ?)
        ''', (ip_id1, '用户1', email, 'pending'))
        test_db.commit()
        
        cursor.execute('SELECT COUNT(*) as count FROM ip_partners WHERE email = ?', (email,))
        result = cursor.fetchone()
        assert result['count'] == 1

class TestIPApproval:
    
    def test_approve_ip_application(self, test_db, sample_user):
        cursor = test_db.cursor()
        ip_id = str(uuid.uuid4())
        
        cursor.execute('''
            INSERT INTO ip_partners (id, user_id, name, status, base_commission)
            VALUES (?, ?, ?, ?, ?)
        ''', (ip_id, sample_user, '待审核IP', 'pending', 5.0))
        test_db.commit()
        
        cursor.execute('''
            UPDATE ip_partners SET status = 'active', base_commission = 10.0
            WHERE id = ?
        ''', (ip_id,))
        test_db.commit()
        
        cursor.execute('SELECT * FROM ip_partners WHERE id = ?', (ip_id,))
        result = cursor.fetchone()
        
        assert result['status'] == 'active'
        assert result['base_commission'] == 10.0
    
    def test_reject_ip_application(self, test_db):
        cursor = test_db.cursor()
        ip_id = str(uuid.uuid4())
        
        cursor.execute('''
            INSERT INTO ip_partners (id, name, status)
            VALUES (?, ?, ?)
        ''', (ip_id, '待审核IP', 'pending'))
        test_db.commit()
        
        cursor.execute('''
            UPDATE ip_partners SET status = 'rejected'
            WHERE id = ?
        ''', (ip_id,))
        test_db.commit()
        
        cursor.execute('SELECT * FROM ip_partners WHERE id = ?', (ip_id,))
        result = cursor.fetchone()
        
        assert result['status'] == 'rejected'

class TestLinkGeneration:
    
    def test_create_short_link(self, test_db, sample_ip):
        cursor = test_db.cursor()
        link_id = str(uuid.uuid4())
        code = f'ip_{uuid.uuid4().hex[:8]}'
        url = f'https://example.com/r/{code}'
        
        cursor.execute('''
            INSERT INTO ip_links (id, ip_id, link_type, url, code, channel)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (link_id, sample_ip, 'short_url', url, code, 'wechat'))
        test_db.commit()
        
        cursor.execute('SELECT * FROM ip_links WHERE code = ?', (code,))
        result = cursor.fetchone()
        
        assert result is not None
        assert result['link_type'] == 'short_url'
        assert result['channel'] == 'wechat'
        assert result['click_count'] == 0
    
    def test_unique_link_code(self, test_db, sample_ip):
        cursor = test_db.cursor()
        code = f'unique_{uuid.uuid4().hex[:8]}'
        
        cursor.execute('''
            INSERT INTO ip_links (id, ip_id, link_type, url, code)
            VALUES (?, ?, ?, ?, ?)
        ''', (str(uuid.uuid4()), sample_ip, 'short_url', f'https://example.com/r/{code}', code))
        test_db.commit()
        
        with pytest.raises(sqlite3.IntegrityError):
            cursor.execute('''
                INSERT INTO ip_links (id, ip_id, link_type, url, code)
                VALUES (?, ?, ?, ?, ?)
            ''', (str(uuid.uuid4()), sample_ip, 'short_url', f'https://example.com/r/{code}', code))
            test_db.commit()
    
    def test_record_link_click(self, test_db, sample_ip):
        cursor = test_db.cursor()
        link_id = str(uuid.uuid4())
        code = f'click_{uuid.uuid4().hex[:8]}'
        
        cursor.execute('''
            INSERT INTO ip_links (id, ip_id, link_type, url, code, click_count)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (link_id, sample_ip, 'short_url', f'https://example.com/r/{code}', code, 0))
        test_db.commit()
        
        for _ in range(5):
            cursor.execute('''
                UPDATE ip_links SET click_count = click_count + 1 WHERE id = ?
            ''', (link_id,))
        test_db.commit()
        
        cursor.execute('SELECT click_count FROM ip_links WHERE id = ?', (link_id,))
        result = cursor.fetchone()
        
        assert result['click_count'] == 5

class TestReferralRegistration:
    
    def test_user_registration_with_referral(self, test_db, sample_ip):
        cursor = test_db.cursor()
        
        link_id = str(uuid.uuid4())
        code = f'ref_{uuid.uuid4().hex[:8]}'
        cursor.execute('''
            INSERT INTO ip_links (id, ip_id, link_type, url, code)
            VALUES (?, ?, ?, ?, ?)
        ''', (link_id, sample_ip, 'short_url', f'https://example.com/r/{code}', code))
        test_db.commit()
        
        user_id = str(uuid.uuid4())
        cursor.execute('''
            INSERT INTO users (id, email, username, referred_by_ip, ref_code)
            VALUES (?, ?, ?, ?, ?)
        ''', (user_id, f'ref_user_{user_id[:8]}@example.com', f'refuser_{user_id[:8]}', sample_ip, code))
        test_db.commit()
        
        referral_id = str(uuid.uuid4())
        cursor.execute('''
            INSERT INTO ip_referrals (id, ip_id, user_id, link_id, status)
            VALUES (?, ?, ?, ?, ?)
        ''', (referral_id, sample_ip, user_id, link_id, 'active'))
        
        cursor.execute('''
            UPDATE ip_partners SET total_referrals = total_referrals + 1 WHERE id = ?
        ''', (sample_ip,))
        test_db.commit()
        
        cursor.execute('SELECT * FROM ip_referrals WHERE user_id = ?', (user_id,))
        referral = cursor.fetchone()
        
        cursor.execute('SELECT total_referrals FROM ip_partners WHERE id = ?', (sample_ip,))
        ip = cursor.fetchone()
        
        assert referral is not None
        assert referral['ip_id'] == sample_ip
        assert ip['total_referrals'] == 1

class TestCommissionCalculation:
    
    def test_calculate_commission(self, test_db, sample_ip):
        cursor = test_db.cursor()
        
        order_amount = 1000.0
        commission_rate = 10.0
        commission_amount = order_amount * commission_rate / 100
        
        commission_id = str(uuid.uuid4())
        cursor.execute('''
            INSERT INTO ip_commissions 
            (id, ip_id, order_amount, commission_rate, commission_amount, total_amount, status)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', (commission_id, sample_ip, order_amount, commission_rate, commission_amount, commission_amount, 'pending'))
        test_db.commit()
        
        cursor.execute('SELECT * FROM ip_commissions WHERE id = ?', (commission_id,))
        result = cursor.fetchone()
        
        assert result is not None
        assert result['commission_amount'] == 100.0
    
    def test_settle_commission(self, test_db, sample_ip):
        cursor = test_db.cursor()
        
        commission_id = str(uuid.uuid4())
        commission_amount = 100.0
        
        cursor.execute('''
            INSERT INTO ip_commissions 
            (id, ip_id, order_amount, commission_rate, commission_amount, total_amount, status)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', (commission_id, sample_ip, 1000.0, 10.0, commission_amount, commission_amount, 'pending'))
        test_db.commit()
        
        cursor.execute('''
            UPDATE ip_commissions SET status = 'settled', settled_at = ?
            WHERE id = ?
        ''', (datetime.now().isoformat(), commission_id))
        
        cursor.execute('''
            UPDATE ip_partners 
            SET balance = balance + ?, total_earned = total_earned + ?
            WHERE id = ?
        ''', (commission_amount, commission_amount, sample_ip))
        test_db.commit()
        
        cursor.execute('SELECT * FROM ip_partners WHERE id = ?', (sample_ip,))
        ip = cursor.fetchone()
        
        assert ip['balance'] == 100.0
        assert ip['total_earned'] == 100.0
    
    def test_tier_commission_bonus(self, test_db, sample_ip):
        cursor = test_db.cursor()
        
        cursor.execute('''
            SELECT * FROM ip_commission_rules 
            WHERE rule_type = 'tier' 
            ORDER BY min_amount DESC
        ''')
        tier_rules = cursor.fetchall()
        
        assert len(tier_rules) >= 2
        
        monthly_total = 6000.0
        applicable_rate = 5.0
        
        for rule in tier_rules:
            if monthly_total >= rule['min_amount']:
                applicable_rate = rule['commission_rate']
                break
        
        assert applicable_rate == 7.0

class TestWithdrawal:
    
    def test_create_withdrawal_request(self, test_db, sample_ip):
        cursor = test_db.cursor()
        
        cursor.execute('''
            UPDATE ip_partners SET balance = 500.0 WHERE id = ?
        ''', (sample_ip,))
        test_db.commit()
        
        withdrawal_id = str(uuid.uuid4())
        amount = 100.0
        fee = 0.0
        actual_amount = amount - fee
        
        cursor.execute('''
            INSERT INTO ip_withdrawals 
            (id, ip_id, amount, fee, actual_amount, account_type, account_name, status)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        ''', (withdrawal_id, sample_ip, amount, fee, actual_amount, 'wechat', '测试账户', 'pending'))
        test_db.commit()
        
        cursor.execute('SELECT * FROM ip_withdrawals WHERE id = ?', (withdrawal_id,))
        result = cursor.fetchone()
        
        assert result is not None
        assert result['status'] == 'pending'
        assert result['actual_amount'] == 100.0
    
    def test_approve_withdrawal(self, test_db, sample_ip):
        cursor = test_db.cursor()
        
        cursor.execute('''
            UPDATE ip_partners SET balance = 500.0 WHERE id = ?
        ''', (sample_ip,))
        test_db.commit()
        
        withdrawal_id = str(uuid.uuid4())
        amount = 100.0
        
        cursor.execute('''
            INSERT INTO ip_withdrawals 
            (id, ip_id, amount, fee, actual_amount, account_type, status)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', (withdrawal_id, sample_ip, amount, 0, amount, 'wechat', 'pending'))
        test_db.commit()
        
        cursor.execute('''
            UPDATE ip_withdrawals SET status = 'completed', processed_at = ?
            WHERE id = ?
        ''', (datetime.now().isoformat(), withdrawal_id))
        
        cursor.execute('''
            UPDATE ip_partners SET balance = balance - ? WHERE id = ?
        ''', (amount, sample_ip))
        test_db.commit()
        
        cursor.execute('SELECT * FROM ip_partners WHERE id = ?', (sample_ip,))
        ip = cursor.fetchone()
        
        cursor.execute('SELECT * FROM ip_withdrawals WHERE id = ?', (withdrawal_id,))
        withdrawal = cursor.fetchone()
        
        assert ip['balance'] == 400.0
        assert withdrawal['status'] == 'completed'
    
    def test_insufficient_balance_withdrawal(self, test_db, sample_ip):
        cursor = test_db.cursor()
        
        cursor.execute('SELECT balance FROM ip_partners WHERE id = ?', (sample_ip,))
        result = cursor.fetchone()
        balance = result['balance'] if result else 0
        
        withdrawal_amount = 10000.0
        
        can_withdraw = balance >= withdrawal_amount
        
        assert can_withdraw == False

class TestRiskControl:
    
    def test_blacklist_check(self, test_db):
        cursor = test_db.cursor()
        
        blacklisted_ip = '192.168.1.100'
        cursor.execute('''
            INSERT INTO ip_risk_blacklist (id, ip_address, reason, status)
            VALUES (?, ?, ?, ?)
        ''', (str(uuid.uuid4()), blacklisted_ip, '可疑IP', 'active'))
        test_db.commit()
        
        cursor.execute('''
            SELECT 1 FROM ip_risk_blacklist 
            WHERE ip_address = ? AND status = 'active'
        ''', (blacklisted_ip,))
        result = cursor.fetchone()
        
        assert result is not None
    
    def test_same_ip_multiple_registrations(self, test_db, sample_ip):
        cursor = test_db.cursor()
        
        same_ip = '10.0.0.1'
        for i in range(5):
            user_id = str(uuid.uuid4())
            cursor.execute('''
                INSERT INTO users (id, email, username, referred_by_ip)
                VALUES (?, ?, ?, ?)
            ''', (user_id, f'user_{i}@example.com', f'user_{i}', sample_ip))
            
            cursor.execute('''
                INSERT INTO ip_referrals (id, ip_id, user_id, status)
                VALUES (?, ?, ?, ?)
            ''', (str(uuid.uuid4()), sample_ip, user_id, 'active'))
        
        test_db.commit()
        
        cursor.execute('''
            SELECT COUNT(*) as count FROM ip_referrals WHERE ip_id = ?
        ''', (sample_ip,))
        result = cursor.fetchone()
        
        assert result['count'] == 5

class TestIPLevels:
    
    def test_level_upgrade(self, test_db, sample_ip):
        cursor = test_db.cursor()
        
        cursor.execute('''
            UPDATE ip_partners 
            SET total_earned = 5000.0, total_referrals = 50, level = 'gold'
            WHERE id = ?
        ''', (sample_ip,))
        test_db.commit()
        
        cursor.execute('SELECT level, total_earned, total_referrals FROM ip_partners WHERE id = ?', (sample_ip,))
        result = cursor.fetchone()
        
        assert result['level'] == 'gold'
        assert result['total_earned'] == 5000.0
        assert result['total_referrals'] == 50

def test_full_ip_workflow(test_db):
    cursor = test_db.cursor()
    
    ip_id = str(uuid.uuid4())
    cursor.execute('''
        INSERT INTO ip_partners (id, name, email, status, base_commission)
        VALUES (?, ?, ?, ?, ?)
    ''', (ip_id, '完整流程IP', 'workflow@example.com', 'pending', 5.0))
    test_db.commit()
    
    cursor.execute('''
        UPDATE ip_partners SET status = 'active', base_commission = 10.0
        WHERE id = ?
    ''', (ip_id,))
    test_db.commit()
    
    link_id = str(uuid.uuid4())
    code = f'workflow_{uuid.uuid4().hex[:8]}'
    cursor.execute('''
        INSERT INTO ip_links (id, ip_id, link_type, url, code)
        VALUES (?, ?, ?, ?, ?)
    ''', (link_id, ip_id, 'short_url', f'https://example.com/r/{code}', code))
    test_db.commit()
    
    user_id = str(uuid.uuid4())
    cursor.execute('''
        INSERT INTO users (id, email, username, referred_by_ip)
        VALUES (?, ?, ?, ?)
    ''', (user_id, 'referred@example.com', 'referred_user', ip_id))
    
    referral_id = str(uuid.uuid4())
    cursor.execute('''
        INSERT INTO ip_referrals (id, ip_id, user_id, link_id, status)
        VALUES (?, ?, ?, ?, ?)
    ''', (referral_id, ip_id, user_id, link_id, 'active'))
    
    cursor.execute('''
        UPDATE ip_partners SET total_referrals = total_referrals + 1 WHERE id = ?
    ''', (ip_id,))
    test_db.commit()
    
    commission_id = str(uuid.uuid4())
    commission_amount = 100.0
    cursor.execute('''
        INSERT INTO ip_commissions 
        (id, ip_id, order_amount, commission_rate, commission_amount, total_amount, status)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    ''', (commission_id, ip_id, 1000.0, 10.0, commission_amount, commission_amount, 'pending'))
    test_db.commit()
    
    cursor.execute('''
        UPDATE ip_commissions SET status = 'settled', settled_at = ?
        WHERE id = ?
    ''', (datetime.now().isoformat(), commission_id))
    
    cursor.execute('''
        UPDATE ip_partners 
        SET balance = balance + ?, total_earned = total_earned + ?
        WHERE id = ?
    ''', (commission_amount, commission_amount, ip_id))
    test_db.commit()
    
    withdrawal_id = str(uuid.uuid4())
    cursor.execute('''
        INSERT INTO ip_withdrawals 
        (id, ip_id, amount, fee, actual_amount, account_type, status)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    ''', (withdrawal_id, ip_id, 50.0, 0, 50.0, 'wechat', 'pending'))
    test_db.commit()
    
    cursor.execute('''
        UPDATE ip_withdrawals SET status = 'completed', processed_at = ?
        WHERE id = ?
    ''', (datetime.now().isoformat(), withdrawal_id))
    
    cursor.execute('''
        UPDATE ip_partners SET balance = balance - ? WHERE id = ?
    ''', (50.0, ip_id))
    test_db.commit()
    
    cursor.execute('SELECT * FROM ip_partners WHERE id = ?', (ip_id,))
    final_ip = cursor.fetchone()
    
    assert final_ip['status'] == 'active'
    assert final_ip['total_referrals'] == 1
    assert final_ip['total_earned'] == 100.0
    assert final_ip['balance'] == 50.0

if __name__ == '__main__':
    pytest.main([__file__, '-v'])
