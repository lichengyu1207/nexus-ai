@echo off
echo ========================================
echo 房算云AI - 启动脚本
echo ========================================

echo.
echo [1/3] 检查Python环境...
python --version
if errorlevel 1 (
    echo 错误: 未找到Python，请先安装Python 3.10+
    exit /b 1
)

echo.
echo [2/3] 安装后端依赖...
cd backend
pip install -r requirements.txt -q

echo.
echo [3/3] 启动后端服务...
uvicorn main:app --reload --host 0.0.0.0 --port 8000
