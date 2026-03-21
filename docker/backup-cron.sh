#!/bin/bash
# 容器内自动备份守护进程 - 每小时执行一次

BACKUP_SCRIPT="/app/backup/backup-data.sh"
KEEP_DAYS="${BACKUP_KEEP_DAYS:-30}"

# 检查备份脚本是否存在
if [ ! -f "$BACKUP_SCRIPT" ]; then
    echo "[$(date)] 错误: 备份脚本不存在: $BACKUP_SCRIPT"
    exit 1
fi

echo "[$(date)] 备份守护进程启动..."
echo "[$(date)] 备份脚本: $BACKUP_SCRIPT"
echo "[$(date)] 保留策略: ${KEEP_DAYS}天"

while true; do
    # 等待到下一个整点
    CURRENT_EPOCH=$(date +%s)
    NEXT_HOUR_EPOCH=$(((CURRENT_EPOCH / 3600 + 1) * 3600))
    SLEEP_SECONDS=$((NEXT_HOUR_EPOCH - CURRENT_EPOCH))
    
    echo "[$(date)] 下次备份时间: $(date -d @${NEXT_HOUR_EPOCH} '+%Y-%m-%d %H:%M:%S')"
    sleep $SLEEP_SECONDS
    
    echo "[$(date)] 执行自动备份..."
    if bash "$BACKUP_SCRIPT" "$KEEP_DAYS"; then
        echo "[$(date)] 自动备份完成"
    else
        echo "[$(date)] 自动备份失败"
    fi
done
