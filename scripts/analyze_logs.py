"""
日志分析脚本
分析系统日志，生成统计报告
"""
import os
import re
from datetime import datetime, timedelta
from collections import Counter, defaultdict

LOG_DIR = 'c:/Users/Administrator/Desktop/測試2/logs'

def analyze_logs():
    """分析日志文件"""
    print("=" * 60)
    print("日志分析报告")
    print(f"分析时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 60)
    
    # 日志文件列表
    log_files = ['app.log', 'error.log', 'monitor.log']
    
    stats = {
        'total_lines': 0,
        'by_level': Counter(),
        'by_hour': Counter(),
        'errors': [],
        'warnings': [],
        'slow_requests': [],
        'api_calls': Counter(),
        'status_codes': Counter()
    }
    
    for log_file in log_files:
        log_path = os.path.join(LOG_DIR, log_file)
        if not os.path.exists(log_path):
            continue
        
        print(f"\n分析文件: {log_file}")
        
        with open(log_path, 'r', encoding='utf-8', errors='ignore') as f:
            for line in f:
                stats['total_lines'] += 1
                
                # 提取日志级别
                level_match = re.search(r'\[(DEBUG|INFO|WARNING|ERROR|CRITICAL)\]', line)
                if level_match:
                    level = level_match.group(1)
                    stats['by_level'][level] += 1
                
                # 提取时间
                time_match = re.search(r'(\d{4}-\d{2}-\d{2}) (\d{2}):\d{2}:\d{2}', line)
                if time_match:
                    hour = time_match.group(2)
                    stats['by_hour'][hour] += 1
                
                # 提取API调用
                api_match = re.search(r'(GET|POST|PUT|DELETE) (/api/[^\s]+)', line)
                if api_match:
                    method = api_match.group(1)
                    path = api_match.group(2)
                    stats['api_calls'][f"{method} {path}"] += 1
                
                # 提取HTTP状态码
                status_match = re.search(r'HTTP (\d{3})', line)
                if status_match:
                    stats['status_codes'][status_match.group(1)] += 1
                
                # 提取慢请求
                slow_match = re.search(r'(\d+\.\d+)s$', line)
                if slow_match:
                    duration = float(slow_match.group(1))
                    if duration > 1.0:
                        stats['slow_requests'].append({
                            'line': line.strip()[:100],
                            'duration': duration
                        })
                
                # 收集错误
                if 'ERROR' in line:
                    stats['errors'].append(line.strip()[:200])
                
                # 收集警告
                if 'WARNING' in line:
                    stats['warnings'].append(line.strip()[:200])
    
    # 输出统计结果
    print("\n" + "-" * 60)
    print("日志级别统计:")
    for level, count in sorted(stats['by_level'].items()):
        print(f"  {level}: {count}")
    
    print("\n按小时分布 (最近24小时):")
    for hour in sorted(stats['by_hour'].keys())[-24:]:
        count = stats['by_hour'][hour]
        bar = '█' * min(count // 10, 20)
        print(f"  {hour}:00 {bar} ({count})")
    
    print("\nAPI调用TOP 10:")
    for api, count in stats['api_calls'].most_common(10):
        print(f"  {api}: {count}")
    
    print("\nHTTP状态码分布:")
    for code, count in sorted(stats['status_codes'].items()):
        print(f"  {code}: {count}")
    
    print("\n慢请求 (>1s):")
    slow_sorted = sorted(stats['slow_requests'], key=lambda x: x['duration'], reverse=True)[:5]
    for req in slow_sorted:
        print(f"  [{req['duration']:.2f}s] {req['line']}")
    
    print("\n最近错误:")
    for err in stats['errors'][-5:]:
        print(f"  - {err}")
    
    print("\n最近警告:")
    for warn in stats['warnings'][-5:]:
        print(f"  - {warn}")
    
    print("\n" + "-" * 60)
    print(f"总日志行数: {stats['total_lines']}")
    print(f"错误数: {len(stats['errors'])}")
    print(f"警告数: {len(stats['warnings'])}")
    print(f"慢请求数: {len(stats['slow_requests'])}")
    
    # 健康评估
    print("\n" + "=" * 60)
    print("健康评估:")
    
    issues = []
    if len(stats['errors']) > 10:
        issues.append(f"错误数量过多 ({len(stats['errors'])})")
    if len(stats['slow_requests']) > 5:
        issues.append(f"慢请求过多 ({len(stats['slow_requests'])})")
    if stats['status_codes'].get('500', 0) > 5:
        issues.append(f"500错误过多 ({stats['status_codes'].get('500', 0)})")
    
    if issues:
        print("  [警告] 发现以下问题:")
        for issue in issues:
            print(f"    - {issue}")
    else:
        print("  [OK] 系统运行正常")
    
    print("=" * 60)
    
    return stats

if __name__ == '__main__':
    analyze_logs()
