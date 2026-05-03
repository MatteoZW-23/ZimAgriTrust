#!/bin/bash
# Database Restore Script
# Run this script to restore from a backup

set -e

# Configuration
DB_NAME=${POSTGRES_DB:-agri_trust}
DB_USER=${POSTGRES_USER:-postgres}
DB_HOST=${DB_HOST:-postgres}
DB_PORT=${DB_PORT:-5432}
BACKUP_DIR=${BACKUP_DIR:-./backups}

# Check if backup file is provided
if [ -z "$1" ]; then
    echo "Usage: $0 <backup_file.sql.gz>"
    echo "Available backups:"
    ls -lh ${BACKUP_DIR}/agritrust_backup_*.sql.gz
    exit 1
fi

BACKUP_FILE=$1

# Check if backup file exists
if [ ! -f "${BACKUP_DIR}/${BACKUP_FILE}" ]; then
    echo "ERROR: Backup file not found: ${BACKUP_DIR}/${BACKUP_FILE}"
    exit 1
fi

echo "WARNING: This will replace the current database!"
read -p "Are you sure you want to continue? (yes/no): " confirm

if [ "$confirm" != "yes" ]; then
    echo "Restore cancelled."
    exit 0
fi

echo "Starting database restore at $(date)"

# Stop application services to prevent conflicts
docker-compose stop backend

# Decompress and restore
gunzip -c ${BACKUP_DIR}/${BACKUP_FILE} | docker-compose exec -T postgres psql -U ${DB_USER} ${DB_NAME}

# Restart application services
docker-compose start backend

echo "Database restore completed at $(date)"
