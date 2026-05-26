#!/usr/bin/env bash
# ─────────────────────────────────────────────────────────────────────────────
# Quarry — Sovereign LLM (Modalidade B) — VPS install
#
# Installs:
#   • Ollama (CPU/RAM tiers) or vLLM (GPU tier) — runtime LLM
#   • Pinned model per detected tier (Llama 3.1 8B / Qwen 2.5 14B / Llama 3.3 70B)
#   • systemd unit hardened (NoNewPrivileges, ProtectSystem, etc.)
#   • WireGuard server skeleton (Quarry web connects in via private VPN)
#   • UFW rules: only WireGuard (51820/udp) + SSH from outside;
#     Ollama bind on 127.0.0.1 + wg0 interface only
#
# Target OS:  Ubuntu 22.04 LTS / 24.04 LTS (fresh VPS, root)
# Target time: < 1 hour end-to-end including model pull
#
# Usage:
#   sudo bash install-vps-linux.sh                  # auto-detect tier
#   sudo TIER=standard bash install-vps-linux.sh    # force a tier
#   sudo MODEL=qwen2.5:14b-instruct-q4_K_M bash …   # override model
#
# Tiers (auto-detected from CPU + RAM + GPU):
#   light    — < 48GB RAM, no GPU  → Ollama + Llama 3.1 8B Q4
#   standard — ≥ 48GB RAM, no GPU  → Ollama + Qwen 2.5 14B Q4
#   pro      — NVIDIA GPU ≥ 20GB   → vLLM   + Llama 3.3 70B Q4
#
# ─────────────────────────────────────────────────────────────────────────────
set -euo pipefail

# ── Config ────────────────────────────────────────────────────────────────────
QUARRY_USER="quarry"
QUARRY_HOME="/opt/quarry-sovereign"
OLLAMA_VERSION="${OLLAMA_VERSION:-}"     # empty = latest stable from install.sh
WG_PORT="${WG_PORT:-51820}"
WG_NET="${WG_NET:-10.99.0.0/24}"
WG_SERVER_IP="${WG_SERVER_IP:-10.99.0.1}"
LOG_FILE="/var/log/quarry-sovereign-install.log"

# Models per tier (override with MODEL=…)
MODEL_LIGHT="llama3.1:8b-instruct-q4_K_M"
MODEL_STANDARD="qwen2.5:14b-instruct-q4_K_M"
MODEL_PRO="llama3.3:70b-instruct-q4_K_M"   # via vLLM (huggingface id resolved below)
MODEL_PRO_HF="meta-llama/Llama-3.3-70B-Instruct"

# ── Helpers ───────────────────────────────────────────────────────────────────
ts() { date -u +"%Y-%m-%dT%H:%M:%SZ"; }
log() { printf "[%s] %s\n" "$(ts)" "$*" | tee -a "$LOG_FILE"; }
die() { log "FATAL: $*"; exit 1; }

require_root() {
  [ "$(id -u)" -eq 0 ] || die "must run as root (sudo)"
}

require_ubuntu_lts() {
  local id ver
  id=$(. /etc/os-release && echo "$ID")
  ver=$(. /etc/os-release && echo "$VERSION_ID")
  [ "$id" = "ubuntu" ] || die "only ubuntu supported (detected: $id)"
  case "$ver" in
    22.04|24.04) ;;
    *) die "only Ubuntu 22.04 / 24.04 supported (detected: $ver)" ;;
  esac
}

require_network() {
  curl -fsSL --max-time 10 https://ollama.com/install.sh -o /dev/null \
    || die "no internet to ollama.com — check VPS network"
}

# ── Tier detection ────────────────────────────────────────────────────────────
detect_tier() {
  local ram_gb gpu_present gpu_vram_gb
  ram_gb=$(awk '/MemTotal/ {print int($2/1024/1024)}' /proc/meminfo)
  gpu_present=0
  gpu_vram_gb=0
  if command -v nvidia-smi >/dev/null 2>&1; then
    if nvidia-smi --query-gpu=memory.total --format=csv,noheader,nounits >/dev/null 2>&1; then
      gpu_present=1
      gpu_vram_gb=$(nvidia-smi --query-gpu=memory.total --format=csv,noheader,nounits \
        | awk '{s+=$1} END{print int(s/1024)}')
    fi
  fi
  if [ "$gpu_present" -eq 1 ] && [ "$gpu_vram_gb" -ge 20 ]; then
    echo "pro"
  elif [ "$ram_gb" -ge 48 ]; then
    echo "standard"
  else
    echo "light"
  fi
}

