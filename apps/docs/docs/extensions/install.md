---
id: extensions-install
title: Installing the AiSOC Extension
sidebar_label: Installation
sidebar_position: 2
---

# Installing the AiSOC Extension

## Prerequisites

- osquery ≥ 5.10 installed on the host
- AiSOC TLS enrolment completed (node must be enrolled)
- Network access to `api.tryaisoc.com` on port 443

## Automatic installation (recommended)

The installer script downloads the correct binary for your OS/arch, installs it
to `/usr/local/bin/aisoc-extension`, and writes the systemd unit (Linux) or
launchd plist (macOS) to start the extension automatically.

```bash
curl -fsSL https://releases.tryaisoc.com/extension/install.sh | bash
```

The script uses the node's existing osquery `node_key` (stored in
`/etc/osquery/osquery.db`) to request a host-scoped token from the API.  No
additional credentials are required.

## Manual installation

### 1. Download the binary

```bash
OS=$(uname -s | tr '[:upper:]' '[:lower:]')
ARCH=$(uname -m | sed 's/x86_64/amd64/')
VERSION=1.0.0
curl -Lo /tmp/aisoc-extension \
  "https://releases.tryaisoc.com/extension/${VERSION}/aisoc-extension_${OS}_${ARCH}"
chmod +x /tmp/aisoc-extension
sudo mv /tmp/aisoc-extension /usr/local/bin/aisoc-extension
```

### 2. Configure

Create `/etc/osquery/aisoc-extension.env`:

```ini
AISOC_API_URL=https://api.tryaisoc.com
AISOC_HOST_TOKEN=<host-scoped-token>
AISOC_POLL_INTERVAL=300
```

:::tip Token provisioning
Your `AISOC_HOST_TOKEN` is printed during `osqueryd` TLS enrolment.  It can
also be retrieved from the API:

```bash
curl -H "Authorization: Bearer $TENANT_TOKEN" \
  "https://api.tryaisoc.com/api/v1/nodes/<host_identifier>/extension-token"
```
:::

### 3. Register with osquery

Add to `/etc/osquery/osquery.flags`:

```
--extensions_socket=/var/osquery/osquery.em
--extensions_timeout=3
--extensions_interval=3
```

Add the autoload entry to `/etc/osquery/extensions.load`:

```
/usr/local/bin/aisoc-extension
```

### 4. Start the extension

```bash
# Linux (systemd)
sudo systemctl restart osqueryd

# macOS (launchd)
sudo launchctl kickstart -k system/com.facebook.osqueryd
```

## Verify

```sql
osqueryi "SELECT action_id, action_type, created_at
          FROM aisoc_pending_actions
          LIMIT 5;"
```

## Uninstall

```bash
# Remove extension binary
sudo rm /usr/local/bin/aisoc-extension

# Remove from autoload
sudo sed -i '/aisoc-extension/d' /etc/osquery/extensions.load

# Restart osquery
sudo systemctl restart osqueryd
```
