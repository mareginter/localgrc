#!/bin/sh

TIMESTAMP=$(date +"%Y%m%d_%H%M%S")
BACKUP_DIR="/backups"

echo "[$(date)] Starting automatic backup..."

# 1. Backup da Base de Dados PostgreSQL
echo "Backing up database..."
pg_dump -h db -U "$PGUSER" -d "$PGDATABASE" -F c -f "$BACKUP_DIR/db_$TIMESTAMP.dump"

# 2. Backup dos ficheiros de Upload (PDFs, Evidências, etc.)
echo "Backing up uploads..."
tar -czf "$BACKUP_DIR/uploads_$TIMESTAMP.tar.gz" -C /data/uploads .

# 3. Limpeza: Apagar backups com mais de 7 dias
echo "Cleaning up old backups..."
find "$BACKUP_DIR" -type f -mtime +7 -name "*.dump" -exec rm -f {} \;
find "$BACKUP_DIR" -type f -mtime +7 -name "*.tar.gz" -exec rm -f {} \;

echo "[$(date)] Backup completed successfully."