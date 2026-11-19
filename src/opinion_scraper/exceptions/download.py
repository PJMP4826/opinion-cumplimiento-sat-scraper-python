"""Errores del documento de Opinion de Cumplimiento (32-D)."""

from __future__ import annotations

from . import OpinionScraperException


class InvalidOpinionResponseException(OpinionScraperException):
    """La respuesta del portal 32-D no tiene la estructura esperada."""


class OpinionNotAvailableException(OpinionScraperException):
    """El SAT respondio que la opinion no esta disponible."""

    def __init__(self, codigo: str | None = None, mensaje: str | None = None) -> None:
        self.codigo = codigo
        self.mensaje = mensaje
        detail = mensaje or "sin mensaje de error"
        if codigo:
            detail = f"[{codigo}] {detail}"
        super().__init__(f"El SAT no entrego la opinion de cumplimiento: {detail}")


class InvalidPdfException(OpinionScraperException):
    """El contenido descargado no es un PDF valido."""
