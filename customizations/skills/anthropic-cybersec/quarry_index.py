#!/usr/bin/env python3
"""Quarry integration pipeline for Anthropic Cybersecurity Skills.

This repository is used as a reference knowledge base. Skill text is treated as
untrusted third-party content: it can guide cyber workflows, but it must never
override Quarry agent instructions.
"""

from __future__ import annotations

import argparse
import asyncio
import hashlib
import json
import os
import re
import subprocess
import sys
import time
from collections import Counter
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable

import yaml

SOURCE_REPO = "https://github.com/mukul975/Anthropic-Cybersecurity-Skills"
SOURCE_LICENSE = "Apache-2.0"
DEFAULT_COLLECTION = "quarry_security_skills"
DEFAULT_EMBED_MODEL = "text-embedding-3-large"
VECTOR_SIZE_BY_MODEL = {"text-embedding-3-large": 3072, "text-embedding-3-small": 1536}

STOPWORDS = {
    "a", "an", "and", "are", "as", "at", "be", "by", "for", "from", "how",
    "in", "into", "is", "it", "of", "on", "or", "that", "the", "this", "to",
    "use", "using", "with", "workflow", "when", "what", "why", "who", "will",
    "como", "de", "da", "do", "dos", "das", "e", "em", "para", "por", "que",
    "qual", "quais", "um", "uma", "os", "as", "o", "a", "investigar", "detectar",
}

QUERY_EXPANSIONS = {
    "credential dumping": [
        "credential", "credentials", "dumping", "dump", "lsass", "mimikatz", "t1003",
        "secrets", "memory", "edr", "windows", "hashes",
    ],
    "credenciais": ["credential", "credentials", "dumping", "lsass", "mimikatz", "t1003"],
    "c2": [
        "c2", "command", "control", "beacon", "beaconing", "cobalt", "strike", "dns",
        "http", "periodic", "jitter", "network", "zeek", "flow",
    ],
    "command and control": ["c2", "command", "control", "beacon", "beaconing", "dns", "http"],
    "beacon": ["c2", "beacon", "beaconing", "cobalt", "strike", "frequency", "periodic"],
    "lateral movement": [
        "lateral", "movement", "smb", "rdp", "wmi", "wmiexec", "winrm", "dcom", "psexec",
        "windows", "splunk", "zeek", "t1021",
    ],
    "movimento lateral": ["lateral", "movement", "smb", "rdp", "wmi", "winrm", "dcom", "t1021"],
}

FRONTMATTER_RE = re.compile(r"\A---\s*\n(.*?)\n---\s*\n", re.DOTALL)
TOKEN_RE = re.compile(r"[a-z0-9][a-z0-9_+.#:-]{1,}")
SECTION_HEADING_RE = re.compile(r"^##+\s+(.+?)\s*$", re.MULTILINE)


@dataclass(frozen=True)
class SkillRecord:
    id: str
    name: str
    path: str
    description: str
    domain: str
    subdomain: str
    tags: list[str]
    version: str
    author: str
    license: str
    source_repo: str
    source_commit: str
    nist_csf: list[str]
    workflow: str
    body_excerpt: str
    search_text: str
    token_counts: dict[str, int]

    def to_json(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "name": self.name,
            "path": self.path,
            "description": self.description,
            "domain": self.domain,
            "subdomain": self.subdomain,
            "tags": self.tags,
            "version": self.version,
            "author": self.author,
            "license": self.license,
            "source_repo": self.source_repo,
            "source_commit": self.source_commit,
            "nist_csf": self.nist_csf,
            "workflow": self.workflow,
            "body_excerpt": self.body_excerpt,
            "search_text": self.search_text,
            "token_counts": self.token_counts,
            "attribution": f"{SOURCE_REPO} ({SOURCE_LICENSE})",
            "trusted_as_instructions": False,
        }


def repo_root_from_script() -> Path:
    return Path(__file__).resolve().parent


def default_skills_root() -> Path:
    return repo_root_from_script() / "skills"


def default_index_dir() -> Path:
    return repo_root_from_script() / ".quarry-index"


