"""
积分系统体验优化 - 测试用例
测试签到功能、积分日志记录、积分消耗等
"""
import pytest
import sqlite3
import os
import uuid
from datetime import datetime, date, timedelta

TEST_DB_PATH = os.path.join(os.path.dirname(__file__), 'test_integral.db')

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
            integral REAL DEFAULT 0.0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    cursor.execute('''
        CREATE TABLE integral_logs (
            id TEXT PRIMARY KEY,
            user_id TEXT NOT NULL,
            change REAL NOT NULL,
            balance_after REAL NOT NULL,
            token_change INTEGER,
            token_balance_after INTEGER,
            reason TEXT NOT NULL,
            action_type TEXT,
            resource_id TEXT,
            resource_type TEXT,
            admin_id TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(id)
        )
    ''')
    
    cursor.execute('''
        CREATE TABLE signin_records (
            id TEXT PRIMARY KEY,
            user_id TEXT NOT NULL,
            sign_date DATE NOT NULL,
            reward_integral REAL NOT NULL,
            reward_tokens INTEGER NOT NULL,
            consecutive_days INTEGER,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(id),
            UNIQUE(user_id, sign_date)
        )
    ''')
    
    cursor.execute('''
        CREATE TABLE user_signin_stats (
            user_id TEXT PRIMARY KEY,
            total_days INTEGER DEFAULT 0,
            current_streak INTEGER DEFAULT 0,
            max_streak INTEGER DEFAULT 0,
            last_sign_date DATE,
            total_rewards REAL DEFAULT 0.0,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(id)
        )
    ''')
    
    cursor.execute('''
        CREATE TABLE signin_rewards_config (
            id TEXT PRIMARY KEY,
            day_number INTEGER NOT NULL UNIQUE,
            base_reward REAL NOT NULL,
            bonus_reward REAL DEFAULT 0.0,
            description TEXT,
            is_active INTEGER DEFAULT 1
        )
    ''')
    
    default_rewards = [
        ('reward-1', 1, 1.0, 0.0, '第1天签到'),
        ('reward-7', 7, 1.0, 3.0, '第7天签到(周奖励)'),
        ('reward-30', 30, 1.0, 10.0, '第30天签到(月奖励)'),
    ]
    
    for reward in default_rewards:
        cursor.execute('''
            INSERT INTO signin_rewards_config 
            (id, day_number, base_reward, bonus_reward, description)
            VALUES (?, ?, ?, ?, ?)
        ''', reward)
    
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
        INSERT INTO users (id, email, username, integral)
        VALUES (?, ?, ?, ?)
    ''', (user_id, f'test_{user_id[:8]}@example.com', f'testuser_{user_id[:8]}', 0.0))
    test_db.commit()
    return user_id

class TestIntegralLog:
    
    def test_record_integral_log(self, test_db, sample_user):
        cursor = test_db.cursor()
        
        log_id = str(uuid.uuid4())
        change = 10.0
        balance_after = 10.0
        token_change = int(change * 100)
        token_balance = int(balance_after * 100)
        
        cursor.execute('''
            INSERT INTO integral_logs 
            (id, user_id, change, balance_after, token_change, token_balance_after, reason, action_type, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (log_id, sample_user, change, balance_after, token_change, token_balance, '测试奖励', 'test', datetime.now().isoformat()))
        test_db.commit()
        
        cursor.execute('SELECT * FROM integral_logs WHERE id = ?', (log_id,))
        result = cursor.fetchone()
        
        assert result is not None
        assert result['change'] == 10.0
        assert result['token_change'] == 1000
        assert result['action_type'] == 'test'
    
    def test_integral_log_with_timestamp(self, test_db, sample_user):
        cursor = test_db.cursor()
        
        log_id = str(uuid.uuid4())
        created_at = datetime.now().isoformat()
        
        cursor.execute('''
            INSERT INTO integral_logs 
            (id, user_id, change, balance_after, token_change, token_balance_after, reason, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        ''', (log_id, sample_user, 5.0, 5.0, 500, 500, '带时间戳的日志', created_at))
        test_db.commit()
        
        cursor.execute('SELECT created_at FROM integral_logs WHERE id = ?', (log_id,))
        result = cursor.fetchone()
        
        assert result['created_at'] is not None
        assert len(result['created_at']) > 0

