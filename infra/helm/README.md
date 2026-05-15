# Quarry Helm chart

This directory ships a Helm chart that deploys Quarry onto a Kubernetes cluster.
It is the deployment path the production docs (`apps/docs/docs/deployment/kubernetes.md`)
point at.

```
infra/helm/
├── quarry/                     # The chart itself
│   ├── Chart.yaml             # appVersion tracks the Quarry release
│   ├── values.yaml            # All knobs live here
│   ├── templates/             # Service deployments, HPA, PDB, ingress, etc.
│   └── charts/                # Reserved for vendored sub-charts (currently empty)
└── charts/                    # Reserved for additional umbrella charts (currently empty)
```

## What it deploys

`templates/` renders one `Deployment` per entry in `values.yaml::services` plus
matching `Service`, `HorizontalPodAutoscaler`, `PodDisruptionBudget`, and a
shared `Ingress`. The default `services` map covers:

- `api` — FastAPI core API (`ghcr.io/beenuar/quarry-core-api`)
- `ingest` — Go ingest service (`ghcr.io/beenuar/quarry-ingest`)
- `enrichment` — Go enrichment service (`ghcr.io/beenuar/quarry-enrichment`)
- `agents` — Python AI agents (`ghcr.io/beenuar/quarry-agents`)
- `web` — Next.js UI (`ghcr.io/beenuar/quarry-web`)
- `realtime` — WebSocket service (`ghcr.io/beenuar/quarry-realtime`)

Three feature services have their own templates rather than the generic
deployment because their pod specs differ:

- `honeytokens-deployment.yaml`
- `purple-team-deployment.yaml`
- `ueba-deployment.yaml`

## Data plane assumptions

The chart **does not** install Postgres, Redis, Kafka, OpenSearch, or
ClickHouse by default. `postgresql.enabled` and `redis.enabled` in
`values.yaml` are off. Production deployments are expected to point at managed
services (RDS, ElastiCache, MSK, Opensearch Service) — the Terraform module
under `infra/terraform/` provisions those on AWS.

For local clusters or evaluation deployments, set `postgresql.enabled=true`
and `redis.enabled=true` to bring up the bundled Bitnami sub-charts.

## Quick install

```bash
# 1. Add Bitnami (only needed if you turn the bundled deps on)
helm repo add bitnami https://charts.bitnami.com/bitnami
helm dependency update infra/helm/quarry

# 2. Render the chart
helm template quarry infra/helm/quarry -n quarry --create-namespace

# 3. Install (production layout: managed data plane, no bundled deps)
helm install quarry infra/helm/quarry \
  -n quarry --create-namespace \
  --set ingress.hosts[0].host=quarry.your-domain.com \
  --set global.environment=production \
  --set global.otelEndpoint=http://otel-collector:4317

# 4. Upgrade
helm upgrade quarry infra/helm/quarry -n quarry -f your-overrides.yaml
```

## Common overrides

Every service has the same shape under `services.<name>`. The most-changed
fields:

```yaml
services:
  api:
    replicaCount: 4               # explicit replicas (HPA still applies)
    image:
      repository: my-registry/quarry-core-api
      tag: "5.2.0"
    env:                           # extra env vars merged into the pod
      LOG_LEVEL: debug
    hpa:
      enabled: true
      minReplicas: 2
      maxReplicas: 20
    pdb:
      enabled: true
      minAvailable: 1
```

Connection strings (Postgres DSN, Redis URL, Kafka brokers, etc.) come in via
`global.extraConfig` or per-service `env`, and from a `Secret` you create out
of band. See `apps/docs/docs/deployment/env-vars.md` for the canonical list of
environment variables — note in particular that `KAFKA_BOOTSTRAP_SERVERS` is
the canonical broker variable; `KAFKA_BROKERS` is honored as a backward-compat
alias.

## Releasing a new chart version

1. Bump `Chart.yaml::version` (chart version) and `Chart.yaml::appVersion`
   (Quarry release) in lockstep with the Git tag.
2. `helm lint infra/helm/quarry`
3. `helm template ...` and diff against the previous render before publishing.

## Related docs

- `apps/docs/docs/deployment/kubernetes.md` — end-to-end production guide.
- `apps/docs/docs/deployment/env-vars.md` — environment variable reference.
- `infra/terraform/README.md` — provisions the EKS cluster + managed data plane
  this chart deploys onto.
