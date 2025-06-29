#!/bin/bash

# OpenStack Cinder 备份管理系统启动脚本

echo "=== OpenStack Cinder 备份管理系统 ==="

# 检查Python环境
if ! command -v python3 &> /dev/null; then
    echo "❌ Python3 未安装，请先安装Python3"
    exit 1
fi

# 检查虚拟环境
if [ ! -d "venv" ]; then
    echo "📦 创建虚拟环境..."
    python3 -m venv venv
fi

# 激活虚拟环境
echo "🔧 激活虚拟环境..."
source venv/bin/activate

# 安装依赖
echo "📥 安装依赖包..."
pip install -r requirements.txt

# 检查配置文件
if [ ! -f ".env" ]; then
    echo "⚠️  未找到 .env 配置文件"
    echo "📝 请复制 env_example.txt 为 .env 并配置OpenStack认证信息"
    echo "cp env_example.txt .env"
    echo "然后编辑 .env 文件填入正确的认证信息"
    exit 1
fi

# 检查启动参数
if [ "$1" = "scheduler" ]; then
    echo "⏰ 启动定时备份调度器..."
    echo "📱 调度器将在后台运行，检查 scheduler.log 查看日志"
    echo "⏹️  按 Ctrl+C 停止调度器"
    echo ""
    python scheduler.py
elif [ "$1" = "both" ]; then
    echo "🚀 启动Web服务和定时备份调度器..."
    echo "📱 访问地址: http://localhost:5000"
    echo "⏰ 定时备份调度器将在后台运行"
    echo "⏹️  按 Ctrl+C 停止所有服务"
    echo ""
    
    # 启动调度器在后台
    python scheduler.py &
    SCHEDULER_PID=$!
    
    # 启动Web服务
    python app.py &
    WEB_PID=$!
    
    # 等待用户中断
    trap "echo '正在停止服务...'; kill $SCHEDULER_PID $WEB_PID 2>/dev/null; exit" INT
    wait
else
    echo "🚀 启动Web服务..."
    echo "📱 访问地址: http://localhost:5000"
    echo "⏹️  按 Ctrl+C 停止服务"
    echo ""
    echo "💡 使用以下命令启动其他服务:"
    echo "  ./start.sh scheduler  - 启动定时备份调度器"
    echo "  ./start.sh both       - 同时启动Web服务和调度器"
    echo ""
    python app.py
fi

