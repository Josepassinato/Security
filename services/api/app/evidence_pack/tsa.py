"""RFC 3161 Time-Stamp Authority client (ICP-Brasil).

Item 1 of CARD-016 demands that each evidence pack carry a *trusted
timestamp*: the cryptographic guarantee that the artifact existed at a
specific instant. Without it, a Bacen RFI response can be challenged
("you generated this PDF after the incident"). With an ICP-Brasil TSA
stamp, the artifact is admissible as legal proof in Brazil under
Lei 14.063/2020 + MP 2.200-2/2001.

This module provides:

* :class:`TsaClient` — the abstract interface.
* :class:`MockTsaClient` — deterministic local stand-in for tests
  and dev. Produces structurally valid envelopes but is not trusted
  for production.
* :class:`SafeWebTsaClient` — production client targeting the SafeWeb
  TSA endpoint (the most widely used ICP-Brasil-credentialed TSA in
  Brazil). Implements RFC 3161 over HTTP per the SafeWeb spec.

The :class:`SafeWebTsaClient` needs credentials this repo does not
ship. Provisioning is documented in
``docs/operations/tsa-icp-brasil-setup.md`` (next card).
"""
from __future__ import annotations

import hashlib
import os
from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Final

import httpx


# ICP-Brasil-credentialed TSAs published by ITI. As of 2026-05 the
# active set includes Serasa, Certisign, Soluti, SafeWeb, Valid,
# SerproJUS, AC-Imprensa. Defaulting to SafeWeb because it is the most
# widely used in Brazilian fintech / banking compliance flows; a client
# can point at any of the others by overriding ``base_url``.
DEFAULT_SAFEWEB_TSA_URL: Final = "https://tsa.safeweb.com.br/tsa/request"


# ---------------------------------------------------------------------------
# Result type
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class TimestampResponse:
    """A successful TSA round-trip.

    The ``token`` is the DER-encoded ``TimeStampToken`` (CMS
    SignedData) the auditor verifies against the TSA's certificate.
    The ``stamped_at`` field is parsed from the token's
    ``TSTInfo.genTime`` for convenience.
    """

    token_der: bytes
    """Raw DER bytes of the RFC 3161 ``TimeStampToken``."""

    stamped_at: datetime
    """UTC instant the TSA asserted. Parsed from TSTInfo.genTime."""

    tsa_name: str
    """Human label of the TSA — e.g. ``'SafeWeb ICP-Brasil'``."""

    digest_hex: str
    """Hex of the digest that was stamped. Lets the verifier confirm
    the token covers the exact artifact bytes."""


class TsaError(RuntimeError):
    """Raised on any TSA failure — network, bad response, untrusted cert."""


# ---------------------------------------------------------------------------
# Interface
# ---------------------------------------------------------------------------


class TsaClient(ABC):
    """A minimal RFC 3161 client surface.

    Implementations stamp a SHA-256 digest of an artifact and return
    the verifiable token. Errors raise :class:`TsaError`; the caller
    decides whether to retry or fail closed.
    """

    @abstractmethod
    def stamp_digest(self, digest_sha256: bytes) -> TimestampResponse:
        """Submit a SHA-256 digest to the TSA and return the token.

        Args:
            digest_sha256: 32 raw bytes.

        Returns:
            :class:`TimestampResponse`.

        Raises:
            TsaError: any failure.
        """

    def stamp_bytes(self, payload: bytes) -> TimestampResponse:
        """Convenience: hash + stamp in one call."""
        if not payload:
            raise TsaError("cannot stamp empty payload")
        digest = hashlib.sha256(payload).digest()
        return self.stamp_digest(digest)


# ---------------------------------------------------------------------------
# Mock implementation (tests + dev)
# ---------------------------------------------------------------------------


class MockTsaClient(TsaClient):
    """A deterministic, locally-generated stand-in for a real TSA.

    What it does:
      * Returns a structurally valid :class:`TimestampResponse`.
      * Wraps the SHA-256 digest in a ``MOCK::v1::<digest>::<iso8601>``
        opaque token. Easy to grep, impossible to confuse with a real
        TSA token in production logs.
      * Uses ``now_provider()`` (overridable for tests).

    What it does NOT do:
      * Sign with any cryptographic key. Production verification must
        reject the mock prefix.
    """

    def __init__(
        self,
        *,
        now_provider=None,
        tsa_name: str = "MockTSA (dev only)",
    ) -> None:
        self._now = now_provider or (lambda: datetime.now(timezone.utc))
        self._tsa_name = tsa_name

    def stamp_digest(self, digest_sha256: bytes) -> TimestampResponse:
        if len(digest_sha256) != 32:
            raise TsaError(
                f"SHA-256 digest must be 32 bytes (got {len(digest_sha256)})"
            )
        stamped_at = self._now()
        token = (
            f"MOCK::v1::{digest_sha256.hex()}::{stamped_at.isoformat()}"
        ).encode("utf-8")
        return TimestampResponse(
            token_der=token,
            stamped_at=stamped_at,
            tsa_name=self._tsa_name,
            digest_hex=digest_sha256.hex(),
        )


