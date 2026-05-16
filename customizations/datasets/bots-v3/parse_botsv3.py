#!/usr/bin/env python3
"""Parse Splunk BOTS v3 pre-indexed buckets into Quarry JSONL.

BOTS v3 ships as Splunk rawdata journals, not plain JSON. This parser extracts
printable event records from rawdata/journal.gz using the same strategy as the
Unix `strings` tool, then normalizes JSON records and AWS VPC Flow text rows.
"""
from __future__ import annotations

import argparse
import gzip
import hashlib
import json
import re
import shlex
import subprocess
import time
from collections import Counter, defaultdict
from datetime import datetime, timezone
from email.utils import parsedate_to_datetime
from pathlib import Path
from typing import Any, Iterable

SOURCE_REPO = "https://github.com/splunk/botsv3"
DATASET_URL = "https://botsdataset.s3.amazonaws.com/botsv3/botsv3_data_set.tgz"
EXPECTED_MD5 = "d7ccca99a01cff070dff3c139cdc10eb"
DEFAULT_DATASET_ROOT = Path("datasets/bots-v3")
DEFAULT_EXTRACTED_ROOT = DEFAULT_DATASET_ROOT / "extracted" / "botsv3_data_set"
DEFAULT_OUTPUT = DEFAULT_DATASET_ROOT / "normalized" / "botsv3_events.jsonl.gz"
DEFAULT_MANIFEST = DEFAULT_DATASET_ROOT / "manifest" / "manifest.json"

EVENT_KEYS = {
    "timestamp", "endtime", "time", "unixTime", "eventVersion", "MessageTraceId",
    "eventUid", "DateReceived", "eventTime", "Records", "eventName", "src_ip",
    "dest_ip", "EventCode", "name", "ruleName", "formattedTimestamp", "calendarTime",
    "CreationTime", "Received", "StartTime", "EndTime", "UserId", "Operation",
}
META_RE = re.compile(r"(?:^|[^A-Za-z])(host|source|sourcetype)::([^\r\n]+)$", re.IGNORECASE)
URL_RE = re.compile(r"https?://[^\s\"'<>]+", re.IGNORECASE)
VPC_RE = re.compile(
    r"^\d?\s*(?P<account_id>\d{12})\s+(?P<interface_id>eni-[0-9a-f]+)\s+"
    r"(?P<src_ip>\S+)\s+(?P<dest_ip>\S+)\s+(?P<src_port>\d+)\s+(?P<dest_port>\d+)\s+"
    r"(?P<protocol>\d+)\s+(?P<packets>\d+)\s+(?P<bytes>\d+)\s+"
    r"(?P<start>\d+)\s+(?P<end>\d+)\s+(?P<action>\S+)\s+(?P<log_status>\S+)"
)

BIG_KEYS = {
    "content", "content_body", "raw", "body", "html", "payload", "message", "data",
    "image", "attachments", "Records",
}
IMPORTANT_KEYS = {
    "timestamp", "endtime", "unixTime", "calendarTime", "DateReceived", "eventTime",
    "eventName", "eventSource", "eventType", "EventCode", "ComputerName", "host",
    "hostIdentifier", "name", "action", "ruleName", "formattedTimestamp", "Subject",
    "subject", "sender", "sender_email", "SenderAddress", "receiver", "receiver_email",
    "RecipientAddress", "src_ip", "dest_ip", "src_port", "dest_port", "sourceIPAddress",
    "userIdentity", "userName", "UserId", "Operation", "ObjectId", "MessageTraceId",
    "eventUid", "files", "fileName", "fullPath", "md5", "sha1", "sha256", "columns",
    "decorations", "requestParameters", "responseElements", "errorCode", "errorMessage",
}


def md5_file(path: Path) -> str:
    h = hashlib.md5()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def strip_splunk_prefix(value: str | None, prefix: str) -> str | None:
    if not value:
        return None
    value = str(value).strip().strip("\x00")
    marker = f"{prefix}::"
    idx = value.lower().find(marker)
    if idx >= 0:
        value = value[idx + len(marker) :]
    return value.strip() or None


