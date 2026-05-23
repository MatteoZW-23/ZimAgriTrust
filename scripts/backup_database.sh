#!/bin/bash
# Automated Database Backup Script
# Run this script to backup the PostgreSQL database

set -e

# Configuration
DB_NAME=${POSTGRES_DB:-zimagritrust}
DB_USER=${POSTGRES_USER:-postgres}
DB_HOST=${DB_HOST:-postgres}
DB_PORT=${DB_PORT:-5432}
BACKUP_DIR=${BACKUP_DIR:-./backups}
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
BACKUP_FILE="${BACKUP_DIR}/agritrust_backup_${TIMESTAMP}.sql"
RETENTION_DAYS=${BACKUP_RETENTION_DAYS:-7}

# Create backup directory if it doesn't exist
mkdir -p ${BACKUP_DIR}

echo "Starting database backup at $(date)"

# Perform backup
docker-compose exec -T postgres pg_dump -U ${DB_USER} ${DB_NAME} > ${BACKUP_FILE}

# Compress backup
gzip ${BACKUP_FILE}
BACKUP_FILE="${BACKUP_FILE}.gz"

echo "Backup completed: ${BACKUP_FILE}"

# Remove old backups
find ${BACKUP_DIR} -name "agritrust_backup_*.sql.gz" -type f -mtime +${RETENTION_DAYS} -delete

echo "Old backups removed (older than ${RETENTION_DAYS} days)"

# Verify backup
if [ -f ${BACKUP_FILE} ]; then
    SIZE=$(du -h ${BACKUP_FILE} | cut -f1)
    echo "Backup verified. Size: ${SIZE}"
    exit 0
else
    echo "ERROR: Backup file not found!"
    exit 1
fi
