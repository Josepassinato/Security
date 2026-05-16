# Quarry Public Demo Runbook

## Public endpoint

- URL: `https://quarry.12brain.org`
- VPS IP: `76.13.109.151`
- Web process: PM2 `quarry-web`
- Web port: `127.0.0.1:3014`
- Core API port: `127.0.0.1:8014`
- Agents port: `127.0.0.1:8015`
- Realtime port: `127.0.0.1:8087`
- Nginx site: `/etc/nginx/sites-available/quarry.12brain.org`
- Access log: `/var/log/nginx/quarry.access.json`
- Error log: `/var/log/nginx/quarry.error.log`

## Demo access

The public beta is protected at the Nginx edge with five demo users:

- `meta-demo-1`
- `meta-demo-2`
- `prospect-demo-1`
- `prospect-demo-2`
- `internal-demo`

The app itself runs in demo mode and auto-logins with the deterministic Quarry demo user:

- `demo@quarry.dev`
- `quarry-demo`

Clerk is not wired into this codebase yet. To replace the edge auth with Clerk, add the Clerk publishable/secret keys and middleware for `quarry.12brain.org`, then remove `/etc/nginx/.htpasswd-quarry`.

## Deploy

```bash
cd /root/projetos/quarry
set -a
. ./.env.quarry-public.local
set +a

NEXT_PUBLIC_SITE_URL=https://quarry.12brain.org \
NEXT_PUBLIC_DEMO_MODE=true \
NEXT_PUBLIC_DEMO_DEEPLINK=/demo-cinematografica \
NEXT_PUBLIC_DEMO_BANNER="Beta - Em validacao. Dados sinteticos; uso restrito a apresentacoes autorizadas." \
NEXT_PUBLIC_DEMO_AUTOLOGIN_EMAIL=demo@quarry.dev \
NEXT_PUBLIC_DEMO_AUTOLOGIN_PASSWORD=quarry-demo \
pnpm --filter @quarry/web build

pm2 restart quarry-web --update-env
nginx -t && systemctl reload nginx
```

`API_URL`, `AGENTS_URL` and `REALTIME_URL` must be present during `next build`;
Next bakes rewrite destinations into the production routes manifest.

## Compose services

The public demo uses the slim demo compose profile with isolated host ports in `.env.quarry-public.local`.

```bash
cd /root/projetos/quarry
docker compose -f docker-compose.demo.yml --env-file .env.quarry-public.local ps
docker compose -f docker-compose.demo.yml --env-file .env.quarry-public.local up -d postgres redis zookeeper kafka api agents realtime
docker compose -f docker-compose.demo.yml --env-file .env.quarry-public.local run --rm seed
```

## Reset

Runs every 6 hours:

```bash
/root/projetos/quarry/scripts/quarry-public-reset.sh
```

Logs:

```bash
tail -f /var/log/quarry/reset.jsonl
```

## Monitoring

Local uptime probe:

```bash
/root/projetos/quarry/scripts/quarry-public-healthcheck.sh
tail -f /var/log/quarry/healthcheck.jsonl
```

External UptimeRobot is not configured until an account/API key is provided. Use this monitor URL:

```text
https://quarry.12brain.org/nginx-health
```

## Backup

Daily backup command:

```bash
/root/projetos/quarry/scripts/quarry-public-backup.sh
```

Backups are stored in `/root/backups/quarry/` and retained for 14 days.

Restore test:

```bash
latest="$(ls -td /root/backups/quarry/* | head -1)"
docker exec quarry-demo-postgres dropdb -U quarry --if-exists quarry_restore_check
docker exec quarry-demo-postgres createdb -U quarry quarry_restore_check
docker exec -i quarry-demo-postgres pg_restore -U quarry -d quarry_restore_check < "$latest/quarry-demo-postgres.dump"
docker exec quarry-demo-postgres psql -U quarry -d quarry_restore_check -tAc "select count(*) from aisoc_cases;"
docker exec quarry-demo-postgres dropdb -U quarry quarry_restore_check
```

Latest browser evidence is stored at
`/root/projetos/quarry/artifacts/public-deploy/quarry-public-demo-current.png`.

## Security posture

- `robots.txt` blocks all crawlers.
- Nginx sends `X-Robots-Tag: noindex, nofollow, noarchive`.
- Access logs are JSON and omit client IP, query string, cookies and authorization headers.
- Rate limit is intentionally aggressive for the beta.
- Public health endpoint exposes only `ok`.