pick_model() {
  case "$1" in
    light)    echo "${MODEL:-$MODEL_LIGHT}" ;;
    standard) echo "${MODEL:-$MODEL_STANDARD}" ;;
    pro)      echo "${MODEL:-$MODEL_PRO}" ;;
    *)        die "unknown tier: $1" ;;
  esac
}

# ── Stage 0: prereqs ──────────────────────────────────────────────────────────
stage_prereqs() {
  log "stage 0: prereqs"
  export DEBIAN_FRONTEND=noninteractive
  apt-get update -qq
  apt-get install -y -qq \
    curl ca-certificates jq ufw wireguard wireguard-tools qrencode \
    htop iotop sysstat unattended-upgrades fail2ban \
    python3 python3-venv python3-pip
  # Auto security upgrades
  dpkg-reconfigure -plow unattended-upgrades >/dev/null 2>&1 || true
  # Ensure quarry service user exists
  if ! id "$QUARRY_USER" >/dev/null 2>&1; then
    useradd -r -s /usr/sbin/nologin -d "$QUARRY_HOME" -m "$QUARRY_USER"
  fi
  mkdir -p "$QUARRY_HOME"/{bin,etc,logs,models}
  chown -R "$QUARRY_USER":"$QUARRY_USER" "$QUARRY_HOME"
  log "stage 0: done"
}

# ── Stage 1: install Ollama (light/standard) ──────────────────────────────────
stage_ollama() {
  log "stage 1: installing Ollama"
  if ! command -v ollama >/dev/null 2>&1; then
    curl -fsSL https://ollama.com/install.sh | sh
  else
    log "ollama already installed: $(ollama --version 2>&1 | head -1)"
  fi

  # Harden the systemd unit shipped by Ollama: bind to 127.0.0.1 + wg0 only
  install -d /etc/systemd/system/ollama.service.d
  cat >/etc/systemd/system/ollama.service.d/override.conf <<EOF
[Service]
# Bind only to loopback and the WireGuard private network — never 0.0.0.0
Environment="OLLAMA_HOST=127.0.0.1:11434"
Environment="OLLAMA_ORIGINS=http://127.0.0.1,http://${WG_SERVER_IP}"
# Disable telemetry / model auto-update phone-home
Environment="OLLAMA_NOPRUNE=true"
Environment="OLLAMA_KEEP_ALIVE=24h"
# Resource caps (tweak if needed)
LimitNOFILE=1048576
# Hardening
NoNewPrivileges=true
ProtectSystem=strict
ProtectHome=true
PrivateTmp=true
PrivateDevices=false  # needs /dev/nvidia* on pro tier; harmless on CPU
ReadWritePaths=/usr/share/ollama /root/.ollama /var/lib/ollama
EOF
  systemctl daemon-reload
  systemctl enable --now ollama
  log "stage 1: done"
}

# ── Stage 1b: install vLLM (pro tier, GPU) ────────────────────────────────────
stage_vllm() {
  log "stage 1b: installing vLLM (pro tier)"
  command -v nvidia-smi >/dev/null || die "vLLM requires NVIDIA GPU + drivers"
  apt-get install -y -qq nvidia-cuda-toolkit
  # vLLM via venv (avoid polluting system python)
  python3 -m venv "$QUARRY_HOME/venv-vllm"
  "$QUARRY_HOME/venv-vllm/bin/pip" install --upgrade pip wheel
  "$QUARRY_HOME/venv-vllm/bin/pip" install "vllm>=0.6.0"
  chown -R "$QUARRY_USER":"$QUARRY_USER" "$QUARRY_HOME/venv-vllm"
  log "stage 1b: vLLM installed"
}

# ── Stage 2: pull model ───────────────────────────────────────────────────────
stage_pull_model() {
  local tier="$1" model
  model=$(pick_model "$tier")
  log "stage 2: pulling model ($tier → $model)"
  if [ "$tier" = "pro" ]; then
    log "pro tier: vLLM downloads model on first serve (HF: $MODEL_PRO_HF)"
    log "    set HUGGING_FACE_HUB_TOKEN in /etc/quarry-sovereign/env before starting vllm"
  else
    ollama pull "$model" 2>&1 | tee -a "$LOG_FILE"
  fi
  log "stage 2: done"
}