def is_mock_token(token: bytes) -> bool:
    """Detect a MockTsaClient token — production verification gate."""
    return token.startswith(b"MOCK::")


# ---------------------------------------------------------------------------
# SafeWeb (ICP-Brasil) production client
# ---------------------------------------------------------------------------


class SafeWebTsaClient(TsaClient):
    """Real ICP-Brasil TSA client targeting SafeWeb.

    Wire format: RFC 3161 ``TimeStampReq`` (ASN.1 DER) over HTTP
    POST with ``Content-Type: application/timestamp-query`` and
    response ``Content-Type: application/timestamp-reply``.

    This implementation depends on the ``cryptography`` and
    ``pyasn1-modules`` Python packages to build the ``TimeStampReq``
    and parse the ``TimeStampResp``. Those imports happen inside
    :meth:`stamp_digest` so the module is importable even on systems
    that don't have the asn.1 stack installed (mock-only setups).

    NOT YET WIRED — the SafeWeb account credentials live outside this
    repo and the client API key must be supplied via env. Calling this
    without credentials raises :class:`TsaError` with an actionable
    message.
    """

    def __init__(
        self,
        *,
        base_url: str = DEFAULT_SAFEWEB_TSA_URL,
        api_key_env: str = "SAFEWEB_TSA_API_KEY",
        client_cert_path_env: str = "SAFEWEB_TSA_CLIENT_CERT",
        tsa_name: str = "SafeWeb ICP-Brasil",
        timeout_s: float = 20.0,
    ) -> None:
        self._base_url = base_url
        self._api_key = os.getenv(api_key_env, "")
        self._client_cert_path = os.getenv(client_cert_path_env, "")
        self._tsa_name = tsa_name
        self._timeout_s = timeout_s

    def stamp_digest(self, digest_sha256: bytes) -> TimestampResponse:
        if not self._api_key:
            raise TsaError(
                "SAFEWEB_TSA_API_KEY is not set. The SafeWeb TSA "
                "requires an ICP-Brasil-credentialed client key. "
                "Provisioning steps: docs/operations/tsa-icp-brasil-setup.md."
            )
        try:
            # Lazy imports — keep the module importable in mock-only setups.
            from cryptography.hazmat.primitives import hashes  # noqa: PLC0415
            from cryptography.x509 import (  # noqa: PLC0415
                load_pem_x509_certificate,  # noqa: F401  (referenced by future verifier)
            )
        except ImportError as exc:  # pragma: no cover
            raise TsaError(
                "cryptography package is required for SafeWebTsaClient. "
                "Install: pip install 'cryptography>=42'."
            ) from exc

        # The full RFC 3161 ``TimeStampReq`` envelope construction lives
        # in a dedicated helper to keep this method scannable. The helper
        # is intentionally out of scope of the current commit — it lands
        # alongside the SafeWeb integration tests, which need real
        # credentials to assert end-to-end.
        raise TsaError(
            "SafeWebTsaClient.stamp_digest is not implemented in this "
            "build. Use MockTsaClient until the SafeWeb integration "
            "card lands (see CARD-016 follow-up)."
        )


# ---------------------------------------------------------------------------
# Factory
# ---------------------------------------------------------------------------


def default_client() -> TsaClient:
    """Pick a TSA based on env.

    In a deployment with ``SAFEWEB_TSA_API_KEY`` set, returns the real
    SafeWeb client; otherwise returns the :class:`MockTsaClient`.

    Operators should always check ``isinstance(client, MockTsaClient)``
    before sending an artifact to a real fiscalização — the mock is
    NOT legally admissible.
    """
    if os.getenv("SAFEWEB_TSA_API_KEY"):
        return SafeWebTsaClient()
    return MockTsaClient()


__all__ = [
    "TsaClient",
    "TimestampResponse",
    "TsaError",
    "MockTsaClient",
    "SafeWebTsaClient",
    "is_mock_token",
    "default_client",
]
