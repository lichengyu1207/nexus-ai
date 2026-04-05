"""
积分系统体验优化 - 数据库迁移脚本
增强积分日志表和签到相关表
"""
import sqlite3
import os
from datetime import datetime

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
    
    print("开始积分系统优化迁移...")
    
    # 1. 检查并增强 integral_logs 表
    if table_exists(cursor, 'integral_logs'):
        print("检查 integral_logs 表结构...")
        
        columns_to_add = [
            ('token_change', 'INTEGER'),
            ('token_balance_after', 'INTEGER'),
            ('action_type', 'TEXT'),
            ('resource_id', 'TEXT'),
            ('resource_type', 'TEXT'),
            ('admin_id', 'TEXT'),
            ('created_at', 'TIMESTAMP DEFAULT CURRENT_TIMESTAMP'),
        ]
        
        for col, col_type in columns_to_add:
            if not column_exists(cursor, 'integral_logs', col):
                try:
                    cursor.execute(f'ALTER TABLE integral_logs ADD COLUMN {col} {col_type}')
                    print(f"  添加列: {col}")
                except Exception as e:
                    print(f"  添加列 {col} 失败: {e}")
    else:
        print("创建 integral_logs 表...")
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
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_integral_logs_user ON integral_logs(user_id)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_integral_logs_created ON integral_logs(created_at)')
    
    # 2. 创建签到记录表
    if not table_exists(cursor, 'signin_records'):
        print("创建 signin_records 表...")
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
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_signin_user_date ON signin_records(user_id, sign_date)')
    else:
        print("signin_records 表已存在")
    
    # 3. 创建用户签到统计表
    if not table_exists(cursor, 'user_signin_stats'):
        print("创建 user_signin_stats 表...")
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
    else:
        print("user_signin_stats 表已存在")
    
    # 4. 创建签到奖励配置表
    if not table_exists(cursor, 'signin_rewards_config'):
        print("创建 signin_rewards_config 表...")
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
        
        # 插入默认签到奖励配置
        default_rewards = [
            ('reward-1', 1, 1.0, 0.0, '第1天签到'),
            ('reward-2', 2, 1.0, 0.0, '第2天签到'),
            ('reward-3', 3, 1.0, 0.0, '第3天签到'),
            ('reward-4', 4, 1.0, 0.0, '第4天签到'),
            ('reward-5', 5, 1.0, 1.0, '第5天签到(连续奖励)'),
            ('reward-6', 6, 1.0, 0.0, '第6天签到'),
            ('reward-7', 7, 1.0, 3.0, '第7天签到(周奖励)'),
            ('reward-14', 14, 1.0, 5.0, '第14天签到(双周奖励)'),
            ('reward-30', 30, 1.0, 10.0, '第30天签到(月奖励)'),
        ]
        
        for reward in default_rewards:
            cursor.execute('''
                INSERT OR IGNORE INTO signin_rewards_config 
                (id, day_number, base_reward, bonus_reward, description)
                VALUES (?, ?, ?, ?, ?)
            ''', reward)
    else:
        print("signin_rewards_config 表已存在")
    
    # 5. 为现有积分日志填充时间戳
    cursor.execute('''
        SELECT COUNT(*) as count FROM integral_logs 
        WHERE created_at IS NULL OR created_at = ''
    ''')
    null_count = cursor.fetchone()[0]
    
    if null_count > 0:
        print(f"为 {null_count} 条积分日志填充时间戳...")
        cursor.execute('''
            UPDATE integral_logs 
            SET created_at = datetime('now', 'localtime')
            WHERE created_at IS NULL OR created_at = ''
        ''')
    
    # 6. 为现有积分日志计算Token值
    cursor.execute('''
        SELECT COUNT(*) as count FROM integral_logs 
        WHERE token_change IS NULL
    ''')
    null_token_count = cursor.fetchone()[0]
    
    if null_token_count > 0:
        print(f"为 {null_token_count} 条积分日志计算Token值...")
        cursor.execute('''
            UPDATE integral_logs 
            SET token_change = CAST(change * 100 AS INTEGER),
                token_balance_after = CAST(balance_after * 100 AS INTEGER)
            WHERE token_change IS NULL
        ''')
    
    conn.commit()
    conn.close()
    
    print("\n积分系统优化迁移完成!")

if __name__ == '__main__':
    migrate()
