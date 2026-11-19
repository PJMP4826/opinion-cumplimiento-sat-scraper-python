"""Excepciones publicas de la libreria."""

from __future__ import annotations


class OpinionScraperException(Exception):
    """Excepcion base de todos los errores de la libreria."""


from .auth import (  # noqa: E402
    AuthenticationException,
    FederationException,
    FielCredentialsException,
    SatFormNotFoundException,
    SatLoginException,
    SatNetworkException,
)
from .download import (  # noqa: E402
    InvalidOpinionResponseException,
    InvalidPdfException,
    OpinionNotAvailableException,
)
from .value_objects import InvalidRfcException  # noqa: E402

__all__ = [
    "AuthenticationException",
    "FederationException",
    "FielCredentialsException",
    "InvalidOpinionResponseException",
    "InvalidPdfException",
    "InvalidRfcException",
    "OpinionNotAvailableException",
    "OpinionScraperException",
    "SatFormNotFoundException",
    "SatLoginException",
    "SatNetworkException",
]
