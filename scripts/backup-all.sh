#!/bin/bash
set -e

# PresenceOS - Automated Backup Script
# Usage: ./scripts/backup-all.sh
# Cron: 0 2 * * * /path/to/presenceos/scripts/backup-all.sh >> /var/log/presenceos-backup.log 2>&1

BACKUP_ROOT="${BACKUP_ROOT:-/tmp/presenceos-backups}"
DATE=$(date +%Y%m%d_%H%M%S)
LOG_FILE="$BACKUP_ROOT/backup_$DATE.log"

# Create backup directories
mkdir -p "$BACKUP_ROOT/postgres"
mkdir -p "$BACKUP_ROOT/redis"
mkdir -p "$BACKUP_ROOT/minio"

echo "=== PresenceOS Backup Started: $DATE ===" | tee "$LOG_FILE"

# 1. PostgreSQL backup
echo "[1/3] Backing up PostgreSQL..." | tee -a "$LOG_FILE"
if docker exec presenceos-db pg_dump -U presenceos presenceos 2>/dev/null | gzip > "$BACKUP_ROOT/postgres/presenceos_$DATE.sql.gz"; then
    echo "  PostgreSQL backup completed ($(du -h "$BACKUP_ROOT/postgres/presenceos_$DATE.sql.gz" | cut -f1))" | tee -a "$LOG_FILE"
else
    echo "  WARNING: PostgreSQL backup failed" | tee -a "$LOG_FILE"
fi

# 2. Redis backup
echo "[2/3] Backing up Redis..." | tee -a "$LOG_FILE"
if docker exec presenceos-redis redis-cli BGSAVE > /dev/null 2>&1; then
    sleep 3
    if docker cp presenceos-redis:/data/dump.rdb "$BACKUP_ROOT/redis/dump_$DATE.rdb" 2>/dev/null; then
        gzip -f "$BACKUP_ROOT/redis/dump_$DATE.rdb"
        echo "  Redis backup completed" | tee -a "$LOG_FILE"
    else
        echo "  WARNING: Redis backup copy failed" | tee -a "$LOG_FILE"
    fi
else
    echo "  WARNING: Redis BGSAVE failed" | tee -a "$LOG_FILE"
fi

# 3. MinIO data backup (optional - only if volume accessible)
echo "[3/3] Checking MinIO data..." | tee -a "$LOG_FILE"
MINIO_DATA="/var/lib/docker/volumes/presenceos_minio-data/_data"
if [ -d "$MINIO_DATA" ]; then
    rsync -av --delete "$MINIO_DATA/" "$BACKUP_ROOT/minio/$DATE/" >> "$LOG_FILE" 2>&1
    echo "  MinIO backup completed" | tee -a "$LOG_FILE"
else
    echo "  MinIO volume not found at $MINIO_DATA (skipping)" | tee -a "$LOG_FILE"
fi

# Cleanup old backups (keep last 30 days)
echo "Cleaning up old backups (>30 days)..." | tee -a "$LOG_FILE"
find "$BACKUP_ROOT/postgres" -name "*.sql.gz" -mtime +30 -delete 2>/dev/null
find "$BACKUP_ROOT/redis" -name "*.rdb.gz" -mtime +30 -delete 2>/dev/null
find "$BACKUP_ROOT/minio" -maxdepth 1 -type d -mtime +30 -exec rm -rf {} \; 2>/dev/null

# Summary
TOTAL_SIZE=$(du -sh "$BACKUP_ROOT" 2>/dev/null | cut -f1)
echo "" | tee -a "$LOG_FILE"
echo "=== Backup Completed: $DATE ===" | tee -a "$LOG_FILE"
echo "Total backup size: $TOTAL_SIZE" | tee -a "$LOG_FILE"
echo "Location: $BACKUP_ROOT" | tee -a "$LOG_FILE"

# Optional: Send notification (uncomment and set SLACK_WEBHOOK_URL)
# if [ -n "$SLACK_WEBHOOK_URL" ]; then
#     curl -s -X POST "$SLACK_WEBHOOK_URL" -d "{\"text\":\"PresenceOS backup completed: $DATE ($TOTAL_SIZE)\"}"
# fi
