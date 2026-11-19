"""Resultado de una autenticacion exitosa."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass, field


@dataclass(frozen=True, slots=True)
class AuthResult:
    """Sesion autenticada lista para consultar el portal."""

    provider: str
    authenticated: bool
    landing_url: str
    metadata: Mapping[str, str] = field(default_factory=dict)