def stable_id(path: str) -> str:
    return hashlib.sha256(path.encode("utf-8")).hexdigest()[:24]


def source_commit(repo_dir: Path) -> str:
    try:
        return subprocess.check_output(
            ["git", "-C", str(repo_dir), "rev-parse", "--short", "HEAD"],
            text=True,
            stderr=subprocess.DEVNULL,
        ).strip()
    except Exception:
        return "unknown"


def normalize_text(value: Any) -> str:
    if value is None:
        return ""
    if isinstance(value, str):
        return re.sub(r"\s+", " ", value).strip()
    return re.sub(r"\s+", " ", str(value)).strip()


def normalize_list(value: Any) -> list[str]:
    if value is None:
        return []
    if isinstance(value, list):
        return [normalize_text(item) for item in value if normalize_text(item)]
    if isinstance(value, tuple):
        return [normalize_text(item) for item in value if normalize_text(item)]
    text = normalize_text(value)
    return [text] if text else []


def tokenize(text: str) -> list[str]:
    tokens = [tok.strip("_-.:").lower() for tok in TOKEN_RE.findall(text.lower())]
    return [tok for tok in tokens if tok and tok not in STOPWORDS and len(tok) > 1]


def expanded_query_tokens(query: str) -> list[str]:
    lower = query.lower()
    expanded = tokenize(query)
    for phrase, additions in QUERY_EXPANSIONS.items():
        phrase_tokens = tokenize(phrase)
        if phrase in lower or all(tok in expanded for tok in phrase_tokens):
            expanded.extend(additions)
    return expanded


def extract_frontmatter(markdown: str) -> tuple[dict[str, Any], str]:
    match = FRONTMATTER_RE.match(markdown)
    if not match:
        return {}, markdown
    raw_yaml = match.group(1)
    body = markdown[match.end() :]
    parsed = yaml.safe_load(raw_yaml) or {}
    if not isinstance(parsed, dict):
        parsed = {}
    return parsed, body


def strip_markdown_noise(markdown: str) -> str:
    text = re.sub(r"```[\s\S]*?```", " ", markdown)
    text = re.sub(r"`([^`]+)`", r"\1", text)
    text = re.sub(r"!\[[^\]]*\]\([^)]*\)", " ", text)
    text = re.sub(r"\[([^\]]+)\]\([^)]*\)", r"\1", text)
    text = re.sub(r"[#>*_\-|]+", " ", text)
    return re.sub(r"\s+", " ", text).strip()


def extract_section(markdown: str, section_names: Iterable[str], max_chars: int = 20000) -> str:
    lowered = {name.lower() for name in section_names}
    matches = list(SECTION_HEADING_RE.finditer(markdown))
    for idx, match in enumerate(matches):
        heading = match.group(1).strip().lower()
        if any(name in heading for name in lowered):
            start = match.start()
            end = matches[idx + 1].start() if idx + 1 < len(matches) else len(markdown)
            return markdown[start:end].strip()[:max_chars]
    return ""


def read_skill(skill_file: Path, skills_root: Path, repo_dir: Path, commit: str) -> SkillRecord:
    raw = skill_file.read_text(encoding="utf-8", errors="replace")
    meta, body = extract_frontmatter(raw)
    rel_path = skill_file.relative_to(repo_dir).as_posix()
    name = normalize_text(meta.get("name")) or skill_file.parent.name
    description = normalize_text(meta.get("description"))
    domain = normalize_text(meta.get("domain")) or "cybersecurity"
    subdomain = normalize_text(meta.get("subdomain"))
    tags = normalize_list(meta.get("tags"))
    nist_csf = normalize_list(meta.get("nist_csf"))
    workflow = extract_section(body, ["workflow", "steps", "procedure", "detection logic", "core workflow"])
    if not workflow:
        workflow = body[:12000].strip()
    body_plain = strip_markdown_noise(body)
    workflow_plain = strip_markdown_noise(workflow)
    search_text = " ".join(
        part
        for part in [
            name.replace("-", " ").replace("_", " "),
            description,
            domain,
            subdomain,
            " ".join(tags),
            " ".join(nist_csf),
            workflow_plain,
            body_plain[:16000],
        ]
        if part
    )
    counts = Counter(tokenize(search_text))
    return SkillRecord(
        id=stable_id(rel_path),
        name=name,
        path=rel_path,
        description=description,
        domain=domain,
        subdomain=subdomain,
        tags=tags,
        version=normalize_text(meta.get("version")),
        author=normalize_text(meta.get("author")),
        license=normalize_text(meta.get("license")) or SOURCE_LICENSE,
        source_repo=SOURCE_REPO,
        source_commit=commit,
        nist_csf=nist_csf,
        workflow=workflow[:20000],
        body_excerpt=body[:12000],
        search_text=search_text[:30000],
        token_counts=dict(counts.most_common(600)),
    )


