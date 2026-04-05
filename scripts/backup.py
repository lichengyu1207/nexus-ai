"""
数据库自动备份脚本
支持定时备份、压缩、清理旧备份
"""
import os
import shutil
import sqlite3
import gzip
import json
from datetime import datetime, timedelta

DB_PATH = 'c:/Users/Administrator/Desktop/測試2/data/property-ai.db'
BACKUP_DIR = 'c:/Users/Administrator/Desktop/測試2/backups'
CONFIG_FILE = 'c:/Users/Administrator/Desktop/測試2/config/backup_config.json'

DEFAULT_CONFIG = {
    'retention_days': 7,
    'max_backups': 10,
    'compress': True
}

def load_config():
    if os.path.exists(CONFIG_FILE):
        with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
            return {**DEFAULT_CONFIG, **json.load(f)}
    return DEFAULT_CONFIG

def backup_database(config):
    os.makedirs(BACKUP_DIR, exist_ok=True)
    
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    backup_name = f"property-ai_{timestamp}.db"
    backup_path = os.path.join(BACKUP_DIR, backup_name)
    
    print(f"备份数据库: {backup_name}")
    
    try:
        source = sqlite3.connect(DB_PATH)
        dest = sqlite3.connect(backup_path)
        source.backup(dest)
        dest.close()
        source.close()
        
        if config.get('compress', True):
            with open(backup_path, 'rb') as f_in:
                with gzip.open(backup_path + '.gz', 'wb') as f_out:
                    shutil.copyfileobj(f_in, f_out)
            os.remove(backup_path)
            print(f"  已压缩: {backup_name}.gz")
        
        return True
    except Exception as e:
        print(f"  备份失败: {e}")
        return False

def cleanup_old_backups(config):
    retention_days = config.get('retention_days', 7)
    max_backups = config.get('max_backups', 10)
    cutoff = datetime.now() - timedelta(days=retention_days)
    
    backups = []
    for f in os.listdir(BACKUP_DIR):
        if f.startswith('property-ai_'):
            path = os.path.join(BACKUP_DIR, f)
            mtime = datetime.fromtimestamp(os.path.getmtime(path))
            backups.append((path, mtime))
    
    backups.sort(key=lambda x: x[1], reverse=True)
    
    deleted = 0
    for i, (path, mtime) in enumerate(backups):
        if mtime < cutoff or i >= max_backups:
            os.remove(path)
            deleted += 1
    
    print(f"清理旧备份: 删除 {deleted} 个")

def run_backup():
    print("=" * 60)
    print(f"数据库备份 - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 60)
    
    config = load_config()
    success = backup_database(config)
    cleanup_old_backups(config)
    
    print("[OK] 备份完成" if success else "[ERROR] 备份失败")
    return success

if __name__ == '__main__':
    run_backup()
