"""
检查并发测试后的数据库状态
"""
import sqlite3
import os

DB_PATH = os.path.join(os.path.dirname(__file__), '..', 'data', 'property-ai.db')

def check_status():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    print("\n" + "="*60)
    print("IP扶持计划 - 数据库状态检查")
    print("="*60)
    
    # IP统计
    cursor.execute("SELECT COUNT(*) as count FROM ip_partners")
    total_ips = cursor.fetchone()['count']
    
    cursor.execute("SELECT COUNT(*) as count FROM ip_partners WHERE status = 'active'")
    active_ips = cursor.fetchone()['count']
    
    cursor.execute("SELECT COUNT(*) as count FROM ip_partners WHERE status = 'pending'")
    pending_ips = cursor.fetchone()['count']
    
    cursor.execute("SELECT SUM(total_earned) as total FROM ip_partners")
    total_earned = cursor.fetchone()['total'] or 0
    
    cursor.execute("SELECT SUM(balance) as total FROM ip_partners")
    total_balance = cursor.fetchone()['total'] or 0
    
    print(f"\nIP统计:")
    print(f"  总IP数: {total_ips}")
    print(f"  活跃IP: {active_ips}")
    print(f"  待审核: {pending_ips}")
    print(f"  总收益: {total_earned:.2f}元")
    print(f"  总余额: {total_balance:.2f}元")
    
    # 链接统计
    cursor.execute("SELECT COUNT(*) as count FROM ip_links")
    total_links = cursor.fetchone()['count']
    
    cursor.execute("SELECT SUM(click_count) as total FROM ip_links")
    total_clicks = cursor.fetchone()['total'] or 0
    
    cursor.execute("SELECT SUM(register_count) as total FROM ip_links")
    total_registers = cursor.fetchone()['total'] or 0
    
    print(f"\n链接统计:")
    print(f"  总链接数: {total_links}")
    print(f"  总点击数: {total_clicks}")
    print(f"  总注册数: {total_registers}")
    
    # 佣金统计
    cursor.execute("SELECT COUNT(*) as count FROM ip_commissions")
    total_commissions = cursor.fetchone()['count']
    
    cursor.execute("SELECT COUNT(*) as count FROM ip_commissions WHERE status = 'pending'")
    pending_commissions = cursor.fetchone()['count']
    
    cursor.execute("SELECT COUNT(*) as count FROM ip_commissions WHERE status = 'settled'")
    settled_commissions = cursor.fetchone()['count']
    
    cursor.execute("SELECT SUM(commission_amount) as total FROM ip_commissions")
    total_commission_amount = cursor.fetchone()['total'] or 0
    
    print(f"\n佣金统计:")
    print(f"  总记录数: {total_commissions}")
    print(f"  待结算: {pending_commissions}")
    print(f"  已结算: {settled_commissions}")
    print(f"  总佣金: {total_commission_amount:.2f}元")
    
    # 提现统计
    cursor.execute("SELECT COUNT(*) as count FROM ip_withdrawals")
    total_withdrawals = cursor.fetchone()['count']
    
    cursor.execute("SELECT COUNT(*) as count FROM ip_withdrawals WHERE status = 'pending'")
    pending_withdrawals = cursor.fetchone()['count']
    
    cursor.execute("SELECT COUNT(*) as count FROM ip_withdrawals WHERE status = 'completed'")
    completed_withdrawals = cursor.fetchone()['count']
    
    cursor.execute("SELECT SUM(amount) as total FROM ip_withdrawals")
    total_withdrawal_amount = cursor.fetchone()['total'] or 0
    
    print(f"\n提现统计:")
    print(f"  总记录数: {total_withdrawals}")
    print(f"  待处理: {pending_withdrawals}")
    print(f"  已完成: {completed_withdrawals}")
    print(f"  总金额: {total_withdrawal_amount:.2f}元")
    
    # 风控统计
    cursor.execute("SELECT COUNT(*) as count FROM ip_risk_blacklist")
    blacklist_count = cursor.fetchone()['count']
    
    print(f"\n风控统计:")
    print(f"  黑名单记录: {blacklist_count}")
    
    # 最近创建的IP（并发测试创建的）
    cursor.execute('''
        SELECT name, status, created_at 
        FROM ip_partners 
        WHERE name LIKE '%并发测试%' OR name LIKE '%测试IP%'
        ORDER BY created_at DESC 
        LIMIT 5
    ''')
    recent_ips = cursor.fetchall()
    
    if recent_ips:
        print(f"\n最近测试创建的IP:")
        for ip in recent_ips:
            print(f"  - {ip['name']}: {ip['status']} ({ip['created_at']})")
    
    conn.close()
    
    print("\n" + "="*60)

if __name__ == "__main__":
    check_status()
