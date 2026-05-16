#!/usr/bin/env python3
"""Validate the normalized BOTS v3 dataset and build demo artifacts."""

from __future__ import annotations

import argparse
import gzip
import hashlib
import json
import sys
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any, Iterable

EXPECTED_MD5 = "d7ccca99a01cff070dff3c139cdc10eb"
EXPECTED_STAGES = {"persistence", "cloud_key_exposure", "extortion_notice"}
EXPECTED_TECHNIQUES = {"T1041", "T1546.008", "T1552", "T1657"}
CAMPAIGN = "wayne_ransomware_exfiltration"
DEFAULT_MANIFEST = Path("datasets/bots-v3/manifest/manifest.json")
DEFAULT_HUNT_DIR = Path("customizations/hunts/bots-v3")
DEFAULT_OUTPUT_DIR = Path("datasets/bots-v3/normalized")


def md5_file(path: Path) -> str:
    digest = hashlib.md5()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def read_jsonl_gz(path: Path) -> Iterable[dict[str, Any]]:
    with gzip.open(path, "rt", encoding="utf-8") as fh:
        for line_no, line in enumerate(fh, 1):
            if not line.strip():
                continue
            try:
                yield json.loads(line)
            except json.JSONDecodeError as exc:
                raise SystemExit(f"invalid JSON in {path}:{line_no}: {exc}") from exc


def add_node(nodes: dict[str, dict[str, Any]], node_id: str | None, label: str | None, node_type: str) -> str | None:
    if not node_id:
        return None
    node_id = str(node_id)[:300]
    if node_id not in nodes:
        nodes[node_id] = {"id": node_id, "label": (label or node_id)[:300], "type": node_type}
    return node_id


def append_limited(values: set[str], incoming: Any, *, limit: int = 12) -> None:
    if incoming is None or len(values) >= limit:
        return
    if isinstance(incoming, list):
        for item in incoming:
            append_limited(values, item, limit=limit)
        return
    text = str(incoming)
    if text:
        values.add(text[:300])


def build_timeline(events: list[dict[str, Any]]) -> list[dict[str, Any]]:
    grouped: dict[str, dict[str, Any]] = {}
    for event in events:
        stage = event.get("attack_stage") or "unknown"
        row = grouped.setdefault(
            stage,
            {
                "stage": stage,
                "count": 0,
                "first_seen": None,
                "last_seen": None,
                "hosts": set(),
                "users": set(),
                "sources": set(),
                "mitre_techniques": set(),
                "example_event_ids": [],
                "example_messages": [],
            },
        )
        row["count"] += 1
        event_time = event.get("_time")
        if event_time:
            row["first_seen"] = event_time if row["first_seen"] is None else min(row["first_seen"], event_time)
            row["last_seen"] = event_time if row["last_seen"] is None else max(row["last_seen"], event_time)
        append_limited(row["hosts"], event.get("host"))
        append_limited(row["users"], event.get("user"))
        append_limited(row["sources"], event.get("sourcetype"))
        append_limited(row["mitre_techniques"], event.get("mitre_techniques"))
        if len(row["example_event_ids"]) < 5:
            row["example_event_ids"].append(event.get("event_id"))
        message = event.get("message")
        if message and len(row["example_messages"]) < 5:
            row["example_messages"].append(message)

    order = ["persistence", "cloud_key_exposure", "public_exfiltration", "extortion_notice", "ransomware_activity", "unknown"]
    ordered = sorted(grouped.values(), key=lambda item: (order.index(item["stage"]) if item["stage"] in order else 99, item["first_seen"] or ""))
    for row in ordered:
        for key in ["hosts", "users", "sources", "mitre_techniques"]:
            row[key] = sorted(row[key])
    return ordered


