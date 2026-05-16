#!/usr/bin/env bash
set -euo pipefail

cd /root/projetos/quarry

export NODE_ENV=production
export NEXT_TELEMETRY_DISABLED=1
export API_URL="http://127.0.0.1:8014"
export AGENTS_URL="http://127.0.0.1:8015"
export REALTIME_URL="http://127.0.0.1:8087"
export NEXT_PUBLIC_SITE_URL="https://quarry.12brain.org"
export NEXT_PUBLIC_DEMO_MODE="true"
export NEXT_PUBLIC_DEMO_DEEPLINK="/demo-cinematografica"
export NEXT_PUBLIC_DEMO_BANNER="Beta - Em validacao. Dados sinteticos; uso restrito a apresentacoes autorizadas."
export NEXT_PUBLIC_DEMO_AUTOLOGIN_EMAIL="demo@quarry.dev"
export NEXT_PUBLIC_DEMO_AUTOLOGIN_PASSWORD="quarry-demo"

exec pnpm --filter @quarry/web exec next start -p 3014 -H 127.0.0.1
