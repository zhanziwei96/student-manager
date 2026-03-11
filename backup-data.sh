#!/bin/bash
# 学生管理系统数据备份脚本（SQLite 在线热备份）
# 使用 SQLite .backup 命令，备份过程中不锁库，系统可正常使用
# 备份目录: /root/student-manage-v2/backups
# 保留数量: 5个

DB_FILE="/root/student-manage-v2/backend/data/class_system.db"
BACKUP_DIR="/root/student-manage-v2/backups"
MAX_BACKUPS=5
DATE=$(date +%Y%m%d_%H%M%S)
BACKUP_NAME="class_system_backup_${DATE}.db"

# 检查数据库文件是否存在
if [ ! -f "$DB_FILE" ]; then
    echo "[ERROR] 数据库文件不存在: $DB_FILE"
    exit 1
fi

# 检查 sqlite3 是否安装
if ! command -v sqlite3 &> /dev/null; then
    echo "[ERROR] sqlite3 命令未找到"
    exit 1
fi

# 创建备份目录
mkdir -p "$BACKUP_DIR"

# 使用 SQLite 在线热备份
echo "[INFO] 开始在线备份: $DB_FILE"
echo "[INFO] 备份目标: ${BACKUP_DIR}/${BACKUP_NAME}"

# .backup 命令：在线热备份，不锁库，事务安全
if sqlite3 "$DB_FILE" ".backup '${BACKUP_DIR}/${BACKUP_NAME}'"; then
    echo "[INFO] 备份完成: ${BACKUP_NAME}"
    
    # 显示备份文件大小
    BACKUP_SIZE=$(ls -lh "${BACKUP_DIR}/${BACKUP_NAME}" | awk '{print $5}')
    echo "[INFO] 备份文件大小: ${BACKUP_SIZE}"
else
    echo "[ERROR] 备份失败"
    exit 1
fi

# 轮转清理：只保留最新的5个备份
cd "$BACKUP_DIR" || exit 1
BACKUP_COUNT=$(ls -1t class_system_backup_*.db 2>/dev/null | wc -l)

if [ "$BACKUP_COUNT" -gt "$MAX_BACKUPS" ]; then
    echo "[INFO] 备份数量($BACKUP_COUNT)超过限制($MAX_BACKUPS)，清理旧备份..."
    ls -1t class_system_backup_*.db | tail -n +$((MAX_BACKUPS + 1)) | xargs -r rm -f
    echo "[INFO] 清理完成，保留最新 $MAX_BACKUPS 个备份"
fi

# 显示当前备份列表
echo "[INFO] 当前备份列表:"
ls -lh class_system_backup_*.db 2>/dev/null | awk '{print "  - " $9 " (" $5 ")"}'

echo "[INFO] 备份任务完成: $(date)"
