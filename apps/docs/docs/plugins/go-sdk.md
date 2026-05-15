---
sidebar_position: 3
---

# Go Plugin SDK

## Installation

```bash
go get github.com/beenuar/quarry/plugin-sdk-go
```

## Quick Start: Enricher

```go
package main

import (
    "context"
    "github.com/beenuar/quarry/plugin-sdk-go/quarry"
)

type IPReputationEnricher struct {
    quarry.BasePlugin
}

func (e *IPReputationEnricher) Manifest() quarry.PluginManifest {
    return quarry.PluginManifest{
        ID:          "myorg.ip-reputation",
        Name:        "IP Reputation",
        Version:     "1.0.0",
        PluginType:  quarry.PluginTypeEnricher,
    }
}

func (e *IPReputationEnricher) Enrich(
    ctx context.Context,
    req quarry.EnrichmentRequest,
    pluginCtx quarry.PluginContext,
) (quarry.EnrichmentResult, error) {
    return quarry.EnrichmentResult{
        IndicatorType:  req.IndicatorType,
        IndicatorValue: req.IndicatorValue,
        Enrichments:    map[string]any{"score": 42},
        Malicious:      true,
        Confidence:     0.87,
    }, nil
}

func main() {
    registry := quarry.NewRegistry()
    plugin := &IPReputationEnricher{}
    registry.Register(plugin)
    ctx := quarry.PluginContext{APIBaseURL: "http://localhost:8000"}
    registry.LoadAll(context.Background(), ctx)
}
```

## Quick Start: Action

```go
type BlockIPAction struct {
    quarry.BasePlugin
}

func (a *BlockIPAction) Manifest() quarry.PluginManifest {
    return quarry.PluginManifest{
        ID:         "myorg.block-ip",
        Name:       "Block IP",
        Version:    "1.0.0",
        PluginType: quarry.PluginTypeAction,
    }
}

func (a *BlockIPAction) SupportedActions() []string {
    return []string{"block_ip"}
}

func (a *BlockIPAction) Execute(
    ctx context.Context,
    req quarry.ActionRequest,
    pluginCtx quarry.PluginContext,
) (quarry.ActionResult, error) {
    if req.DryRun {
        return quarry.ActionResult{
            ActionID: req.ActionID, Success: true, DryRun: true,
        }, nil
    }
    return quarry.ActionResult{ActionID: req.ActionID, Success: true}, nil
}
```

## Development

```bash
cd packages/plugin-sdk-go
go test ./...
go vet ./...
```
