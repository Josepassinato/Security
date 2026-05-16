# Quarry SecRL Benchmark Adapter

This adapter runs Quarry against Microsoft's SecRL / ExCyTIn-Bench incident
databases. It is intentionally read-only and uses the same operational limits
requested in CARD-012:

- GPT-4o investigation model.
- GPT-4o evaluator model.
- Temperature 0.
- Max 25 SQL/tool steps.
- One MySQL-backed incident database per scenario.

## Setup

```bash
cd /root/projetos/SecRL
python3 -m venv .venv
. .venv/bin/activate
pip install -e . --use-pep517
bash scripts/setup_docker.sh
```

The official setup expects the dataset under
`/root/projetos/SecRL/secgym/database/data_anonymized`. In this VPS we keep a
symlink to `/root/projetos/SecRL/data_anonymized` to avoid duplicating the
3.4GB incident extract.

## Run

```bash
cd /root/projetos/quarry
set -a
. /root/projetos/intake-portal/.env
set +a
/root/projetos/SecRL/.venv/bin/python benchmarks/secrl/quarry_secrl_runner.py
```

By default the script runs one question from each of the 8 incidents. To run
the full question set:

```bash
/root/projetos/SecRL/.venv/bin/python benchmarks/secrl/quarry_secrl_runner.py --limit-per-incident 0
```

Outputs:

- `docs/benchmarks/secrl-results.json`
- `docs/benchmarks/microsoft-secrl-results.md`
