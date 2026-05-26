#!/usr/bin/env bash
set -euo pipefail

cd /root/projetos/quarry

: "${API_URL:?set API_URL for the production API service}"
: "${AGENTS_URL:?set AGENTS_URL for the production agents service}"
: "${REALTIME_URL:?set REALTIME_URL for the production realtime service}"

export NODE_ENV=production
export NEXT_TELEMETRY_DISABLED=1
export NEXT_PUBLIC_SITE_URL="${NEXT_PUBLIC_SITE_URL:-https://quarry.12brain.org}"
export NEXT_PUBLIC_DEMO_MODE=false
unset NEXT_PUBLIC_DEMO_AUTOLOGIN_EMAIL
unset NEXT_PUBLIC_DEMO_AUTOLOGIN_PASSWORD
unset NEXT_PUBLIC_DEMO_DEEPLINK
unset NEXT_PUBLIC_DEMO_BANNER

exec pnpm --filter @quarry/web build
