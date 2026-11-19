"""Helpers de navegacion con cabeceras Origin/Referer."""

from __future__ import annotations

from collections.abc import Mapping
from urllib.parse import urlsplit

import httpx

from ..exceptions.auth import SatNetworkException


def origin_of(url: str) -> str:
    parts = urlsplit(url)
    return f"{parts.scheme}://{parts.netloc}"


def _navigation_headers(url: str, referer: str | None) -> dict[str, str]:
    reference = referer or url
    return {"Origin": origin_of(reference), "Referer": reference}


async def get_url(
    client: httpx.AsyncClient,
    url: str,
    *,
    referer: str | None = None,
) -> httpx.Response:
    try:
        response = await client.get(url, headers=_navigation_headers(url, referer))
    except httpx.HTTPError as exc:
        raise SatNetworkException(url) from exc
    _raise_for_status(response)
    return response


async def post_form(
    client: httpx.AsyncClient,
    url: str,
    fields: Mapping[str, str],
    *,
    referer: str | None = None,
) -> httpx.Response:
    try:
        response = await client.post(
            url,
            data=dict(fields),
            headers=_navigation_headers(url, referer),
        )
    except httpx.HTTPError as exc:
        raise SatNetworkException(url) from exc
    _raise_for_status(response)
    return response


def _raise_for_status(response: httpx.Response) -> None:
    if response.status_code >= 400:
        raise SatNetworkException(str(response.url), response.status_code)
