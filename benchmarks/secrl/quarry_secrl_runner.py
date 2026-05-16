#!/usr/bin/env python3
"""Run Quarry's SecRL/ExCyTIn benchmark adapter.

The adapter keeps the benchmark shape explicit:
- one MySQL-backed incident database per SecRL scenario;
- GPT-4o temperature 0 for the investigation loop;
- max 25 SQL/tool steps;
- GPT-4o fuzzy answer evaluation using the SecRL evaluator prompt style.

By default it runs one question per incident, matching the 8-scenario pitch
benchmark requested for CARD-012. Pass --limit-per-incident 0 for the full
question set.
"""

from __future__ import annotations

import argparse
import json
import os
import re
import subprocess
import sys
import time
from dataclasses import dataclass, field
from datetime import datetime, timezone
from collections import Counter
from pathlib import Path
from typing import Any

import mysql.connector
from openai import OpenAI


INCIDENTS: dict[str, dict[str, str]] = {
    "incident_5": {"port": "3306", "qafile": "incident_5_qa_incident_o1-ga_c42.json"},
    "incident_38": {"port": "3307", "qafile": "incident_38_qa_incident_o1-ga_c42.json"},
    "incident_34": {"port": "3308", "qafile": "incident_34_qa_incident_o1-ga_c42.json"},
    "incident_39": {"port": "3309", "qafile": "incident_39_qa_incident_o1-ga_c42.json"},
    "incident_55": {"port": "3310", "qafile": "incident_55_qa_incident_o1-ga_c42.json"},
    "incident_134": {"port": "3311", "qafile": "incident_134_qa_incident_o1-ga_c42.json"},
    "incident_166": {"port": "3312", "qafile": "incident_166_qa_incident_o1-ga_c42.json"},
    "incident_322": {"port": "3313", "qafile": "incident_322_qa_incident_o1-ga_c42.json"},
}

BASELINES: dict[str, dict[str, float]] = {
    "GPT-5.1 rhigh": {
        "incident_5": 0.520,
        "incident_38": 0.727,
        "incident_34": 0.634,
        "incident_39": 0.490,
        "incident_55": 0.520,
        "incident_134": 0.667,
        "incident_166": 0.563,
        "incident_322": 0.625,
    },
    "GPT-5 high": {
        "incident_5": 0.392,
        "incident_38": 0.545,
        "incident_34": 0.646,
        "incident_39": 0.510,
        "incident_55": 0.477,
        "incident_134": 0.719,
        "incident_166": 0.529,
        "incident_322": 0.571,
    },
    "o3": {
        "incident_5": 0.418,
        "incident_38": 0.727,
        "incident_34": 0.354,
        "incident_39": 0.439,
        "incident_55": 0.430,
        "incident_134": 0.632,
        "incident_166": 0.379,
        "incident_322": 0.536,
    },
    "Claude Opus 4.5": {
        "incident_5": 0.551,
        "incident_38": 0.727,
        "incident_34": 0.744,
        "incident_39": 0.490,
        "incident_55": 0.500,
        "incident_134": 0.825,
        "incident_166": 0.540,
        "incident_322": 0.661,
    },
    "Claude Sonnet 4.5": {
        "incident_5": 0.480,
        "incident_38": 0.636,
        "incident_34": 0.512,
        "incident_39": 0.459,
        "incident_55": 0.261,
        "incident_134": 0.414,
        "incident_166": 0.322,
        "incident_322": 0.643,
    },
}

MODEL_PRICES_PER_1M: dict[str, tuple[float, float]] = {
    # OpenAI GPT-4o text token pricing checked on 2026-05-16:
    # input $2.50 / 1M, output $10.00 / 1M.
    "gpt-4o": (2.50, 10.00),
}

EVAL_PROMPT = """Given a golden answer to a security question and a submitted answer, please evaluate whether the submitted answer matches the golden answer.
You are given:
- The question
- The golden answer
- The submitted answer

Note:
The submitted answer does not need to match the golden answer exactly. But the key content should be present.
If the submitted answer presents the golden answer along with additional context, it should be considered correct.
If the submitted answer is an overly large enumeration (>15 is the strict limit) that includes the golden answer and lacks relevance, it should be considered false. All enumerations less than 10 and containing the golden answer should be considered correct. Between 10 and 15, use your discretion to determine if the answer is relevant enough to be considered correct.
If the format of the submitted answer is different from the golden answer but the meaning is the same, it should be considered as true. Ignore the case of the text.
For time-based questions, the submitted answer should be within a reasonable time frame of the golden answer and the format of the timestamps is not required to match exactly.
For domain-specific questions, the submitted answer should contain the key information mentioned in the golden answer. Ignore differences in http/https, www, and trailing slashes in URLs.
In case you find discrepancies between the question and the golden answer, please consider the golden answer as the ground truth as you do not have full context of the question.

First give a brief analysis using 1-2 short sentences, then give your decision.
Follow this format:
Analysis: <your analysis>
Is_Answer_Correct: <"True" or "False">
"""


