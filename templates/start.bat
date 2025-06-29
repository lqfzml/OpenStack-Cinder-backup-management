@echo off
chcp 65001 >nul

echo === OpenStack Cinder 备份管理系统 ===

REM 检查Python环境
python --version >nul 2>&1
if errorlevel 1 (
    echo ❌ Python 未安装，请先安装Python
    pause
    exit /b 1
)

REM 检查虚拟环境
if not exist "venv" (
    echo 📦 创建虚拟环境...
    python -m venv venv
)

REM 激活虚拟环境
echo 🔧 激活虚拟环境...
call venv\Scripts\activate.bat

REM 安装依赖
echo 📥 安装依赖包...
pip install -r requirements.txt

REM 检查配置文件
if not exist ".env" (
    echo ⚠️  未找到 .env 配置文件
    echo 📝 请复制 env_example.txt 为 .env 并配置OpenStack认证信息和MySQL数据库配置
    echo copy env_example.txt .env
    echo 然后编辑 .env 文件填入正确的认证信息
    pause
    exit /b 1
)

REM 检查数据库连接
echo 🔍 检查数据库连接...
python -c "import sys; from database import get_db_manager; db = get_db_manager(); print('✅ 数据库连接成功')" 2>nul
if errorlevel 1 (
    echo ❌ 数据库连接失败
    echo 请确保MySQL服务正在运行，并且.env文件中的数据库配置正确
    pause
    exit /b 1
)

REM 检查启动参数
if "%1"=="scheduler" (
    echo ⏰ 启动定时备份调度器...
    echo 📱 调度器将在后台运行，检查 scheduler.log 查看日志
    echo ⏹️  按 Ctrl+C 停止调度器
    echo.
    
) else if "%1"=="both" (
    echo 🚀 启动Web服务和定时备份调度器...
    echo 📱 访问地址: http://localhost:5000
    echo ⏰ 定时备份调度器将在后台运行
    echo ⏹️  按 Ctrl+C 停止所有服务
    echo.
    
    REM 启动调度器在后台
    start /B python scheduler.py
    
    REM 启动Web服务
    python app.py
) else (
    echo 🚀 启动Web服务...
    echo 📱 访问地址: http://localhost:5000
    echo ⏹️  按 Ctrl+C 停止服务
    echo.
    echo 💡 使用以下命令启动其他服务:
    echo   start.bat scheduler  - 启动定时备份调度器
    echo   start.bat both       - 同时启动Web服务和调度器
    echo.
    python app.py
)

pause 