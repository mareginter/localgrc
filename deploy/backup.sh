#!/bin/sh
# Produces a complete, verifiable backup set. A set is considered valid only
# after both the PostgreSQL dump and uploads archive have been checked.
set -eu

BACKUP_DIR="${BACKUP_DIR:-/backups}"
UPLOADS_DIR="${UPLOADS_DIR:-/data/uploads}"
TIMESTAMP="$(date -u +"%Y%m%dT%H%M%SZ")"
FINAL_DIR="$BACKUP_DIR/$TIMESTAMP"
TMP_DIR="$BACKUP_DIR/.tmp-$TIMESTAMP-$$"

log() { printf '[%s] %s\n' "$(date -u +"%Y-%m-%dT%H:%M:%SZ")" "$*"; }
fail() { log "ERROR: $*" >&2; exit 1; }

: "${PGHOST:=db}"
: "${PGUSER:?PGUSER must be set}"
: "${PGDATABASE:?PGDATABASE must be set}"
: "${PGPASSWORD:?PGPASSWORD must be set}"

mkdir -p "$BACKUP_DIR"
[ -d "$UPLOADS_DIR" ] || fail "Uploads directory does not exist: $UPLOADS_DIR"
[ ! -e "$FINAL_DIR" ] || fail "Backup destination already exists: $FINAL_DIR"
mkdir "$TMP_DIR"
trap 'rm -rf "$TMP_DIR"' EXIT HUP INT TERM

log "Starting backup set $TIMESTAMP"

log "Creating PostgreSQL custom-format dump"
pg_dump -h "$PGHOST" -U "$PGUSER" -d "$PGDATABASE" -F c \
  --no-owner --no-privileges -f "$TMP_DIR/database.dump"
[ -s "$TMP_DIR/database.dump" ] || fail "PostgreSQL dump is empty"
pg_restore --list "$TMP_DIR/database.dump" >/dev/null \
  || fail "PostgreSQL dump failed validation"

log "Creating uploads archive"
tar -czf "$TMP_DIR/uploads.tar.gz" -C "$UPLOADS_DIR" .
[ -s "$TMP_DIR/uploads.tar.gz" ] || fail "Uploads archive is empty"
tar -tzf "$TMP_DIR/uploads.tar.gz" >/dev/null \
  || fail "Uploads archive failed validation"

cat > "$TMP_DIR/manifest.txt" <<EOF
backup_timestamp_utc=$TIMESTAMP
postgres_database=$PGDATABASE
postgres_host=$PGHOST
database_dump_bytes=$(wc -c < "$TMP_DIR/database.dump" | tr -d ' ')
uploads_archive_bytes=$(wc -c < "$TMP_DIR/uploads.tar.gz" | tr -d ' ')
validation=pg_restore_list_and_tar_test_passed
EOF

# Publish the entire set atomically on the same filesystem.
mv "$TMP_DIR" "$FINAL_DIR"
trap - EXIT HUP INT TERM
log "Backup set published: $FINAL_DIR"

# Retain the seven newest complete sets. Incomplete temp folders are not counted.
find "$BACKUP_DIR" -mindepth 1 -maxdepth 1 -type d -name '20*T*Z' -print \
  | sort -r | awk 'NR > 7 {print}' |
while IFS= read -r old_set; do
  [ -n "$old_set" ] || continue
  log "Removing expired backup set $old_set"
  rm -rf "$old_set"
done

# Remove legacy flat backup files only after a complete new-format set exists.
find "$BACKUP_DIR" -maxdepth 1 -type f \
  \( -name 'db_*.dump' -o -name 'uploads_*.tar.gz' \) -mtime +7 -delete

log "Backup completed successfully"
