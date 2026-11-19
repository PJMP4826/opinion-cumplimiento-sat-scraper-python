"""Fabrica del cliente HTTP con cabeceras de navegador."""

from __future__ import annotations

import ssl
from collections.abc import Mapping

import httpx

from .tls import create_sat_ssl_context

DEFAULT_HEADERS: Mapping[str, str] = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/147.0.0.0 Safari/537.36"
    ),
    "Accept": (
        "text/html,application/xhtml+xml,application/xml;q=0.9,"
        "image/avif,image/webp,image/apng,*/*;q=0.8"
    ),
    "Accept-Language": "es-MX,es;q=0.9,en;q=0.7",
    "Cache-Control": "no-cache",
    "Pragma": "no-cache",
}

DEFAULT_TIMEOUT_SECONDS = 30.0
DEFAULT_CONNECT_TIMEOUT_SECONDS = 10.0


class SatHttpClientFactory:
    """Construye `httpx.AsyncClient` con la configuracion del SAT."""

    def __init__(
        self,
        headers: Mapping[str, str] | None = None,
        ssl_context: ssl.SSLContext | None = None,
    ) -> None:
        self._headers = dict(DEFAULT_HEADERS if headers is None else headers)
        self._ssl_context = ssl_context

    def create(
        self,
        *,
        trust_env: bool = False,
        timeout: float = DEFAULT_TIMEOUT_SECONDS,
    ) -> httpx.AsyncClient:
        ssl_context = self._ssl_context or create_sat_ssl_context()
        return httpx.AsyncClient(
            headers=self._headers,
            timeout=httpx.Timeout(timeout, connect=DEFAULT_CONNECT_TIMEOUT_SECONDS),
            follow_redirects=True,
            verify=ssl_context,
            trust_env=trust_env,
        )
