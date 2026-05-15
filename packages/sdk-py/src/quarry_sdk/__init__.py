"""quarry-sdk — Python client for Quarry.

Usage::

    from quarry_sdk import QuarryClient

    async with QuarryClient(base_url="https://soc.example.com", token="aisoc_...") as client:
        alerts = await client.alerts.list(severity="critical")
"""

from .client import QuarryClient, QuarryError
from .models import (
    Alert,
    AlertFilters,
    AlertSeverity,
    AlertStatus,
    ApiKey,
    ApiKeyCreateRequest,
    ApiKeyCreateResponse,
    Case,
    CaseFilters,
    CasePriority,
    CaseStatus,
    Connector,
    DetectionRule,
    Page,
    Playbook,
    PlaybookRun,
)

__all__ = [
    "QuarryClient",
    "QuarryError",
    "Alert",
    "AlertFilters",
    "AlertSeverity",
    "AlertStatus",
    "ApiKey",
    "ApiKeyCreateRequest",
    "ApiKeyCreateResponse",
    "Case",
    "CaseFilters",
    "CasePriority",
    "CaseStatus",
    "Connector",
    "DetectionRule",
    "Page",
    "Playbook",
    "PlaybookRun",
]

__version__ = "4.0.0"