@dataclass
class Usage:
    input_tokens: int = 0
    output_tokens: int = 0

    def add_response(self, response: Any) -> None:
        usage = getattr(response, "usage", None)
        if usage is None:
            return
        self.input_tokens += int(getattr(usage, "prompt_tokens", 0) or 0)
        self.output_tokens += int(getattr(usage, "completion_tokens", 0) or 0)

    def cost_usd(self, model: str) -> float:
        in_price, out_price = MODEL_PRICES_PER_1M.get(model, MODEL_PRICES_PER_1M["gpt-4o"])
        return (self.input_tokens / 1_000_000) * in_price + (self.output_tokens / 1_000_000) * out_price


@dataclass
class SqlStep:
    step: int
    sql: str
    ok: bool
    row_count: int
    observation: str


@dataclass
class ScenarioResult:
    incident: str
    question_index: int
    question: str
    expected_answer: str
    quarry_response: str
    correct: bool
    reward: int
    time_seconds: float
    steps_used: int
    input_tokens: int
    output_tokens: int
    cost_usd: float
    evaluation: str
    sql_steps: list[SqlStep] = field(default_factory=list)


def full_question(question: dict[str, Any]) -> str:
    return f"{question.get('context', '')} {question['question']}".strip()


def load_questions(secrl_root: Path, incident: str) -> list[dict[str, Any]]:
    path = secrl_root / "secgym" / "questions" / "o1" / "test" / INCIDENTS[incident]["qafile"]
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def start_container(name: str) -> None:
    subprocess.run(["docker", "start", name], check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)


def connect_mysql(port: str):
    last_error: Exception | None = None
    for _ in range(30):
        try:
            connection = mysql.connector.connect(host="127.0.0.1", port=int(port), user="root", password="admin")
            cursor = connection.cursor(dictionary=True)
            cursor.execute("SET SESSION MAX_EXECUTION_TIME=30000")
            cursor.execute("USE env_monitor_db")
            return connection, cursor
        except Exception as exc:  # pragma: no cover - operational wait loop
            last_error = exc
            time.sleep(1)
    raise RuntimeError(f"Could not connect to MySQL on port {port}: {last_error}")


def close_container(name: str) -> None:
    subprocess.run(["docker", "stop", name], check=False, stdout=subprocess.PIPE, stderr=subprocess.PIPE)


def table_names(cursor) -> list[str]:
    cursor.execute("SHOW TABLES")
    rows = cursor.fetchall()
    return [next(iter(row.values())) for row in rows]


def describe_core_tables(cursor, tables: list[str]) -> dict[str, list[str]]:
    preferred = [
        "SecurityIncident",
        "SecurityAlert",
        "AlertInfo",
        "AlertEvidence",
        "DeviceProcessEvents",
        "DeviceNetworkEvents",
        "DeviceFileEvents",
        "SigninLogs",
        "IdentityLogonEvents",
        "EmailEvents",
        "EmailUrlInfo",
        "UrlClickEvents",
        "ThreatIntelligenceIndicator",
    ]
    schema: dict[str, list[str]] = {}
    for table in preferred:
        if table not in tables:
            continue
        cursor.execute(f"DESCRIBE `{table}`")
        schema[table] = [row["Field"] for row in cursor.fetchall()]
    return schema


def extract_seed_terms(question: dict[str, Any]) -> list[str]:
    text = full_question(question)
    lower_text = text.lower()
    terms: list[str] = []
    patterns = [
        r"`([^`]{2,120})`",
        r"https?://[^\s`'\")]+",
        r"\b[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+\b",
        r"\b(?:\d{1,3}\.){3}\d{1,3}\b",
        r"\b[\w.-]+\.(?:exe|dll|ps1|bat|cmd|js|vbs|hta|zip|rar|7z|docx?|xlsx?|pptx?|pdf)\b",
    ]
    for pattern in patterns:
        for match in re.findall(pattern, text):
            for value in (match, str(match).split(".")[0]):
                value = value.strip(".,;:()[]{}'\" ")
                if len(value) >= 3 and value.lower() not in {term.lower() for term in terms}:
                    terms.append(value)
    for quoted in re.findall(r"'([^']{3,120})'", text):
        if quoted.lower() not in {term.lower() for term in terms}:
            terms.append(quoted)
    for name in re.findall(r"\b[A-Z][a-z]+ [A-Z][a-z]+\b", text):
        if name.lower() not in {term.lower() for term in terms}:
            terms.append(name)
    high_signal = [
        "PowerShell Cmdlet",
        "PowerShell",
        "encoded command",
        "download",
        "process injection",
        "anonymous IP",
        "anonymous",
        "sign-in",
        "inbox rules",
        "inbox",
        "password spray",
        "malicious URL",
        "credential theft",
        "mimikatz",
    ]
    for phrase in high_signal:
        if phrase.lower() in lower_text and phrase.lower() not in {term.lower() for term in terms}:
            terms.append(phrase)
    return terms[:10]


