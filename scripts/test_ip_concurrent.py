"""
IP扶持计划 - 并发压力测试
模拟1000人在全周期使用中的各种场景，包括日常使用和突发高峰
"""
import sqlite3
import os
import uuid
import time
import random
import threading
from datetime import datetime, timedelta
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass
from typing import List, Dict
import queue

DB_PATH = os.path.join(os.path.dirname(__file__), '..', 'data', 'property-ai.db')

# 线程安全的统计收集
class StatsCollector:
    def __init__(self):
        self.lock = threading.Lock()
        self.results = {
            'success': 0,
            'failure': 0,
            'errors': [],
            'latencies': [],
            'operations': {}
        }
    
    def record_success(self, operation: str, latency: float):
        with self.lock:
            self.results['success'] += 1
            self.results['latencies'].append(latency)
            if operation not in self.results['operations']:
                self.results['operations'][operation] = {'success': 0, 'failure': 0}
            self.results['operations'][operation]['success'] += 1
    
    def record_failure(self, operation: str, error: str):
        with self.lock:
            self.results['failure'] += 1
            self.results['errors'].append({'operation': operation, 'error': str(error)[:100]})
            if operation not in self.results['operations']:
                self.results['operations'][operation] = {'success': 0, 'failure': 0}
            self.results['operations'][operation]['failure'] += 1
    
    def get_stats(self):
        with self.lock:
            latencies = self.results['latencies']
            avg_latency = sum(latencies) / len(latencies) if latencies else 0
            max_latency = max(latencies) if latencies else 0
            min_latency = min(latencies) if latencies else 0
            
            return {
                'total': self.results['success'] + self.results['failure'],
                'success': self.results['success'],
                'failure': self.results['failure'],
                'success_rate': self.results['success'] / (self.results['success'] + self.results['failure']) * 100 if (self.results['success'] + self.results['failure']) > 0 else 0,
                'avg_latency_ms': avg_latency * 1000,
                'max_latency_ms': max_latency * 1000,
                'min_latency_ms': min_latency * 1000,
                'operations': self.results['operations'],
                'errors': self.results['errors'][:10]  # 只显示前10个错误
            }

stats = StatsCollector()

def get_db_connection():
    conn = sqlite3.connect(DB_PATH, timeout=30.0)
    conn.row_factory = sqlite3.Row
    return conn

# ========== 测试操作 ==========

def test_ip_apply(user_id: int):
    """测试IP申请"""
    start = time.time()
    conn = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        ip_id = str(uuid.uuid4())
        unique_id = str(uuid.uuid4())[:8]
        
        cursor.execute('''
            INSERT INTO ip_partners 
            (id, name, contact, email, platform, platform_id, platform_name, followers, status, commission_rate, balance, total_earned, level)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (ip_id, f'并发测试IP_{user_id}', f'wechat_{unique_id}', 
              f'ip_{unique_id}@test.com', 'zhihu', f'zhihu_{unique_id}', 
              '知乎测试账号', random.randint(1000, 100000), 'pending', 5, 0.0, 0.0, 'bronze'))
        conn.commit()
        
        latency = time.time() - start
        stats.record_success('ip_apply', latency)
        return {'success': True, 'ip_id': ip_id}
    except Exception as e:
        latency = time.time() - start
        stats.record_failure('ip_apply', str(e))
        return {'success': False, 'error': str(e)}
    finally:
        if conn:
            conn.close()

def test_link_create(ip_id: str, user_id: int):
    """测试链接创建"""
    start = time.time()
    conn = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        link_id = str(uuid.uuid4())
        link_code = f'link_{uuid.uuid4().hex[:8]}_{user_id}'
        
        cursor.execute('''
            INSERT INTO ip_links 
            (id, ip_id, link_type, url, code, channel, click_count, register_count)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        ''', (link_id, ip_id, 'short_url', f'https://example.com/r/{link_code}', 
              link_code, random.choice(['wechat', 'zhihu', 'douyin', 'bilibili']), 0, 0))
        conn.commit()
        
        latency = time.time() - start
        stats.record_success('link_create', latency)
        return {'success': True, 'link_code': link_code}
    except Exception as e:
        latency = time.time() - start
        stats.record_failure('link_create', str(e))
        return {'success': False, 'error': str(e)}
    finally:
        if conn:
            conn.close()

def test_link_click(link_code: str):
    """测试链接点击"""
    start = time.time()
    conn = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            UPDATE ip_links SET click_count = click_count + 1 WHERE code = ?
        ''', (link_code,))
        conn.commit()
        
        latency = time.time() - start
        stats.record_success('link_click', latency)
        return {'success': True}
    except Exception as e:
        latency = time.time() - start
        stats.record_failure('link_click', str(e))
        return {'success': False, 'error': str(e)}
    finally:
        if conn:
            conn.close()