def build_attack_graph(events: list[dict[str, Any]]) -> dict[str, Any]:
    nodes: dict[str, dict[str, Any]] = {}
    edges: list[dict[str, Any]] = []
    campaign_id = add_node(nodes, CAMPAIGN, "Wayne ransomware + exfiltration", "campaign")
    for event in events:
        event_id = add_node(nodes, f"event:{event.get('event_id')}", event.get("message") or event.get("event_id"), "event")
        if campaign_id and event_id:
            edges.append({"source": campaign_id, "target": event_id, "relationship": "contains", "stage": event.get("attack_stage")})
        for field, prefix, relation, node_type in [
            ("host", "host", "observed_on", "host"),
            ("user", "user", "involves_user", "identity"),
            ("src_ip", "ip", "source_ip", "ip"),
            ("dest_ip", "ip", "destination_ip", "ip"),
            ("file_path", "file", "touches_file", "file"),
        ]:
            value = event.get(field)
            node = add_node(nodes, f"{prefix}:{value}", str(value) if value else None, node_type) if value else None
            if event_id and node:
                edges.append({"source": event_id, "target": node, "relationship": relation, "stage": event.get("attack_stage")})
        for url in event.get("urls") or []:
            node = add_node(nodes, f"url:{url}", url, "url")
            if event_id and node:
                edges.append({"source": event_id, "target": node, "relationship": "references_url", "stage": event.get("attack_stage")})
        for technique in event.get("mitre_techniques") or []:
            node = add_node(nodes, f"mitre:{technique}", technique, "mitre_technique")
            if event_id and node:
                edges.append({"source": event_id, "target": node, "relationship": "maps_to", "stage": event.get("attack_stage")})
    return {"nodes": list(nodes.values()), "edges": edges[:5000]}


def build_mitre_heatmap(events: list[dict[str, Any]]) -> dict[str, Any]:
    counts = Counter()
    by_stage: dict[str, Counter] = defaultdict(Counter)
    for event in events:
        stage = event.get("attack_stage") or "unknown"
        for technique in event.get("mitre_techniques") or []:
            counts[technique] += 1
            by_stage[stage][technique] += 1
    return {
        "dataset": "bots-v3",
        "campaign": CAMPAIGN,
        "coverage": dict(counts.most_common()),
        "by_stage": {stage: dict(counter.most_common()) for stage, counter in sorted(by_stage.items())},
    }


def build_federated_search_sample(events: list[dict[str, Any]]) -> dict[str, Any]:
    hits = []
    for event in events[:25]:
        hits.append(
            {
                "id": event.get("event_id"),
                "timestamp": event.get("_time"),
                "source": event.get("sourcetype"),
                "host": event.get("host"),
                "user": event.get("user"),
                "stage": event.get("attack_stage"),
                "summary": event.get("message"),
            }
        )
    return {
        "query": 'dataset:"bots-v3" attack_campaign:"wayne_ransomware_exfiltration"',
        "mode": "local_normalized_corpus_stand_in_for_federated_search",
        "total": len(events),
        "hits": hits,
    }