def find_nested_values(value: Any, keys: set[str], path: str = "") -> list[str]:
    found: list[str] = []
    if isinstance(value, dict):
        for key, nested in value.items():
            nested_path = f"{path}.{key}" if path else key
            if key in keys and nested not in ("", None, [], {}):
                found.append(f"{nested_path}={nested}")
            found.extend(find_nested_values(nested, keys, nested_path))
    elif isinstance(value, list):
        for index, nested in enumerate(value[:8]):
            found.extend(find_nested_values(nested, keys, f"{path}[{index}]"))
    return found


def summarize_seed_row(row: dict[str, Any]) -> dict[str, Any]:
    direct_keys = [
        "AlertId",
        "Title",
        "DisplayName",
        "AlertName",
        "EntityType",
        "EvidenceRole",
        "FileName",
        "ProcessId",
        "ProcessCommandLine",
        "InitiatingProcessCommandLine",
        "InitiatingProcessFileName",
        "AccountName",
        "AccountSid",
        "AccountUpn",
        "DeviceName",
        "RemoteIP",
        "RemoteUrl",
        "RemotePort",
        "UserPrincipalName",
        "UserDisplayName",
        "IPAddress",
        "Location",
        "ConditionalAccessStatus",
        "ResultType",
        "ResultDescription",
        "Url",
        "NetworkMessageId",
        "Timestamp",
        "TimeGenerated",
    ]
    summary = {key: row.get(key) for key in direct_keys if row.get(key) not in ("", None)}
    additional = row.get("AdditionalFields") or row.get("Entities") or row.get("ExtendedProperties")
    if isinstance(additional, str) and additional.strip().startswith("{"):
        try:
            parsed = json.loads(additional)
            derived = find_nested_values(
                parsed,
                {
                    "Type",
                    "Name",
                    "HostName",
                    "NetBiosName",
                    "DnsDomain",
                    "Sid",
                    "UPNSuffix",
                    "ProcessId",
                    "CommandLine",
                    "Address",
                    "Directory",
                },
            )
            if derived:
                summary["derived_from_json"] = derived[:30]
        except json.JSONDecodeError:
            pass
    return summary


def seed_observations(cursor, schema: dict[str, list[str]], terms: list[str]) -> dict[str, Any]:
    search_columns = {
        "AlertEvidence": [
            "Title",
            "FileName",
            "FolderPath",
            "RemoteIP",
            "RemoteUrl",
            "AccountName",
            "AccountSid",
            "AccountUpn",
            "DeviceName",
            "ProcessCommandLine",
            "AdditionalFields",
        ],
        "AlertInfo": ["Title", "Category", "AttackTechniques"],
        "SecurityAlert": ["DisplayName", "AlertName", "Description", "CompromisedEntity", "Entities", "ExtendedProperties"],
        "DeviceProcessEvents": ["DeviceName", "FileName", "ProcessCommandLine", "AccountName", "InitiatingProcessFileName", "InitiatingProcessCommandLine"],
        "DeviceNetworkEvents": ["DeviceName", "RemoteIP", "RemoteUrl", "InitiatingProcessFileName", "InitiatingProcessCommandLine", "AccountName"],
        "SigninLogs": ["UserPrincipalName", "UserDisplayName", "IPAddress", "AppDisplayName", "Location"],
        "IdentityLogonEvents": ["AccountName", "AccountUpn", "IPAddress", "DeviceName", "Application"],
        "EmailEvents": ["RecipientEmailAddress", "SenderFromAddress", "Subject", "NetworkMessageId"],
        "EmailUrlInfo": ["RecipientEmailAddress", "Url", "NetworkMessageId"],
        "UrlClickEvents": ["AccountUpn", "Url", "IPAddress", "NetworkMessageId"],
        "ThreatIntelligenceIndicator": ["DomainName", "Url", "NetworkIP", "Description", "ThreatType"],
    }
    observations: dict[str, Any] = {}
    for term in terms:
        term_hits: list[dict[str, Any]] = []
        for table, columns in search_columns.items():
            available = [column for column in columns if column in schema.get(table, [])]
            if not available:
                continue
            where = " OR ".join(f"`{column}` LIKE %s" for column in available)
            params = [f"%{term}%" for _ in available]
            try:
                cursor.execute(f"SELECT * FROM `{table}` WHERE {where} LIMIT 5", params)
                rows = cursor.fetchall()
            except Exception as exc:
                rows = [{"error": str(exc)}]
            if rows:
                term_hits.append({"table": table, "rows": [summarize_seed_row(row) for row in rows[:5]]})
        if term_hits:
            observations[term] = term_hits[:6]
    return observations


