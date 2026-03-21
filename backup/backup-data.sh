#!/bin/bash
# ============================================
# 数据库备份脚本
# 功能：备份SQLite数据库并自动清理旧备份
# 用法：./backup-data.sh [保留天数]
# ============================================

set -e

# 配置
BACKUP_DIR="/home/yufeng/student-manage-v3-security/student-manager/backup/data"
DB_FILE="/home/yufeng/student-manage-v3-security/student-manager/data/class_system.db"
LOG_FILE="/home/yufeng/student-manage-v3-security/student-manager/logs/backup.log"
KEEP_DAYS="${1:-30}"  # 默认保留30天，可通过参数覆盖

# 创建备份目录
mkdir -p "$BACKUP_DIR"
mkdir -p "$(dirname "$LOG_FILE")"

# 日志函数
log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1" | tee -a "$LOG_FILE"
}

# 检查数据库文件
if [ ! -f "$DB_FILE" ]; then
    log "ERROR: 数据库文件不存在: $DB_FILE"
    exit 1
fi

# 生成备份文件名
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
BACKUP_FILE="$BACKUP_DIR/class_system_${TIMESTAMP}.db"

log "=========================================="
log "开始备份..."
log "源文件: $DB_FILE"
log "备份文件: $BACKUP_FILE"
log "保留策略: ${KEEP_DAYS}天"

# 执行备份（使用SQLite的备份命令确保一致性）
if sqlite3 "$DB_FILE" ".backup '$BACKUP_FILE'"; then
    # 压缩备份文件
    gzip "$BACKUP_FILE"
    BACKUP_FILE="${BACKUP_FILE}.gz"
    
    # 计算文件大小
    FILE_SIZE=$(du -h "$BACKUP_FILE" | cut -f1)
    log "备份成功: $BACKUP_FILE (大小: $FILE_SIZE)"
else
    log "ERROR: 备份失败"
    exit 1
fi

# 清理旧备份
log "清理 ${KEEP_DAYS} 天前的旧备份..."
DELETED_COUNT=0
DELETED_SIZE=0

while IFS= read -r file; do
    if [ -n "$file" ]; then
        file_size=$(stat -f%z "$file" 2>/dev/null || stat -c%s "$file" 2>/dev/null || echo 0)
        rm -f "$file"
        DELETED_COUNT=$((DELETED_COUNT + 1))
        DELETED_SIZE=$((DELETED_SIZE + file_size))
        log "删除: $file"
    fi
done < <(find "$BACKUP_DIR" -name "class_system_*.db*" -type f -mtime +$KEEP_DAYS 2>/dev/null)

# 转换为可读大小
if [ $DELETED_SIZE -gt 1073741824 ]; then
    DELETED_SIZE_HUMAN=$(echo "scale=2; $DELETED_SIZE/1073741824" | bc)"GB"
elif [ $DELETED_SIZE -gt 1048576 ]; then
    DELETED_SIZE_HUMAN=$(echo "scale=2; $DELETED_SIZE/1048576" | bc)"MB"
elif [ $DELETED_SIZE -gt 1024 ]; then
    DELETED_SIZE_HUMAN=$(echo "scale=2; $DELETED_SIZE/1024" | bc)"KB"
else
    DELETED_SIZE_HUMAN="${DELETED_SIZE}B"
fi

log "清理完成: 删除 $DELETED_COUNT 个文件, 释放 $DELETED_SIZE_HUMAN"

# 显示当前备份统计
BACKUP_COUNT=$(find "$BACKUP_DIR" -name "class_system_*.db*" -type f | wc -l)
BACKUP_TOTAL_SIZE=$(du -sh "$BACKUP_DIR" | cut -f1)
log "当前备份: $BACKUP_COUNT 个文件, 总大小: $BACKUP_TOTAL_SIZE"
log "=========================================="

exit 0
