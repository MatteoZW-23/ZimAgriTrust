#!/bin/bash
# Backup PostgreSQL database
TIMESTAMP=$(date +"%Y%m%d_%H%M%S")
BACKUP_FILE="agritrust_backup_$TIMESTAMP.sql"

echo "Starting backup to $BACKUP_FILE..."
docker exec -t agritrust-postgres-1 pg_dump -U postgres zimagritrust > ./backups/$BACKUP_FILE

echo "Backup completed successfully."