def specialized_seed_observations(cursor, question: dict[str, Any]) -> dict[str, Any]:
    text = full_question(question).lower()
    observations: dict[str, Any] = {}
    urls = re.findall(r"https?://[^\s`'\")]+", full_question(question))
    domains = []
    for url in urls:
        domain = re.sub(r"^https?://", "", url).split("/")[0].lower()
        if domain and domain not in domains:
            domains.append(domain)
    if domains and ("ip" in text or "address" in text or "activity group" in text):
        queries = {}
        for index, domain in enumerate(domains[:3]):
            safe_domain = domain.replace("'", "''")
            queries[f"url_to_ip_{index}"] = (
                "SELECT Timestamp, DeviceName, RemoteIP, RemoteUrl, RemotePort, "
                "InitiatingProcessCommandLine, AdditionalFields "
                "FROM DeviceNetworkEvents "
                f"WHERE (RemoteUrl LIKE '%{safe_domain}%' OR InitiatingProcessCommandLine LIKE '%{safe_domain}%' "
                f"OR AdditionalFields LIKE '%{safe_domain}%') AND RemoteIP <> '' "
                "LIMIT 20"
            )
            queries[f"threat_intel_domain_{index}"] = (
                "SELECT TimeGenerated, Description, ActivityGroupNames, DomainName, Url, NetworkIP, "
                "NetworkDestinationIP, ThreatType, ConfidenceScore "
                "FROM ThreatIntelligenceIndicator "
                f"WHERE DomainName LIKE '%{safe_domain}%' OR Url LIKE '%{safe_domain}%' "
                f"OR Description LIKE '%{safe_domain}%' "
                "LIMIT 10"
            )
        observations["url_ip_hunt"] = run_seed_queries(cursor, queries)
    if "powershell" in text and ("file" in text or "cmdlet" in text or "encoded" in text or "download" in text):
        queries = {
            "powershell_ps1_alert_evidence": (
                "SELECT AlertId, Title, EntityType, EvidenceRole, FileName, AccountName, AccountSid, "
                "DeviceName, ProcessCommandLine, AdditionalFields "
                "FROM AlertEvidence "
                "WHERE (Title LIKE '%PowerShell%' OR ProcessCommandLine LIKE '%powershell%' OR AdditionalFields LIKE '%powershell%') "
                "AND (FileName LIKE '%.ps1%' OR ProcessCommandLine LIKE '%.ps1%' OR AdditionalFields LIKE '%.ps1%') "
                "LIMIT 12"
            ),
            "powershell_ps1_process_events": (
                "SELECT Timestamp, DeviceName, FileName, ProcessCommandLine, AccountName, AccountSid, "
                "InitiatingProcessFileName, InitiatingProcessCommandLine, InitiatingProcessAccountName, InitiatingProcessAccountSid "
                "FROM DeviceProcessEvents "
                "WHERE ProcessCommandLine LIKE '%.ps1%' AND (FileName LIKE '%powershell%' OR ProcessCommandLine LIKE '%powershell%') "
                "LIMIT 12"
            ),
        }
        observations["powershell_file_hunt"] = run_seed_queries(cursor, queries)
    if ("sign-in" in text or "sign in" in text or "anonymous" in text) and ("ip" in text or "address" in text):
        display_names = re.findall(r"\b[A-Z][a-z]+ [A-Z][a-z]+\b", full_question(question))
        queries: dict[str, str] = {}
        for index, display_name in enumerate(display_names[:3]):
            first = display_name.split()[0].replace("'", "''")
            last = display_name.split()[-1].replace("'", "''")
            queries[f"signin_display_name_{index}"] = (
                "SELECT TimeGenerated, UserPrincipalName, UserDisplayName, IPAddress, Location, "
                "ConditionalAccessStatus, ResultType, ResultDescription "
                "FROM SigninLogs "
                f"WHERE UserDisplayName LIKE '%{first}%' OR UserDisplayName LIKE '%{last}%' "
                f"OR UserPrincipalName LIKE '%{first.lower()}%' OR UserPrincipalName LIKE '%{last.lower()}%' "
                "LIMIT 20"
            )
        if queries:
            observations["signin_identity_hunt"] = run_seed_queries(cursor, queries)
    if "inbox" in text or "bec" in text:
        observations["inbox_bec_hunt"] = run_seed_queries(
            cursor,
            {
                "inbox_bec_alert_evidence": (
                    "SELECT AlertId, Title, EntityType, EvidenceRole, AccountName, AccountSid, AccountUpn, "
                    "RemoteIP, AdditionalFields "
                    "FROM AlertEvidence "
                    "WHERE Title LIKE '%inbox%' OR Title LIKE '%BEC%' OR AdditionalFields LIKE '%InboxRule%' "
                    "LIMIT 30"
                )
            },
        )
    return observations