class TestSignin:
    
    def test_first_signin(self, test_db, sample_user):
        cursor = test_db.cursor()
        today = date.today().isoformat()
        
        signin_id = str(uuid.uuid4())
        reward = 1.0
        reward_tokens = int(reward * 100)
        
        cursor.execute('''
            INSERT INTO signin_records 
            (id, user_id, sign_date, reward_integral, reward_tokens, consecutive_days)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (signin_id, sample_user, today, reward, reward_tokens, 1))
        
        cursor.execute('''
            UPDATE users SET integral = integral + ? WHERE id = ?
        ''', (reward, sample_user))
        
        cursor.execute('''
            INSERT INTO user_signin_stats (user_id, total_days, current_streak, max_streak, last_sign_date, total_rewards)
            VALUES (?, 1, 1, 1, ?, ?)
        ''', (sample_user, today, reward))
        
        test_db.commit()
        
        cursor.execute('SELECT * FROM signin_records WHERE user_id = ?', (sample_user,))
        signin = cursor.fetchone()
        
        cursor.execute('SELECT * FROM user_signin_stats WHERE user_id = ?', (sample_user,))
        stats = cursor.fetchone()
        
        cursor.execute('SELECT integral FROM users WHERE id = ?', (sample_user,))
        user = cursor.fetchone()
        
        assert signin is not None
        assert signin['consecutive_days'] == 1
        assert stats['current_streak'] == 1
        assert user['integral'] == 1.0
    
    def test_duplicate_signin(self, test_db, sample_user):
        cursor = test_db.cursor()
        today = date.today().isoformat()
        
        signin_id = str(uuid.uuid4())
        cursor.execute('''
            INSERT INTO signin_records 
            (id, user_id, sign_date, reward_integral, reward_tokens, consecutive_days)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (signin_id, sample_user, today, 1.0, 100, 1))
        test_db.commit()
        
        with pytest.raises(sqlite3.IntegrityError):
            cursor.execute('''
                INSERT INTO signin_records 
                (id, user_id, sign_date, reward_integral, reward_tokens, consecutive_days)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', (str(uuid.uuid4()), sample_user, today, 1.0, 100, 1))
            test_db.commit()
    
    def test_consecutive_signin(self, test_db, sample_user):
        cursor = test_db.cursor()
        
        yesterday = (date.today() - timedelta(days=1)).isoformat()
        signin_id1 = str(uuid.uuid4())
        cursor.execute('''
            INSERT INTO signin_records 
            (id, user_id, sign_date, reward_integral, reward_tokens, consecutive_days)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (signin_id1, sample_user, yesterday, 1.0, 100, 1))
        
        cursor.execute('''
            INSERT INTO user_signin_stats (user_id, total_days, current_streak, max_streak, last_sign_date)
            VALUES (?, 1, 1, 1, ?)
        ''', (sample_user, yesterday))
        
        test_db.commit()
        
        today = date.today().isoformat()
        signin_id2 = str(uuid.uuid4())
        cursor.execute('''
            INSERT INTO signin_records 
            (id, user_id, sign_date, reward_integral, reward_tokens, consecutive_days)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (signin_id2, sample_user, today, 2.0, 200, 2))
        
        cursor.execute('''
            UPDATE user_signin_stats 
            SET total_days = 2, current_streak = 2, max_streak = 2, last_sign_date = ?
            WHERE user_id = ?
        ''', (today, sample_user))
        
        test_db.commit()
        
        cursor.execute('SELECT * FROM user_signin_stats WHERE user_id = ?', (sample_user,))
        stats = cursor.fetchone()
        
        assert stats['current_streak'] == 2
        assert stats['total_days'] == 2

class TestSigninRewards:
    
    def test_base_reward(self, test_db):
        cursor = test_db.cursor()
        
        cursor.execute('''
            SELECT base_reward, bonus_reward FROM signin_rewards_config
            WHERE day_number = 1
        ''')
        result = cursor.fetchone()
        
        assert result['base_reward'] == 1.0
        assert result['bonus_reward'] == 0.0
    
    def test_weekly_bonus(self, test_db):
        cursor = test_db.cursor()
        
        cursor.execute('''
            SELECT base_reward, bonus_reward FROM signin_rewards_config
            WHERE day_number = 7
        ''')
        result = cursor.fetchone()
        
        assert result['base_reward'] == 1.0
        assert result['bonus_reward'] == 3.0
    
    def test_monthly_bonus(self, test_db):
        cursor = test_db.cursor()
        
        cursor.execute('''
            SELECT base_reward, bonus_reward FROM signin_rewards_config
            WHERE day_number = 30
        ''')
        result = cursor.fetchone()
        
        assert result['base_reward'] == 1.0
        assert result['bonus_reward'] == 10.0

class TestTokenConversion:
    
    def test_integral_to_token(self, test_db, sample_user):
        cursor = test_db.cursor()
        
        integral = 5.5
        tokens = int(integral * 100)
        
        assert tokens == 550
    
    def test_log_token_calculation(self, test_db, sample_user):
        cursor = test_db.cursor()
        
        log_id = str(uuid.uuid4())
        change = 3.5
        balance_after = 3.5
        token_change = int(change * 100)
        token_balance = int(balance_after * 100)
        
        cursor.execute('''
            INSERT INTO integral_logs 
            (id, user_id, change, balance_after, token_change, token_balance_after, reason, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        ''', (log_id, sample_user, change, balance_after, token_change, token_balance, '测试', datetime.now().isoformat()))
        test_db.commit()
        
        cursor.execute('SELECT * FROM integral_logs WHERE id = ?', (log_id,))
        result = cursor.fetchone()
        
        assert result['token_change'] == 350
        assert result['token_balance_after'] == 350

class TestIntegralConsumption:
    
    def test_consume_integral(self, test_db, sample_user):
        cursor = test_db.cursor()
        
        cursor.execute('UPDATE users SET integral = 10.0 WHERE id = ?', (sample_user,))
        test_db.commit()
        
        consume_amount = 5.0
        cursor.execute('SELECT integral FROM users WHERE id = ?', (sample_user,))
        old_balance = cursor.fetchone()['integral']
        
        new_balance = old_balance - consume_amount
        cursor.execute('UPDATE users SET integral = ? WHERE id = ?', (new_balance, sample_user))
        
        log_id = str(uuid.uuid4())
        cursor.execute('''
            INSERT INTO integral_logs 
            (id, user_id, change, balance_after, token_change, token_balance_after, reason, action_type, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (log_id, sample_user, -consume_amount, new_balance, int(-consume_amount * 100), int(new_balance * 100), '消费', 'consume', datetime.now().isoformat()))
        
        test_db.commit()
        
        cursor.execute('SELECT integral FROM users WHERE id = ?', (sample_user,))
        result = cursor.fetchone()
        
        assert result['integral'] == 5.0
    
    def test_insufficient_balance(self, test_db, sample_user):
        cursor = test_db.cursor()
        
        cursor.execute('SELECT integral FROM users WHERE id = ?', (sample_user,))
        balance = cursor.fetchone()['integral']
        
        consume_amount = balance + 100
        
        can_consume = balance >= consume_amount
        
        assert can_consume == False

def test_full_signin_flow(test_db):
    cursor = test_db.cursor()
    
    user_id = str(uuid.uuid4())
    cursor.execute('''
        INSERT INTO users (id, email, username, integral)
        VALUES (?, ?, ?, ?)
    ''', (user_id, f'flow_{user_id[:8]}@example.com', f'flowuser_{user_id[:8]}', 0.0))
    test_db.commit()
    
    for day in range(1, 8):
        sign_date = (date.today() - timedelta(days=7-day)).isoformat()
        signin_id = str(uuid.uuid4())
        
        cursor.execute('''
            SELECT base_reward + bonus_reward as total FROM signin_rewards_config
            WHERE day_number = ? AND is_active = 1
        ''', (day,))
        reward_result = cursor.fetchone()
        reward = reward_result['total'] if reward_result else 1.0
        
        cursor.execute('''
            INSERT INTO signin_records 
            (id, user_id, sign_date, reward_integral, reward_tokens, consecutive_days)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (signin_id, user_id, sign_date, reward, int(reward * 100), day))
        
        cursor.execute('UPDATE users SET integral = integral + ? WHERE id = ?', (reward, user_id))
        
        log_id = str(uuid.uuid4())
        cursor.execute('SELECT integral FROM users WHERE id = ?', (user_id,))
        current_balance = cursor.fetchone()['integral']
        
        cursor.execute('''
            INSERT INTO integral_logs 
            (id, user_id, change, balance_after, token_change, token_balance_after, reason, action_type, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (log_id, user_id, reward, current_balance, int(reward * 100), int(current_balance * 100), 
              f'签到奖励(第{day}天)', 'signin', datetime.now().isoformat()))
        
        test_db.commit()
    
    cursor.execute('SELECT integral FROM users WHERE id = ?', (user_id,))
    final_balance = cursor.fetchone()['integral']
    
    cursor.execute('SELECT COUNT(*) as count FROM signin_records WHERE user_id = ?', (user_id,))
    signin_count = cursor.fetchone()['count']
    
    cursor.execute('SELECT COUNT(*) as count FROM integral_logs WHERE user_id = ?', (user_id,))
    log_count = cursor.fetchone()['count']
    
    assert signin_count == 7
    assert log_count == 7
    assert final_balance > 7.0

if __name__ == '__main__':
    pytest.main([__file__, '-v'])
