#!/bin/bash
# 容器内自动备份守护进程 - 每小时执行一次

while true; do
    # 等待到下一个整点
    sleep $((3600 - $(date +%s) % 3600))
    
    echo "[$(date)] 执行自动备份..."
    /app/backup-data.sh
    echo "[$(date)] 自动备份完成"
done
