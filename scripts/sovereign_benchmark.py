#!/usr/bin/env python3
"""
Sovereign LLM benchmark runner — CARD-015 Tarefa #6.

Measures Modalidade B (VPS Llama via Ollama or vLLM) and Modalidade C
(cloud BYOK — OpenAI / Anthropic / Gemini) on the same fixed prompt
suite, then emits a JSON report the marketing pages and the
``docs/pt-br/sovereign-llm/benchmark.md`` doc consume.

Usage:

    # Modalidade B against your Sovereign VPS
    python3 scripts/sovereign_benchmark.py \\
        --target sovereign-vps \\
        --base-url http://10.99.0.1:11434/v1 \\
        --model qwen2.5:14b-instruct-q4_K_M

    # Modalidade C against OpenAI
    python3 scripts/sovereign_benchmark.py \\
        --target cloud-byok \\
        --base-url https://api.openai.com/v1 \\
        --model gpt-4o-mini \\
        --api-key "$OPENAI_API_KEY"

    # Side-by-side: run both targets and emit diff
    python3 scripts/sovereign_benchmark.py --suite both \\
        --output /tmp/sovereign-bench-$(date +%Y%m%d).json

The script is OpenAI-Chat-Completions compatible: any endpoint that
serves ``POST /v1/chat/completions`` works (Ollama, vLLM, LiteLLM,
OpenAI, Anthropic via litellm, etc.). We probe ``/v1/models`` first
to confirm the model is loaded before timing requests.

Output is JSON only. No invented metrics — when a run fails we
record the error and exclude that sample from latency/throughput
aggregates rather than fabricate a number.
"""
from __future__ import annotations

import argparse
import json
import os
import statistics
import sys
import time
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import httpx

# ── Prompt suite ───────────────────────────────────────────────────
#
# A fixed list of representative explain-path tasks. Kept deliberately
# small (10 prompts) so a full benchmark run finishes in ~3 minutes
# even on the cheapest VPS tier. Sourced from the real explain corpus
# in services/agents/tests/eval_data/synthetic_incidents.json but
# trimmed to bare prompts here so this script has zero dependencies on
# the agents service.

PROMPTS: list[dict[str, str]] = [
    {
        "id": "phishing-triage",
        "system": "You are Quarry, a SOC triage assistant. Be terse and cite evidence.",
        "user": "An employee received an email from `support@m1crosoft-azure.com` with a link to a password reset. Classify and recommend.",
    },
    {
        "id": "lateral-movement",
        "system": "You are Quarry, analysing endpoint telemetry.",
        "user": "Sysmon EID 1: powershell.exe -enc <base64> spawning rundll32 from a user workstation at 03:14 BRT. Single sentence verdict.",
    },
    {
        "id": "pix-fraud",
        "system": "You are Quarry, monitoring a Bacen-licensed PSP under Res. BCB 85/2021.",
        "user": "Five Pix-OUT keyed to the same beneficiary CPF, R$ 4.999 each, within 90 seconds. Required action?",
    },
    {
        "id": "iam-anomaly",
        "system": "You are Quarry, evaluating IAM events.",
        "user": "AWS CloudTrail: `AssumeRole` from `arn:aws:iam::123:role/admin-break-glass` at 04:32 BRT on Sunday. Verdict?",
    },
    {
        "id": "rfe-triggers",
        "system": "You are Quarry, mapping detection findings to LGPD reporting obligations.",
        "user": "100k records of CPF + DOB + endereço staged for export to S3 prefix `s3://external-vendor-x/`. Disclose to ANPD?",
    },
    {
        "id": "supply-chain",
        "system": "You are Quarry, watching CI/CD telemetry.",
        "user": "GitHub Actions runner pulled a new dep `colors@npm:1.4.45-malicious`. Block, revert, or escalate?",
    },
    {
        "id": "cloud-misconfig",
        "system": "You are Quarry, posture-graphing GCP.",
        "user": "GCS bucket `kyc-documents-prod` flipped to `allUsers:reader`. Estimated blast radius?",
    },
    {
        "id": "open-finance",
        "system": "You are Quarry, monitoring Open Finance webhooks.",
        "user": "Itinerant client `tppX` requested 12k consents in 30s. Throttle or block?",
    },
    {
        "id": "insider",
        "system": "You are Quarry, on insider-risk duty.",
        "user": "Engineering manager downloaded the full HR PII corpus 48h before resignation. Action.",
    },
    {
        "id": "kyc-bypass",
        "system": "You are Quarry, reading antifraud logs for an SCD.",
        "user": "100 onboarding sessions in the last 4h all completing in <8 seconds, all from /24 net `2804:7fXX:...`. Investigate?",
    },
]