def iter_strings_lines(journal: Path) -> Iterable[str]:
    cmd = f"gzip -cd {shlex.quote(str(journal))} | strings -n 8"
    proc = subprocess.Popen(
        ["bash", "-lc", cmd],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        errors="replace",
        bufsize=1024 * 1024,
    )
    assert proc.stdout is not None
    for line in proc.stdout:
        yield line.rstrip("\r\n")
    _, stderr = proc.communicate()
    if proc.returncode != 0:
        raise RuntimeError(f"failed to extract strings from {journal}: {stderr[:500]}")


def update_context_from_line(line: str, ctx: dict[str, str | None]) -> None:
    if "{" in line or len(line) > 500:
        return
    match = META_RE.search(line.strip())
    if not match:
        return
    key, value = match.group(1).lower(), match.group(2).strip()
    if key == "host":
        ctx["host"] = strip_splunk_prefix(value, "host")
    elif key == "source":
        ctx["source"] = strip_splunk_prefix(value, "source")
    elif key == "sourcetype":
        ctx["sourcetype"] = strip_splunk_prefix(value, "sourcetype")


def json_event_from_line(line: str) -> dict[str, Any] | None:
    idx = line.find("{")
    if idx < 0:
        return None
    prefix = line[:idx].strip()
    if prefix and not prefix.isdigit():
        return None
    try:
        obj, _ = json.JSONDecoder().raw_decode(line[idx:])
    except json.JSONDecodeError:
        return None
    if not isinstance(obj, dict):
        return None
    if set(obj.keys()) <= {""}:
        return None
    if EVENT_KEYS.intersection(obj.keys()):
        return obj
    return None


def parse_vpc_flow(line: str) -> dict[str, Any] | None:
    match = VPC_RE.match(line)
    if not match:
        return None
    data: dict[str, Any] = match.groupdict()
    for key in ["src_port", "dest_port", "protocol", "packets", "bytes", "start", "end"]:
        data[key] = int(data[key])
    data["event_type"] = "aws_vpc_flow"
    return data


def parse_time(value: Any) -> tuple[str | None, float | None]:
    if value is None or value == "":
        return None, None
    if isinstance(value, (int, float)):
        seconds = float(value) / 1000.0 if float(value) > 10_000_000_000 else float(value)
        return datetime.fromtimestamp(seconds, tz=timezone.utc).isoformat(), seconds
    text = str(value).strip()
    ms = re.search(r"/Date\((\d+)\)/", text)
    if ms:
        return parse_time(int(ms.group(1)))
    if text.isdigit():
        return parse_time(int(text))
    iso = text.replace("Z", "+00:00")
    try:
        dt = datetime.fromisoformat(iso)
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        return dt.astimezone(timezone.utc).isoformat(), dt.timestamp()
    except ValueError:
        pass
    for fmt in ["%a %b %d %H:%M:%S %Y %Z", "%Y-%m-%d %H:%M:%S", "%m/%d/%Y %H:%M:%S"]:
        try:
            dt = datetime.strptime(text, fmt).replace(tzinfo=timezone.utc)
            return dt.isoformat(), dt.timestamp()
        except ValueError:
            pass
    try:
        dt = parsedate_to_datetime(text)
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        return dt.astimezone(timezone.utc).isoformat(), dt.timestamp()
    except Exception:
        return None, None


def first_present(data: dict[str, Any], *keys: str) -> Any:
    for key in keys:
        cur: Any = data
        ok = True
        for part in key.split("."):
            if isinstance(cur, dict) and part in cur:
                cur = cur[part]
            else:
                ok = False
                break
        if ok and cur not in (None, "", []):
            return cur
    return None


def iter_text_values(value: Any, depth: int = 0) -> Iterable[str]:
    if depth > 3:
        return
    if isinstance(value, str):
        yield value[:4000]
    elif isinstance(value, (int, float, bool)):
        yield str(value)
    elif isinstance(value, dict):
        for key, item in list(value.items())[:80]:
            if str(key) in BIG_KEYS and isinstance(item, (list, dict, str)):
                yield str(item)[:4000]
            else:
                yield from iter_text_values(item, depth + 1)
    elif isinstance(value, list):
        for item in value[:30]:
            yield from iter_text_values(item, depth + 1)


