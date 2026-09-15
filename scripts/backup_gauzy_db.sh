#!/usr/bin/env bash
# ===================================================================
# EVER GAUZY POSTGRESQL DISASTER RECOVERY & BACKUP AUTOMATION SCRIPT
# ===================================================================

set -euo pipefail

# Configuration Parameters
BACKUP_DIR="${BACKUP_DIR:-/var/backups/gauzy}"
DB_CONTAINER="${DB_CONTAINER:-gauzy-postgres}"
DB_NAME="${DB_DATABASE:-gauzy_db}"
DB_USER="${DB_USERNAME:-gauzy}"
RETENTION_DAYS=30
TIMESTAMP=$(date +"%Y%m%d_%H%M%S")
BACKUP_FILE="${BACKUP_DIR}/gauzy_db_backup_${TIMESTAMP}.sql.gz"

echo "======================================================"
echo "Starting Ever Gauzy PostgreSQL Backup: ${TIMESTAMP}"
echo "======================================================"

# 1. Ensure backup destination directory exists
mkdir -p "${BACKUP_DIR}"

# 2. Execute pg_dump inside Docker container with gzip compression
echo "[1/3] Dumping database '${DB_NAME}' from container '${DB_CONTAINER}'..."
docker exec -t "${DB_CONTAINER}" pg_dump -U "${DB_USER}" -d "${DB_NAME}" --clean --if-exists | gzip > "${BACKUP_FILE}"

# 3. Verify backup file creation and non-zero size
if [ -s "${BACKUP_FILE}" ]; then
    FILE_SIZE=$(du -h "${BACKUP_FILE}" | cut -f1)
    echo "[2/3] Backup completed successfully! File: ${BACKUP_FILE} (Size: ${FILE_SIZE})"
else
    echo "[ERROR] Backup failed or generated an empty file!" >&2
    exit 1
fi

# 4. Enforce retention policy (Delete backups older than RETENTION_DAYS)
echo "[3/3] Enforcing ${RETENTION_DAYS}-day retention policy..."
find "${BACKUP_DIR}" -type f -name "gauzy_db_backup_*.sql.gz" -mtime +"${RETENTION_DAYS}" -exec rm -vf {} \;

echo "======================================================"
echo "Backup & Disaster Recovery Process Complete."
echo "======================================================"
