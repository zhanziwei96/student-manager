# ============================================
# ClassHub Docker 备份脚本
# 备份 SQLite 数据库到 /app/backups
# ============================================

set -e

# 配置
BACKUP_DIR="${BACKUP_DIR:-/app/backups}"
DB_FILE="${DB_FILE:-/app/backend/app/data/student_manage.db}"
LOG_FILE="${LOG_FILE:-/app/backend/logs/backup.log}"
KEEP_DAYS="${1:-30}"

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
BACKUP_FILE="$BACKUP_DIR/student_manage_${TIMESTAMP}.db"

log "=========================================="
log "开始备份..."
log "源文件: $DB_FILE"
log "备份文件: $BACKUP_FILE"
log "保留策略: ${KEEP_DAYS}天"

# 执行备份（使用 SQLite 的 backup 命令确保一致性）
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

while IFS= read -r file; do
    if [ -n "$file" ]; then
        rm -f "$file"
        DELETED_COUNT=$((DELETED_COUNT + 1))
        log "删除: $file"
    fi
done < <(find "$BACKUP_DIR" -name "student_manage_*.db*" -type f -mtime +$KEEP_DAYS 2>/dev/null)

log "清理完成: 删除 $DELETED_COUNT 个文件"

# 显示当前备份统计
BACKUP_COUNT=$(find "$BACKUP_DIR" -name "student_manage_*.db*" -type f | wc -l)
BACKUP_TOTAL_SIZE=$(du -sh "$BACKUP_DIR" | cut -f1 2>/dev/null || echo "0B")
log "当前备份: $BACKUP_COUNT 个文件, 总大小: $BACKUP_TOTAL_SIZE"
log "=========================================="

exit 0
