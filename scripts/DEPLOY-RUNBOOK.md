# Deploy runbook — AML screening (and the api image) on the demo VPS

> Written after the 2026-06-27 incident: a manual `docker compose up` with the
> wrong env took the demo down for ~25 min. This is the correct procedure +
> the traps that caused it.

## Reality of this deployment

- Prod/demo runs from a **published image** `ghcr.io/beenuar/quarry-core-api:latest`,
  **not** from local source. **This repo's CI does NOT build/publish that image**
  (no `docker push`/`ghcr` workflow) — it is published by an external (beenuar)
  process. So **merging to `main` does not deploy.**
- The demo stack is launched by `pnpm quarry:demo` (`scripts/quarry-demo.ts`),
  which **auto-detects free host ports** and passes them via `QUARRY_*_PORT`
  env vars. Current demo ports: api `8014`, postgres `5542`, redis `6382`,
  kafka `9093`, agents `8015`, realtime `8087`, web `3014`.

## Traps (do NOT repeat)

1. **Never run bare `docker compose -f docker-compose.demo.yml up`** without the
   `QUARRY_*_PORT` env. It falls back to default ports (redis `6379` collides
   with the host's native redis; api `8000` not `8014`) and recreates/kills
   already-running containers (postgres, redis). Use the launcher, or pass the
   ports + `--no-deps` (see below).
2. **The api build context is `./services/api`.** Anything outside it (e.g.
   repo-root `customizations/`) is **NOT** in the image. Dossier templates live
   at `services/api/app/evidence_pack/dossier_templates/` for this reason.
3. **No `Path(__file__).parents[N]` that walks above the package.** In the
   container the layout is `/app/app/...`; resolve paths relative to a module
   (`Path(module.__file__).parent`).

## Deploy the AML code to the running demo (local-build stopgap)

Until beenuar republishes the image from `main`, the demo runs a **locally built**
image (drift). To (re)deploy local source:

```bash
cd /root/projetos/quarry
KEY=$(grep -h OPENSANCTIONS_API_KEY .planning/private/.opensanctions-key.env | cut -d= -f2)
docker compose -f docker-compose.demo.yml build api          # build from local source
OPENSANCTIONS_API_KEY=$KEY QUARRY_POSTGRES_PORT=5542 QUARRY_REDIS_PORT=6382 QUARRY_API_PORT=8014 \
  docker compose -f docker-compose.demo.yml up -d --no-deps --wait --wait-timeout 90 api
scripts/screening-smoke.sh                                   # MANDATORY post-deploy check
```

`--no-deps` keeps the running postgres/redis/kafka/neo4j untouched. `--wait`
blocks until the api healthcheck passes.

## Rollback (to the published image)

```bash
docker pull ghcr.io/beenuar/quarry-core-api:latest           # restore published image
QUARRY_API_PORT=8014 docker compose -f docker-compose.demo.yml up -d --no-deps api
scripts/screening-smoke.sh
```

## The proper fix (kill the drift)

Have the **beenuar** image pipeline rebuild `quarry-core-api:latest` from `main`
(which now includes the AML layer + the path hotfix). Then `docker pull` + the
rollback command above puts the demo back on the canonical image — no drift.
Do NOT hand-`docker push` to `ghcr.io/beenuar/*` from here: it bypasses the
official build (multi-arch/provenance) and overwrites the canonical tag.

## Post-deploy verification (always)

`scripts/screening-smoke.sh` — hits `/health`, screening reads, a 404, and (with
`FULL=1`) a real intake. Exit non-zero on any failure. This is the check that
would have caught the import-crash immediately instead of 25 min later.
