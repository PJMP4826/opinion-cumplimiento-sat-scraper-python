"""Login FIEL contra el formulario `certform` de Novell NIDP."""

from __future__ import annotations

import re

import httpx

from ...config import PortalConfig
from ...exceptions.auth import SatLoginException
from ...form_utils import extract_form
from ...services._portal import get_url, post_form
from ..ports.signer_port import SignerPort
from .token import generate_token

_LOGIN_ID_PATTERN = re.compile(r"([?&])id=[^&]*")


class NidpCertFormLogin:
    """Resuelve la cadena de formularios hasta firmar el `certform`."""

    def __init__(
        self,
        signer: SignerPort,
        *,
        login_id: str = "fiel",
        max_bootstrap_forms: int = 3,
    ) -> None:
        self._signer = signer
        self._login_id = login_id
        self._max_bootstrap_forms = max_bootstrap_forms

    async def login(self, client: httpx.AsyncClient, portal: PortalConfig) -> httpx.Response:
        response = await get_url(client, portal.entry_url)
        cert_form = extract_form(response.text, form_id="certform", base_url=str(response.url))

        attempts = 0
        while cert_form is None:
            if attempts >= self._max_bootstrap_forms:
                raise SatLoginException(
                    "No se encontro el formulario certform de la FIEL en el portal."
                )
            form = extract_form(response.text, base_url=str(response.url))
            if form is None:
                raise SatLoginException("No se encontro un formulario de login en el portal.")
            action = self._rewrite_login_id(form.action or str(response.url))
            response = await post_form(
                client,
                action,
                form.fields,
                referer=str(response.url),
            )
            cert_form = extract_form(
                response.text,
                form_id="certform",
                base_url=str(response.url),
            )
            attempts += 1

        guid = cert_form.fields.get("guid")
        if not guid:
            raise SatLoginException("El formulario certform no contiene el campo guid.")

        fields = dict(cert_form.fields)
        fields["token"] = generate_token(self._signer, guid)
        fields["fert"] = self._signer.fert
        action = cert_form.action or str(response.url)
        return await post_form(client, action, fields, referer=str(response.url))

    def _rewrite_login_id(self, action: str) -> str:
        if "nidp/app/login" not in action:
            return action
        return _LOGIN_ID_PATTERN.sub(rf"\1id={self._login_id}", action, count=1)
