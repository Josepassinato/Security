#!/usr/bin/env python3
"""Roda o benchmark de auto-triage FP reduction contra alertas FinPlay.

Modos:
  --mode mock         (default) — só baseline estática, zero LLM call, zero custo
  --mode wet          — chama OpenRouter (modelo configurável) pra cada alerta
  --mode both         — roda os dois lado a lado pra comparar

Saída:
  runs/YYYY-MM-DD-<sha>/{alerts.jsonl, results.jsonl, report.md}

Métricas reportadas:
  - auto_close_rate         — % alertas auto-fechados pelo agente
  - false_close_rate        — % auto-fechados que eram TP (erro perigoso!)
  - precision_close         — 1 - false_close_rate
  - latency_p50_ms / p95_ms
  - cost_usd_total (modo wet)
"""
from __future__ import annotations

import argparse
import asyncio
import datetime as dt
import hashlib
import json
import os
import statistics
import sys
import time
from pathlib import Path
from typing import Any

from synthesize_alerts import synthesize, write_jsonl  # type: ignore[import]
from baseline_static import classify_static  # type: ignore[import]


OPENROUTER_API_URL = "https://openrouter.ai/api/v1/chat/completions"
DEFAULT_OPENROUTER_MODEL = "openai/gpt-4o-mini"

_SYSTEM_PROMPT = """\
You are the Auto-Triage Agent of an AI Security Operations Centre serving a
Brazilian fintech regulated by BACEN.

Given a security alert (summary + raw payload), classify it into exactly one
of three verdicts:
  - true_positive
  - false_positive
  - benign

Respond with a JSON object ONLY:
{"verdict": "...", "confidence": <0.0-1.0>, "rationale": "<2-3 sentences>"}

Guidelines:
- Severity high/critical + risk_score >= 0.7 with concrete IOCs/TTPs → likely TP.
- Authorized internal activity (pentest tickets, scheduled scans, signed publishers) → FP.
- Pure operational/info events with no IOCs → benign.
- When uncertain, prefer true_positive over auto-closing.
- Recurring well-known patterns with audit trail → likely FP.
- Confidence reflects certainty, not severity.
"""


def _load_openrouter_key() -> str | None:
    if key := os.getenv("OPENROUTER_API_KEY"):
        return key
    env_file = Path("/root/.api_keys/openrouter.env")
    if env_file.exists():
        for line in env_file.read_text().splitlines():
            line = line.strip()
            if line.startswith("OPENROUTER_API_KEY="):
                return line.split("=", 1)[1].strip().strip('"').strip("'")
    return None


def _build_alert_context(alert: dict[str, Any]) -> str:
    parts = [
        f"Alert Summary: {alert['summary']}",
        f"Rule: {alert['rule_id']}",
        f"Severity: {alert['severity']}",
        f"Risk Score: {alert['risk_score']:.2f}",
    ]
    if alert.get("mitre_techniques"):
        parts.append(f"MITRE Techniques: {', '.join(alert['mitre_techniques'])}")
    raw = alert.get("raw") or {}
    if raw:
        raw_clean = {k: v for k, v in raw.items() if not k.startswith("fraud_label_internal")}
        parts.append("Raw event fields:")
        for k, v in sorted(raw_clean.items()):
            parts.append(f"  {k}: {v}")
    return "\n".join(parts)


def _parse_llm_json(text: str) -> dict[str, Any]:
    cleaned = text.strip()
    if cleaned.startswith("```"):
        lines = [ln for ln in cleaned.split("\n") if not ln.strip().startswith("```")]
        cleaned = "\n".join(lines).strip()
    try:
        return json.loads(cleaned)
    except json.JSONDecodeError:
        start = cleaned.find("{")
        end = cleaned.rfind("}") + 1
        if start >= 0 and end > start:
            return json.loads(cleaned[start:end])
        raise


async def _call_openrouter(
    alert: dict[str, Any],
    api_key: str,
    model: str,
    client: Any,
) -> dict[str, Any]:
    t0 = time.monotonic()
    ctx = _build_alert_context(alert)
    payload = {
        "model": model,
        "temperature": 0.0,
        "max_tokens": 256,
        "messages": [
            {"role": "system", "content": _SYSTEM_PROMPT},
            {"role": "user", "content": ctx},
        ],
    }
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
        "HTTP-Referer": "https://quarry.12brain.org",
        "X-Title": "Quarry CARD-013 Auto-Triage FP Benchmark",
    }
    try:
        r = await client.post(OPENROUTER_API_URL, json=payload, headers=headers, timeout=30.0)
        r.raise_for_status()
        data = r.json()
    except Exception as exc:
        return {
            "verdict": "true_positive",
            "confidence": 0.0,
            "rationale": f"LLM error escalated: {exc}",
            "auto_closed": False,
            "latency_ms": (time.monotonic() - t0) * 1000,
            "cost_usd": 0.0,
            "error": str(exc),
        }
    choice = data["choices"][0]["message"]["content"]
    parsed = _parse_llm_json(choice)
    verdict = parsed.get("verdict", "true_positive")
    if verdict not in {"true_positive", "false_positive", "benign"}:
        verdict = "true_positive"
    confidence = float(parsed.get("confidence", 0.5))
    confidence = max(0.0, min(1.0, confidence))
    usage = data.get("usage", {}) or {}
    # Rough cost estimate gpt-4o-mini: $0.15/1M input + $0.60/1M output
    cost = (usage.get("prompt_tokens", 0) * 0.15 + usage.get("completion_tokens", 0) * 0.60) / 1_000_000
    return {
        "verdict": verdict,
        "confidence": confidence,
        "rationale": parsed.get("rationale", ""),
        "auto_closed": verdict in {"false_positive", "benign"} and confidence >= 0.85,
        "latency_ms": (time.monotonic() - t0) * 1000,
        "cost_usd": cost,
        "prompt_tokens": usage.get("prompt_tokens"),
        "completion_tokens": usage.get("completion_tokens"),
    }