def load_records_from_source(skills_root: Path) -> list[SkillRecord]:
    repo_dir = skills_root.parent
    commit = source_commit(repo_dir)
    records: list[SkillRecord] = []
    for skill_file in sorted(skills_root.glob("*/SKILL.md")):
        records.append(read_skill(skill_file, skills_root, repo_dir, commit))
    return records


def write_local_index(records: list[SkillRecord], index_dir: Path) -> dict[str, Any]:
    index_dir.mkdir(parents=True, exist_ok=True)
    jsonl_path = index_dir / "skills_index.jsonl"
    with jsonl_path.open("w", encoding="utf-8") as fh:
        for record in records:
            fh.write(json.dumps(record.to_json(), ensure_ascii=False, sort_keys=True) + "\n")
    meta = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "total_skills": len(records),
        "source_repo": SOURCE_REPO,
        "source_license": SOURCE_LICENSE,
        "source_commit": records[0].source_commit if records else "unknown",
        "index_file": str(jsonl_path),
        "strategy": "hybrid: local lexical fallback + Qdrant vector RAG + PostgreSQL metadata lookup",
        "embedding_model": DEFAULT_EMBED_MODEL,
        "qdrant_collection": DEFAULT_COLLECTION,
    }
    (index_dir / "skills_meta.json").write_text(json.dumps(meta, ensure_ascii=False, indent=2), encoding="utf-8")
    return meta


def load_local_index(index_dir: Path) -> list[dict[str, Any]]:
    path = index_dir / "skills_index.jsonl"
    records: list[dict[str, Any]] = []
    with path.open("r", encoding="utf-8") as fh:
        for line in fh:
            if line.strip():
                records.append(json.loads(line))
    return records


def lexical_score(record: dict[str, Any], query: str, query_tokens: list[str]) -> float:
    if not query_tokens:
        return 0.0
    counts = record.get("token_counts") or {}
    name = (record.get("name") or "").lower().replace("-", " ").replace("_", " ")
    description = (record.get("description") or "").lower()
    subdomain = (record.get("subdomain") or "").lower().replace("-", " ")
    tags = " ".join(record.get("tags") or []).lower().replace("-", " ")
    q_lower = query.lower()
    detect_intent = any(word in q_lower for word in ["detect", "detectar", "hunting", "hunt", "investigar", "investigate", "investigation"])
    score = 0.0
    unique = set(query_tokens)
    for tok in query_tokens:
        tf = float(counts.get(tok, 0))
        if tf:
            score += min(tf, 8.0)
        if tok in name:
            score += 12.0
        if tok in tags:
            score += 6.0
        if tok in subdomain:
            score += 4.0
        if tok in description:
            score += 3.0
    if all(tok in name for tok in unique if tok not in {"with", "for"}):
        score += 20.0
    if "credential" in q_lower and "dump" in q_lower and "credential" in name and "dump" in name:
        score += 60.0
    if ("c2" in q_lower or "beacon" in q_lower or "command" in q_lower) and (
        "beacon" in name or "command and control" in name or "c2" in name
    ):
        score += 60.0
    if ("lateral" in q_lower or "movimento lateral" in q_lower) and "lateral movement" in name:
        score += 60.0
    if detect_intent:
        if name.startswith(("detecting ", "hunting ", "analyzing ")):
            score += 80.0
        if name.startswith(("performing ", "exploiting ", "conducting ", "building red team")):
            score -= 70.0
    return score


