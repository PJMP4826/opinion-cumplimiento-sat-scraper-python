"""Errores de value objects."""

from __future__ import annotations

from . import OpinionScraperException


class InvalidRfcException(OpinionScraperException, ValueError):
    """El RFC no tiene un formato valido."""