def write_ledger(path: Path, timeline: list[dict[str, Any]], hunt_summary: dict[str, Any]) -> None:
    rows = [
        {
            "step": 1,
            "title": "Escopo do caso",
            "reasoning": "Filtrar eventos BOTS v3 marcados como campanha Wayne ransomware + exfiltration.",
            "evidence": {"campaign": CAMPAIGN, "hunt": hunt_summary},
        },
        {
            "step": 2,
            "title": "Reconstrução da timeline",
            "reasoning": "Agrupar eventos por estágio de ataque para mostrar persistência, exposição de chave, exfiltração/extorsão e ransomware.",
            "evidence": {"timeline_stages": [row["stage"] for row in timeline]},
        },
        {
            "step": 3,
            "title": "Cobertura MITRE",
            "reasoning": "Mapear as evidências para técnicas ATT&CK usadas no brief Wayne Enterprises.",
            "evidence": {"expected_techniques": sorted(EXPECTED_TECHNIQUES)},
        },
    ]
    with path.open("w", encoding="utf-8") as fh:
        for row in rows:
            fh.write(json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n")


def run_hunt(hunt_dir: Path, events: list[dict[str, Any]]) -> dict[str, Any]:
    sys.path.insert(0, str(Path("services/agents")))
    try:
        from app.hunt.engine import HuntEngine
        from app.hunt.loader import HuntCorpus
    except Exception as exc:  # pragma: no cover - only used when env is incomplete
        return {"status": "skipped", "reason": f"could not import hunt engine: {exc}"}

    corpus = HuntCorpus(hunt_dir)
    loaded = corpus.reload()
    hunt = corpus.get("HUNT-BOTS-WAYNE-001")
    if hunt is None:
        return {"status": "failed", "loaded": loaded, "reason": "HUNT-BOTS-WAYNE-001 not loaded"}
    result = HuntEngine(max_findings_per_run=20).run(hunt, events)
    return {
        "status": "ok" if result.findings else "failed",
        "loaded": loaded,
        "events_scanned": result.events_scanned,
        "findings": len(result.findings),
        "match_score": result.match_score,
        "hunt_id": result.hunt_id,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate BOTS v3 normalized corpus and Wayne demo artifacts")
    parser.add_argument("--manifest", type=Path, default=DEFAULT_MANIFEST)
    parser.add_argument("--hunt-dir", type=Path, default=DEFAULT_HUNT_DIR)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    args = parser.parse_args()

    errors: list[str] = []
    if not args.manifest.exists():
        raise SystemExit(f"manifest not found: {args.manifest}")
    manifest = json.loads(args.manifest.read_text(encoding="utf-8"))

    archive = Path("datasets/bots-v3/archives/botsv3_data_set.tgz")
    if archive.exists():
        archive_md5 = md5_file(archive)
        if archive_md5 != EXPECTED_MD5:
            errors.append(f"archive MD5 mismatch: {archive_md5} != {EXPECTED_MD5}")
    elif not manifest.get("md5_ok"):
        errors.append("archive is missing and manifest md5_ok is false")

    normalized_path = Path(manifest.get("normalized_events", ""))
    if not normalized_path.exists():
        raise SystemExit(f"normalized event file not found: {normalized_path}")

    total = 0
    campaign_events: list[dict[str, Any]] = []
    stages = Counter()
    techniques = Counter()
    for event in read_jsonl_gz(normalized_path):
        total += 1
        if event.get("attack_campaign") != CAMPAIGN:
            continue
        campaign_events.append(event)
        if event.get("attack_stage"):
            stages[event["attack_stage"]] += 1
        for technique in event.get("mitre_techniques") or []:
            techniques[technique] += 1

    manifest_total = int(manifest.get("stats", {}).get("events_total", 0))
    if total != manifest_total:
        errors.append(f"event count mismatch: manifest={manifest_total} actual={total}")
    if not campaign_events:
        errors.append(f"campaign {CAMPAIGN} returned no events")
    missing_stages = EXPECTED_STAGES - set(stages)
    if missing_stages:
        errors.append(f"missing expected stages: {sorted(missing_stages)}")
    missing_techniques = EXPECTED_TECHNIQUES - set(techniques)
    if missing_techniques:
        errors.append(f"missing expected MITRE techniques: {sorted(missing_techniques)}")

    campaign_events.sort(key=lambda item: (item.get("time_unix") is None, item.get("time_unix") or 0, item.get("event_id") or ""))
    timeline = build_timeline(campaign_events)
    attack_graph = build_attack_graph(campaign_events)
    mitre_heatmap = build_mitre_heatmap(campaign_events)
    federated_sample = build_federated_search_sample(campaign_events)
    hunt_summary = run_hunt(args.hunt_dir, campaign_events)
    if hunt_summary.get("status") != "ok":
        errors.append(f"hunt validation failed: {hunt_summary}")

    args.output_dir.mkdir(parents=True, exist_ok=True)
    (args.output_dir / "wayne_ransomware_timeline.json").write_text(json.dumps(timeline, ensure_ascii=False, indent=2), encoding="utf-8")
    (args.output_dir / "attack_graph.json").write_text(json.dumps(attack_graph, ensure_ascii=False, indent=2), encoding="utf-8")
    (args.output_dir / "mitre_heatmap.json").write_text(json.dumps(mitre_heatmap, ensure_ascii=False, indent=2), encoding="utf-8")
    (args.output_dir / "federated_search_sample.json").write_text(json.dumps(federated_sample, ensure_ascii=False, indent=2), encoding="utf-8")
    write_ledger(args.output_dir / "investigation_ledger_sample.jsonl", timeline, hunt_summary)

    result = {
        "status": "ok" if not errors else "failed",
        "events_total": total,
        "campaign_events": len(campaign_events),
        "stages": dict(stages.most_common()),
        "mitre_techniques": dict(techniques.most_common()),
        "timeline_stages": [row["stage"] for row in timeline],
        "hunt": hunt_summary,
        "artifacts": {
            "timeline": str(args.output_dir / "wayne_ransomware_timeline.json"),
            "attack_graph": str(args.output_dir / "attack_graph.json"),
            "mitre_heatmap": str(args.output_dir / "mitre_heatmap.json"),
            "federated_search_sample": str(args.output_dir / "federated_search_sample.json"),
            "investigation_ledger": str(args.output_dir / "investigation_ledger_sample.jsonl"),
        },
        "errors": errors,
    }
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0 if not errors else 1


if __name__ == "__main__":
    raise SystemExit(main())
