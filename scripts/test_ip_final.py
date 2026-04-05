"""
IP扶持计划 - 最终数据库测试（适配实际表结构）
"""
import sqlite3
import os
import uuid
from datetime import datetime

DB_PATH = os.path.join(os.path.dirname(__file__), '..', 'data', 'property-ai.db')

def test_database():
    print("\n" + "="*60)
    print("IP扶持计划 - 全周期可用性测试")
    print("="*60 + "\n")
    
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    # 1. 检查表是否存在
    print("1. 检查数据库表...")
    tables = ['ip_partners', 'ip_links', 'ip_referrals', 'ip_commissions', 
              'ip_withdrawals', 'ip_content_drafts', 'ip_commission_rules', 
              'ip_levels', 'ip_operation_logs', 'ip_risk_blacklist']
    
    all_tables_exist = True
    for table in tables:
        cursor.execute(f"SELECT name FROM sqlite_master WHERE type='table' AND name=?", (table,))
        if cursor.fetchone():
            print(f"   ✅ {table}")
        else:
            print(f"   ❌ {table} 不存在")
            all_tables_exist = False
    
    if not all_tables_exist:
        print("\n   请先运行迁移脚本: python scripts/migrate_ip_plan.py")
        conn.close()
        return
    
    # 2. 检查IP等级配置
    print("\n2. IP等级配置...")
    cursor.execute("SELECT * FROM ip_levels ORDER BY min_earnings")
    levels = cursor.fetchall()
    for level in levels:
        print(f"   ✅ {level['level_name']}: 收益≥{level['min_earnings']}元, 加成{level['commission_bonus']}%")
    
    # 3. 检查佣金规则
    print("\n3. 佣金规则配置...")
    cursor.execute("SELECT * FROM ip_commission_rules WHERE is_active = 1 ORDER BY priority")
    rules = cursor.fetchall()
    for rule in rules:
        print(f"   ✅ {rule['name']}: {rule['commission_rate']}%")
    
    # 4. 创建测试IP
    print("\n4. 创建测试IP...")
    test_ip_id = str(uuid.uuid4())
    unique_id = str(uuid.uuid4())[:8]
    try:
        cursor.execute('''
            INSERT INTO ip_partners 
            (id, name, contact, email, platform, platform_id, platform_name, followers, status, commission_rate, balance, total_earned, level)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (test_ip_id, f'测试IP_{unique_id}', f'wechat_{unique_id}', 
              f'ip_{unique_id}@test.com', 'zhihu', f'zhihu_{unique_id}', 
              '知乎测试账号', 50000, 'active', 10, 0.0, 0.0, 'bronze'))
        conn.commit()
        print(f"   ✅ IP创建成功: {test_ip_id[:8]}...")
    except Exception as e:
        print(f"   ❌ 创建失败: {e}")
        conn.close()
        return
    
    # 5. 创建推广链接
    print("\n5. 创建推广链接...")
    link_id = str(uuid.uuid4())
    link_code = f'test_{uuid.uuid4().hex[:8]}'
    try:
        cursor.execute('''
            INSERT INTO ip_links 
            (id, ip_id, link_type, url, code, channel, click_count, register_count)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        ''', (link_id, test_ip_id, 'short_url', f'https://example.com/r/{link_code}', 
              link_code, 'wechat', 0, 0))
        conn.commit()
        print(f"   ✅ 链接创建成功: {link_code}")
    except Exception as e:
        print(f"   ❌ 创建失败: {e}")
    
    # 6. 模拟点击
    print("\n6. 模拟链接点击...")
    try:
        cursor.execute('UPDATE ip_links SET click_count = click_count + 1 WHERE id = ?', (link_id,))
        conn.commit()
        cursor.execute('SELECT click_count FROM ip_links WHERE id = ?', (link_id,))
        result = cursor.fetchone()
        print(f"   ✅ 点击次数: {result['click_count']}")
    except Exception as e:
        print(f"   ❌ 点击失败: {e}")
    
    # 7. 佣金计算
    print("\n7. 佣金计算...")
    commission_id = str(uuid.uuid4())
    order_amount = 1000.0
    commission_rate = 10.0
    commission_amount = order_amount * commission_rate / 100
    
    try:
        cursor.execute('''
            INSERT INTO ip_commissions 
            (id, ip_id, order_amount, commission_rate, commission_amount, total_amount, status, order_type)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        ''', (commission_id, test_ip_id, order_amount, commission_rate, 
              commission_amount, commission_amount, 'pending', 'recharge'))
        conn.commit()
        print(f"   ✅ 佣金记录: 订单{order_amount}元 → 佣金{commission_amount}元")
    except Exception as e:
        print(f"   ❌ 创建失败: {e}")
    
    # 8. 佣金结算
    print("\n8. 佣金结算...")
    try:
        cursor.execute('''
            UPDATE ip_commissions SET status = 'settled', settled_at = ?
            WHERE id = ?
        ''', (datetime.now().isoformat(), commission_id))
        
        cursor.execute('''
            UPDATE ip_partners 
            SET balance = balance + ?, total_earned = total_earned + ?
            WHERE id = ?
        ''', (commission_amount, commission_amount, test_ip_id))
        conn.commit()
        
        cursor.execute('SELECT balance, total_earned FROM ip_partners WHERE id = ?', (test_ip_id,))
        result = cursor.fetchone()
        print(f"   ✅ 结算成功: 余额={result['balance']}元, 总收益={result['total_earned']}元")
    except Exception as e:
        print(f"   ❌ 结算失败: {e}")
    
    # 9. 提现申请
    print("\n9. 提现申请...")
    withdrawal_id = str(uuid.uuid4())
    try:
        cursor.execute('''
            INSERT INTO ip_withdrawals 
            (id, ip_id, amount, account_type, account_info, status)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (withdrawal_id, test_ip_id, 50.0, 'wechat', 'test_wechat_id', 'pending'))
        conn.commit()
        print(f"   ✅ 提现申请: 50元")
    except Exception as e:
        print(f"   ❌ 申请失败: {e}")
    
    # 10. 提现处理
    print("\n10. 提现处理...")
    try:
        cursor.execute('''
            UPDATE ip_withdrawals SET status = 'completed', processed_at = ?
            WHERE id = ?
        ''', (datetime.now().isoformat(), withdrawal_id))
        
        cursor.execute('''
            UPDATE ip_partners SET balance = balance - ? WHERE id = ?
        ''', (50.0, test_ip_id))
        conn.commit()
        
        cursor.execute('SELECT balance FROM ip_partners WHERE id = ?', (test_ip_id,))
        result = cursor.fetchone()
        print(f"   ✅ 提现成功: 剩余余额={result['balance']}元")
    except Exception as e:
        print(f"   ❌ 处理失败: {e}")
    
    # 11. 风控检查
    print("\n11. 风控黑名单...")
    try:
        cursor.execute('SELECT COUNT(*) as count FROM ip_risk_blacklist')
        count = cursor.fetchone()['count']
        print(f"   ✅ 黑名单记录: {count}条")
    except Exception as e:
        print(f"   ❌ 查询失败: {e}")
    
    # 12. 操作日志
    print("\n12. 操作日志...")
    try:
        log_id = str(uuid.uuid4())
        cursor.execute('''
            INSERT INTO ip_operation_logs (id, ip_id, operation_type, details, created_at)
            VALUES (?, ?, ?, ?, ?)
        ''', (log_id, test_ip_id, 'test', '全周期测试完成', datetime.now().isoformat()))
        conn.commit()
        
        cursor.execute('SELECT COUNT(*) as count FROM ip_operation_logs')
        count = cursor.fetchone()['count']
        print(f"   ✅ 日志记录: {count}条")
    except Exception as e:
        print(f"   ❌ 记录失败: {e}")
    
    # 13. 最终统计
    print("\n13. 最终统计...")
    cursor.execute("SELECT COUNT(*) as count FROM ip_partners")
    total_ips = cursor.fetchone()['count']
    
    cursor.execute("SELECT COUNT(*) as count FROM ip_partners WHERE status = 'active'")
    active_ips = cursor.fetchone()['count']
    
    cursor.execute("SELECT SUM(total_earned) as total FROM ip_partners")
    total_earned = cursor.fetchone()['total'] or 0
    
    cursor.execute("SELECT COUNT(*) as count FROM ip_commissions")
    total_commissions = cursor.fetchone()['count']
    
    cursor.execute("SELECT COUNT(*) as count FROM ip_links")
    total_links = cursor.fetchone()['count']
    
    print(f"   总IP数: {total_ips}")
    print(f"   活跃IP: {active_ips}")
    print(f"   推广链接: {total_links}")
    print(f"   佣金记录: {total_commissions}")
    print(f"   总佣金: {total_earned}元")
    
    conn.close()
    
    print("\n" + "="*60)
    print("✅ IP扶持计划全周期测试完成!")
    print("="*60)

if __name__ == "__main__":
    test_database()
