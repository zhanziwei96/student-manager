#!/bin/bash
# 学生管理系统数据备份脚本（支持宿主机和容器环境）
# 使用 SQLite .backup 命令，在线热备份，不锁库

# 自动检测环境（容器 vs 宿主机）
if [ -f "/app/data/class_system.db" ]; then
    # 容器环境
    DB_FILE="/app/data/class_system.db"
    BACKUP_DIR="/app/backups"
    echo "[INFO] 检测到容器环境"
elif [ -f "backend/data/class_system.db" ]; then
    # 宿主机环境 - v3 项目目录
    DB_FILE="backend/data/class_system.db"
    BACKUP_DIR="backups"
    echo "[INFO] 检测到宿主机环境 (v3)"
elif [ -f "/root/student-manage-v3/backend/data/class_system.db" ]; then
    # 宿主机绝对路径
    DB_FILE="/root/student-manage-v3/backend/data/class_system.db"
    BACKUP_DIR="/root/student-manage-v3/backups"
    echo "[INFO] 检测到宿主机环境 (绝对路径)"
else
    echo "[ERROR] 未找到数据库文件"
    exit 1
fi

MAX_BACKUPS=10
DATE=$(date +%Y%m%d_%H%M%S)
BACKUP_NAME="class_system_backup_${DATE}.db"

# 检查 sqlite3
if ! command -v sqlite3 &> /dev/null; then
    echo "[ERROR] sqlite3 未安装"
    exit 1
fi

# 创建备份目录
mkdir -p "$BACKUP_DIR"

# 执行备份
echo "[INFO] 开始备份: $DB_FILE"
echo "[INFO] 备份目标: ${BACKUP_DIR}/${BACKUP_NAME}"

if sqlite3 "$DB_FILE" ".backup '${BACKUP_DIR}/${BACKUP_NAME}'"; then
    BACKUP_SIZE=$(ls -lh "${BACKUP_DIR}/${BACKUP_NAME}" | awk '{print $5}')
    echo "[INFO] 备份完成: ${BACKUP_NAME} (${BACKUP_SIZE})"
else
    echo "[ERROR] 备份失败"
    exit 1
fi

# 清理旧备份
cd "$BACKUP_DIR" || exit 1
BACKUP_COUNT=$(ls -1t class_system_backup_*.db 2>/dev/null | wc -l)
if [ "$BACKUP_COUNT" -gt "$MAX_BACKUPS" ]; then
    echo "[INFO] 清理旧备份，保留最新 $MAX_BACKUPS 个..."
    ls -1t class_system_backup_*.db | tail -n +$((MAX_BACKUPS + 1)) | xargs -r rm -f
fi

# 显示备份列表
echo "[INFO] 当前备份列表:"
ls -lh class_system_backup_*.db 2>/dev/null | awk '{print "  - " $9 " (" $5 ")"}'

echo "[INFO] 完成: $(date)"
