"""
检查并修复IP扶持计划数据库表结构
"""
import sqlite3
import os

DB_PATH = os.path.join(os.path.dirname(__file__), '..', 'data', 'property-ai.db')

def check_and_fix():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    print("检查 ip_partners 表结构...")
    cursor.execute('PRAGMA table_info(ip_partners)')
    columns = [col[1] for col in cursor.fetchall()]
    print(f"当前列: {columns}")
    
    required_columns = {
        'email': 'TEXT',
        'balance': 'REAL DEFAULT 0.0',
        'total_earned': 'REAL DEFAULT 0.0',
        'frozen_balance': 'REAL DEFAULT 0.0',
        'total_orders': 'INTEGER DEFAULT 0',
        'admin_notes': 'TEXT',
        'avatar': 'TEXT',
        'platform_name': 'TEXT',
    }
    
    for col, col_type in required_columns.items():
        if col not in columns:
            try:
                cursor.execute(f'ALTER TABLE ip_partners ADD COLUMN {col} {col_type}')
                print(f"  添加列: {col}")
            except Exception as e:
                print(f"  添加列 {col} 失败: {e}")
    
    conn.commit()
    
    print("\n检查 ip_commissions 表结构...")
    cursor.execute('PRAGMA table_info(ip_commissions)')
    columns = [col[1] for col in cursor.fetchall()]
    print(f"当前列: {columns}")
    
    commission_columns = {
        'bonus_amount': 'REAL DEFAULT 0.0',
        'total_amount': 'REAL NOT NULL DEFAULT 0.0',
        'settled_at': 'TIMESTAMP',
        'notes': 'TEXT',
    }
    
    for col, col_type in commission_columns.items():
        if col not in columns:
            try:
                cursor.execute(f'ALTER TABLE ip_commissions ADD COLUMN {col} {col_type}')
                print(f"  添加列: {col}")
            except Exception as e:
                print(f"  添加列 {col} 失败: {e}")
    
    conn.commit()
    
    print("\n检查 ip_withdrawals 表结构...")
    cursor.execute('PRAGMA table_info(ip_withdrawals)')
    columns = [col[1] for col in cursor.fetchall()]
    print(f"当前列: {columns}")
    
    withdrawal_columns = {
        'account_name': 'TEXT',
        'processed_at': 'TIMESTAMP',
        'processed_by': 'TEXT',
    }
    
    for col, col_type in withdrawal_columns.items():
        if col not in columns:
            try:
                cursor.execute(f'ALTER TABLE ip_withdrawals ADD COLUMN {col} {col_type}')
                print(f"  添加列: {col}")
            except Exception as e:
                print(f"  添加列 {col} 失败: {e}")
    
    conn.commit()
    
    print("\n最终 ip_partners 表结构:")
    cursor.execute('PRAGMA table_info(ip_partners)')
    for col in cursor.fetchall():
        print(f"  {col[1]}: {col[2]}")
    
    conn.close()
    print("\n数据库结构检查完成!")

if __name__ == "__main__":
    check_and_fix()
