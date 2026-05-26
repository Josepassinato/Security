"""Pluggable dispatcher for regulatory communications (Bacen, ANPD).

Three adapters:

* ``EmailDispatcher``    — SMTP via env-configured server. The MVP path
                           for CSIRT-Bacen (manual email today, no public API).
* ``WebhookDispatcher``  — POSTs the artifact + metadata to a tenant-configured
                           URL. For fintechs that have an internal SIEM /
                           compliance pipeline that wants the artifact.
* ``SisbacenDispatcher`` — stub. Returns NotImplementedError with a
                           message pointing to the fact that SISBACEN has
                           no published API for incident submission as of
                           2026-05. Wiring is ready for the day the Bacen
                           publishes one; until then, ``email`` is the
                           defensible channel.

Configuration is read from environment variables prefixed
``QUARRY_REGCOMM_``. We avoid pydantic Settings for now because
fintechs deploy this in air-gapped mode and bringing the whole
``app.core.config`` graph in just for two SMTP fields adds startup
fragility. When the UI flow lands and there's a settings panel, this
moves into the main config.
"""

from __future__ import annotations

import asyncio
import os
import smtplib
import ssl
from abc import ABC, abstractmethod
from dataclasses import dataclass
from email.message import EmailMessage
from typing import Any

import httpx


@dataclass(frozen=True)
class DispatchResult:
    """Persistent record of a single dispatch attempt."""

    ok: bool
    channel: str
    target: str
    detail: str
    # Raw provider response (SMTP code, HTTP body) for forensics.
    provider_response: dict[str, Any] | None = None

    def to_jsonable(self) -> dict[str, Any]:
        return {
            "ok": self.ok,
            "channel": self.channel,
            "target": self.target,
            "detail": self.detail,
            "provider_response": self.provider_response,
        }


class RegulatoryDispatcher(ABC):
    """Strategy: send a regulatory artifact through a single channel."""

    channel: str

    @abstractmethod
    async def send(
        self,
        *,
        subject: str,
        body_md: str,
        target: str,
        attachments: dict[str, bytes] | None = None,
    ) -> DispatchResult:
        ...


# ---------------------------------------------------------------------------
# EmailDispatcher — SMTP. Renderiza o body_md como texto puro no corpo +
# attachment .md. Não tenta converter pra HTML — auditor lê o .md cru.
# ---------------------------------------------------------------------------


class EmailDispatcher(RegulatoryDispatcher):
    channel = "email"

    def __init__(
        self,
        *,
        host: str | None = None,
        port: int | None = None,
        username: str | None = None,
        password: str | None = None,
        from_addr: str | None = None,
        use_tls: bool | None = None,
    ) -> None:
        self.host = host or os.environ.get("QUARRY_REGCOMM_SMTP_HOST", "")
        self.port = port or int(os.environ.get("QUARRY_REGCOMM_SMTP_PORT", "465"))
        self.username = username or os.environ.get("QUARRY_REGCOMM_SMTP_USER", "")
        self.password = password or os.environ.get("QUARRY_REGCOMM_SMTP_PASS", "")
        self.from_addr = from_addr or os.environ.get(
            "QUARRY_REGCOMM_FROM", self.username
        )
        # SMTPS (port 465) por default. Quem usa 587 (STARTTLS) seta
        # USE_TLS=true e o adapter usa starttls() em vez de SMTP_SSL.
        env_tls = os.environ.get("QUARRY_REGCOMM_USE_TLS", "false").lower()
        self.use_tls = use_tls if use_tls is not None else env_tls == "true"

    def _build_message(
        self,
        *,
        subject: str,
        body_md: str,
        target: str,
        attachments: dict[str, bytes] | None,
    ) -> EmailMessage:
        msg = EmailMessage()
        msg["Subject"] = subject
        msg["From"] = self.from_addr
        msg["To"] = target
        msg.set_content(body_md)  # corpo plain-text
        for name, data in (attachments or {}).items():
            msg.add_attachment(
                data, maintype="application", subtype="octet-stream", filename=name
            )
        return msg

    def _send_sync(self, msg: EmailMessage) -> dict[str, Any]:
        if not self.host:
            raise RuntimeError(
                "EmailDispatcher: QUARRY_REGCOMM_SMTP_HOST não configurado"
            )
        if self.use_tls:
            with smtplib.SMTP(self.host, self.port, timeout=30) as srv:
                srv.ehlo()
                srv.starttls(context=ssl.create_default_context())
                srv.ehlo()
                if self.username:
                    srv.login(self.username, self.password)
                refused = srv.send_message(msg)
            return {"mode": "starttls", "refused": refused}
        with smtplib.SMTP_SSL(
            self.host, self.port, timeout=30, context=ssl.create_default_context()
        ) as srv:
            if self.username:
                srv.login(self.username, self.password)
            refused = srv.send_message(msg)
        return {"mode": "smtps", "refused": refused}

    async def send(
        self,
        *,
        subject: str,
        body_md: str,
        target: str,
        attachments: dict[str, bytes] | None = None,
    ) -> DispatchResult:
        msg = self._build_message(
            subject=subject, body_md=body_md, target=target, attachments=attachments
        )
        try:
            provider_response = await asyncio.to_thread(self._send_sync, msg)
        except Exception as exc:  # noqa: BLE001 — adapter de borda, propaga via DispatchResult
            return DispatchResult(
                ok=False,
                channel=self.channel,
                target=target,
                detail=f"smtp_error: {type(exc).__name__}: {exc}",
            )
        refused = provider_response.get("refused") or {}
        if refused:
            return DispatchResult(
                ok=False,
                channel=self.channel,
                target=target,
                detail=f"recipients_refused: {list(refused.keys())}",
                provider_response=provider_response,
            )
        return DispatchResult(
            ok=True,
            channel=self.channel,
            target=target,
            detail="sent",
            provider_response=provider_response,
        )


