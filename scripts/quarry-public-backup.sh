#!/usr/bin/env bash
set -euo pipefail

BACKUP_ROOT="/root/backups/quarry"
STAMP="$(date +%Y%m%d-%H%M%S)"
DEST="$BACKUP_ROOT/$STAMP"

mkdir -p "$DEST" /var/log/quarry

{
  echo "{\"ts\":\"$(date -Iseconds)\",\"event\":\"backup_start\",\"dest\":\"$DEST\"}"

  if docker ps --format '{{.Names}}' | grep -qx quarry-demo-postgres; then
    docker exec quarry-demo-postgres pg_dump -U quarry -d quarry -Fc > "$DEST/quarry-demo-postgres.dump"
    pg_restore --list "$DEST/quarry-demo-postgres.dump" >/dev/null
  fi

  tar -C /root/projetos -czf "$DEST/quarry-config.tgz" \
    quarry/.env.quarry-public.local \
    quarry/docs/operations/runbook.md \
    quarry/scripts/quarry-public-reset.sh \
    quarry/scripts/quarry-public-backup.sh \
    quarry/scripts/quarry-public-healthcheck.sh

  find "$BACKUP_ROOT" -mindepth 1 -maxdepth 1 -type d -mtime +14 -exec rm -rf {} +
  echo "{\"ts\":\"$(date -Iseconds)\",\"event\":\"backup_done\",\"dest\":\"$DEST\"}"
} >> /var/log/quarry/backup.jsonl 2>&1
