"""Tests for OIDC id_token signature + claim verification.

Regression coverage for the hardening that replaced
``jwt.decode(..., {"verify_signature": False})`` with real JWKS-based
verification in ``app.auth.oidc``. These exercise the pure verification helper
(``_verify_id_token``) directly so they need no network and no full app import.
"""

from __future__ import annotations

import asyncio
import base64
import time

import jwt as _jwt
import pytest
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import rsa

from app.auth import oidc

ISSUER = "https://idp.example.test"
CLIENT_ID = "quarry-client"
KID = "test-kid-1"


def _b64u(n: int) -> str:
    raw = n.to_bytes((n.bit_length() + 7) // 8, "big")
    return base64.urlsafe_b64encode(raw).rstrip(b"=").decode()


def _rsa_keypair():
    priv = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    pem = priv.private_bytes(
        serialization.Encoding.PEM,
        serialization.PrivateFormat.PKCS8,
        serialization.NoEncryption(),
    )
    nums = priv.public_key().public_numbers()
    jwk = {"kty": "RSA", "kid": KID, "use": "sig", "alg": "RS256",
           "n": _b64u(nums.n), "e": _b64u(nums.e)}
    return pem, jwk


# Signing key advertised in the JWKS, plus an *attacker* key that is not.
_GOOD_PEM, _GOOD_JWK = _rsa_keypair()
_EVIL_PEM, _ = _rsa_keypair()
_JWK_SET = _jwt.PyJWKSet.from_dict({"keys": [_GOOD_JWK]})

_PROVIDER = {
    "issuer": ISSUER,
    "jwks_uri": "https://idp.example.test/jwks",
    "id_token_signing_alg_values_supported": ["RS256"],
}


def _make_token(pem: str, *, aud=CLIENT_ID, iss=ISSUER, nonce="nonce-1",
                exp_delta=300, kid=KID) -> str:
    now = int(time.time())
    return _jwt.encode(
        {"sub": "user-1", "email": "u@example.test", "aud": aud, "iss": iss,
         "nonce": nonce, "iat": now, "exp": now + exp_delta},
        pem, algorithm="RS256", headers={"kid": kid},
    )


@pytest.fixture(autouse=True)
def _patch_jwks(monkeypatch):
    async def _fake_get_jwk_set(provider, issuer, *, force=False):
        return _JWK_SET if provider.get("jwks_uri") else None
    monkeypatch.setattr(oidc, "_get_jwk_set", _fake_get_jwk_set)


def _verify(token: str, *, nonce="nonce-1"):
    return asyncio.run(
        oidc._verify_id_token(_PROVIDER, ISSUER, token, CLIENT_ID, nonce)
    )


def test_valid_token_returns_claims():
    claims = _verify(_make_token(_GOOD_PEM))
    assert claims["sub"] == "user-1"
    assert claims["email"] == "u@example.test"


def test_token_signed_by_unknown_key_is_rejected():
    # Attacker forges a token with their own key (not in the JWKS).
    with pytest.raises(_jwt.InvalidSignatureError):
        _verify(_make_token(_EVIL_PEM))


def test_wrong_audience_is_rejected():
    with pytest.raises(_jwt.InvalidAudienceError):
        _verify(_make_token(_GOOD_PEM, aud="some-other-client"))


def test_wrong_issuer_is_rejected():
    with pytest.raises(_jwt.InvalidIssuerError):
        _verify(_make_token(_GOOD_PEM, iss="https://evil.test"))


def test_expired_token_is_rejected():
    with pytest.raises(_jwt.ExpiredSignatureError):
        _verify(_make_token(_GOOD_PEM, exp_delta=-10))


def test_nonce_mismatch_is_rejected():
    with pytest.raises(_jwt.InvalidTokenError):
        _verify(_make_token(_GOOD_PEM, nonce="attacker-nonce"))


def test_alg_none_downgrade_is_rejected():
    # Unsigned ("alg":"none") token must never be accepted.
    now = int(time.time())
    unsigned = _jwt.encode(
        {"sub": "user-1", "aud": CLIENT_ID, "iss": ISSUER, "nonce": "nonce-1",
         "iat": now, "exp": now + 300},
        key="", algorithm="none",
    )
    with pytest.raises(_jwt.PyJWTError):
        _verify(unsigned)


def test_missing_jwks_uri_fails_closed():
    provider = {"issuer": ISSUER, "id_token_signing_alg_values_supported": ["RS256"]}
    with pytest.raises(oidc.HTTPException) as exc:
        asyncio.run(
            oidc._verify_id_token(provider, ISSUER, _make_token(_GOOD_PEM),
                                  CLIENT_ID, "nonce-1")
        )
    assert exc.value.status_code == 502
