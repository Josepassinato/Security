# Quarry demo vs. production

The public `quarry.12brain.org` deployment is allowed to run as a labelled demo
only when `NEXT_PUBLIC_DEMO_MODE=true`.

## Demo

- Uses synthetic seed data and dashboard fallbacks.
- May auto-login with `demo@quarry.dev`.
- Uses the local demo services on ports `8014`, `8015`, and `8087`.
- Build with `scripts/build-public-web.sh`.

## Production

- Must set `NEXT_PUBLIC_DEMO_MODE=false`.
- Must not expose demo auto-login credentials.
- Must provide real `API_URL`, `AGENTS_URL`, and `REALTIME_URL`.
- Must set `SECRET_KEY`, `QUARRY_CREDENTIAL_KEY`, and datastore passwords from
  a secret manager or an untracked environment file.
- Must fail deployment if the API, agents, Postgres, Redis, Kafka, and Neo4j
  health checks are not green.

Build with:

```bash
API_URL=https://api.example.internal \
AGENTS_URL=https://agents.example.internal \
REALTIME_URL=https://realtime.example.internal \
NEXT_PUBLIC_SITE_URL=https://quarry.example.com \
scripts/build-production-web.sh
```