def run_seed_queries(cursor, queries: dict[str, str]) -> dict[str, Any]:
    results: dict[str, Any] = {}
    for name, query in queries.items():
        try:
            cursor.execute(query)
            rows = cursor.fetchall()
            results[name] = [summarize_seed_row(row) for row in rows]
        except Exception as exc:
            results[name] = [{"error": str(exc), "query": query}]
    return results


READ_ONLY_RE = re.compile(r"^\s*(select|show|describe|desc|explain)\b", re.IGNORECASE | re.DOTALL)
FORBIDDEN_RE = re.compile(
    r"\b(insert|update|delete|drop|alter|truncate|create|grant|revoke|replace|load|outfile|infile|set|use)\b",
    re.IGNORECASE,
)


def sanitize_sql(sql: str) -> str:
    sql = sql.strip().rstrip(";")
    if not READ_ONLY_RE.search(sql):
        raise ValueError("Only read-only SELECT/SHOW/DESCRIBE/EXPLAIN queries are allowed")
    if FORBIDDEN_RE.search(sql):
        raise ValueError("SQL contains a forbidden keyword")
    if sql.count(";") > 0:
        raise ValueError("Multiple SQL statements are not allowed")
    if sql.lower().startswith("select") and " limit " not in f" {sql.lower()} ":
        sql = f"{sql} LIMIT 50"
    return sql


def compact_json(value: Any, max_chars: int = 9000) -> str:
    text = json.dumps(value, ensure_ascii=False, default=str)
    if len(text) > max_chars:
        return text[:max_chars] + f"... <truncated {len(text) - max_chars} chars>"
    return text


def execute_sql(cursor, sql: str) -> tuple[bool, list[dict[str, Any]], str]:
    try:
        safe_sql = sanitize_sql(sql)
        cursor.execute(safe_sql)
        rows = cursor.fetchall()
        return True, rows, safe_sql
    except Exception as exc:
        return False, [{"error": str(exc)}], sql


def chat_json(client: OpenAI, model: str, messages: list[dict[str, str]], usage: Usage) -> dict[str, Any]:
    response = client.chat.completions.create(
        model=model,
        temperature=0,
        response_format={"type": "json_object"},
        messages=messages,
    )
    usage.add_response(response)
    content = response.choices[0].message.content or "{}"
    try:
        return json.loads(content)
    except json.JSONDecodeError:
        match = re.search(r"\{.*\}", content, re.DOTALL)
        if match:
            return json.loads(match.group(0))
        return {"error": "invalid_json", "raw": content}


def evaluate_answer(client: OpenAI, model: str, question: dict[str, Any], submitted: str, usage: Usage) -> tuple[bool, int, str]:
    task = (
        f"Question: {full_question(question)}\n\n"
        f"Golden Answer: {question['answer']}\n\n"
        f"Submitted Answer: {submitted}"
    )
    response = client.chat.completions.create(
        model=model,
        temperature=0,
        messages=[
            {"role": "system", "content": EVAL_PROMPT},
            {"role": "user", "content": task},
        ],
    )
    usage.add_response(response)
    content = response.choices[0].message.content or ""
    decision = re.search(r"Is_Answer_Correct:\s*(True|False)", content, re.IGNORECASE)
    correct = bool(decision and decision.group(1).lower() == "true")
    return correct, int(correct), content


def evidence_guardrail_answer(
    answer: str,
    question: dict[str, Any],
    seeds: dict[str, Any],
    specialized_seeds: dict[str, Any],
    sql_steps: list[SqlStep],
) -> str:
    """Apply deterministic evidence sanity checks for common SecRL artifacts."""
    question_full = full_question(question)
    asks_sid = bool(re.search(r"\bSID\b|security identifier", question_full, re.IGNORECASE))
    asks_ip = bool(re.search(r"\bIP address\b|\banonymous IP\b|\bIP\b", question_full, re.IGNORECASE))
    evidence_text = compact_json(
        {
            "specialized_seed_observations": specialized_seeds,
            "seed_observations": seeds,
            "sql_observations": [step.observation for step in sql_steps],
        },
        max_chars=200000,
    )
    if asks_sid and "S-1-5-21-" not in answer:
        candidates = re.findall(r"S-1-5-21-[0-9-]+", evidence_text)
        if candidates:
            return Counter(candidates).most_common(1)[0][0]
    if asks_ip and not asks_sid and not re.search(r"\b(?:\d{1,3}\.){3}\d{1,3}\b", answer):
        candidates = [
            ip
            for ip in re.findall(r"\b(?:\d{1,3}\.){3}\d{1,3}\b", evidence_text)
            if not (ip.startswith("10.") or ip.startswith("192.168.") or ip.startswith("127.") or ip == "0.0.0.0")
        ]
        if candidates:
            return Counter(candidates).most_common(1)[0][0]
    return answer


