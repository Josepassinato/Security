"""Tests for regulatory_dispatch adapters.

Cobre o que é testável sem rede:
- ``SisbacenDispatcher`` sempre retorna ``ok=False`` com mensagem clara
  (stub explícito até API pública existir).
- ``get_dispatcher`` resolve cada channel pra classe correta e
  cacheia por processo.
- ``DispatchResult.to_jsonable`` é serializável.
- ``EmailDispatcher`` rejeita config ausente sem panicar.
- ``WebhookDispatcher`` rejeita target vazio sem panicar.
"""

from __future__ import annotations

import json

import pytest

from app.services.regulatory_dispatch import (
    DispatchResult,
    EmailDispatcher,
    RegulatoryDispatcher,
    SisbacenDispatcher,
    WebhookDispatcher,
    _reset_registry_for_tests,
    get_dispatcher,
)


@pytest.fixture(autouse=True)
def _clean_registry():
    _reset_registry_for_tests()
    yield
    _reset_registry_for_tests()


@pytest.mark.asyncio
async def test_sisbacen_dispatcher_returns_not_implemented_clearly():
    d = SisbacenDispatcher()
    r = await d.send(subject="t", body_md="body", target="anything")
    assert r.ok is False
    assert r.channel == "sisbacen"
    assert "sisbacen_api_unavailable" in r.detail
    # Mensagem deve mencionar alternativa (email)
    assert "email" in r.detail.lower()


@pytest.mark.asyncio
async def test_email_dispatcher_without_host_returns_smtp_error():
    d = EmailDispatcher(host="", port=465)
    r = await d.send(subject="t", body_md="b", target="x@y.com")
    assert r.ok is False
    assert "smtp_error" in r.detail


@pytest.mark.asyncio
async def test_webhook_dispatcher_without_url_returns_missing_url():
    d = WebhookDispatcher(default_url="")
    r = await d.send(subject="t", body_md="b", target="")
    assert r.ok is False
    assert r.detail == "missing_url"


def test_get_dispatcher_returns_correct_class_and_caches():
    a1 = get_dispatcher("sisbacen")
    a2 = get_dispatcher("sisbacen")
    assert a1 is a2  # cached
    assert isinstance(a1, SisbacenDispatcher)
    assert isinstance(get_dispatcher("email"), EmailDispatcher)
    assert isinstance(get_dispatcher("webhook"), WebhookDispatcher)


def test_get_dispatcher_unknown_channel_raises():
    with pytest.raises(ValueError):
        get_dispatcher("carrierpigeon")


def test_dispatch_result_is_jsonable():
    r = DispatchResult(
        ok=True,
        channel="email",
        target="dpo@x.com",
        detail="sent",
        provider_response={"refused": {}},
    )
    payload = r.to_jsonable()
    blob = json.dumps(payload)
    parsed = json.loads(blob)
    assert parsed["ok"] is True
    assert parsed["channel"] == "email"
    assert parsed["provider_response"]["refused"] == {}


def test_registry_subclass_contract():
    # Sanity: todo dispatcher precisa ter ``channel`` definido como str
    for ch in ("email", "webhook", "sisbacen"):
        d = get_dispatcher(ch)
        assert isinstance(d, RegulatoryDispatcher)
        assert d.channel == ch
