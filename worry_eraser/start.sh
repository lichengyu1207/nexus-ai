#!/bin/bash

# 启动脚本 - 烦恼橡皮擦应用

echo "=== 烦恼橡皮擦启动脚本 ==="

# 检查Python环境
if ! command -v python3 &> /dev/null; then
    echo "错误: Python 3 未找到"
    exit 1
fi

# 安装依赖
echo "安装依赖..."
pip3 install -r requirements.txt

# 启动服务
echo "启动后端服务..."
python3 -m uvicorn main:app --host 0.0.0.0 --port 8000 --reload