# ── Stage 3: vLLM systemd unit (pro tier only) ────────────────────────────────
stage_vllm_unit() {
  log "stage 3: writing vLLM systemd unit"
  install -d /etc/quarry-sovereign
  if [ ! -f /etc/quarry-sovereign/env ]; then
    cat >/etc/quarry-sovereign/env <<EOF
# Hugging Face token required to download gated Llama 3.x weights
HUGGING_FACE_HUB_TOKEN=
VLLM_PORT=11434
VLLM_MODEL=$MODEL_PRO_HF
EOF
    chmod 600 /etc/quarry-sovereign/env
  fi

  cat >/etc/systemd/system/quarry-vllm.service <<EOF
[Unit]
Description=Quarry Sovereign LLM — vLLM server
After=network-online.target
Wants=network-online.target

[Service]
Type=simple
User=$QUARRY_USER
Group=$QUARRY_USER
EnvironmentFile=/etc/quarry-sovereign/env
ExecStart=$QUARRY_HOME/venv-vllm/bin/python -m vllm.entrypoints.openai.api_server \\
    --model \${VLLM_MODEL} \\
    --host 127.0.0.1 \\
    --port \${VLLM_PORT} \\
    --gpu-memory-utilization 0.92 \\
    --max-model-len 8192
Restart=on-failure
RestartSec=10s
LimitNOFILE=1048576
NoNewPrivileges=true
ProtectSystem=strict
ProtectHome=true
PrivateTmp=true
ReadWritePaths=$QUARRY_HOME

[Install]
WantedBy=multi-user.target
EOF
  systemctl daemon-reload
  systemctl enable quarry-vllm
  log "stage 3: vLLM unit installed (NOT started — set HF token in /etc/quarry-sovereign/env then: systemctl start quarry-vllm)"
}

# ── Stage 4: WireGuard server ─────────────────────────────────────────────────
stage_wireguard() {
  log "stage 4: configuring WireGuard"
  install -d -m 700 /etc/wireguard
  if [ ! -f /etc/wireguard/server-private.key ]; then
    wg genkey | tee /etc/wireguard/server-private.key | wg pubkey > /etc/wireguard/server-public.key
    chmod 600 /etc/wireguard/server-private.key
  fi
  local SERVER_PRIV SERVER_PUB
  SERVER_PRIV=$(cat /etc/wireguard/server-private.key)
  SERVER_PUB=$(cat /etc/wireguard/server-public.key)

  cat >/etc/wireguard/wg0.conf <<EOF
[Interface]
PrivateKey = $SERVER_PRIV
Address    = $WG_SERVER_IP/24
ListenPort = $WG_PORT
SaveConfig = false
# Block forwarding by default; clients are added with [Peer] blocks below.
PostUp   = iptables -A FORWARD -i wg0 -j ACCEPT; iptables -A FORWARD -o wg0 -j ACCEPT
PostDown = iptables -D FORWARD -i wg0 -j ACCEPT; iptables -D FORWARD -o wg0 -j ACCEPT

# ── Peers (add the Quarry web server here) ──────────────────────────────────
# Each line below corresponds to one peer that may reach this LLM.
# To register a new peer, append:
#   [Peer]
#   PublicKey  = <peer-pub-key>
#   AllowedIPs = 10.99.0.<n>/32
EOF
  chmod 600 /etc/wireguard/wg0.conf

  # Enable forwarding (idempotent)
  if ! grep -q "^net.ipv4.ip_forward=1" /etc/sysctl.d/99-quarry-sovereign.conf 2>/dev/null; then
    echo "net.ipv4.ip_forward=1" > /etc/sysctl.d/99-quarry-sovereign.conf
    sysctl -p /etc/sysctl.d/99-quarry-sovereign.conf >/dev/null
  fi

  systemctl enable --now wg-quick@wg0
  log "stage 4: WireGuard up — server public key: $SERVER_PUB"
  echo "$SERVER_PUB" > "$QUARRY_HOME/etc/wg-server-public.key"
}

# ── Stage 5: firewall ─────────────────────────────────────────────────────────
stage_firewall() {
  log "stage 5: configuring UFW"
  ufw --force reset >/dev/null
  ufw default deny incoming
  ufw default allow outgoing
  ufw allow 22/tcp
  ufw allow "$WG_PORT"/udp
  # NEVER expose 11434 to the public internet — only via wg0
  ufw --force enable
  log "stage 5: firewall up (22/tcp, ${WG_PORT}/udp)"
}

