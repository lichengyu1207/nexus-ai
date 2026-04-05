"""
系统监控脚本
定期检查系统健康状态并发送告警
"""
import requests
import json
import os
from datetime import datetime

BASE_URL = 'http://localhost:8000'
LOG_FILE = 'c:/Users/Administrator/Desktop/測試2/logs/monitor.log'

def log(message, level='INFO'):
    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    log_line = f"[{timestamp}] [{level}] {message}"
    print(log_line)
    
    os.makedirs(os.path.dirname(LOG_FILE), exist_ok=True)
    with open(LOG_FILE, 'a', encoding='utf-8') as f:
        f.write(log_line + '\n')

def check_health():
    """检查系统健康状态"""
    try:
        r = requests.get(f'{BASE_URL}/health', timeout=10)
        if r.status_code == 200:
            data = r.json()
            status = data.get('status', 'unknown')
            
            if status == 'healthy':
                log(f"[OK] 系统健康 - {json.dumps(data.get('components', {}), ensure_ascii=False)}")
                return True, data
            else:
                log(f"[WARN] 系统异常 - {json.dumps(data, ensure_ascii=False)}", 'WARNING')
                return False, data
        else:
            log(f"[ERROR] 健康检查失败 - HTTP {r.status_code}", 'ERROR')
            return False, None
    except Exception as e:
        log(f"[ERROR] 无法连接到服务 - {str(e)}", 'ERROR')
        return False, None

def check_disk_space():
    """检查磁盘空间"""
    import shutil
    try:
        disk = shutil.disk_usage("/")
        percent = (disk.used / disk.total) * 100
        
        if percent > 90:
            log(f"[CRITICAL] 磁盘空间不足 - 已使用 {percent:.1f}%", 'CRITICAL')
            return False
        elif percent > 80:
            log(f"[WARN] 磁盘空间警告 - 已使用 {percent:.1f}%", 'WARNING')
            return True
        else:
            log(f"[OK] 磁盘空间正常 - 已使用 {percent:.1f}%")
            return True
    except Exception as e:
        log(f"[ERROR] 磁盘检查失败 - {str(e)}", 'ERROR')
        return False

def check_database():
    """检查数据库状态"""
    import sqlite3
    db_path = 'c:/Users/Administrator/Desktop/測試2/data/property-ai.db'
    
    try:
        if not os.path.exists(db_path):
            log(f"[ERROR] 数据库文件不存在", 'ERROR')
            return False
        
        size_mb = os.path.getsize(db_path) / (1024 * 1024)
        
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM users")
        user_count = cursor.fetchone()[0]
        conn.close()
        
        log(f"[OK] 数据库正常 - 大小: {size_mb:.1f}MB, 用户数: {user_count}")
        return True
    except Exception as e:
        log(f"[ERROR] 数据库检查失败 - {str(e)}", 'ERROR')
        return False

def check_error_logs():
    """检查最近的错误日志"""
    error_log = 'c:/Users/Administrator/Desktop/測試2/logs/error.log'
    
    try:
        if not os.path.exists(error_log):
            log("[OK] 无错误日志文件")
            return True
        
        with open(error_log, 'r', encoding='utf-8', errors='ignore') as f:
            lines = f.readlines()[-10:]
        
        error_count = sum(1 for line in lines if 'ERROR' in line)
        
        if error_count > 5:
            log(f"[WARN] 最近有 {error_count} 条错误日志", 'WARNING')
            return False
        else:
            log(f"[OK] 错误日志正常 - 最近 {error_count} 条错误")
            return True
    except Exception as e:
        log(f"[ERROR] 日志检查失败 - {str(e)}", 'ERROR')
        return False

def run_monitor():
    """运行监控检查"""
    log("=" * 60)
    log("系统监控检查开始")
    log("=" * 60)
    
    results = {
        'health': check_health()[0],
        'disk': check_disk_space(),
        'database': check_database(),
        'logs': check_error_logs()
    }
    
    log("-" * 60)
    
    all_ok = all(results.values())
    
    if all_ok:
        log("[OK] 所有检查通过 - 系统运行正常")
    else:
        failed = [k for k, v in results.items() if not v]
        log(f"[ALERT] 检查失败项: {', '.join(failed)}", 'ALERT')
    
    log("=" * 60)
    return all_ok

if __name__ == '__main__':
    run_monitor()
