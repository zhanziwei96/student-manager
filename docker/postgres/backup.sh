#!/bin/sh
set -e

# PostgreSQL 每日自动备份脚本
# 由 pg_backup 容器通过 crontab 每日 02:00 执行

BACKUP_DIR="/backups"
DB_NAME="${POSTGRES_DB:-classhub}"
DB_USER="${POSTGRES_USER:-classhub}"
DATE=$(date +%Y%m%d_%H%M%S)
FILE="${BACKUP_DIR}/${DB_NAME}_${DATE}.sql"

# 保留最近 14 天的备份
echo "[$(date '+%Y-%m-%d %H:%M:%S')] Starting backup of ${DB_NAME}..."
pg_dump -h "${PGHOST}" -U "${DB_USER}" -d "${DB_NAME}" -Fc -f "${FILE}"
gzip -f "${FILE}"
echo "[$(date '+%Y-%m-%d %H:%M:%S')] Backup saved to ${FILE}.gz"

# 清理旧备份（保留 14 天）
find "${BACKUP_DIR}" -name "${DB_NAME}_*.sql.gz" -type f -mtime +14 -delete
echo "[$(date '+%Y-%m-%d %H:%M:%S')] Old backups cleaned up (retained 14 days)"
