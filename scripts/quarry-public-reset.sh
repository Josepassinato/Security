#!/usr/bin/env bash
set -euo pipefail

cd /root/projetos/quarry

COMPOSE_ENV="/root/projetos/quarry/.env.quarry-public.local"
COMPOSE=(docker compose -f docker-compose.demo.yml --env-file "$COMPOSE_ENV")

mkdir -p /var/log/quarry

{
  echo "{\"ts\":\"$(date -Iseconds)\",\"event\":\"reset_start\"}"
  "${COMPOSE[@]}" up -d postgres redis zookeeper kafka api agents realtime
  "${COMPOSE[@]}" run --rm seed || true
  if [ -d customizations/datasets/br-fintech-generator ]; then
    echo "{\"ts\":\"$(date -Iseconds)\",\"event\":\"br_fintech_dataset_present\"}"
  fi
  if ! pm2 describe quarry-web >/dev/null 2>&1; then
    pm2 start scripts/start-public-web.sh --name quarry-web
  fi
  echo "{\"ts\":\"$(date -Iseconds)\",\"event\":\"reset_done\"}"
} >> /var/log/quarry/reset.jsonl 2>&1