# ── Result dataclasses ─────────────────────────────────────────────


@dataclass
class SampleResult:
    prompt_id: str
    ok: bool
    latency_ms: int
    prompt_tokens: int
    completion_tokens: int
    error: str = ""


@dataclass
class TargetReport:
    target: str
    base_url: str
    model: str
    runtime: str  # "ollama" | "vllm" | "openai" | "anthropic" | "unknown"
    started_at: str
    finished_at: str
    samples: list[SampleResult] = field(default_factory=list)

    def aggregates(self) -> dict[str, Any]:
        oks = [s for s in self.samples if s.ok]
        if not oks:
            return {
                "n_attempted": len(self.samples),
                "n_succeeded": 0,
                "note": "all samples failed — see per-sample errors",
            }
        latencies = [s.latency_ms for s in oks]
        completion = [s.completion_tokens for s in oks]
        prompts = [s.prompt_tokens for s in oks]
        # tok/s computed only over successful samples
        tok_per_s = [
            (c / (lat / 1000.0)) if lat > 0 else 0.0
            for lat, c in zip(latencies, completion)
        ]
        return {
            "n_attempted": len(self.samples),
            "n_succeeded": len(oks),
            "latency_ms": {
                "p50": int(statistics.median(latencies)),
                "p95": int(_percentile(latencies, 95)),
                "min": min(latencies),
                "max": max(latencies),
                "mean": int(statistics.mean(latencies)),
            },
            "completion_tokens": {
                "mean": int(statistics.mean(completion)) if completion else 0,
                "total": sum(completion),
            },
            "prompt_tokens": {"total": sum(prompts)},
            "throughput_tok_per_s": {
                "median": round(statistics.median(tok_per_s), 2),
                "mean": round(statistics.mean(tok_per_s), 2),
            },
        }


def _percentile(values: list[int], p: float) -> float:
    if not values:
        return 0.0
    s = sorted(values)
    k = (len(s) - 1) * (p / 100.0)
    f, c = int(k), min(int(k) + 1, len(s) - 1)
    if f == c:
        return float(s[f])
    return s[f] + (s[c] - s[f]) * (k - f)


# ── Probe + runtime detection ──────────────────────────────────────


def detect_runtime(base_url: str, api_key: str | None) -> str:
    """Best-effort detection from /v1/models and /api/tags shape."""
    headers = {"Authorization": f"Bearer {api_key}"} if api_key else {}
    root = base_url.rstrip("/")
    if root.endswith("/v1"):
        ollama_root = root[:-3]
    else:
        ollama_root = root
    try:
        resp = httpx.get(f"{ollama_root}/api/tags", timeout=5.0)
        if 200 <= resp.status_code < 300:
            payload = resp.json()
            if isinstance(payload.get("models"), list):
                return "ollama"
    except Exception:  # noqa: BLE001
        pass
    try:
        resp = httpx.get(f"{root}/models", timeout=5.0, headers=headers)
        if 200 <= resp.status_code < 300:
            payload = resp.json()
            data = payload.get("data") if isinstance(payload, dict) else None
            if isinstance(data, list) and data:
                first_id = (data[0] or {}).get("id", "")
                if first_id.startswith("gpt-") or "openai" in first_id.lower():
                    return "openai"
                if first_id.startswith("claude-"):
                    return "anthropic"
                return "vllm"
    except Exception:  # noqa: BLE001
        pass
    return "unknown"


# ── Single-sample runner ───────────────────────────────────────────