def compact_value(value: Any, key: str = "", depth: int = 0) -> Any:
    if depth > 4:
        return "<truncated-depth>"
    if isinstance(value, str):
        limit = 600 if key in BIG_KEYS else 1200
        return value if len(value) <= limit else value[:limit] + f"...<truncated {len(value) - limit} chars>"
    if isinstance(value, (int, float, bool)) or value is None:
        return value
    if isinstance(value, list):
        limit = 8 if key in BIG_KEYS else 20
        out = [compact_value(item, key=key, depth=depth + 1) for item in value[:limit]]
        if len(value) > limit:
            out.append(f"<truncated {len(value) - limit} items>")
        return out
    if isinstance(value, dict):
        items = value.items()
        if depth == 0:
            items = [(k, v) for k, v in value.items() if k in IMPORTANT_KEYS or k not in BIG_KEYS]
        out: dict[str, Any] = {}
        for idx, (k, v) in enumerate(items):
            if idx >= 90:
                out["_truncated_keys"] = len(value) - idx
                break
            out[str(k)] = compact_value(v, key=str(k), depth=depth + 1)
        return out
    return str(value)[:500]


def collect_hashes(data: Any) -> list[str]:
    text = " ".join(iter_text_values(data))
    hashes = set(re.findall(r"\b[0-9a-fA-F]{32}\b|\b[0-9a-fA-F]{40}\b|\b[0-9a-fA-F]{64}\b", text))
    return sorted(hashes)[:20]


def classify_event(data: dict[str, Any], sourcetype: str | None, message: str) -> tuple[str | None, str | None, list[str], list[str]]:
    lower = message.lower()
    tags: list[str] = []
    mitre: set[str] = set()
    stage: str | None = None
    campaign: str | None = None

    if "all your datas belong to us" in lower or "sdbukwse" in lower or "pastebin.com/sdbukwse" in lower:
        stage = "extortion_notice"
        campaign = "wayne_ransomware_exfiltration"
        tags.extend(["extortion", "ransomware-note", "data-leak"])
        mitre.update(["T1657", "T1041"])
    if "frothly-servers.pem" in lower or "awspe..." in lower or "awspeMKeyMatch".lower() in lower or "com.code42.rules.awspemkeymatch" in lower:
        stage = stage or "cloud_key_exposure"
        campaign = campaign or "wayne_ransomware_exfiltration"
        tags.extend(["cloud-key-exposure", "exfiltration-risk"])
        mitre.update(["T1552", "T1041"])
    if "pastebin.com" in lower and ("brought your data" in lower or "imported it" in lower):
        stage = stage or "public_exfiltration"
        campaign = campaign or "wayne_ransomware_exfiltration"
        tags.extend(["pastebin", "exfiltration"])
        mitre.add("T1041")
    if "osk.exe" in lower and "stickykeys" in lower:
        stage = stage or "persistence"
        campaign = campaign or "wayne_ransomware_exfiltration"
        tags.extend(["sticky-keys", "persistence"])
        mitre.add("T1546.008")
    if "ransom" in lower or "encrypted" in lower or "decrypt" in lower:
        stage = stage or "ransomware_activity"
        campaign = campaign or "wayne_ransomware_exfiltration"
        tags.append("ransomware")
        mitre.add("T1486")
    if sourcetype == "aws:cloudwatchlogs:vpcflow" and any(ip in lower for ip in ["172.16.0.178", "172.16.3.197"]):
        tags.append("vpc-east-west-traffic")
    return stage, campaign, sorted(set(mitre)), sorted(set(tags))


