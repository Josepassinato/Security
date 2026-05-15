// Package main is the Tailscale ACL action reference implementation in Go.
//
// Demonstrates the Quarry Go Plugin SDK for an isolation/network response action
// against the Tailscale REST API.
package main

import (
	"context"
	"encoding/json"
	"errors"
	"fmt"
	"io"
	"net/http"
	"time"

	"github.com/beenuar/quarry/plugin-sdk-go/quarry"
)

const tsAPIBase = "https://api.tailscale.com/api/v2"

// TailscaleACLAction implements quarry.Action for the Tailscale API.
type TailscaleACLAction struct {
	quarry.BasePlugin

	httpClient *http.Client
}

func (t *TailscaleACLAction) Manifest() quarry.PluginManifest {
	return quarry.PluginManifest{
		ID:          "tailscale-acl",
		Name:        "Tailscale ACL Action",
		Version:     "1.0.0",
		PluginType:  quarry.PluginTypeAction,
		Description: "Manage Tailscale devices and tailnet ACLs as response actions.",
		Author:      "Quarry Core Team",
		Tags:        []string{"network", "tailscale", "zerotrust", "response", "isolation"},
	}
}

func (t *TailscaleACLAction) OnLoad(ctx context.Context, pctx quarry.PluginContext) error {
	t.httpClient = &http.Client{Timeout: 30 * time.Second}
	return nil
}

func (t *TailscaleACLAction) SupportedActions() []string {
	return []string{
		"list_devices",
		"get_device",
		"delete_device",
		"get_acl",
		"update_acl",
	}
}

func (t *TailscaleACLAction) Execute(
	ctx context.Context,
	req quarry.ActionRequest,
	pctx quarry.PluginContext,
) (quarry.ActionResult, error) {
	apiKey, _ := pctx.Config["api_key"].(string)
	tailnet, _ := pctx.Config["tailnet"].(string)
	if apiKey == "" || tailnet == "" {
		return quarry.ActionResult{
			ActionID: req.ActionID,
			Error:    "api_key and tailnet are required",
		}, errors.New("api_key and tailnet are required")
	}

	switch req.ActionID {
	case "list_devices":
		body, err := t.do(ctx, apiKey, "GET",
			fmt.Sprintf("/tailnet/%s/devices", tailnet), nil, "")
		if err != nil {
			return quarry.ActionResult{ActionID: req.ActionID, Error: err.Error()}, err
		}
		var parsed map[string]any
		_ = json.Unmarshal(body, &parsed)
		return quarry.ActionResult{
			ActionID: req.ActionID,
			Success:  true,
			Summary:  "listed Tailscale devices",
			Details:  parsed,
		}, nil
	case "delete_device":
		deviceID, _ := req.Params["device_id"].(string)
		_, err := t.do(ctx, apiKey, "DELETE", "/device/"+deviceID, nil, "")
		if err != nil {
			return quarry.ActionResult{ActionID: req.ActionID, Error: err.Error()}, err
		}
		return quarry.ActionResult{
			ActionID: req.ActionID,
			Success:  true,
			Summary:  fmt.Sprintf("deleted device %s", deviceID),
		}, nil
	default:
		return quarry.ActionResult{
			ActionID: req.ActionID,
			Error:    "unsupported action: " + req.ActionID,
		}, nil
	}
}

func (t *TailscaleACLAction) do(
	ctx context.Context,
	apiKey, method, path string,
	body []byte,
	contentType string,
) ([]byte, error) {
	req, err := http.NewRequestWithContext(ctx, method, tsAPIBase+path, nil)
	if err != nil {
		return nil, err
	}
	req.SetBasicAuth(apiKey, "")
	if contentType != "" {
		req.Header.Set("Content-Type", contentType)
	}
	resp, err := t.httpClient.Do(req)
	if err != nil {
		return nil, err
	}
	defer resp.Body.Close()
	if resp.StatusCode >= 400 {
		return nil, errors.New("tailscale api: " + resp.Status)
	}
	return io.ReadAll(resp.Body)
}

func main() {
	registry := quarry.NewRegistry()
	if err := registry.Register(&TailscaleACLAction{}); err != nil {
		panic(err)
	}
	fmt.Println("tailscale-acl reference plugin loaded")
}
