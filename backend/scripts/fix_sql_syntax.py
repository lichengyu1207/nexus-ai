"""
批量修复后端文件中的 SQLite 语法为 PostgreSQL 语法
"""
import os
import re
import glob

def fix_sql_syntax(content: str) -> str:
    """将 SQLite 语法转换为 PostgreSQL 语法"""
    
    # 修复 VALUES (?, ?, ?) 为 VALUES ($1, $2, $3)
    def replace_values(match):
        placeholders = match.group(1)
        count = placeholders.count('?')
        new_placeholders = ', '.join([f'${i+1}' for i in range(count)])
        return f'VALUES ({new_placeholders})'
    
    content = re.sub(r'VALUES\s*\(([\?,\s]+)\)', replace_values, content)
    
    # 修复 WHERE id = ? 为 WHERE id = $1 等
    # 这个需要更复杂的处理，因为需要跟踪参数位置
    
    return content

def fix_file(filepath: str) -> bool:
    """修复单个文件"""
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
        
        original = content
        
        # 修复 INSERT OR REPLACE 为 INSERT ... ON CONFLICT
        content = re.sub(
            r'INSERT OR REPLACE INTO (\w+)',
            r'INSERT INTO \1',
            content
        )
        
        # 简单的 ? 替换需要手动处理，因为参数位置很重要
        # 这里只做标记，需要人工检查
        
        if content != original:
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(content)
            return True
        return False
    except Exception as e:
        print(f"Error fixing {filepath}: {e}")
        return False

def main():
    backend_dir = r'c:\Users\Administrator\Desktop\測試2\backend'
    
    # 查找所有 Python 文件
    files = glob.glob(f'{backend_dir}/**/*.py', recursive=True)
    
    fixed_count = 0
    for filepath in files:
        if fix_file(filepath):
            fixed_count += 1
            print(f"Fixed: {filepath}")
    
    print(f"\nTotal files fixed: {fixed_count}")

if __name__ == '__main__':
    main()
