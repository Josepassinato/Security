"""OpenSanctions API client — the list-of-record / version witness (G1).

Per the signed engine decision, OpenSanctions is the source-of-record for the
sanctions list version: it both screens the name and stamps the exact dataset
build it ran against, from the same source — so the version on the ledger is
always consistent with the match. ComplyAdvantage is a later matching-enrichment
layer, not the version witness.

Two calls:
* :meth:`match` — POST /match/{scope}: name → scored candidates (score 0..1).
* :meth:`dataset_version` — GET /catalog: the dataset's build version + release
  date (the "carimbo" that defends "against which build did you screen").

The API key is a credential: pass it in, never hardcode. Read it from
``settings.OPENSANCTIONS_API_KEY`` / ``OPENSANCTIONS_API_KEY`` at the edge.
"""
from __future__ import annotations

from typing import Any

import httpx

_DEFAULT_BASE = "https://api.opensanctions.org"


class OpenSanctionsError(RuntimeError):
    """Raised when the OpenSanctions API returns a non-success response."""


class OpenSanctionsClient:
    def __init__(
        self,
        api_key: str,
        *,
        base_url: str = _DEFAULT_BASE,
        timeout: float = 30.0,
    ) -> None:
        if not api_key:
            raise ValueError("OpenSanctions API key is required")
        self._base_url = base_url.rstrip("/")
        self._headers = {"Authorization": f"ApiKey {api_key}"}
        self._timeout = timeout

    async def match(
        self,
        name: str,
        *,
        scope: str = "us_ofac_sdn",
        schema: str = "Person",
        algorithm: str = "best",
    ) -> list[dict[str, Any]]:
        """Screen ``name`` against ``scope`` (a dataset like ``us_ofac_sdn`` or a
        collection like ``sanctions``). Returns scored candidates, best first."""
        payload = {"queries": {"q1": {"schema": schema, "properties": {"name": [name]}}}}
        async with httpx.AsyncClient(timeout=self._timeout) as client:
            resp = await client.post(
                f"{self._base_url}/match/{scope}",
                params={"algorithm": algorithm},
                headers=self._headers,
                json=payload,
            )
        if resp.status_code != 200:
            raise OpenSanctionsError(f"/match {resp.status_code}: {resp.text[:200]}")
        return resp.json().get("responses", {}).get("q1", {}).get("results", [])

    async def dataset_version(self, dataset: str = "us_ofac_sdn") -> tuple[str | None, str | None]:
        """Return ``(version, release_date_iso)`` for ``dataset`` — the build stamp."""
        async with httpx.AsyncClient(timeout=self._timeout) as client:
            resp = await client.get(f"{self._base_url}/catalog", headers=self._headers)
        if resp.status_code != 200:
            raise OpenSanctionsError(f"/catalog {resp.status_code}: {resp.text[:200]}")
        for ds in resp.json().get("datasets", []):
            if ds.get("name") == dataset:
                return ds.get("version"), (ds.get("last_export") or ds.get("updated_at"))
        raise OpenSanctionsError(f"dataset {dataset!r} not found in catalog")


__all__ = ["OpenSanctionsClient", "OpenSanctionsError"]
