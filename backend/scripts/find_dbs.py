import os
from pathlib import Path

# 搜索所有.db文件
base_path = Path(r"c:\Users\Administrator\Desktop")
db_files = []

for root, dirs, files in os.walk(base_path):
    for file in files:
        if file.endswith('.db'):
            full_path = os.path.join(root, file)
            db_files.append(full_path)

print(f"找到 {len(db_files)} 个数据库文件:")
for db in db_files:
    print(f"  - {db}")
