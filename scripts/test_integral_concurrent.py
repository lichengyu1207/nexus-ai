"""
积分系统体验优化 - 可用性与并发压力测试
测试签到功能、积分日志、并发场景
"""
import sqlite3
import os
import uuid
import time
import random
import threading
from datetime import datetime, date, timedelta
from concurrent.futures import ThreadPoolExecutor, as_completed

DB_PATH = os.path.join(os.path.dirname(__file__), '..', 'data', 'property-ai.db')
TOKEN_MULTIPLIER = 100

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
                'errors': self.results['errors'][:10]
            }

def get_db():
    conn = sqlite3.connect(DB_PATH, timeout=30.0)
    conn.row_factory = sqlite3.Row
    return conn

def test_database_tables():
    """测试数据库表是否存在"""
    print("\n1. 测试数据库表结构...")
    conn = get_db()
    cursor = conn.cursor()
    
    tables = ['integral_logs', 'signin_records', 'user_signin_stats', 'signin_rewards_config']
    all_exist = True
    
    for table in tables:
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name=?", (table,))
        if cursor.fetchone():
            print(f"   ✅ {table} 表存在")
        else:
            print(f"   ❌ {table} 表不存在")
            all_exist = False
    
    conn.close()
    return all_exist

def test_signin_rewards_config():
    """测试签到奖励配置"""
    print("\n2. 测试签到奖励配置...")
    conn = get_db()
    cursor = conn.cursor()
    
    cursor.execute("SELECT * FROM signin_rewards_config WHERE is_active = 1 ORDER BY day_number")
    rewards = cursor.fetchall()
    
    if len(rewards) > 0:
        print(f"   ✅ 签到奖励配置: {len(rewards)} 条")
        for r in rewards:
            print(f"      第{r['day_number']}天: 基础{r['base_reward']}+奖励{r['bonus_reward']}={r['base_reward']+r['bonus_reward']}积分")
    else:
        print("   ⚠️ 没有签到奖励配置，使用默认值")
    
    conn.close()
    return len(rewards) > 0

