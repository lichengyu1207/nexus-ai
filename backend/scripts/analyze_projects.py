import os
from pathlib import Path
import json
from datetime import datetime

def analyze_project(path):
    """分析项目文件夹"""
    result = {
        "path": str(path),
        "exists": path.exists(),
        "files_count": 0,
        "dirs_count": 0,
        "has_backend": False,
        "has_frontend": False,
        "has_db": False,
        "db_files": [],
        "package_json": None,
        "main_files": [],
        "created_time": None,
        "modified_time": None
    }
    
    if not path.exists():
        return result
    
    # 获取创建和修改时间
    try:
        stat = path.stat()
        result["created_time"] = datetime.fromtimestamp(stat.st_ctime).isoformat()
        result["modified_time"] = datetime.fromtimestamp(stat.st_mtime).isoformat()
    except:
        pass
    
    # 遍历目录
    for root, dirs, files in os.walk(path):
        # 跳过 node_modules 和 .git
        dirs[:] = [d for d in dirs if d not in ['node_modules', '.git', '__pycache__', '.venv', 'venv']]
        
        result["dirs_count"] += len(dirs)
        result["files_count"] += len(files)
        
        for file in files:
            full_path = os.path.join(root, file)
            
            # 检查后端
            if file == 'main.py' and 'backend' in root:
                result["has_backend"] = True
                result["main_files"].append(full_path)
            
            # 检查前端
            if file == 'package.json':
                result["has_frontend"] = True
                try:
                    with open(full_path, 'r', encoding='utf-8') as f:
                        result["package_json"] = json.load(f)
                except:
                    pass
            
            # 检查数据库
            if file.endswith('.db'):
                result["has_db"] = True
                result["db_files"].append(full_path)
    
    return result

# 搜索桌面上的项目文件夹
desktop = Path(r"c:\Users\Administrator\Desktop")
projects = []

for item in desktop.iterdir():
    if item.is_dir() and not item.name.startswith('.'):
        # 检查是否是项目目录
        has_backend = (item / "backend").exists()
        has_frontend = (item / "frontend").exists()
        has_package = (item / "package.json").exists() or (item / "frontend" / "package.json").exists()
        
        if has_backend or has_frontend or has_package:
            analysis = analyze_project(item)
            projects.append(analysis)

print("=" * 60)
print("桌面项目文件夹分析报告")
print("=" * 60)

for i, proj in enumerate(projects, 1):
    print(f"\n项目 {i}: {Path(proj['path']).name}")
    print(f"  路径: {proj['path']}")
    print(f"  创建时间: {proj['created_time']}")
    print(f"  修改时间: {proj['modified_time']}")
    print(f"  文件数: {proj['files_count']}")
    print(f"  目录数: {proj['dirs_count']}")
    print(f"  有后端: {'✅' if proj['has_backend'] else '❌'}")
    print(f"  有前端: {'✅' if proj['has_frontend'] else '❌'}")
    print(f"  有数据库: {'✅' if proj['has_db'] else '❌'}")
    if proj['db_files']:
        print(f"  数据库文件:")
        for db in proj['db_files']:
            print(f"    - {db}")
    if proj['package_json']:
        print(f"  项目名称: {proj['package_json'].get('name', 'N/A')}")

print("\n" + "=" * 60)
print("建议")
print("=" * 60)

# 找出最完整的项目
most_complete = max(projects, key=lambda p: (
    int(p['has_backend']) + int(p['has_frontend']) + int(p['has_db']) + p['files_count']
))

print(f"\n最完整的项目: {Path(most_complete['path']).name}")
print(f"  原因: 后端={most_complete['has_backend']}, 前端={most_complete['has_frontend']}, 数据库={most_complete['has_db']}, 文件数={most_complete['files_count']}")
