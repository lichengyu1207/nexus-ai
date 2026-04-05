@echo off

REM 启动脚本 - 烦恼橡皮擦应用

echo === 烦恼橡皮擦启动脚本 ===

REM 检查Python环境
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo 错误: Python 未找到
    pause
    exit /b 1
)

REM 安装依赖
echo 安装依赖...
pip install -r requirements.txt

REM 启动服务
echo 启动后端服务...
python -m uvicorn main:app --host 0.0.0.0 --port 8000 --reload

pause