def test_create_user():
    """测试创建测试用户"""
    print("\n3. 测试创建用户...")
    conn = get_db()
    cursor = conn.cursor()
    
    user_id = str(uuid.uuid4())
    unique_id = str(uuid.uuid4())[:8]
    
    try:
        cursor.execute('''
            INSERT INTO users (id, email, username, hashed_password, integral, role)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (user_id, f'test_{unique_id}@test.com', f'testuser_{unique_id}', 'test_hashed_password', 0.0, 'user'))
        conn.commit()
        print(f"   ✅ 创建用户成功: {user_id[:8]}...")
        conn.close()
        return user_id
    except Exception as e:
        print(f"   ❌ 创建用户失败: {e}")
        conn.close()
        return None

def test_signin(user_id: str):
    """测试签到功能"""
    print("\n4. 测试签到功能...")
    conn = get_db()
    cursor = conn.cursor()
    
    today = date.today().isoformat()
    
    try:
        cursor.execute('SELECT 1 FROM signin_records WHERE user_id = ? AND sign_date = ?', (user_id, today))
        if cursor.fetchone():
            print("   ⚠️ 今日已签到")
            conn.close()
            return True
        
        cursor.execute('''
            SELECT base_reward, bonus_reward FROM signin_rewards_config
            WHERE day_number = 1 AND is_active = 1
        ''')
        reward_config = cursor.fetchone()
        
        if reward_config:
            reward = reward_config['base_reward'] + reward_config['bonus_reward']
        else:
            reward = 1.0
        
        signin_id = str(uuid.uuid4())
        cursor.execute('''
            INSERT INTO signin_records 
            (id, user_id, sign_date, reward_integral, reward_tokens, consecutive_days)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (signin_id, user_id, today, reward, int(reward * TOKEN_MULTIPLIER), 1))
        
        cursor.execute('UPDATE users SET integral = integral + ? WHERE id = ?', (reward, user_id))
        
        cursor.execute('SELECT integral FROM users WHERE id = ?', (user_id,))
        new_balance = cursor.fetchone()['integral']
        
        log_id = str(uuid.uuid4())
        cursor.execute('''
            INSERT INTO integral_logs 
            (id, user_id, change, balance_after, token_change, token_balance_after, reason, action_type, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (log_id, user_id, int(reward * TOKEN_MULTIPLIER), int(new_balance * TOKEN_MULTIPLIER), int(reward * TOKEN_MULTIPLIER), int(new_balance * TOKEN_MULTIPLIER),
              '签到奖励(第1天)', 'signin', datetime.now().isoformat()))
        
        cursor.execute('''
            INSERT INTO user_signin_stats (user_id, total_days, current_streak, max_streak, last_sign_date, total_rewards)
            VALUES (?, 1, 1, 1, ?, ?)
            ON CONFLICT(user_id) DO UPDATE SET
                total_days = total_days + 1,
                current_streak = current_streak + 1,
                max_streak = MAX(max_streak, current_streak + 1),
                last_sign_date = ?,
                total_rewards = total_rewards + ?,
                updated_at = ?
        ''', (user_id, today, reward, today, reward, datetime.now().isoformat()))
        
        conn.commit()
        print(f"   ✅ 签到成功: 获得{reward}积分 ({int(reward * TOKEN_MULTIPLIER)} Token)")
        print(f"      当前余额: {new_balance}积分 ({int(new_balance * TOKEN_MULTIPLIER)} Token)")
        conn.close()
        return True
    except Exception as e:
        print(f"   ❌ 签到失败: {e}")
        conn.rollback()
        conn.close()
        return False

def test_integral_logs(user_id: str):
    """测试积分日志查询"""
    print("\n5. 测试积分日志查询...")
    conn = get_db()
    cursor = conn.cursor()
    
    try:
        cursor.execute('''
            SELECT * FROM integral_logs WHERE user_id = ? ORDER BY created_at DESC LIMIT 5
        ''', (user_id,))
        logs = cursor.fetchall()
        
        if logs:
            print(f"   ✅ 积分日志记录: {len(logs)} 条")
            for log in logs:
                print(f"      {log['created_at'][:19]} | {log['action_type']} | {log['change']:+.2f}积分 | {log['token_change']:+d}Token")
        else:
            print("   ⚠️ 没有积分日志记录")
        
        conn.close()
        return len(logs) > 0
    except Exception as e:
        print(f"   ❌ 查询失败: {e}")
        conn.close()
        return False

def test_consume_integral(user_id: str, amount: float):
    """测试积分消耗"""
    print(f"\n6. 测试积分消耗({amount}积分)...")
    conn = get_db()
    cursor = conn.cursor()
    
    try:
        cursor.execute('SELECT integral FROM users WHERE id = ?', (user_id,))
        user = cursor.fetchone()
        
        if not user:
            print("   ❌ 用户不存在")
            conn.close()
            return False
        
        old_balance = user['integral']
        
        if old_balance < amount:
            print(f"   ⚠️ 余额不足: {old_balance} < {amount}")
            conn.close()
            return False
        
        new_balance = old_balance - amount
        
        cursor.execute('UPDATE users SET integral = ? WHERE id = ?', (new_balance, user_id))
        
        log_id = str(uuid.uuid4())
        cursor.execute('''
            INSERT INTO integral_logs 
            (id, user_id, change, balance_after, token_change, token_balance_after, reason, action_type, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (log_id, user_id, int(-amount * TOKEN_MULTIPLIER), int(new_balance * TOKEN_MULTIPLIER), int(-amount * TOKEN_MULTIPLIER), int(new_balance * TOKEN_MULTIPLIER),
              '测试消耗', 'test_consume', datetime.now().isoformat()))
        
        conn.commit()
        print(f"   ✅ 消耗成功: {old_balance} -> {new_balance}积分")
        print(f"      Token: {int(old_balance * TOKEN_MULTIPLIER)} -> {int(new_balance * TOKEN_MULTIPLIER)}")
        conn.close()
        return True
    except Exception as e:
        print(f"   ❌ 消耗失败: {e}")
        conn.rollback()
        conn.close()
        return False

def concurrent_signin(user_id: str, user_index: int, stats: StatsCollector):
    """并发签到测试"""
    start = time.time()
    conn = None
    try:
        conn = get_db()
        cursor = conn.cursor()
        
        signin_date = (date.today() - timedelta(days=user_index % 30)).isoformat()
        
        cursor.execute('SELECT 1 FROM signin_records WHERE user_id = ? AND sign_date = ?', (user_id, signin_date))
        if cursor.fetchone():
            latency = time.time() - start
            stats.record_success('signin_skip', latency)
            conn.close()
            return {'success': True, 'skipped': True}
        
        cursor.execute('''
            SELECT base_reward, bonus_reward FROM signin_rewards_config
            WHERE day_number = ? AND is_active = 1
        ''', ((user_index % 30) + 1,))
        reward_config = cursor.fetchone()
        
        if reward_config:
            reward = reward_config['base_reward'] + reward_config['bonus_reward']
        else:
            reward = 1.0
        
        signin_id = str(uuid.uuid4())
        cursor.execute('''
            INSERT OR IGNORE INTO signin_records 
            (id, user_id, sign_date, reward_integral, reward_tokens, consecutive_days)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (signin_id, user_id, signin_date, reward, int(reward * TOKEN_MULTIPLIER), (user_index % 30) + 1))
        
        if cursor.rowcount > 0:
            cursor.execute('UPDATE users SET integral = integral + ? WHERE id = ?', (reward, user_id))
            
            cursor.execute('SELECT integral FROM users WHERE id = ?', (user_id,))
            new_balance = cursor.fetchone()['integral']
            
            log_id = str(uuid.uuid4())
            cursor.execute('''
                INSERT INTO integral_logs 
                (id, user_id, change, balance_after, token_change, token_balance_after, reason, action_type, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (log_id, user_id, int(reward * TOKEN_MULTIPLIER), int(new_balance * TOKEN_MULTIPLIER), int(reward * TOKEN_MULTIPLIER), int(new_balance * TOKEN_MULTIPLIER),
                  f'并发签到奖励', 'concurrent_signin', datetime.now().isoformat()))
            
            conn.commit()
            latency = time.time() - start
            stats.record_success('signin', latency)
            return {'success': True, 'reward': reward}
        else:
            latency = time.time() - start
            stats.record_success('signin_duplicate', latency)
            return {'success': True, 'duplicate': True}
            
    except Exception as e:
        latency = time.time() - start
        stats.record_failure('signin', str(e))
        return {'success': False, 'error': str(e)}
    finally:
        if conn:
            conn.close()

def concurrent_consume(user_id: str, amount: float, stats: StatsCollector):
    """并发积分消耗测试"""
    start = time.time()
    conn = None
    try:
        conn = get_db()
        cursor = conn.cursor()
        
        cursor.execute('SELECT integral FROM users WHERE id = ?', (user_id,))
        user = cursor.fetchone()
        
        if not user:
            latency = time.time() - start
            stats.record_failure('consume', 'user not found')
            return {'success': False, 'error': 'user not found'}
        
        old_balance = user['integral']
        
        if old_balance < amount:
            latency = time.time() - start
            stats.record_success('consume_insufficient', latency)
            return {'success': True, 'insufficient': True}
        
        new_balance = old_balance - amount
        
        cursor.execute('UPDATE users SET integral = ? WHERE id = ?', (new_balance, user_id))
        
        log_id = str(uuid.uuid4())
        cursor.execute('''
            INSERT INTO integral_logs 
            (id, user_id, change, balance_after, token_change, token_balance_after, reason, action_type, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (log_id, user_id, int(-amount * TOKEN_MULTIPLIER), int(new_balance * TOKEN_MULTIPLIER), int(-amount * TOKEN_MULTIPLIER), int(new_balance * TOKEN_MULTIPLIER),
              '并发消耗', 'concurrent_consume', datetime.now().isoformat()))
        
        conn.commit()
        latency = time.time() - start
        stats.record_success('consume', latency)
        return {'success': True, 'old_balance': old_balance, 'new_balance': new_balance}
        
    except Exception as e:
        latency = time.time() - start
        stats.record_failure('consume', str(e))
        return {'success': False, 'error': str(e)}
    finally:
        if conn:
            conn.close()

def concurrent_query_logs(user_id: str, stats: StatsCollector):
    """并发日志查询测试"""
    start = time.time()
    conn = None
    try:
        conn = get_db()
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT * FROM integral_logs WHERE user_id = ? ORDER BY created_at DESC LIMIT 20
        ''', (user_id,))
        logs = cursor.fetchall()
        
        latency = time.time() - start
        stats.record_success('query_logs', latency)
        return {'success': True, 'count': len(logs)}
        
    except Exception as e:
        latency = time.time() - start
        stats.record_failure('query_logs', str(e))
        return {'success': False, 'error': str(e)}
    finally:
        if conn:
            conn.close()

def run_concurrent_tests(concurrent_users: int = 1000):
    """运行并发测试"""
    
    print(f"\n{'='*60}")
    print(f"积分系统并发压力测试 - {concurrent_users}用户")
    print(f"{'='*60}")
    
    # 创建测试用户
    print(f"\n创建 {concurrent_users} 个测试用户...")
    conn = get_db()
    cursor = conn.cursor()
    
    user_ids = []
    for i in range(concurrent_users):
        user_id = str(uuid.uuid4())
        unique_id = str(uuid.uuid4())[:8]
        try:
            cursor.execute('''
                INSERT INTO users (id, email, username, hashed_password, integral, role)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', (user_id, f'concurrent_{unique_id}@test.com', f'concurrent_{unique_id}', 'test_hashed_password', 100.0, 'user'))
            user_ids.append(user_id)
        except:
            pass
    
    conn.commit()
    conn.close()
    print(f"   ✅ 创建了 {len(user_ids)} 个用户")
    
    max_workers = 50
    
    # 场景1: 并发签到
    print(f"\n场景1: {concurrent_users}人并发签到...")
    signin_stats = StatsCollector()
    start_time = time.time()
    
    completed = 0
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        futures = {executor.submit(concurrent_signin, user_ids[i], i, signin_stats): i for i in range(len(user_ids))}
        for future in as_completed(futures):
            completed += 1
            if completed % 100 == 0:
                print(f"   进度: {completed}/{concurrent_users}")
    
    total_time = time.time() - start_time
    signin_result = signin_stats.get_stats()
    
    print(f"   总耗时: {total_time:.2f}秒")
    print(f"   成功: {signin_result['operations'].get('signin', {}).get('success', 0)}")
    print(f"   QPS: {signin_result['total']/total_time:.2f}")
    print(f"   平均延迟: {signin_result['avg_latency_ms']:.2f}ms")
    
    # 场景2: 并发积分消耗
    print(f"\n场景2: {concurrent_users}人并发积分消耗...")
    consume_stats = StatsCollector()
    start_time = time.time()
    
    completed = 0
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        futures = {executor.submit(concurrent_consume, user_ids[i], random.uniform(1, 50), consume_stats): i for i in range(len(user_ids))}
        for future in as_completed(futures):
            completed += 1
            if completed % 100 == 0:
                print(f"   进度: {completed}/{concurrent_users}")
    
    total_time = time.time() - start_time
    consume_result = consume_stats.get_stats()
    
    print(f"   总耗时: {total_time:.2f}秒")
    print(f"   成功: {consume_result['operations'].get('consume', {}).get('success', 0)}")
    print(f"   QPS: {consume_result['total']/total_time:.2f}")
    print(f"   平均延迟: {consume_result['avg_latency_ms']:.2f}ms")
    
    # 场景3: 并发日志查询
    print(f"\n场景3: {concurrent_users}人并发日志查询...")
    query_stats = StatsCollector()
    start_time = time.time()
    
    completed = 0
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        futures = {executor.submit(concurrent_query_logs, user_ids[i], query_stats): i for i in range(len(user_ids))}
        for future in as_completed(futures):
            completed += 1
            if completed % 100 == 0:
                print(f"   进度: {completed}/{concurrent_users}")
    
    total_time = time.time() - start_time
    query_result = query_stats.get_stats()
    
    print(f"   总耗时: {total_time:.2f}秒")
    print(f"   成功: {query_result['success']}")
    print(f"   QPS: {query_result['total']/total_time:.2f}")
    print(f"   平均延迟: {query_result['avg_latency_ms']:.2f}ms")
    
    # 场景4: 混合并发
    print(f"\n场景4: 混合并发操作(签到+消耗+查询)...")
    mixed_stats = StatsCollector()
    start_time = time.time()
    
    def mixed_operation(user_id: str, index: int):
        op_type = random.choice(['signin', 'consume', 'query'])
        if op_type == 'signin':
            return concurrent_signin(user_id, index, mixed_stats)
        elif op_type == 'consume':
            return concurrent_consume(user_id, random.uniform(1, 20), mixed_stats)
        else:
            return concurrent_query_logs(user_id, mixed_stats)
    
    completed = 0
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        futures = {executor.submit(mixed_operation, user_ids[i], i): i for i in range(len(user_ids))}
        for future in as_completed(futures):
            completed += 1
            if completed % 100 == 0:
                print(f"   进度: {completed}/{concurrent_users}")
    
    total_time = time.time() - start_time
    mixed_result = mixed_stats.get_stats()
    
    print(f"   总耗时: {total_time:.2f}秒")
    print(f"   成功: {mixed_result['success']}, 失败: {mixed_result['failure']}")
    print(f"   成功率: {mixed_result['success_rate']:.2f}%")
    print(f"   QPS: {mixed_result['total']/total_time:.2f}")
    print(f"   平均延迟: {mixed_result['avg_latency_ms']:.2f}ms")
    
    # 最终统计
    print(f"\n{'='*60}")
    print("最终数据库统计")
    print(f"{'='*60}")
    
    conn = get_db()
    cursor = conn.cursor()
    
    cursor.execute("SELECT COUNT(*) as count FROM users")
    total_users = cursor.fetchone()['count']
    
    cursor.execute("SELECT COUNT(*) as count FROM signin_records")
    total_signins = cursor.fetchone()['count']
    
    cursor.execute("SELECT COUNT(*) as count FROM integral_logs")
    total_logs = cursor.fetchone()['count']
    
    cursor.execute("SELECT SUM(integral) as total FROM users")
    total_integral = cursor.fetchone()['total'] or 0
    
    cursor.execute("SELECT COUNT(*) as count FROM user_signin_stats")
    stats_count = cursor.fetchone()['count']
    
    conn.close()
    
    print(f"   总用户数: {total_users}")
    print(f"   签到记录: {total_signins}")
    print(f"   积分日志: {total_logs}")
    print(f"   总积分: {total_integral:.2f}")
    print(f"   签到统计: {stats_count}")
    
    return {
        'signin': signin_result,
        'consume': consume_result,
        'query': query_result,
        'mixed': mixed_result
    }

def run_all_tests():
    """运行所有测试"""
    print("\n" + "="*60)
    print("积分系统体验优化 - 可用性与并发测试")
    print("="*60)
    
    # 可用性测试
    test_database_tables()
    test_signin_rewards_config()
    
    user_id = test_create_user()
    if user_id:
        test_signin(user_id)
        test_integral_logs(user_id)
        test_consume_integral(user_id, 0.5)
        test_integral_logs(user_id)
    
    # 并发测试
    run_concurrent_tests(1000)
    
    print("\n" + "="*60)
    print("✅ 积分系统测试完成!")
    print("="*60)

if __name__ == "__main__":
    run_all_tests()
