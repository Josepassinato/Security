"""Application configuration for the Quarry Actions service.

Loaded once at import time from environment (and optional ``.env``). Two settings
matter for the ChatOps user-verification flow added in Wave 1:

* ``QUARRY_CREDENTIAL_KEY`` — the same Fernet key the API + connectors services
  use. We only need it when the action payload itself ships an encrypted
  ``vault:v1:`` token (e.g. a Slack bot token persisted by the click-and-connect
  connector flow). See ``app.security.credential_vault``.
* ``QUARRY_API_BASE_URL`` + ``QUARRY_API_SERVICE_TOKEN`` — used to call the
  ``services/api`` ``add_timeline_event`` endpoint when a ChatOps response lands.

We deliberately do **not** auto-generate credential keys here. The actions
service is internal infrastructure, so missing config should fail loud, not
silently invent ephemeral keys that would break decryption on restart.
"""

from __future__ import annotations

from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class ActionsSettings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore",
    )

    QUARRY_API_BASE_URL: str = Field(
        default="http://quarry-api:8000",
        description="Base URL of the services/api FastAPI app, e.g. http://quarry-api:8000.",
    )
    QUARRY_API_SERVICE_TOKEN: str = Field(
        default="",
        description=(
            "API-key token (aisoc_…) used by services/actions to call services/api "
            "endpoints that require cases:write. Mounted as a secret in production."
        ),
    )

    QUARRY_CREDENTIAL_KEY: str = Field(
        default="",
        description=(
            "Fernet key shared with services/api + services/connectors. Required "
            "only when an action payload contains a vault:v1: ciphertext."
        ),
    )
    QUARRY_CREDENTIAL_KEY_ROTATION_FROM: str = Field(
        default="",
        description="Comma-separated historical Fernet keys for transparent re-decryption.",
    )

    QUARRY_FEATURE_CHATOPS_VERIFY: bool = Field(
        default=True,
        description="Master toggle for the Slack/Teams interactive user-verification action.",
    )

    QUARRY_CHATOPS_RESPONSE_SECRET: str = Field(
        default="",
        description=("HMAC secret used to sign ChatOps response tokens so we can verify a callback genuinely came from a message we sent."),
    )

    QUARRY_CHATOPS_TIMEOUT_SECONDS: int = Field(
        default=900,
        description="How long a verification prompt stays valid (default 15 min).",
    )

    QUARRY_ACTIONS_PUBLIC_URL: str = Field(
        default="http://localhost:8003",
        description=(
            "Externally-reachable base URL of services/actions. Used to build the callback links embedded in ChatOps verification messages."
        ),
    )


@lru_cache(maxsize=1)
def get_settings() -> ActionsSettings:
    return ActionsSettings()
