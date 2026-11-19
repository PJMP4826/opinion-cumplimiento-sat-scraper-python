"""Seguimiento de la federacion OIDC/SAML por formularios ocultos."""

from __future__ import annotations

from urllib.parse import urljoin

import httpx

from ...exceptions.auth import FederationException
from ...form_utils import FormExtractionResult, extract_form, extract_js_redirect
from ...services._portal import get_url, post_form

_FEDERATION_FIELDS = frozenset(
    {"SAMLResponse", "SAMLRequest", "RelayState", "code", "state", "id_token", "access_token"}
)
_FEDERATION_ACTION_HINTS = ("/saml", "/oauth", "/callback", "/acs", "/sso")


def _is_federation_form(form: FormExtractionResult) -> bool:
    if _FEDERATION_FIELDS.intersection(form.fields):
        return True
    action = (form.action or "").lower()
    return any(hint in action for hint in _FEDERATION_ACTION_HINTS)


class OidcFederationHandler:
    """Reenvia formularios `form_post` hasta que el portal deja de emitirlos."""

    def __init__(self, *, max_forms: int = 10) -> None:
        self._max_forms = max_forms

    async def follow(self, client: httpx.AsyncClient, response: httpx.Response) -> httpx.Response:
        response = await self._follow_js_redirect(client, response)
        for _ in range(self._max_forms):
            form = extract_form(response.text, base_url=str(response.url))
            if form is None or not _is_federation_form(form):
                return response
            action = form.action or str(response.url)
            response = await post_form(
                client,
                action,
                form.fields,
                referer=str(response.url),
            )
            response = await self._follow_js_redirect(client, response)
        if extract_form(response.text, base_url=str(response.url)) is None:
            return response
        raise FederationException(
            "La federacion no termino dentro del limite de formularios permitido."
        )

    async def _follow_js_redirect(
        self,
        client: httpx.AsyncClient,
        response: httpx.Response,
    ) -> httpx.Response:
        target = extract_js_redirect(response.text)
        if target is None:
            return response
        url = urljoin(str(response.url), target)
        return await get_url(client, url, referer=str(response.url))
