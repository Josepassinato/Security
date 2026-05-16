#!/usr/bin/env bash
set -euo pipefail

URL="${1:-https://quarry.12brain.org/nginx-health}"
LOG="/var/log/quarry/healthcheck.jsonl"
mkdir -p /var/log/quarry

STATUS="$(curl -k -sS -o /dev/null -w '%{http_code}' "$URL" || true)"
if [ "$STATUS" = "200" ]; then
  echo "{\"ts\":\"$(date -Iseconds)\",\"event\":\"uptime_ok\",\"status\":200}" >> "$LOG"
  exit 0
fi

echo "{\"ts\":\"$(date -Iseconds)\",\"event\":\"uptime_fail\",\"status\":\"$STATUS\"}" >> "$LOG"
exit 1
