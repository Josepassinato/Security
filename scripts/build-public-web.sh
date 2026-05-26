#!/usr/bin/env bash
set -euo pipefail

cd /root/projetos/quarry

# Keep the public Next.js rewrites pointed at the local demo services.
# Next writes these routes during `next build`, so relying only on the
# PM2 start environment makes /api/v1/* fall back to localhost:8000.
export NODE_ENV=production
export NEXT_TELEMETRY_DISABLED=1
export API_URL="${API_URL:-http://127.0.0.1:8014}"
export AGENTS_URL="${AGENTS_URL:-http://127.0.0.1:8015}"
export REALTIME_URL="${REALTIME_URL:-http://127.0.0.1:8087}"
export NEXT_PUBLIC_SITE_URL="${NEXT_PUBLIC_SITE_URL:-https://quarry.12brain.org}"
export NEXT_PUBLIC_DEMO_MODE="${NEXT_PUBLIC_DEMO_MODE:-true}"
export NEXT_PUBLIC_DEMO_DEEPLINK="${NEXT_PUBLIC_DEMO_DEEPLINK:-/demo-cinematografica}"
export NEXT_PUBLIC_DEMO_BANNER="${NEXT_PUBLIC_DEMO_BANNER:-Beta - Em validacao. Dados sinteticos; uso restrito a apresentacoes autorizadas.}"
export NEXT_PUBLIC_DEMO_AUTOLOGIN_EMAIL="${NEXT_PUBLIC_DEMO_AUTOLOGIN_EMAIL:-demo@quarry.dev}"
export NEXT_PUBLIC_DEMO_AUTOLOGIN_PASSWORD="${NEXT_PUBLIC_DEMO_AUTOLOGIN_PASSWORD:-quarry-demo}"

exec pnpm --filter @quarry/web build
