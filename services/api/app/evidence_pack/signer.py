"""e-CNPJ / PKCS#7 detached signature for evidence artifacts.

The pipeline:

  evidence pack runtime    →  rendered PDF (renderer.py)
                                 │
                                 ▼
                          SHA-256 digest
                                 │
                                 ▼
                         RFC 3161 timestamp  (tsa.py)
                                 │
                                 ▼
                      PKCS#7 signature here  (signer.py)
                                 │
                                 ▼
              auditor-ready bundle (PDF + token + signature)

The signature is **detached** — we don't embed it inside the PDF
(though we can in a follow-up: PDF can carry CMS signatures natively
under ISO 32000-2). For the first cut we ship a sidecar ``.p7s``
because it is simpler to verify with stock OpenSSL on the auditor's
side and works for any artifact type, not only PDF.

This module mirrors the TSA module shape: an abstract base, a mock
implementation for tests/dev, and a real implementation that needs an
e-CNPJ certificate (PKCS#12 file) the repository does not ship.
"""
from __future__ import annotations

import hashlib
import hmac
import os
from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Final


# ---------------------------------------------------------------------------
# Result type
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class SignatureResult:
    """A detached signature over an artifact."""

    signature_der: bytes
    """DER-encoded CMS SignedData (PKCS#7) bytes. The sidecar ``.p7s``."""

    signed_at: datetime
    """UTC instant the signer asserts the artifact was signed."""

    signer_subject: str
    """Subject DN of the e-CNPJ cert that signed — for the audit
    appendix. e.g. ``'CN=INCREASE TRAINER INC:00.000.000/0001-00, OU=...'``."""

    digest_algorithm: str
    """``'SHA-256'`` always, for now."""

    digest_hex: str
    """Hex of the artifact digest the signature covers."""


class SignerError(RuntimeError):
    """Signing failure — bad cert, expired, key locked, etc."""


# ---------------------------------------------------------------------------
# Interface
# ---------------------------------------------------------------------------


class ArtifactSigner(ABC):
    """A minimal detached-signature surface."""

    @abstractmethod
    def sign_digest(self, digest_sha256: bytes) -> SignatureResult:
        """Sign a SHA-256 digest, return the detached CMS bytes.

        Args:
            digest_sha256: 32 raw bytes.
        """

    def sign_bytes(self, payload: bytes) -> SignatureResult:
        """Convenience: hash + sign in one call."""
        if not payload:
            raise SignerError("cannot sign empty payload")
        return self.sign_digest(hashlib.sha256(payload).digest())


# ---------------------------------------------------------------------------
# Mock implementation
# ---------------------------------------------------------------------------


_MOCK_HMAC_KEY: Final = b"quarry-dev-mock-signer-key-not-secret"


class MockSigner(ArtifactSigner):
    """Deterministic local signer for tests + dev.

    Uses HMAC-SHA-256 with a fixed key as a "signature" so:

      * The output is reproducible in tests.
      * The format clearly identifies as mock (``MOCK::SIG::v1::...``).
      * Production verification can refuse mock signatures by prefix.

    NOT cryptographically meaningful. NOT a substitute for an
    ICP-Brasil e-CNPJ signature.
    """

    def __init__(
        self,
        *,
        signer_subject: str = "CN=MOCK SIGNER (dev only), O=Quarry, C=BR",
        now_provider=None,
    ) -> None:
        self._subject = signer_subject
        self._now = now_provider or (lambda: datetime.now(timezone.utc))

    def sign_digest(self, digest_sha256: bytes) -> SignatureResult:
        if len(digest_sha256) != 32:
            raise SignerError(
                f"SHA-256 digest must be 32 bytes (got {len(digest_sha256)})"
            )
        signed_at = self._now()
        mac = hmac.new(_MOCK_HMAC_KEY, digest_sha256, hashlib.sha256).digest()
        envelope = (
            b"MOCK::SIG::v1::"
            + digest_sha256.hex().encode("ascii")
            + b"::"
            + signed_at.isoformat().encode("ascii")
            + b"::"
            + mac.hex().encode("ascii")
        )
        return SignatureResult(
            signature_der=envelope,
            signed_at=signed_at,
            signer_subject=self._subject,
            digest_algorithm="SHA-256",
            digest_hex=digest_sha256.hex(),
        )


def is_mock_signature(signature: bytes) -> bool:
    """Detect a MockSigner envelope — production must refuse these."""
    return signature.startswith(b"MOCK::SIG::")


# ---------------------------------------------------------------------------
# Real e-CNPJ PKCS#12 signer (interface only)
# ---------------------------------------------------------------------------


class ECNPJPkcs12Signer(ArtifactSigner):
    """PKCS#7 detached signer using an ICP-Brasil e-CNPJ PKCS#12 cert.

    The certificate path is read from ``ECNPJ_PKCS12_PATH`` and the
    password from ``ECNPJ_PKCS12_PASSWORD``. Both are required.

    Implementation status: **interface only**. The actual PKCS#7
    SignedData construction with cryptography / asn1crypto lands in the
    follow-up card that wires SafeWeb TSA and signing end-to-end in
    production. Until then this class raises :class:`SignerError` with
    actionable guidance.
    """

    def __init__(
        self,
        *,
        pkcs12_path_env: str = "ECNPJ_PKCS12_PATH",
        password_env: str = "ECNPJ_PKCS12_PASSWORD",
    ) -> None:
        self._pkcs12_path = os.getenv(pkcs12_path_env, "")
        self._password = os.getenv(password_env, "")

    def sign_digest(self, digest_sha256: bytes) -> SignatureResult:
        if not self._pkcs12_path:
            raise SignerError(
                "ECNPJ_PKCS12_PATH is not set. The e-CNPJ signer "
                "requires a valid PKCS#12 from an ICP-Brasil-credentialed "
                "AC (Serasa, Certisign, Soluti, ...). Use MockSigner for "
                "dev and tests."
            )
        if not Path(self._pkcs12_path).is_file():
            raise SignerError(f"e-CNPJ PKCS#12 not found: {self._pkcs12_path}")
        if not self._password:
            raise SignerError("ECNPJ_PKCS12_PASSWORD is not set.")
        raise SignerError(
            "ECNPJPkcs12Signer.sign_digest is not implemented in this "
            "build. Use MockSigner until the e-CNPJ integration card lands."
        )


# ---------------------------------------------------------------------------
# Factory
# ---------------------------------------------------------------------------


def default_signer() -> ArtifactSigner:
    """Pick a signer based on env.

    Returns :class:`ECNPJPkcs12Signer` if an e-CNPJ PKCS#12 is configured;
    otherwise falls back to :class:`MockSigner`.

    Operators MUST gate production exports on
    ``not is_mock_signature(result.signature_der)``.
    """
    if os.getenv("ECNPJ_PKCS12_PATH"):
        return ECNPJPkcs12Signer()
    return MockSigner()


__all__ = [
    "ArtifactSigner",
    "SignatureResult",
    "SignerError",
    "MockSigner",
    "ECNPJPkcs12Signer",
    "is_mock_signature",
    "default_signer",
]