def normalize_event(raw: dict[str, Any], ctx: dict[str, str | None], bucket: str, ordinal: int, line: str) -> dict[str, Any]:
    sourcetype = strip_splunk_prefix(ctx.get("sourcetype"), "sourcetype")
    source = strip_splunk_prefix(ctx.get("source"), "source")
    host = (
        first_present(raw, "hostIdentifier", "host", "ComputerName", "computer_name", "columns.computer_name")
        or strip_splunk_prefix(ctx.get("host"), "host")
    )
    timestamp = first_present(
        raw,
        "timestamp", "endtime", "unixTime", "DateReceived", "eventTime", "CreationTime",
        "calendarTime", "Received", "start",
    )
    iso_time, epoch = parse_time(timestamp)
    if iso_time is None and "start" in raw:
        iso_time, epoch = parse_time(raw.get("start"))
    message = str(
        first_present(
            raw,
            "message", "Message", "Subject", "subject", "eventName", "eventType", "name", "ruleName",
            "Operation", "EventCode", "action",
        )
        or ""
    )
    text = " ".join(iter_text_values(raw))
    urls = sorted(set(URL_RE.findall(text)))[:15]
    src_ip = first_present(raw, "src_ip", "sourceIPAddress", "FromIP", "client_ip")
    dest_ip = first_present(raw, "dest_ip", "ToIP", "destinationIPAddress")
    user = first_present(
        raw,
        "user", "userName", "UserId", "SenderAddress", "sender_email", "RecipientAddress",
        "decorations.username", "columns.user", "userIdentity.userName", "userIdentity.arn",
    )
    file_path = first_present(raw, "files.0.fullPath", "columns.path", "TargetFilename", "ObjectId")
    file_name = first_present(raw, "files.0.fileName", "columns.name", "attach_filename.0", "name")
    full_message = f"{message} {text[:8000]}"
    stage, campaign, mitre, tags = classify_event(raw, sourcetype, full_message)
    event_id_seed = f"{bucket}:{ordinal}:{epoch}:{message}:{src_ip}:{dest_ip}:{user}"
    return {
        "dataset": "bots-v3",
        "demo_persona": "Wayne Enterprises",
        "source_dataset_persona": "BOTS v3 / Frothly",
        "source_format": "splunk_preindexed_journal",
        "source_repo": SOURCE_REPO,
        "bucket": bucket,
        "event_id": hashlib.sha256(event_id_seed.encode("utf-8", "replace")).hexdigest()[:24],
        "_time": iso_time,
        "time_unix": epoch,
        "host": str(host) if host else None,
        "source": source,
        "sourcetype": sourcetype,
        "message": message[:500],
        "src_ip": str(src_ip) if src_ip is not None else None,
        "dest_ip": str(dest_ip) if dest_ip is not None else None,
        "src_port": raw.get("src_port"),
        "dest_port": raw.get("dest_port"),
        "user": str(user)[:500] if user is not None else None,
        "file_path": str(file_path)[:1000] if file_path is not None else None,
        "file_name": str(file_name)[:500] if file_name is not None else None,
        "urls": urls,
        "hashes": collect_hashes(raw),
        "attack_stage": stage,
        "attack_campaign": campaign,
        "mitre_techniques": mitre,
        "tags": tags,
        "event": compact_value(raw),
    }