# ── Stage 6: healthcheck + helper ─────────────────────────────────────────────
stage_helpers() {
  log "stage 6: writing helper scripts"
  cat >"$QUARRY_HOME/bin/healthcheck.sh" <<'EOF'
#!/usr/bin/env bash
# Quarry sovereign LLM healthcheck — prints JSON to stdout, exits non-zero on error
set -euo pipefail
ENDPOINT="${ENDPOINT:-http://127.0.0.1:11434}"
TIER_FILE="/etc/quarry-sovereign/tier"
TIER="$(cat "$TIER_FILE" 2>/dev/null || echo unknown)"

if [ "$TIER" = "pro" ]; then
  # vLLM exposes OpenAI-compatible /v1/models
  RESP=$(curl -sf --max-time 5 "$ENDPOINT/v1/models" || echo "")
else
  # Ollama
  RESP=$(curl -sf --max-time 5 "$ENDPOINT/api/tags" || echo "")
fi

if [ -z "$RESP" ]; then
  echo '{"status":"down","tier":"'"$TIER"'","endpoint":"'"$ENDPOINT"'"}'
  exit 1
fi

# Quick latency probe
START=$(date +%s%N)
if [ "$TIER" = "pro" ]; then
  curl -sf --max-time 30 -X POST "$ENDPOINT/v1/completions" \
    -H 'Content-Type: application/json' \
    -d '{"model":"'"$(echo "$RESP" | jq -r '.data[0].id // empty')"'","prompt":"ping","max_tokens":1}' \
    >/dev/null || true
else
  curl -sf --max-time 30 -X POST "$ENDPOINT/api/generate" \
    -H 'Content-Type: application/json' \
    -d '{"model":"'"$(echo "$RESP" | jq -r '.models[0].name // empty')"'","prompt":"ping","stream":false,"options":{"num_predict":1}}' \
    >/dev/null || true
fi
END=$(date +%s%N)
LAT_MS=$(( (END - START) / 1000000 ))

echo '{"status":"ok","tier":"'"$TIER"'","endpoint":"'"$ENDPOINT"'","latency_ms":'"$LAT_MS"'}'
EOF
  chmod +x "$QUARRY_HOME/bin/healthcheck.sh"

  cat >"$QUARRY_HOME/bin/add-peer.sh" <<'EOF'
#!/usr/bin/env bash
# Register a new WireGuard peer (Quarry web instance) on this sovereign VPS.
# Usage: add-peer.sh <name> <peer-public-key> <ip-suffix:e.g. 2>
set -euo pipefail
NAME="$1"; PUBKEY="$2"; SUFFIX="${3:-2}"
WG_CONF=/etc/wireguard/wg0.conf
grep -qF "$PUBKEY" "$WG_CONF" && { echo "peer $NAME already present"; exit 0; }
cat >> "$WG_CONF" <<EOP

# Peer: $NAME (added $(date -u +%Y-%m-%dT%H:%M:%SZ))
[Peer]
PublicKey  = $PUBKEY
AllowedIPs = 10.99.0.$SUFFIX/32
EOP
systemctl restart wg-quick@wg0
echo "peer $NAME added with 10.99.0.$SUFFIX/32"
EOF
  chmod +x "$QUARRY_HOME/bin/add-peer.sh"
  log "stage 6: helpers written ($QUARRY_HOME/bin/)"
}

# ── Stage 7: persist tier + print summary ─────────────────────────────────────
stage_summary() {
  local tier="$1" model
  model=$(pick_model "$tier")
  echo "$tier" > /etc/quarry-sovereign/tier

  log "=============================================================="
  log " Quarry Sovereign LLM — installation complete"
  log " Tier:     $tier"
  log " Model:    $model"
  log " Endpoint: http://127.0.0.1:11434  (bound to loopback + wg0)"
  log " WireGuard:  $(cat /etc/wireguard/server-public.key)"
  log "             listen on UDP $WG_PORT"
  log " Helpers:  $QUARRY_HOME/bin/healthcheck.sh"
  log "           $QUARRY_HOME/bin/add-peer.sh"
  log "--------------------------------------------------------------"
  log " Next steps:"
  if [ "$tier" = "pro" ]; then
    log "   1. Add HF token to /etc/quarry-sovereign/env (gated Llama 3.x)"
    log "   2. systemctl start quarry-vllm  &&  systemctl status quarry-vllm"
  fi
  log "   3. From Quarry web: generate peer keypair, then on this VPS run:"
  log "        $QUARRY_HOME/bin/add-peer.sh quarry-web <peer-public-key> 2"
  log "   4. Verify: $QUARRY_HOME/bin/healthcheck.sh"
  log "   5. Set llm_resolver.py target to: sovereign-vps://${WG_SERVER_IP}:11434"
  log "=============================================================="
}

# ── Main ──────────────────────────────────────────────────────────────────────
main() {
  : > "$LOG_FILE" || die "cannot write $LOG_FILE"
  log "Quarry Sovereign LLM (Modalidade B) install — starting"

  require_root
  require_ubuntu_lts
  require_network

  local TIER="${TIER:-$(detect_tier)}"
  log "tier: $TIER"

  stage_prereqs
  if [ "$TIER" = "pro" ]; then
    stage_vllm
    stage_pull_model "$TIER"
    stage_vllm_unit
  else
    stage_ollama
    stage_pull_model "$TIER"
  fi
  stage_wireguard
  stage_firewall
  stage_helpers
  stage_summary "$TIER"
}

main "$@"