# ---------------------------------------------------------------------------
# WebhookDispatcher — POST JSON pra URL configurada pelo tenant. Útil pra
# fintechs com SIEM interno que querem o artefato no pipeline delas.
# ---------------------------------------------------------------------------


class WebhookDispatcher(RegulatoryDispatcher):
    channel = "webhook"

    def __init__(self, *, default_url: str | None = None) -> None:
        self.default_url = default_url or os.environ.get(
            "QUARRY_REGCOMM_WEBHOOK_URL", ""
        )
        self.shared_secret = os.environ.get("QUARRY_REGCOMM_WEBHOOK_SECRET", "")

    async def send(
        self,
        *,
        subject: str,
        body_md: str,
        target: str,
        attachments: dict[str, bytes] | None = None,
    ) -> DispatchResult:
        url = target or self.default_url
        if not url:
            return DispatchResult(
                ok=False,
                channel=self.channel,
                target=target,
                detail="missing_url",
            )
        headers = {"Content-Type": "application/json"}
        if self.shared_secret:
            # HMAC seria mais correto; placeholder pra MVP.
            headers["X-Quarry-Secret"] = self.shared_secret
        payload = {
            "subject": subject,
            "body_md": body_md,
            "attachments": {
                k: v.decode("utf-8", errors="replace")
                for k, v in (attachments or {}).items()
            },
        }
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                resp = await client.post(url, json=payload, headers=headers)
        except Exception as exc:  # noqa: BLE001
            return DispatchResult(
                ok=False,
                channel=self.channel,
                target=url,
                detail=f"http_error: {type(exc).__name__}: {exc}",
            )
        ok = 200 <= resp.status_code < 300
        return DispatchResult(
            ok=ok,
            channel=self.channel,
            target=url,
            detail=f"http_{resp.status_code}",
            provider_response={
                "status_code": resp.status_code,
                "body": resp.text[:500],
            },
        )


# ---------------------------------------------------------------------------
# SisbacenDispatcher — stub explícito. SISBACEN não tem API pública de
# submissão de incidentes em 2026-05. Quando publicar, plug aqui.
# ---------------------------------------------------------------------------


class SisbacenDispatcher(RegulatoryDispatcher):
    channel = "sisbacen"

    async def send(
        self,
        *,
        subject: str,
        body_md: str,
        target: str,
        attachments: dict[str, bytes] | None = None,
    ) -> DispatchResult:
        return DispatchResult(
            ok=False,
            channel=self.channel,
            target=target,
            detail=(
                "sisbacen_api_unavailable: Bacen não publicou endpoint público "
                "de submissão de incidentes até 2026-05. Use channel=email pra "
                "CSIRT-Bacen ou webhook pra pipeline interno."
            ),
        )


# ---------------------------------------------------------------------------
# Resolver — quem chama do endpoint não precisa saber qual adapter
# instanciar. ``get_dispatcher`` resolve por channel e cacheia por
# processo (configs vêm de env, mudam só com restart).
# ---------------------------------------------------------------------------


_REGISTRY: dict[str, RegulatoryDispatcher] = {}


def get_dispatcher(channel: str) -> RegulatoryDispatcher:
    """Resolve um dispatcher pelo channel name. Cacheado por processo."""
    if channel in _REGISTRY:
        return _REGISTRY[channel]
    if channel == "email":
        _REGISTRY[channel] = EmailDispatcher()
    elif channel == "webhook":
        _REGISTRY[channel] = WebhookDispatcher()
    elif channel == "sisbacen":
        _REGISTRY[channel] = SisbacenDispatcher()
    else:
        raise ValueError(f"unknown dispatcher channel: {channel!r}")
    return _REGISTRY[channel]


def _reset_registry_for_tests() -> None:
    """Limpa cache. Apenas pra fixtures de teste."""
    _REGISTRY.clear()


__all__ = [
    "DispatchResult",
    "EmailDispatcher",
    "RegulatoryDispatcher",
    "SisbacenDispatcher",
    "WebhookDispatcher",
    "get_dispatcher",
]
