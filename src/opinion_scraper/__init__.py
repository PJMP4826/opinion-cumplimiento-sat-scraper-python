"""Descarga de la Opinion de Cumplimiento del SAT (32-D) con FIEL."""

from __future__ import annotations

from .config import DEFAULT_32D, PortalConfig
from .exceptions import (
    AuthenticationException,
    FederationException,
    FielCredentialsException,
    InvalidOpinionResponseException,
    InvalidPdfException,
    InvalidRfcException,
    OpinionNotAvailableException,
    OpinionScraperException,
    SatFormNotFoundException,
    SatLoginException,
    SatNetworkException,
)
from .value_objects import AuthResult, FielCredentials, OpinionPdf, Rfc

__version__ = "0.1.0"

__all__ = [
    "DEFAULT_32D",
    "AuthResult",
    "AuthenticationException",
    "FederationException",
    "FielCredentials",
    "FielCredentialsException",
    "InvalidOpinionResponseException",
    "InvalidPdfException",
    "InvalidRfcException",
    "OpinionDownloader",
    "OpinionNotAvailableException",
    "OpinionPdf",
    "OpinionScraperException",
    "PortalConfig",
    "Rfc",
    "SatFormNotFoundException",
    "SatLoginException",
    "SatNetworkException",
    "__version__",
]


def __getattr__(name: str) -> object:
    if name == "OpinionDownloader":
        from importlib import import_module

        module = import_module(".downloader", __name__)
        return module.OpinionDownloader
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
