"""YAML → ``EvidencePack`` loader.

Two entry points:

* :func:`load_pack` — read a single pack from a file path. Raises with
  a useful error message that an author can act on.
* :func:`load_packs_in_directory` — recursively load every ``*.yaml``
  file in a directory, returning the valid packs and a list of
  per-file errors. Use this from the compiler / API endpoint that
  serves the pack catalogue.

We deliberately *don't* swallow validation errors at the framework
level — a pack that fails to load is a pack that cannot be shipped to
an auditor. The caller decides whether to block startup, log a warning,
or surface a 5xx.
"""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Iterable

import yaml
from pydantic import ValidationError

from app.evidence_pack.schema import EvidencePack


# ---------------------------------------------------------------------------
# Errors
# ---------------------------------------------------------------------------


class EvidencePackError(Exception):
    """Base for pack-loading errors. ``path`` is the offending file."""

    def __init__(self, message: str, path: Path | str | None = None) -> None:
        super().__init__(message)
        self.path = Path(path) if path is not None else None


class EvidencePackParseError(EvidencePackError):
    """YAML failed to parse."""


class EvidencePackValidationError(EvidencePackError):
    """YAML parsed but did not match the schema."""


# ---------------------------------------------------------------------------
# Single-file loader
# ---------------------------------------------------------------------------


def load_pack(path: Path | str) -> EvidencePack:
    """Load and validate a single pack file.

    Args:
        path: Path to a ``*.yaml`` file.

    Returns:
        Validated :class:`EvidencePack`.

    Raises:
        EvidencePackParseError: YAML is malformed.
        EvidencePackValidationError: YAML parsed but failed schema
            validation. The wrapped Pydantic error is in ``__cause__``.
    """
    p = Path(path)
    try:
        raw = p.read_text(encoding="utf-8")
    except OSError as exc:
        raise EvidencePackError(f"could not read {p}: {exc}", path=p) from exc

    try:
        data = yaml.safe_load(raw)
    except yaml.YAMLError as exc:
        raise EvidencePackParseError(
            f"YAML parse error in {p}: {exc}", path=p
        ) from exc

    if not isinstance(data, dict):
        raise EvidencePackParseError(
            f"top-level YAML must be a mapping (got {type(data).__name__})",
            path=p,
        )

    try:
        return EvidencePack.model_validate(data)
    except ValidationError as exc:
        raise EvidencePackValidationError(
            f"schema validation failed for {p}:\n{exc}",
            path=p,
        ) from exc


# ---------------------------------------------------------------------------
# Directory loader
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class PackLoadResult:
    """Outcome of loading a directory of packs."""

    packs: list[EvidencePack]
    errors: list[EvidencePackError]


def load_packs_in_directory(directory: Path | str) -> PackLoadResult:
    """Load every ``*.yaml`` under ``directory`` (recursive).

    Returns successful packs and per-file errors separately, so the
    caller can decide policy: serve the valid ones and report on the
    broken ones, or fail closed.
    """
    base = Path(directory)
    if not base.is_dir():
        raise EvidencePackError(
            f"not a directory: {base}", path=base
        )

    packs: list[EvidencePack] = []
    errors: list[EvidencePackError] = []
    for yaml_path in sorted(_iter_yaml_files(base)):
        try:
            packs.append(load_pack(yaml_path))
        except EvidencePackError as exc:
            errors.append(exc)
    return PackLoadResult(packs=packs, errors=errors)


def _iter_yaml_files(base: Path) -> Iterable[Path]:
    yield from base.rglob("*.yaml")
    yield from base.rglob("*.yml")
