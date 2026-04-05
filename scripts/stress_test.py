"""
压力测试脚本
测试系统在高并发下的性能表现
"""
import requests
import time
import threading
import statistics
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime

BASE_URL = 'http://localhost:8000'

class StressTest:
    def __init__(self):
        self.results = []
        self.errors = []
        self.lock = threading.Lock()
    
    def login(self):
        """获取测试token"""
        r = requests.post(f'{BASE_URL}/api/auth/login', json={
            'email': '1558691995@qq.com',
            'password': '147258@Zxcvbnm'
        }, timeout=10)
        if r.status_code == 200:
            return r.json().get('access_token')
        return None
    
    def test_endpoint(self, name, method, url, headers=None, data=None):
        """测试单个端点"""
        start = time.time()
        try:
            if method == 'GET':
                r = requests.get(url, headers=headers, timeout=30)
            else:
                r = requests.post(url, headers=headers, json=data, timeout=30)
            
            duration = time.time() - start
            
            with self.lock:
                self.results.append({
                    'name': name,
                    'status': r.status_code,
                    'duration': duration,
                    'success': r.status_code < 400
                })
            
            return r.status_code, duration
        except Exception as e:
            duration = time.time() - start
            with self.lock:
                self.errors.append({
                    'name': name,
                    'error': str(e),
                    'duration': duration
                })
            return None, duration
    
    def run_concurrent_test(self, name, func, count=10):
        """并发测试"""
        print(f"\n并发测试: {name} ({count}次)")
        print("-" * 40)
        
        start_time = time.time()
        
        with ThreadPoolExecutor(max_workers=10) as executor:
            futures = [executor.submit(func) for _ in range(count)]
            for future in as_completed(futures):
                future.result()
        
        total_time = time.time() - start_time
        
        # 统计结果
        test_results = [r for r in self.results if r['name'] == name]
        durations = [r['duration'] for r in test_results]
        success_count = sum(1 for r in test_results if r['success'])
        
        print(f"  总耗时: {total_time:.2f}s")
        print(f"  成功率: {success_count}/{count} ({success_count/count*100:.1f}%)")
        if durations:
            print(f"  平均响应: {statistics.mean(durations):.3f}s")
            print(f"  最小响应: {min(durations):.3f}s")
            print(f"  最大响应: {max(durations):.3f}s")
    
    def test_health(self):
        """测试健康检查"""
        return self.test_endpoint('health', 'GET', f'{BASE_URL}/health')
    
    def test_articles(self):
        """测试文章列表"""
        return self.test_endpoint('articles', 'GET', f'{BASE_URL}/api/articles')
    
    def test_tasks(self, token):
        """测试任务列表"""
        headers = {'Authorization': f'Bearer {token}'}
        return self.test_endpoint('tasks', 'GET', f'{BASE_URL}/api/tasks', headers=headers)
    
    def test_analyze(self, token):
        """测试分析接口"""
        headers = {'Authorization': f'Bearer {token}'}
        return self.test_endpoint('analyze', 'POST', f'{BASE_URL}/api/analyze', 
                                  headers=headers, data={'query': '测试地址'})
    
    def run_all_tests(self):
        """运行所有测试"""
        print("=" * 60)
        print("压力测试")
        print(f"测试时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print("=" * 60)
        
        # 登录获取token
        print("\n登录获取token...")
        token = self.login()
        if not token:
            print("[ERROR] 登录失败，无法继续测试")
            return
        print("[OK] 登录成功")
        
        # 并发测试
        self.run_concurrent_test('health', self.test_health, count=20)
        self.run_concurrent_test('articles', self.test_articles, count=20)
        self.run_concurrent_test('tasks', lambda: self.test_tasks(token), count=10)
        
        # 汇总报告
        print("\n" + "=" * 60)
        print("测试报告汇总")
        print("=" * 60)
        
        # 按端点统计
        endpoints = {}
        for r in self.results:
            if r['name'] not in endpoints:
                endpoints[r['name']] = {'count': 0, 'success': 0, 'durations': []}
            endpoints[r['name']]['count'] += 1
            if r['success']:
                endpoints[r['name']]['success'] += 1
            endpoints[r['name']]['durations'].append(r['duration'])
        
        print("\n端点统计:")
        print(f"{'端点':<15} {'请求':<8} {'成功':<8} {'成功率':<10} {'平均响应':<10}")
        print("-" * 60)
        
        for name, stats in endpoints.items():
            success_rate = stats['success'] / stats['count'] * 100
            avg_duration = statistics.mean(stats['durations'])
            print(f"{name:<15} {stats['count']:<8} {stats['success']:<8} {success_rate:.1f}%     {avg_duration:.3f}s")
        
        # 错误统计
        if self.errors:
            print(f"\n错误统计 ({len(self.errors)}个):")
            for e in self.errors[:5]:
                print(f"  - {e['name']}: {e['error'][:50]}")
        
        # 性能评估
        print("\n" + "-" * 60)
        print("性能评估:")
        
        all_durations = [r['duration'] for r in self.results]
        if all_durations:
            avg = statistics.mean(all_durations)
            p95 = sorted(all_durations)[int(len(all_durations) * 0.95)]
            
            if avg < 0.5:
                print(f"  [OK] 平均响应时间优秀: {avg:.3f}s")
            elif avg < 1.0:
                print(f"  [WARN] 平均响应时间一般: {avg:.3f}s")
            else:
                print(f"  [ALERT] 平均响应时间较慢: {avg:.3f}s")
            
            print(f"  P95响应时间: {p95:.3f}s")
        
        total_success = sum(1 for r in self.results if r['success'])
        total_requests = len(self.results)
        success_rate = total_success / total_requests * 100 if total_requests > 0 else 0
        
        if success_rate >= 99:
            print(f"  [OK] 成功率: {success_rate:.1f}%")
        elif success_rate >= 95:
            print(f"  [WARN] 成功率: {success_rate:.1f}%")
        else:
            print(f"  [ALERT] 成功率: {success_rate:.1f}%")
        
        print("=" * 60)

if __name__ == '__main__':
    test = StressTest()
    test.run_all_tests()
