# quarry-cli

Developer CLI for building, validating, and publishing Quarry plugins and detection rules.

## Installation

```bash
pip install quarry-cli
```

Or from source:
```bash
pip install -e packages/quarry-cli
```

## Commands

### Plugin Scaffold
```bash
quarry plugin scaffold my-enricher
quarry plugin scaffold my-connector --type connector
```

### Plugin Validate
```bash
quarry plugin validate ./my-enricher
quarry plugin validate ./my-enricher/plugin.yaml
```

### Plugin Publish
```bash
export QUARRY_API_URL=https://api.example.com
export QUARRY_API_KEY=sk-...
quarry plugin publish ./my-enricher
```

### Detection Validate
```bash
quarry detection validate ./detections/brute-force.yaml
```

### Key Generation
```bash
quarry keygen              # generates ~/.quarry/signing.key + signing.pub
```

## Environment Variables

| Variable | Description |
|---|---|
| `QUARRY_API_URL` | Quarry API base URL (default: `http://localhost:8000`) |
| `QUARRY_API_KEY` | API key for authentication |
| `QUARRY_SIGNING_KEY` | Path to Ed25519 private key (default: `~/.quarry/signing.key`) |
