#!/bin/bash
set -e

# PresenceOS - Backup Restore Test
# Usage: ./scripts/test-restore.sh <backup_date>
# Example: ./scripts/test-restore.sh 20260217_020000

BACKUP_ROOT="${BACKUP_ROOT:-/tmp/presenceos-backups}"
BACKUP_DATE="${1:-$(ls -1t "$BACKUP_ROOT/postgres/" 2>/dev/null | head -1 | sed 's/presenceos_//;s/.sql.gz//')}"

if [ -z "$BACKUP_DATE" ]; then
    echo "Error: No backup found. Run backup-all.sh first."
    exit 1
fi

echo "=== PresenceOS Restore Test ==="
echo "Backup date: $BACKUP_DATE"
echo ""

# Check files exist
PG_BACKUP="$BACKUP_ROOT/postgres/presenceos_$BACKUP_DATE.sql.gz"
REDIS_BACKUP="$BACKUP_ROOT/redis/dump_$BACKUP_DATE.rdb.gz"

echo "Checking backup files..."
[ -f "$PG_BACKUP" ] && echo "  PostgreSQL: $PG_BACKUP" || echo "  PostgreSQL: NOT FOUND"
[ -f "$REDIS_BACKUP" ] && echo "  Redis: $REDIS_BACKUP" || echo "  Redis: NOT FOUND"

echo ""
echo "To restore PostgreSQL:"
echo "  gunzip -c $PG_BACKUP | docker exec -i presenceos-db psql -U presenceos presenceos"
echo ""
echo "To restore Redis:"
echo "  gunzip -c $REDIS_BACKUP > /tmp/dump.rdb"
echo "  docker cp /tmp/dump.rdb presenceos-redis:/data/dump.rdb"
echo "  docker restart presenceos-redis"
echo ""
echo "=== Test Complete ==="
