#!/usr/bin/env bash
# Post-deploy smoke test for the AML screening evidence layer.
#
# Catches the failure class that took the demo down on 2026-06-27: a packaging
# bug (template path overran in the container) crash-looped the API and nobody
# noticed until a manual curl. Run this after EVERY deploy of the api image.
#
#   scripts/screening-smoke.sh [BASE_URL]        # reads only (safe, non-mutating)
#   FULL=1 scripts/screening-smoke.sh [BASE_URL] # also exercises POST intake
#
# Default BASE_URL targets the demo api (127.0.0.1:8014). In dev/demo mode the
# api's dev-auth resolves an unauthenticated request to the demo tenant, so no
# token is needed. Exits non-zero on the first failure.
set -uo pipefail

BASE="${1:-http://127.0.0.1:8014}"
fail=0

check() { # name  expected_code  url  [curl args...]
  local name="$1" want="$2" url="$3"; shift 3
  local code
  code=$(curl -s -o /dev/null -w "%{http_code}" "$@" "$url" 2>/dev/null)
  if [ "$code" = "$want" ]; then
    echo "  ✓ $name → $code"
  else
    echo "  ✗ $name → $code (expected $want)  [$url]"
    fail=1
  fi
}

echo "screening smoke @ $BASE"
check "health"            200 "$BASE/health"
check "verify-chain"      200 "$BASE/api/v1/screening/verify-chain"
check "portfolio (json)"  200 "$BASE/api/v1/screening/portfolio"
check "portfolio (html)"  200 "$BASE/api/v1/screening/portfolio?format=html"
# A bogus UUID must 404 (proves the route + tenant scoping resolve, not 500/crash).
check "get unknown 404"   404 "$BASE/api/v1/screening/00000000-0000-0000-0000-0000000000ff"

if [ "${FULL:-0}" = "1" ]; then
  echo "  -- FULL: POST intake (writes a ledger record) --"
  body='{"counterparty_name":"Smoke Test Person","counterparty_id_type":"OTHER"}'
  check "intake POST"     201 "$BASE/api/v1/screening" \
        -X POST -H "Content-Type: application/json" -d "$body"
fi

if [ "$fail" = "0" ]; then echo "SMOKE OK"; else echo "SMOKE FAILED"; fi
exit "$fail"
