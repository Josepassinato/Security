# quarry-plugin-sdk · Go

The official Go SDK for building Quarry plugins — custom enrichers, response
actions, and data-source connectors.

## Installation

```bash
go get github.com/beenuar/quarry/plugin-sdk-go
```

## Quick Start

### Enricher

```go
package main

import (
    "context"
    "github.com/beenuar/quarry/plugin-sdk-go/quarry"
)

type VTEnricher struct{ quarry.BasePlugin }

func (e *VTEnricher) Manifest() quarry.PluginManifest {
    return quarry.PluginManifest{
        ID:         "myorg.virustotal",
        Name:       "VirusTotal Enricher",
        Version:    "1.0.0",
        PluginType: quarry.PluginTypeEnricher,
    }
}

func (e *VTEnricher) Enrich(
    ctx context.Context,
    req quarry.EnrichmentRequest,
    pctx quarry.PluginContext,
) (quarry.EnrichmentResult, error) {
    // call VirusTotal API here …
    malicious := false
    confidence := 0.95
    return quarry.EnrichmentResult{
        IndicatorType:  req.IndicatorType,
        IndicatorValue: req.IndicatorValue,
        Enrichments:    map[string]any{"vt_score": 72},
        Malicious:      &malicious,
        Confidence:     &confidence,
    }, nil
}
```

### Response Action

```go
type BlockIPAction struct{ quarry.BasePlugin }

func (a *BlockIPAction) Manifest() quarry.PluginManifest {
    return quarry.PluginManifest{
        ID: "myorg.block-ip", Name: "Block IP",
        Version: "1.0.0", PluginType: quarry.PluginTypeAction,
    }
}

func (a *BlockIPAction) SupportedActions() []string { return []string{"block_ip"} }

func (a *BlockIPAction) Execute(
    ctx context.Context,
    req quarry.ActionRequest,
    pctx quarry.PluginContext,
) (quarry.ActionResult, error) {
    if req.DryRun {
        return quarry.ActionResult{ActionID: req.ActionID, Success: true, DryRun: true,
            Summary: "Would block " + req.Params["ip"].(string)}, nil
    }
    // … firewall API call …
    return quarry.ActionResult{ActionID: req.ActionID, Success: true, Summary: "Blocked"}, nil
}
```

### Plugin Registry

```go
reg := quarry.NewRegistry()
reg.Register(&VTEnricher{})
reg.Register(&BlockIPAction{})

pctx := quarry.PluginContext{APIBaseURL: "http://api:8000", APIToken: "…"}
if err := reg.LoadAll(ctx, pctx); err != nil {
    log.Fatal(err)
}

for _, e := range reg.Enrichers() {
    result, _ := e.Enrich(ctx, req, pctx)
    // …
}
```

## Running the Example

```bash
cd examples/enricher
go run main.go
```

## Development

```bash
go test ./...
go vet ./...
```

## License

MIT — see [LICENSE](../../LICENSE).