def test_commission_create(ip_id: str, order_amount: float):
    """测试佣金创建"""
    start = time.time()
    conn = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        commission_id = str(uuid.uuid4())
        commission_rate = 10.0
        commission_amount = order_amount * commission_rate / 100
        
        cursor.execute('''
            INSERT INTO ip_commissions 
            (id, ip_id, order_amount, commission_rate, commission_amount, total_amount, status, order_type)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        ''', (commission_id, ip_id, order_amount, commission_rate, 
              commission_amount, commission_amount, 'pending', 'recharge'))
        conn.commit()
        
        latency = time.time() - start
        stats.record_success('commission_create', latency)
        return {'success': True, 'commission_id': commission_id}
    except Exception as e:
        latency = time.time() - start
        stats.record_failure('commission_create', str(e))
        return {'success': False, 'error': str(e)}
    finally:
        if conn:
            conn.close()

def test_commission_settle(ip_id: str, amount: float):
    """测试佣金结算"""
    start = time.time()
    conn = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # 获取一个待结算的佣金
        cursor.execute('''
            SELECT id, commission_amount FROM ip_commissions 
            WHERE ip_id = ? AND status = 'pending' LIMIT 1
        ''', (ip_id,))
        commission = cursor.fetchone()
        
        if commission:
            cursor.execute('''
                UPDATE ip_commissions SET status = 'settled', settled_at = ?
                WHERE id = ?
            ''', (datetime.now().isoformat(), commission['id']))
            
            cursor.execute('''
                UPDATE ip_partners 
                SET balance = balance + ?, total_earned = total_earned + ?
                WHERE id = ?
            ''', (commission['commission_amount'], commission['commission_amount'], ip_id))
            conn.commit()
        
        latency = time.time() - start
        stats.record_success('commission_settle', latency)
        return {'success': True}
    except Exception as e:
        latency = time.time() - start
        stats.record_failure('commission_settle', str(e))
        return {'success': False, 'error': str(e)}
    finally:
        if conn:
            conn.close()