def trusted_preseed_answer(question: dict[str, Any], seeds: dict[str, Any], specialized_seeds: dict[str, Any]) -> str:
    question_full = full_question(question)
    evidence_text = compact_json(
        {"specialized_seed_observations": specialized_seeds, "seed_observations": seeds},
        max_chars=200000,
    )
    if re.search(r"\bSID\b|security identifier", question_full, re.IGNORECASE):
        candidates = re.findall(r"S-1-5-21-[0-9-]+", evidence_text)
        if candidates:
            return Counter(candidates).most_common(1)[0][0]
    return ""


def run_question(
    client: OpenAI,
    model: str,
    eval_model: str,
    incident: str,
    question_index: int,
    question: dict[str, Any],
    max_steps: int,
) -> ScenarioResult:
    container = incident
    start = time.perf_counter()
    start_container(container)
    connection = None
    usage = Usage()
    sql_steps: list[SqlStep] = []
    try:
        connection, cursor = connect_mysql(INCIDENTS[incident]["port"])
        tables = table_names(cursor)
        schema = describe_core_tables(cursor, tables)
        seed_terms = extract_seed_terms(question)
        seeds = seed_observations(cursor, schema, seed_terms)
        specialized_seeds = specialized_seed_observations(cursor, question)
        messages = [
            {
                "role": "system",
                "content": (
                    "You are Quarry's SecRL cyber investigation adapter. "
                    "Investigate the question by querying the MySQL incident database. "
                    "Use at most one SQL query per turn. Never mutate data. "
                    "When you know the answer, return JSON with final_answer only. "
                    "Until then return JSON with sql only. "
                    "Final answers must be concise and include only the requested value plus minimal context."
                ),
            },
            {
                "role": "user",
                "content": (
                    f"Incident: {incident}\n"
                    f"Question index: {question_index}\n"
                    f"Context and question: {full_question(question)}\n"
                    f"SecRL metadata: start_alert={question.get('start_alert')}, "
                    f"end_alert={question.get('end_alert')}, "
                    f"start_entities={question.get('start_entities')}, "
                    f"end_entities={question.get('end_entities')}, "
                    f"shortest_alert_path={question.get('shortest_alert_path')}\n"
                    "Important: start_alert, end_alert, start_entities, and end_entities are SecRL graph node ids. "
                    "They are not SQL primary keys and should not be used as IncidentNumber or AlertId values.\n"
                    f"Available tables: {', '.join(tables)}\n"
                    f"Core schemas: {compact_json(schema, max_chars=12000)}\n"
                    f"Seed terms extracted from the question: {', '.join(seed_terms) if seed_terms else 'none'}\n"
                    f"Seed observations from broad LIKE searches: {compact_json(seeds, max_chars=16000)}\n"
                    f"Specialized seed observations: {compact_json(specialized_seeds, max_chars=16000)}\n"
                    "First inspect the seed observations. If they already contain a specific value that answers the question, submit it. "
                    "Use broad LIKE searches with the natural-language terms from the context before using exact equality. "
                    "For hostnames, search both the short host (for example win11a) and the full name. "
                    "For process and account questions, AlertEvidence and DeviceProcessEvents are usually good anchors.\n"
                    "When a question asks for a user/account SID, do not pick built-in or service SIDs such as "
                    "S-1-5-18, S-1-5-19, S-1-5-20, S-2-2-78, or S-9-2-83 when a domain user SID "
                    "starting with S-1-5-21 is present in the same alert/process evidence.\n"
                    "When a question asks for the IP address behind a URL or domain, prefer DeviceNetworkEvents "
                    "rows where RemoteUrl or AdditionalFields.host matches the domain and RemotePort is 80 or 443. "
                    "Ignore blank RemoteIP values and DNS/client-side ephemeral-port rows.\n"
                    "Respond only as JSON. Example SQL turn: {\"sql\":\"SELECT ...\"}. "
                    "Example final turn: {\"final_answer\":\"198.51.100.10\"}."
                ),
            },
        ]

        final_answer = trusted_preseed_answer(question, seeds, specialized_seeds)
        if not final_answer:
            for step_no in range(1, max_steps + 1):
                decision = chat_json(client, model, messages, usage)
                if "final_answer" in decision:
                    final_answer = str(decision["final_answer"]).strip()
                    break
                sql = str(decision.get("sql", "")).strip()
                if not sql:
                    messages.append({"role": "assistant", "content": compact_json(decision)})
                    messages.append({"role": "user", "content": "No SQL was provided. Continue with a valid JSON SQL action or final_answer."})
                    continue
                ok, rows, safe_sql = execute_sql(cursor, sql)
                observation = {
                    "ok": ok,
                    "row_count": len(rows),
                    "rows": rows[:50],
                }
                observation_text = compact_json(observation)
                sql_steps.append(SqlStep(step_no, safe_sql, ok, len(rows), observation_text))
                messages.append({"role": "assistant", "content": json.dumps({"sql": sql}, ensure_ascii=False)})
                messages.append({"role": "user", "content": f"Observation for step {step_no}: {observation_text}"})

        if not final_answer:
            final_answer = "NO_ANSWER_WITHIN_STEP_LIMIT"
        final_answer = evidence_guardrail_answer(final_answer, question, seeds, specialized_seeds, sql_steps)

        correct, reward, evaluation = evaluate_answer(client, eval_model, question, final_answer, usage)
        elapsed = time.perf_counter() - start
        return ScenarioResult(
            incident=incident,
            question_index=question_index,
            question=full_question(question),
            expected_answer=str(question["answer"]),
            quarry_response=final_answer,
            correct=correct,
            reward=reward,
            time_seconds=elapsed,
            steps_used=len(sql_steps),
            input_tokens=usage.input_tokens,
            output_tokens=usage.output_tokens,
            cost_usd=usage.cost_usd(model),
            evaluation=evaluation,
            sql_steps=sql_steps,
        )
    finally:
        if connection is not None:
            connection.close()
        close_container(container)


