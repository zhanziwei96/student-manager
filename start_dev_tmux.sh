#!/bin/bash

# 班级管理系统 - Linux Tmux启动脚本（推荐）
# 需要安装 tmux: sudo apt-get install tmux

SESSION_NAME="student-manage"

# 检查tmux是否安装
if ! command -v tmux &> /dev/null; then
    echo "[错误] 未安装 tmux，请先安装: sudo apt-get install tmux"
    echo ""
    echo "或者使用其他启动脚本:"
    echo "  ./start_dev.sh        (前台运行，Ctrl+C停止)"
    echo "  ./start_dev_simple.sh (后台运行，./stop_dev.sh停止)"
    exit 1
fi

# 检查是否已有会话
if tmux has-session -t $SESSION_NAME 2>/dev/null; then
    echo "[提示] 检测到已有会话，正在附加..."
    tmux attach -t $SESSION_NAME
    exit 0
fi

# 获取脚本所在目录
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"

echo "=========================================="
echo "    班级管理系统 - Tmux开发环境"
echo "=========================================="
echo ""

# 创建新会话
cd "$SCRIPT_DIR"
tmux new-session -d -s $SESSION_NAME

# 创建后端窗口
tmux rename-window -t $SESSION_NAME:0 'backend'
tmux send-keys -t $SESSION_NAME:0 "cd $SCRIPT_DIR/backend && python3 app.py" C-m

# 创建前端窗口
tmux new-window -t $SESSION_NAME:1 -n 'frontend'
tmux send-keys -t $SESSION_NAME:1 "cd $SCRIPT_DIR/frontend && npm run dev" C-m

# 创建日志窗口
tmux new-window -t $SESSION_NAME:2 -n 'logs'
tmux split-window -h -t $SESSION_NAME:2
tmux send-keys -t $SESSION_NAME:2.0 "cd $SCRIPT_DIR && tail -f backend.log 2>/dev/null || echo '后端日志将在后端启动后显示' && sleep 5 && tail -f backend.log" C-m
tmux send-keys -t $SESSION_NAME:2.1 "cd $SCRIPT_DIR && tail -f frontend.log 2>/dev/null || echo '前端日志将在前端启动后显示' && sleep 5 && tail -f frontend.log" C-m

# 回到第一个窗口
tmux select-window -t $SESSION_NAME:0

# 附加到会话
echo "[启动] 正在启动服务..."
sleep 2
echo ""
echo "=========================================="
echo "  服务启动成功！"
echo "=========================================="
echo ""
echo "  后端: http://localhost:5000"
echo "  前端: http://localhost:3000"
echo ""
echo "  默认账号: admin / admin123"
echo ""
echo "=========================================="
echo ""
echo "Tmux 快捷键:"
echo "  Ctrl+b, 0    - 切换到后端窗口"
echo "  Ctrl+b, 1    - 切换到前端窗口"
echo "  Ctrl+b, 2    - 切换到日志窗口"
echo "  Ctrl+b, c    - 创建新窗口"
echo "  Ctrl+b, d    - 分离会话（后台运行）"
echo "  Ctrl+b, %    - 垂直分割窗口"
echo "  Ctrl+b, \"    - 水平分割窗口"
echo ""
echo "其他命令:"
echo "  tmux attach -t $SESSION_NAME  - 重新附加会话"
echo "  tmux kill-session -t $SESSION_NAME  - 停止服务"
echo ""
echo "=========================================="
echo ""

# 附加到会话
tmux attach -t $SESSION_NAME
