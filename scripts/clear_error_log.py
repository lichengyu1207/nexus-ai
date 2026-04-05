"""
清理错误日志
"""
LOG_FILE = 'c:/Users/Administrator/Desktop/測試2/logs/error.log'

# 清空错误日志
with open(LOG_FILE, 'w', encoding='utf-8') as f:
    f.write('')

print("错误日志已清空")