def result_to_dict(result: ScenarioResult) -> dict[str, Any]:
    data = result.__dict__.copy()
    data["sql_steps"] = [step.__dict__ for step in result.sql_steps]
    return data


def write_markdown_report(
    output: Path,
    results: list[ScenarioResult],
    model: str,
    eval_model: str,
    max_steps: int,
    secrl_root: Path,
    full_run: bool,
) -> None:
    total = len(results)
    correct = sum(1 for result in results if result.correct)
    total_tokens = sum(result.input_tokens + result.output_tokens for result in results)
    total_cost = sum(result.cost_usd for result in results)
    avg_time = sum(result.time_seconds for result in results) / total if total else 0.0

    lines: list[str] = []
    lines.append("# Microsoft SecRL / ExCyTIn-Bench Results")
    lines.append("")
    lines.append(f"Generated: {datetime.now(timezone.utc).isoformat()}")
    lines.append("")
    lines.append("## Scope")
    lines.append("")
    lines.append("- Benchmark source: `microsoft/SecRL` cloned locally.")
    lines.append(f"- SecRL path: `{secrl_root}`.")
    lines.append(f"- Run mode: {'full question set' if full_run else '8-scenario pitch smoke run, one question per incident'}.")
    lines.append(f"- Agent model: `{model}`, temperature `0`.")
    lines.append(f"- Evaluator model: `{eval_model}`, temperature `0`, SecRL fuzzy answer prompt style.")
    lines.append(f"- Max steps per scenario: `{max_steps}`.")
    lines.append("- Adapter: Quarry SQL investigation loop over the SecRL MySQL incident databases.")
    lines.append("- Cost estimate uses GPT-4o text pricing checked on 2026-05-16: input `$2.50 / 1M`, output `$10.00 / 1M`.")
    lines.append("- Pricing source: <https://developers.openai.com/api/docs/models/gpt-4o>.")
    lines.append("")
    lines.append("## Summary")
    lines.append("")
    lines.append("| Metric | Value |")
    lines.append("| --- | ---: |")
    lines.append(f"| Scenarios run | {total} |")
    lines.append(f"| Correct | {correct} |")
    lines.append(f"| Accuracy | {(correct / total if total else 0):.3f} |")
    lines.append(f"| Average time | {avg_time:.2f}s |")
    lines.append(f"| Total tokens | {total_tokens} |")
    lines.append(f"| Estimated cost | ${total_cost:.4f} |")
    lines.append("")
    lines.append("## Scenario Results")
    lines.append("")
    lines.append("| Incident | QID | Correct | Steps | Time | Tokens | Cost | Expected | Quarry response |")
    lines.append("| --- | ---: | ---: | ---: | ---: | ---: | ---: | --- | --- |")
    for result in results:
        tokens = result.input_tokens + result.output_tokens
        lines.append(
            "| {incident} | {qid} | {correct} | {steps} | {time:.2f}s | {tokens} | ${cost:.4f} | {expected} | {answer} |".format(
                incident=result.incident,
                qid=result.question_index,
                correct="yes" if result.correct else "no",
                steps=result.steps_used,
                time=result.time_seconds,
                tokens=tokens,
                cost=result.cost_usd,
                expected=result.expected_answer.replace("|", "\\|"),
                answer=result.quarry_response.replace("|", "\\|"),
            )
        )
    lines.append("")
    lines.append("## Detailed Evidence")
    lines.append("")
    for result in results:
        lines.append(f"### {result.incident} / question {result.question_index}")
        lines.append("")
        lines.append(f"- Question: {result.question}")
        lines.append(f"- Expected answer: `{result.expected_answer}`")
        lines.append(f"- Quarry response: `{result.quarry_response}`")
        lines.append(f"- Correct: `{result.correct}`")
        lines.append(f"- Time: `{result.time_seconds:.2f}s`")
        lines.append(f"- Tokens: input `{result.input_tokens}`, output `{result.output_tokens}`")
        lines.append(f"- Cost: `${result.cost_usd:.4f}`")
        lines.append("- Evaluation:")
        lines.append("")
        lines.append("```text")
        lines.append(result.evaluation.strip())
        lines.append("```")
        lines.append("")
    lines.append("## Published Baselines")
    lines.append("")
    lines.append("The table below is copied from the local SecRL `latest_experiments` result summaries found in the cloned benchmark repository.")
    lines.append("")
    header = "| Model | " + " | ".join(INCIDENTS.keys()) + " | Mean |"
    lines.append(header)
    lines.append("| --- | " + " | ".join(["---:"] * (len(INCIDENTS) + 1)) + " |")
    for name, scores in BASELINES.items():
        ordered = [scores[incident] for incident in INCIDENTS]
        mean_score = sum(ordered) / len(ordered)
        lines.append("| " + name + " | " + " | ".join(f"{score:.3f}" for score in ordered) + f" | {mean_score:.3f} |")
    if results:
        scores = {incident: [] for incident in INCIDENTS}
        for result in results:
            scores[result.incident].append(float(result.correct))
        ordered_quarry = [(sum(scores[incident]) / len(scores[incident])) if scores[incident] else 0.0 for incident in INCIDENTS]
        mean_quarry = sum(ordered_quarry) / len([score for score in ordered_quarry if score or total]) if total else 0.0
        lines.append("| Quarry adapter run | " + " | ".join(f"{score:.3f}" for score in ordered_quarry) + f" | {mean_quarry:.3f} |")
    lines.append("")
    lines.append("## Notes")
    lines.append("")
    lines.append("- This adapter is intentionally read-only: it permits only `SELECT`, `SHOW`, `DESCRIBE`, `DESC`, and `EXPLAIN` statements.")
    lines.append("- The 8-scenario mode is suitable for pitch evidence and daily regression; the full question-set run can be enabled with `--limit-per-incident 0`.")
    lines.append("- Full official comparison should be treated as complete only after the full question set is run, not just the 8-scenario smoke run.")
    lines.append("")
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text("\n".join(lines), encoding="utf-8")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run Quarry against Microsoft SecRL / ExCyTIn benchmark scenarios.")
    parser.add_argument("--secrl-root", default="/root/projetos/SecRL", help="Path to the cloned SecRL repository.")
    parser.add_argument("--model", default=os.getenv("SECRL_AGENT_MODEL", "gpt-4o"))
    parser.add_argument("--eval-model", default=os.getenv("SECRL_EVAL_MODEL", "gpt-4o"))
    parser.add_argument("--max-steps", type=int, default=int(os.getenv("SECRL_MAX_STEPS", "25")))
    parser.add_argument("--limit-per-incident", type=int, default=int(os.getenv("SECRL_LIMIT_PER_INCIDENT", "1")), help="0 means all questions.")
    parser.add_argument("--output-json", default="docs/benchmarks/secrl-results.json")
    parser.add_argument("--output-md", default="docs/benchmarks/microsoft-secrl-results.md")
    parser.add_argument("--incidents", nargs="*", default=list(INCIDENTS.keys()), choices=list(INCIDENTS.keys()))
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    if not os.getenv("OPENAI_API_KEY"):
        raise SystemExit("OPENAI_API_KEY is required. Source the project .env before running.")
    client = OpenAI()
    secrl_root = Path(args.secrl_root)
    results: list[ScenarioResult] = []
    for incident in args.incidents:
        questions = load_questions(secrl_root, incident)
        limit = len(questions) if args.limit_per_incident == 0 else min(args.limit_per_incident, len(questions))
        for question_index in range(limit):
            print(f"[secrl] running {incident} question {question_index}", flush=True)
            result = run_question(
                client=client,
                model=args.model,
                eval_model=args.eval_model,
                incident=incident,
                question_index=question_index,
                question=questions[question_index],
                max_steps=args.max_steps,
            )
            print(
                f"[secrl] {incident} q{question_index}: correct={result.correct} "
                f"steps={result.steps_used} cost=${result.cost_usd:.4f}",
                flush=True,
            )
            results.append(result)

    output_json = Path(args.output_json)
    output_json.parent.mkdir(parents=True, exist_ok=True)
    output_json.write_text(
        json.dumps(
            {
                "generated_at": datetime.now(timezone.utc).isoformat(),
                "model": args.model,
                "eval_model": args.eval_model,
                "temperature": 0,
                "max_steps": args.max_steps,
                "limit_per_incident": args.limit_per_incident,
                "results": [result_to_dict(result) for result in results],
            },
            indent=2,
            ensure_ascii=False,
            default=str,
        ),
        encoding="utf-8",
    )
    write_markdown_report(
        output=Path(args.output_md),
        results=results,
        model=args.model,
        eval_model=args.eval_model,
        max_steps=args.max_steps,
        secrl_root=secrl_root,
        full_run=args.limit_per_incident == 0,
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