def test_withdraw(ip_id: str, amount: float):
    """测试提现申请"""
    start = time.time()
    conn = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        withdrawal_id = str(uuid.uuid4())
        
        cursor.execute('''
            INSERT INTO ip_withdrawals 
            (id, ip_id, amount, account_type, account_info, status)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (withdrawal_id, ip_id, amount, 'wechat', f'wechat_{uuid.uuid4().hex[:8]}', 'pending'))
        conn.commit()
        
        latency = time.time() - start
        stats.record_success('withdraw', latency)
        return {'success': True, 'withdrawal_id': withdrawal_id}
    except Exception as e:
        latency = time.time() - start
        stats.record_failure('withdraw', str(e))
        return {'success': False, 'error': str(e)}
    finally:
        if conn:
            conn.close()

def test_dashboard_query(ip_id: str):
    """测试仪表盘查询"""
    start = time.time()
    conn = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # 模拟仪表盘查询
        cursor.execute('''
            SELECT balance, total_earned, total_referrals, level, status
            FROM ip_partners WHERE id = ?
        ''', (ip_id,))
        ip_data = cursor.fetchone()
        
        cursor.execute('''
            SELECT COUNT(*) as count FROM ip_links WHERE ip_id = ?
        ''', (ip_id,))
        links_count = cursor.fetchone()
        
        cursor.execute('''
            SELECT COUNT(*) as count FROM ip_commissions WHERE ip_id = ?
        ''', (ip_id,))
        commissions_count = cursor.fetchone()
        
        latency = time.time() - start
        stats.record_success('dashboard_query', latency)
        return {'success': True}
    except Exception as e:
        latency = time.time() - start
        stats.record_failure('dashboard_query', str(e))
        return {'success': False, 'error': str(e)}
    finally:
        if conn:
            conn.close()

# ========== 测试场景 ==========

def scenario_burst_apply(concurrent_users: int):
    """场景1: 突发申请 - 大量用户同时申请成为IP"""
    print(f"\n{'='*60}")
    print(f"场景1: 突发申请测试 - {concurrent_users}人同时申请")
    print(f"{'='*60}")
    
    global stats
    stats = StatsCollector()
    
    start_time = time.time()
    
    with ThreadPoolExecutor(max_workers=concurrent_users) as executor:
        futures = [executor.submit(test_ip_apply, i) for i in range(concurrent_users)]
        for future in as_completed(futures):
            pass
    
    total_time = time.time() - start_time
    result = stats.get_stats()
    
    print(f"总耗时: {total_time:.2f}秒")
    print(f"成功: {result['success']}, 失败: {result['failure']}")
    print(f"成功率: {result['success_rate']:.2f}%")
    print(f"平均延迟: {result['avg_latency_ms']:.2f}ms")
    print(f"最大延迟: {result['max_latency_ms']:.2f}ms")
    print(f"QPS: {result['total']/total_time:.2f}")
    
    return result

def scenario_burst_click(concurrent_clicks: int):
    """场景2: 突发点击 - 链接被大量点击"""
    print(f"\n{'='*60}")
    print(f"场景2: 突发点击测试 - {concurrent_clicks}次并发点击")
    print(f"{'='*60}")
    
    global stats
    stats = StatsCollector()
    
    # 先获取一些链接
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT code FROM ip_links LIMIT 10')
    links = [row['code'] for row in cursor.fetchall()]
    conn.close()
    
    if not links:
        print("没有可用的链接进行测试")
        return None
    
    start_time = time.time()
    
    with ThreadPoolExecutor(max_workers=concurrent_clicks) as executor:
        futures = [executor.submit(test_link_click, random.choice(links)) 
                   for _ in range(concurrent_clicks)]
        for future in as_completed(futures):
            pass
    
    total_time = time.time() - start_time
    result = stats.get_stats()
    
    print(f"总耗时: {total_time:.2f}秒")
    print(f"成功: {result['success']}, 失败: {result['failure']}")
    print(f"成功率: {result['success_rate']:.2f}%")
    print(f"平均延迟: {result['avg_latency_ms']:.2f}ms")
    print(f"QPS: {result['total']/total_time:.2f}")
    
    return result

def scenario_mixed_daily(concurrent_users: int, duration_seconds: int = 60):
    """场景3: 日常混合使用 - 模拟日常各种操作混合"""
    print(f"\n{'='*60}")
    print(f"场景3: 日常混合使用 - {concurrent_users}用户持续{duration_seconds}秒")
    print(f"{'='*60}")
    
    global stats
    stats = StatsCollector()
    
    # 获取一些IP用于测试
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT id FROM ip_partners WHERE status = "active" OR status = "pending" LIMIT 50')
    ip_ids = [row['id'] for row in cursor.fetchall()]
    cursor.execute('SELECT code FROM ip_links LIMIT 20')
    link_codes = [row['code'] for row in cursor.fetchall()]
    conn.close()
    
    if not ip_ids:
        print("没有可用的IP进行测试")
        return None
    
    start_time = time.time()
    operations_count = 0
    
    def user_session(user_id: int):
        nonlocal operations_count
        session_ops = 0
        end_time = start_time + duration_seconds
        
        while time.time() < end_time:
            # 随机选择操作类型
            op_type = random.choices(
                ['click', 'query', 'commission', 'withdraw', 'link_create'],
                weights=[40, 30, 15, 10, 5]  # 点击最频繁，提现最少
            )[0]
            
            if op_type == 'click' and link_codes:
                test_link_click(random.choice(link_codes))
            elif op_type == 'query':
                test_dashboard_query(random.choice(ip_ids))
            elif op_type == 'commission':
                test_commission_create(random.choice(ip_ids), random.uniform(10, 1000))
            elif op_type == 'withdraw':
                test_withdraw(random.choice(ip_ids), random.uniform(10, 100))
            elif op_type == 'link_create':
                test_link_create(random.choice(ip_ids), user_id)
            
            session_ops += 1
            time.sleep(random.uniform(0.01, 0.1))  # 模拟用户思考时间
        
        return session_ops
    
    with ThreadPoolExecutor(max_workers=concurrent_users) as executor:
        futures = [executor.submit(user_session, i) for i in range(concurrent_users)]
        for future in as_completed(futures):
            operations_count += future.result()
    
    total_time = time.time() - start_time
    result = stats.get_stats()
    
    print(f"实际运行时间: {total_time:.2f}秒")
    print(f"总操作数: {operations_count}")
    print(f"成功: {result['success']}, 失败: {result['failure']}")
    print(f"成功率: {result['success_rate']:.2f}%")
    print(f"平均延迟: {result['avg_latency_ms']:.2f}ms")
    print(f"OPS: {operations_count/total_time:.2f}")
    
    print("\n操作分布:")
    for op, counts in result['operations'].items():
        print(f"  {op}: 成功{counts['success']}, 失败{counts['failure']}")
    
    return result

def scenario_commission_burst(concurrent_orders: int):
    """场景4: 佣金计算突发 - 大量订单同时结算"""
    print(f"\n{'='*60}")
    print(f"场景4: 佣金计算突发 - {concurrent_orders}笔订单同时结算")
    print(f"{'='*60}")
    
    global stats
    stats = StatsCollector()
    
    # 获取活跃IP
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT id FROM ip_partners WHERE status = "active" LIMIT 50')
    ip_ids = [row['id'] for row in cursor.fetchall()]
    conn.close()
    
    if not ip_ids:
        print("没有活跃的IP进行测试")
        return None
    
    start_time = time.time()
    
    with ThreadPoolExecutor(max_workers=concurrent_orders) as executor:
        futures = [executor.submit(test_commission_create, random.choice(ip_ids), 
                                   random.uniform(10, 1000)) 
                   for _ in range(concurrent_orders)]
        for future in as_completed(futures):
            pass
    
    total_time = time.time() - start_time
    result = stats.get_stats()
    
    print(f"总耗时: {total_time:.2f}秒")
    print(f"成功: {result['success']}, 失败: {result['failure']}")
    print(f"成功率: {result['success_rate']:.2f}%")
    print(f"平均延迟: {result['avg_latency_ms']:.2f}ms")
    print(f"QPS: {result['total']/total_time:.2f}")
    
    return result

def scenario_withdraw_burst(concurrent_withdraws: int):
    """场景5: 提现突发 - 大量用户同时申请提现"""
    print(f"\n{'='*60}")
    print(f"场景5: 提现突发 - {concurrent_withdraws}人同时申请提现")
    print(f"{'='*60}")
    
    global stats
    stats = StatsCollector()
    
    # 获取有余额的IP
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT id FROM ip_partners WHERE balance > 0 LIMIT 50')
    ip_ids = [row['id'] for row in cursor.fetchall()]
    
    if not ip_ids:
        cursor.execute('SELECT id FROM ip_partners LIMIT 50')
        ip_ids = [row['id'] for row in cursor.fetchall()]
    
    conn.close()
    
    if not ip_ids:
        print("没有可用的IP进行测试")
        return None
    
    start_time = time.time()
    
    with ThreadPoolExecutor(max_workers=concurrent_withdraws) as executor:
        futures = [executor.submit(test_withdraw, random.choice(ip_ids), 
                                   random.uniform(10, 100)) 
                   for _ in range(concurrent_withdraws)]
        for future in as_completed(futures):
            pass
    
    total_time = time.time() - start_time
    result = stats.get_stats()
    
    print(f"总耗时: {total_time:.2f}秒")
    print(f"成功: {result['success']}, 失败: {result['failure']}")
    print(f"成功率: {result['success_rate']:.2f}%")
    print(f"平均延迟: {result['avg_latency_ms']:.2f}ms")
    print(f"QPS: {result['total']/total_time:.2f}")
    
    return result

def run_all_scenarios():
    """运行所有测试场景"""
    print("\n" + "="*60)
    print("IP扶持计划 - 并发压力测试")
    print("="*60)
    
    results = {}
    
    # 场景1: 1000人同时申请
    results['burst_apply'] = scenario_burst_apply(1000)
    
    # 场景2: 1000次并发点击
    results['burst_click'] = scenario_burst_click(1000)
    
    # 场景3: 100人日常混合使用30秒
    results['mixed_daily'] = scenario_mixed_daily(100, 30)
    
    # 场景4: 500笔订单同时结算
    results['commission_burst'] = scenario_commission_burst(500)
    
    # 场景5: 200人同时提现
    results['withdraw_burst'] = scenario_withdraw_burst(200)
    
    # 汇总报告
    print("\n" + "="*60)
    print("测试汇总报告")
    print("="*60)
    
    for name, result in results.items():
        if result:
            print(f"\n{name}:")
            print(f"  成功率: {result['success_rate']:.2f}%")
            print(f"  平均延迟: {result['avg_latency_ms']:.2f}ms")
            print(f"  最大延迟: {result['max_latency_ms']:.2f}ms")
    
    # 检查是否有问题
    issues = []
    for name, result in results.items():
        if result and result['success_rate'] < 99:
            issues.append(f"{name}: 成功率 {result['success_rate']:.2f}%")
        if result and result['avg_latency_ms'] > 100:
            issues.append(f"{name}: 平均延迟 {result['avg_latency_ms']:.2f}ms")
    
    if issues:
        print("\n⚠️ 发现问题:")
        for issue in issues:
            print(f"  - {issue}")
    else:
        print("\n✅ 所有测试通过，系统表现良好！")
    
    # 最终数据库统计
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute("SELECT COUNT(*) as count FROM ip_partners")
    total_ips = cursor.fetchone()['count']
    
    cursor.execute("SELECT COUNT(*) as count FROM ip_links")
    total_links = cursor.fetchone()['count']
    
    cursor.execute("SELECT COUNT(*) as count FROM ip_commissions")
    total_commissions = cursor.fetchone()['count']
    
    cursor.execute("SELECT COUNT(*) as count FROM ip_withdrawals")
    total_withdrawals = cursor.fetchone()['count']
    
    cursor.execute("SELECT SUM(click_count) as total FROM ip_links")
    total_clicks = cursor.fetchone()['total'] or 0
    
    conn.close()
    
    print("\n数据库最终状态:")
    print(f"  IP总数: {total_ips}")
    print(f"  链接总数: {total_links}")
    print(f"  总点击数: {total_clicks}")
    print(f"  佣金记录: {total_commissions}")
    print(f"  提现记录: {total_withdrawals}")

if __name__ == "__main__":
    run_all_scenarios()
