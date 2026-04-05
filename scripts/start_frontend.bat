@echo off
echo ========================================
echo 房算云AI - 前端启动脚本
echo ========================================

echo.
echo [1/3] 检查Node.js环境...
node --version
if errorlevel 1 (
    echo 错误: 未找到Node.js，请先安装Node.js 18+
    exit /b 1
)

echo.
echo [2/3] 安装前端依赖...
call npm install

echo.
echo [3/3] 启动前端开发服务器...
call npm run dev
