"""Tests for ``app.core.config``."""

from __future__ import annotations

import importlib

import pytest


@pytest.fixture(autouse=True)
def _reset_settings_cache(monkeypatch: pytest.MonkeyPatch):
    """
    ``get_settings`` is cached; each test needs a fresh import so the env
    overrides actually take effect.
    """
    from app.core import config as config_module

    config_module.get_settings.cache_clear()
    yield
    config_module.get_settings.cache_clear()


def test_defaults_are_safe_for_local_dev(monkeypatch: pytest.MonkeyPatch):
    """
    With no env vars set, the bot must still import — but signature
    verification must be disabled so we never accept unsigned Slack requests
    in production by accident.
    """
    for var in (
        "SLACK_BOT_TOKEN",
        "SLACK_SIGNING_SECRET",
        "QUARRY_API_SERVICE_TOKEN",
        "QUARRY_ACTIONS_SERVICE_TOKEN",
    ):
        monkeypatch.delenv(var, raising=False)

    from app.core.config import get_settings

    settings = get_settings()
    assert settings.SLACK_BOT_TOKEN == ""
    assert settings.SLACK_SIGNING_SECRET == ""
    assert settings.signature_verification_enabled is False
    assert settings.QUARRY_API_BASE_URL.startswith("http")
    assert settings.QUARRY_ACTIONS_BASE_URL.startswith("http")
    assert settings.QUARRY_SLACK_BOT_PORT == 8089


def test_env_overrides_take_effect(monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setenv("SLACK_BOT_TOKEN", "xoxb-test-1234")
    monkeypatch.setenv("SLACK_SIGNING_SECRET", "shhh")
    monkeypatch.setenv("QUARRY_API_BASE_URL", "http://api.local:9000")
    monkeypatch.setenv("QUARRY_ACTIONS_BASE_URL", "http://actions.local:9001")
    monkeypatch.setenv("QUARRY_API_SERVICE_TOKEN", "aisoc_api_key")
    monkeypatch.setenv("QUARRY_ACTIONS_SERVICE_TOKEN", "aisoc_actions_key")
    monkeypatch.setenv("QUARRY_DEFAULT_TENANT_ID", "11111111-2222-3333-4444-555555555555")
    monkeypatch.setenv("QUARRY_SLACK_BOT_PORT", "9090")

    from app.core import config as config_module

    importlib.reload(config_module)

    settings = config_module.get_settings()
    assert settings.SLACK_BOT_TOKEN == "xoxb-test-1234"
    assert settings.SLACK_SIGNING_SECRET == "shhh"
    assert settings.signature_verification_enabled is True
    assert settings.QUARRY_API_BASE_URL == "http://api.local:9000"
    assert settings.QUARRY_ACTIONS_BASE_URL == "http://actions.local:9001"
    assert settings.QUARRY_API_SERVICE_TOKEN == "aisoc_api_key"
    assert settings.QUARRY_ACTIONS_SERVICE_TOKEN == "aisoc_actions_key"
    assert settings.QUARRY_DEFAULT_TENANT_ID == "11111111-2222-3333-4444-555555555555"
    assert settings.QUARRY_SLACK_BOT_PORT == 9090