def _summarize(results: list[dict[str, Any]], strategy_label: str) -> dict[str, Any]:
    total = len(results)
    if total == 0:
        return {}
    auto_closed = [r for r in results if r["classification"]["auto_closed"]]
    auto_close_rate = len(auto_closed) / total
    closed_but_tp = [r for r in auto_closed if r["alert"]["ground_truth"] == "true_positive"]
    false_close_rate = (len(closed_but_tp) / len(auto_closed)) if auto_closed else 0.0
    precision_close = 1.0 - false_close_rate
    correctly_escalated_tp = [
        r for r in results
        if r["alert"]["ground_truth"] == "true_positive" and not r["classification"]["auto_closed"]
    ]
    tp_total = sum(1 for r in results if r["alert"]["ground_truth"] == "true_positive")
    recall_tp = (len(correctly_escalated_tp) / tp_total) if tp_total else 0.0

    latencies = [r["classification"]["latency_ms"] for r in results]
    latencies.sort()
    p50 = latencies[len(latencies) // 2] if latencies else 0.0
    p95 = latencies[max(0, int(len(latencies) * 0.95) - 1)] if latencies else 0.0
    cost_total = sum(r["classification"].get("cost_usd", 0.0) for r in results)

    return {
        "strategy": strategy_label,
        "n_alerts": total,
        "auto_close_rate": round(auto_close_rate, 4),
        "false_close_rate": round(false_close_rate, 4),
        "precision_close": round(precision_close, 4),
        "recall_tp_escalation": round(recall_tp, 4),
        "latency_p50_ms": round(p50, 2),
        "latency_p95_ms": round(p95, 2),
        "cost_usd_total": round(cost_total, 6),
    }


async def _run_wet(alerts: list[dict[str, Any]], model: str, api_key: str) -> list[dict[str, Any]]:
    import httpx  # type: ignore[import]

    async with httpx.AsyncClient() as client:
        sem = asyncio.Semaphore(4)

        async def one(alert: dict[str, Any]) -> dict[str, Any]:
            async with sem:
                cls = await _call_openrouter(alert, api_key, model, client)
                return {"alert": alert, "classification": cls}

        return await asyncio.gather(*[one(a) for a in alerts])


def _run_mock(alerts: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return [{"alert": a, "classification": classify_static(a)} for a in alerts]


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--mode", choices=["mock", "wet", "both"], default="mock")
    parser.add_argument("--size", type=int, default=100)
    parser.add_argument("--seed", type=int, default=20260524)
    parser.add_argument("--model", default=DEFAULT_OPENROUTER_MODEL)
    parser.add_argument("--out", type=Path, default=None,
                        help="Optional run dir (default: runs/YYYY-MM-DD-<sha>/).")
    args = parser.parse_args()

    alerts_dc = synthesize(sample_size=args.size, seed=args.seed)
    alerts = [a.__dict__ for a in alerts_dc]

    now = dt.datetime.now()
    run_sha = hashlib.sha1(f"{args.mode}-{args.size}-{args.seed}-{now.isoformat()}".encode()).hexdigest()[:8]
    out_dir = args.out or Path(__file__).parent / "runs" / f"{now:%Y-%m-%d}-{run_sha}"
    out_dir.mkdir(parents=True, exist_ok=True)
    print(f"→ run dir: {out_dir}")

    write_jsonl(alerts_dc, out_dir / "alerts.jsonl")
    print(f"  alerts:  {len(alerts)} → alerts.jsonl")

    summaries: list[dict[str, Any]] = []

    if args.mode in {"mock", "both"}:
        print("→ running baseline (static rules)…")
        baseline = _run_mock(alerts)
        s = _summarize(baseline, "baseline_static")
        summaries.append(s)
        (out_dir / "results_baseline.jsonl").write_text(
            "\n".join(json.dumps(r, ensure_ascii=False) for r in baseline)
        )

    if args.mode in {"wet", "both"}:
        api_key = _load_openrouter_key()
        if not api_key:
            print("✗ OPENROUTER_API_KEY not found (.env or /root/.api_keys/openrouter.env)")
            return 2
        print(f"→ running LLM auto-triage via OpenRouter ({args.model})… {len(alerts)} calls")
        llm_results = asyncio.run(_run_wet(alerts, args.model, api_key))
        s = _summarize(llm_results, f"llm_auto_triage:{args.model}")
        summaries.append(s)
        (out_dir / "results_llm.jsonl").write_text(
            "\n".join(json.dumps(r, ensure_ascii=False) for r in llm_results)
        )

    (out_dir / "summary.json").write_text(
        json.dumps({"timestamp": now.isoformat(), "summaries": summaries}, indent=2, ensure_ascii=False)
    )

    print("\n" + "=" * 72)
    print("RESULTS")
    print("=" * 72)
    for s in summaries:
        print(f"\nstrategy: {s['strategy']}")
        for k, v in s.items():
            if k == "strategy":
                continue
            print(f"  {k:>26}: {v}")
    print()

    # Render markdown report
    try:
        from report import render_report  # type: ignore[import]
        report = render_report(summaries, alerts_dc, now, run_sha)
        (out_dir / "report.md").write_text(report)
        print(f"✓ report: {out_dir / 'report.md'}")
    except Exception as exc:
        print(f"! report rendering skipped: {exc}")

    return 0


if __name__ == "__main__":
    sys.exit(main())