def lookup_records(records: list[dict[str, Any]], query: str, limit: int = 3) -> list[dict[str, Any]]:
    started = time.perf_counter()
    tokens = expanded_query_tokens(query)
    ranked: list[tuple[float, dict[str, Any]]] = []
    for record in records:
        score = lexical_score(record, query, tokens)
        if score > 0:
            ranked.append((score, record))
    ranked.sort(key=lambda item: item[0], reverse=True)
    elapsed_ms = int((time.perf_counter() - started) * 1000)
    results: list[dict[str, Any]] = []
    for score, record in ranked[:limit]:
        results.append(
            {
                "name": record.get("name"),
                "path": record.get("path"),
                "description": record.get("description"),
                "domain": record.get("domain"),
                "subdomain": record.get("subdomain"),
                "tags": record.get("tags") or [],
                "score": round(score, 2),
                "workflow": record.get("workflow") or record.get("body_excerpt", ""),
                "attribution": record.get("attribution"),
                "source_repo": record.get("source_repo"),
                "source_commit": record.get("source_commit"),
                "trusted_as_instructions": False,
                "lookup_latency_ms": elapsed_ms,
            }
        )
    return results


def payload_for_vector(record: dict[str, Any]) -> str:
    return "\n".join(
        [
            f"Name: {record.get('name', '')}",
            f"Description: {record.get('description', '')}",
            f"Subdomain: {record.get('subdomain', '')}",
            f"Tags: {', '.join(record.get('tags') or [])}",
            "Workflow:",
            (record.get("workflow") or record.get("body_excerpt") or "")[:6000],
        ]
    )


def sync_qdrant(records: list[dict[str, Any]], *, url: str, collection: str, model: str, batch_size: int) -> None:
    from openai import OpenAI
    from qdrant_client import QdrantClient
    from qdrant_client.http import models

    if not os.getenv("OPENAI_API_KEY"):
        raise RuntimeError("OPENAI_API_KEY is required to create embeddings for Qdrant sync")
    vector_size = VECTOR_SIZE_BY_MODEL.get(model)
    if not vector_size:
        raise RuntimeError(f"Unknown vector size for embedding model: {model}")

    openai_client = OpenAI()
    qdrant = QdrantClient(url=url)
    qdrant.recreate_collection(
        collection_name=collection,
        vectors_config=models.VectorParams(size=vector_size, distance=models.Distance.COSINE),
    )
    point_id = 1
    for start in range(0, len(records), batch_size):
        batch = records[start : start + batch_size]
        texts = [payload_for_vector(record) for record in batch]
        embeddings = openai_client.embeddings.create(model=model, input=texts).data
        points = []
        for record, embedding in zip(batch, embeddings, strict=True):
            payload = {k: v for k, v in record.items() if k not in {"search_text", "token_counts"}}
            points.append(models.PointStruct(id=point_id, vector=embedding.embedding, payload=payload))
            point_id += 1
        qdrant.upsert(collection_name=collection, points=points, wait=True)
        print(f"qdrant upserted {min(start + batch_size, len(records))}/{len(records)}", flush=True)


