#!/bin/bash
# Restores a given database backup
if [ -z "$1" ]; then
  echo "Usage: ./rollback.sh <backup_file.sql>"
  exit 1
fi

echo "Restoring database from $1..."
cat "$1" | docker exec -i agritrust-postgres-1 psql -U postgres -d zimagritrust

echo "Rollback sequence completed."
