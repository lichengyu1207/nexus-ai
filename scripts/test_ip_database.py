"""
IP扶持计划 - 数据库直接测试
"""
import sqlite3
import os
import uuid
from datetime import datetime

DB_PATH = os.path.join(os.path.dirname(__file__), '..', 'data', 'property-ai.db')

def test_database():
    print("\n" + "="*60)
    print("IP扶持计划 - 数据库直接测试")
    print("="*60 + "\n")
    
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    # 1. 检查表是否存在
    print("1. 检查数据库表...")
    tables = ['ip_partners', 'ip_links', 'ip_referrals', 'ip_commissions', 
              'ip_withdrawals', 'ip_content_drafts', 'ip_commission_rules', 
              'ip_levels', 'ip_operation_logs', 'ip_risk_blacklist']
    
    for table in tables:
        cursor.execute(f"SELECT name FROM sqlite_master WHERE type='table' AND name=?", (table,))
        if cursor.fetchone():
            print(f"   ✅ {table} 表存在")
        else:
            print(f"   ❌ {table} 表不存在")
    
    # 2. 检查IP等级配置
    print("\n2. 检查IP等级配置...")
    cursor.execute("SELECT * FROM ip_levels ORDER BY min_earnings")
    levels = cursor.fetchall()
    for level in levels:
        print(f"   - {level['level_name']}: 最低收益{level['min_earnings']}元, 佣金加成{level['commission_bonus']}%")
    
    # 3. 检查佣金规则
    print("\n3. 检查佣金规则...")
    cursor.execute("SELECT * FROM ip_commission_rules WHERE is_active = 1 ORDER BY priority")
    rules = cursor.fetchall()
    for rule in rules:
        print(f"   - {rule['name']}: {rule['commission_rate']}% (类型: {rule['rule_type']})")
    
    # 4. 创建测试IP
    print("\n4. 创建测试IP...")
    test_ip_id = str(uuid.uuid4())
    unique_id = str(uuid.uuid4())[:8]
    try:
        cursor.execute('''
            INSERT INTO ip_partners 
            (id, name, contact, email, platform_type, platform_id, followers, status, base_commission, level)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (test_ip_id, f'测试IP_{unique_id}', f'wechat_{unique_id}', 
              f'ip_{unique_id}@test.com', 'zhihu', f'zhihu_{unique_id}', 
              50000, 'active', 10.0, 'bronze'))
        conn.commit()
        print(f"   ✅ 测试IP创建成功: {test_ip_id[:8]}...")
    except Exception as e:
        print(f"   ❌ 创建失败: {e}")
    
    # 5. 创建测试链接
    print("\n5. 创建测试推广链接...")
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
        print(f"   ✅ 测试链接创建成功: {link_code}")
    except Exception as e:
        print(f"   ❌ 创建失败: {e}")
    
    # 6. 模拟佣金计算
    print("\n6. 模拟佣金计算...")
    commission_id = str(uuid.uuid4())
    order_amount = 1000.0
    commission_rate = 10.0
    commission_amount = order_amount * commission_rate / 100
    
    try:
        cursor.execute('''
            INSERT INTO ip_commissions 
            (id, ip_id, order_amount, commission_rate, commission_amount, total_amount, status)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', (commission_id, test_ip_id, order_amount, commission_rate, 
              commission_amount, commission_amount, 'pending'))
        conn.commit()
        print(f"   ✅ 佣金记录创建: 订单{order_amount}元, 佣金{commission_amount}元")
    except Exception as e:
        print(f"   ❌ 创建失败: {e}")
    
    # 7. 结算佣金
    print("\n7. 结算佣金...")
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
        print(f"   ✅ 佣金结算成功: +{commission_amount}元")
    except Exception as e:
        print(f"   ❌ 结算失败: {e}")
    
    # 8. 检查IP余额
    print("\n8. 检查IP余额...")
    cursor.execute('SELECT balance, total_earned FROM ip_partners WHERE id = ?', (test_ip_id,))
    result = cursor.fetchone()
    if result:
        print(f"   ✅ 余额: {result['balance']}元, 总收益: {result['total_earned']}元")
    
    # 9. 创建提现申请
    print("\n9. 创建提现申请...")
    withdrawal_id = str(uuid.uuid4())
    try:
        cursor.execute('''
            INSERT INTO ip_withdrawals 
            (id, ip_id, amount, fee, actual_amount, account_type, account_name, status)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        ''', (withdrawal_id, test_ip_id, 50.0, 0, 50.0, 'wechat', '测试账户', 'pending'))
        conn.commit()
        print(f"   ✅ 提现申请创建: 50元")
    except Exception as e:
        print(f"   ❌ 创建失败: {e}")
    
    # 10. 处理提现
    print("\n10. 处理提现...")
    try:
        cursor.execute('''
            UPDATE ip_withdrawals SET status = 'completed', processed_at = ?
            WHERE id = ?
        ''', (datetime.now().isoformat(), withdrawal_id))
        
        cursor.execute('''
            UPDATE ip_partners SET balance = balance - ? WHERE id = ?
        ''', (50.0, test_ip_id))
        conn.commit()
        print(f"   ✅ 提现处理成功: -50元")
    except Exception as e:
        print(f"   ❌ 处理失败: {e}")
    
    # 11. 最终状态
    print("\n11. 最终IP状态...")
    cursor.execute('SELECT * FROM ip_partners WHERE id = ?', (test_ip_id,))
    ip = cursor.fetchone()
    if ip:
        print(f"   名称: {ip['name']}")
        print(f"   状态: {ip['status']}")
        print(f"   等级: {ip['level']}")
        print(f"   余额: {ip['balance']}元")
        print(f"   总收益: {ip['total_earned']}元")
    
    # 12. 统计数据
    print("\n12. 统计数据...")
    cursor.execute("SELECT COUNT(*) as count FROM ip_partners")
    total_ips = cursor.fetchone()['count']
    
    cursor.execute("SELECT COUNT(*) as count FROM ip_partners WHERE status = 'active'")
    active_ips = cursor.fetchone()['count']
    
    cursor.execute("SELECT SUM(total_earned) as total FROM ip_partners")
    total_earned = cursor.fetchone()['total'] or 0
    
    cursor.execute("SELECT COUNT(*) as count FROM ip_commissions")
    total_commissions = cursor.fetchone()['count']
    
    print(f"   总IP数: {total_ips}")
    print(f"   活跃IP: {active_ips}")
    print(f"   总佣金: {total_earned}元")
    print(f"   佣金记录: {total_commissions}条")
    
    conn.close()
    
    print("\n" + "="*60)
    print("数据库测试完成!")
    print("="*60)

if __name__ == "__main__":
    test_database()