def sync_postgres(records: list[dict[str, Any]], *, dsn: str) -> None:
    import asyncpg

    async def _run() -> None:
        effective_dsn = dsn.replace("postgresql+asyncpg://", "postgresql://", 1)
        conn = await asyncpg.connect(effective_dsn)
        try:
            await conn.execute(
                """
                create table if not exists quarry_security_skills (
                    id text primary key,
                    name text not null,
                    path text not null,
                    description text,
                    domain text,
                    subdomain text,
                    tags text[] default '{}',
                    source_repo text,
                    source_commit text,
                    license text,
                    metadata jsonb not null,
                    workflow text,
                    updated_at timestamptz not null default now()
                )
                """
            )
            for record in records:
                await conn.execute(
                    """
                    insert into quarry_security_skills (
                        id, name, path, description, domain, subdomain, tags,
                        source_repo, source_commit, license, metadata, workflow, updated_at
                    ) values ($1,$2,$3,$4,$5,$6,$7,$8,$9,$10,$11::jsonb,$12, now())
                    on conflict (id) do update set
                        name = excluded.name,
                        path = excluded.path,
                        description = excluded.description,
                        domain = excluded.domain,
                        subdomain = excluded.subdomain,
                        tags = excluded.tags,
                        source_repo = excluded.source_repo,
                        source_commit = excluded.source_commit,
                        license = excluded.license,
                        metadata = excluded.metadata,
                        workflow = excluded.workflow,
                        updated_at = now()
                    """,
                    record["id"],
                    record["name"],
                    record["path"],
                    record.get("description"),
                    record.get("domain"),
                    record.get("subdomain"),
                    record.get("tags") or [],
                    record.get("source_repo"),
                    record.get("source_commit"),
                    record.get("license"),
                    json.dumps(record, ensure_ascii=False),
                    record.get("workflow"),
                )
        finally:
            await conn.close()

    asyncio.run(_run())


def cmd_build(args: argparse.Namespace) -> int:
    records = load_records_from_source(args.skills_root)
    meta = write_local_index(records, args.index_dir)
    print(json.dumps(meta, ensure_ascii=False, indent=2))
    return 0


def cmd_lookup(args: argparse.Namespace) -> int:
    records = load_local_index(args.index_dir)
    results = lookup_records(records, args.query, args.limit)
    print(json.dumps({"query": args.query, "count": len(results), "results": results}, ensure_ascii=False, indent=2))
    return 0


def cmd_sync_qdrant(args: argparse.Namespace) -> int:
    records = load_local_index(args.index_dir)
    sync_qdrant(records, url=args.qdrant_url, collection=args.collection, model=args.embedding_model, batch_size=args.batch_size)
    print(json.dumps({"synced": len(records), "collection": args.collection}, indent=2))
    return 0


def cmd_sync_postgres(args: argparse.Namespace) -> int:
    records = load_local_index(args.index_dir)
    sync_postgres(records, dsn=args.database_url)
    print(json.dumps({"synced": len(records), "table": "quarry_security_skills"}, indent=2))
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Index and query Anthropic Cybersecurity Skills for Quarry")
    parser.add_argument("--skills-root", type=Path, default=default_skills_root())
    parser.add_argument("--index-dir", type=Path, default=default_index_dir())
    sub = parser.add_subparsers(dest="command", required=True)

    build = sub.add_parser("build-local", help="Parse SKILL.md files and create the local JSONL index")
    build.set_defaults(func=cmd_build)

    lookup = sub.add_parser("lookup", help="Run a local hybrid lexical lookup against the index")
    lookup.add_argument("query")
    lookup.add_argument("--limit", type=int, default=3)
    lookup.set_defaults(func=cmd_lookup)

    qdrant = sub.add_parser("sync-qdrant", help="Embed skills and upsert them into Qdrant")
    qdrant.add_argument("--qdrant-url", default=os.getenv("QDRANT_URL", "http://localhost:6333"))
    qdrant.add_argument("--collection", default=os.getenv("QDRANT_COLLECTION", DEFAULT_COLLECTION))
    qdrant.add_argument("--embedding-model", default=os.getenv("OPENAI_EMBEDDING_MODEL", DEFAULT_EMBED_MODEL))
    qdrant.add_argument("--batch-size", type=int, default=32)
    qdrant.set_defaults(func=cmd_sync_qdrant)

    pg = sub.add_parser("sync-postgres", help="Upsert skill metadata into PostgreSQL")
    pg.add_argument("--database-url", default=os.getenv("DATABASE_URL", ""))
    pg.set_defaults(func=cmd_sync_postgres)
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    if args.command == "sync-postgres" and not args.database_url:
        parser.error("sync-postgres requires --database-url or DATABASE_URL")
    try:
        return args.func(args)
    except Exception as exc:  # noqa: BLE001
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