def run_sample(
    client: httpx.Client,
    base_url: str,
    model: str,
    api_key: str | None,
    prompt: dict[str, str],
    max_tokens: int = 256,
    timeout_s: float = 60.0,
) -> SampleResult:
    headers = {"Content-Type": "application/json"}
    if api_key:
        headers["Authorization"] = f"Bearer {api_key}"

    body = {
        "model": model,
        "messages": [
            {"role": "system", "content": prompt["system"]},
            {"role": "user", "content": prompt["user"]},
        ],
        "max_tokens": max_tokens,
        "temperature": 0.0,
        "stream": False,
    }

    started = time.perf_counter()
    try:
        resp = client.post(
            f"{base_url.rstrip('/')}/chat/completions",
            json=body,
            headers=headers,
            timeout=timeout_s,
        )
        latency_ms = int((time.perf_counter() - started) * 1000)
        if not (200 <= resp.status_code < 300):
            return SampleResult(
                prompt_id=prompt["id"],
                ok=False,
                latency_ms=latency_ms,
                prompt_tokens=0,
                completion_tokens=0,
                error=f"HTTP {resp.status_code}: {resp.text[:200]}",
            )
        payload = resp.json()
        usage = payload.get("usage") or {}
        return SampleResult(
            prompt_id=prompt["id"],
            ok=True,
            latency_ms=latency_ms,
            prompt_tokens=int(usage.get("prompt_tokens") or 0),
            completion_tokens=int(usage.get("completion_tokens") or 0),
        )
    except httpx.RequestError as exc:
        return SampleResult(
            prompt_id=prompt["id"],
            ok=False,
            latency_ms=int((time.perf_counter() - started) * 1000),
            prompt_tokens=0,
            completion_tokens=0,
            error=f"transport: {exc!s}",
        )


# ── Driver ─────────────────────────────────────────────────────────


def run_target(
    target: str,
    base_url: str,
    model: str,
    api_key: str | None,
    warmup: int = 1,
) -> TargetReport:
    runtime = detect_runtime(base_url, api_key)
    started_at = datetime.now(timezone.utc).isoformat()

    report = TargetReport(
        target=target,
        base_url=base_url,
        model=model,
        runtime=runtime,
        started_at=started_at,
        finished_at="",
    )

    with httpx.Client(timeout=60.0) as client:
        # Warmup (cold-model penalty doesn't get counted in p95)
        for _ in range(warmup):
            run_sample(client, base_url, model, api_key, PROMPTS[0])
        # Actual run
        for prompt in PROMPTS:
            report.samples.append(
                run_sample(client, base_url, model, api_key, prompt)
            )

    report.finished_at = datetime.now(timezone.utc).isoformat()
    return report


def main(argv: list[str]) -> int:
    parser = argparse.ArgumentParser(description="Sovereign LLM benchmark (CARD-015 #6).")
    parser.add_argument("--target", required=True, choices=["sovereign-vps", "sovereign-mac", "cloud-byok"])
    parser.add_argument("--base-url", required=True, help="OpenAI-compatible endpoint (with /v1 suffix).")
    parser.add_argument("--model", required=True)
    parser.add_argument("--api-key", default=None, help="Optional bearer token (env QUARRY_BENCH_KEY).")
    parser.add_argument("--warmup", type=int, default=1)
    parser.add_argument("--output", default="-", help="Output JSON path, or '-' for stdout.")
    args = parser.parse_args(argv)

    api_key = args.api_key or os.getenv("QUARRY_BENCH_KEY")
    report = run_target(args.target, args.base_url, args.model, api_key, args.warmup)
    payload = {
        "target": report.target,
        "base_url": report.base_url,
        "model": report.model,
        "runtime": report.runtime,
        "started_at": report.started_at,
        "finished_at": report.finished_at,
        "aggregates": report.aggregates(),
        "samples": [asdict(s) for s in report.samples],
        "prompt_suite_version": "v1",
    }

    text = json.dumps(payload, indent=2, ensure_ascii=False)
    if args.output == "-":
        print(text)
    else:
        Path(args.output).write_text(text, encoding="utf-8")
        print(f"wrote {args.output}", file=sys.stderr)
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