def parse_buckets(extracted_root: Path, output: Path, *, limit: int | None = None, include_disabled: bool = False) -> dict[str, Any]:
    db_root = extracted_root / "var" / "lib" / "splunk" / "botsv3" / "db"
    journals = sorted(db_root.glob("*/rawdata/journal.gz"))
    if not include_disabled:
        journals = [j for j in journals if not j.parent.parent.name.startswith("DISABLED-")]
    output.parent.mkdir(parents=True, exist_ok=True)
    stats: dict[str, Any] = {
        "started_at": datetime.now(timezone.utc).isoformat(),
        "output": str(output),
        "events_total": 0,
        "json_events": 0,
        "vpc_flow_events": 0,
        "buckets": {},
        "sourcetypes": Counter(),
        "attack_campaigns": Counter(),
        "attack_stages": Counter(),
        "mitre_techniques": Counter(),
    }
    started = time.time()
    with gzip.open(output, "wt", encoding="utf-8", compresslevel=6) as out:
        for journal in journals:
            bucket = journal.parent.parent.name
            ctx: dict[str, str | None] = {"host": None, "source": None, "sourcetype": None}
            bucket_stats = {"strings_lines": 0, "json_events": 0, "vpc_flow_events": 0, "events": 0}
            ordinal = 0
            for line in iter_strings_lines(journal):
                bucket_stats["strings_lines"] += 1
                update_context_from_line(line, ctx)
                raw = json_event_from_line(line)
                event_kind = "json"
                if raw is None:
                    raw = parse_vpc_flow(line)
                    event_kind = "vpc_flow" if raw else ""
                if raw is None:
                    continue
                ordinal += 1
                normalized = normalize_event(raw, ctx, bucket, ordinal, line)
                normalized["parser_event_kind"] = event_kind
                out.write(json.dumps(normalized, ensure_ascii=False, sort_keys=True) + "\n")
                bucket_stats["events"] += 1
                if event_kind == "json":
                    bucket_stats["json_events"] += 1
                    stats["json_events"] += 1
                elif event_kind == "vpc_flow":
                    bucket_stats["vpc_flow_events"] += 1
                    stats["vpc_flow_events"] += 1
                stats["events_total"] += 1
                stats["sourcetypes"][normalized.get("sourcetype") or "unknown"] += 1
                if normalized.get("attack_campaign"):
                    stats["attack_campaigns"][normalized["attack_campaign"]] += 1
                if normalized.get("attack_stage"):
                    stats["attack_stages"][normalized["attack_stage"]] += 1
                for technique in normalized.get("mitre_techniques") or []:
                    stats["mitre_techniques"][technique] += 1
                if limit and stats["events_total"] >= limit:
                    break
            stats["buckets"][bucket] = bucket_stats
            if limit and stats["events_total"] >= limit:
                break
    stats["completed_at"] = datetime.now(timezone.utc).isoformat()
    stats["duration_seconds"] = round(time.time() - started, 3)
    stats["sourcetypes"] = dict(stats["sourcetypes"].most_common())
    stats["attack_campaigns"] = dict(stats["attack_campaigns"].most_common())
    stats["attack_stages"] = dict(stats["attack_stages"].most_common())
    stats["mitre_techniques"] = dict(stats["mitre_techniques"].most_common())
    return stats


def write_manifest(manifest_path: Path, archive: Path, extracted_root: Path, output: Path, stats: dict[str, Any]) -> dict[str, Any]:
    manifest_path.parent.mkdir(parents=True, exist_ok=True)
    archive_md5 = md5_file(archive) if archive.exists() else None
    payload = {
        "dataset": "bots-v3",
        "demo_persona": "Wayne Enterprises",
        "source_dataset_persona": "BOTS v3 / Frothly",
        "source_repo": SOURCE_REPO,
        "dataset_url": DATASET_URL,
        "license": "CC0-1.0 per upstream repository",
        "expected_md5": EXPECTED_MD5,
        "archive_md5": archive_md5,
        "md5_ok": archive_md5 == EXPECTED_MD5,
        "extracted_root": str(extracted_root),
        "normalized_events": str(output),
        "parser": "customizations/datasets/bots-v3/parse_botsv3.py",
        "stats": stats,
    }
    manifest_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True), encoding="utf-8")
    return payload


def main() -> int:
    parser = argparse.ArgumentParser(description="Parse Splunk BOTS v3 journals into normalized Quarry JSONL")
    parser.add_argument("--dataset-root", type=Path, default=DEFAULT_DATASET_ROOT)
    parser.add_argument("--extracted-root", type=Path, default=DEFAULT_EXTRACTED_ROOT)
    parser.add_argument("--archive", type=Path, default=DEFAULT_DATASET_ROOT / "archives" / "botsv3_data_set.tgz")
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--manifest", type=Path, default=DEFAULT_MANIFEST)
    parser.add_argument("--limit", type=int, default=0, help="Optional event limit for quick parser tests")
    parser.add_argument("--include-disabled", action="store_true")
    args = parser.parse_args()
    if not args.extracted_root.exists():
        raise SystemExit(f"extracted root not found: {args.extracted_root}")
    if args.archive.exists():
        actual = md5_file(args.archive)
        if actual != EXPECTED_MD5:
            raise SystemExit(f"archive MD5 mismatch: {actual} != {EXPECTED_MD5}")
    stats = parse_buckets(args.extracted_root, args.output, limit=args.limit or None, include_disabled=args.include_disabled)
    manifest = write_manifest(args.manifest, args.archive, args.extracted_root, args.output, stats)
    print(json.dumps({"status": "ok", "events_total": stats["events_total"], "md5_ok": manifest["md5_ok"], "duration_seconds": stats["duration_seconds"]}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
