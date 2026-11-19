"""Proveedor de autenticacion FIEL para el portal 32-D."""

from __future__ import annotations

import httpx

from ...config import PortalConfig
from ...exceptions.auth import AuthenticationException, FielCredentialsException
from ...form_utils import extract_form
from ...services._portal import get_url
from ...value_objects.auth_result import AuthResult
from ...value_objects.fiel_credentials import FielCredentials
from ...value_objects.rfc import Rfc
from ..ports.auth_provider_port import AuthProviderPort
from ..ports.signer_port import SignerPort
from .nidp_login import NidpCertFormLogin
from .oidc_federation import OidcFederationHandler
from .signer import Signer


class FielAuthProvider(AuthProviderPort):
    """Autentica con e.firma siguiendo NIDP + federacion OIDC."""

    def __init__(
        self,
        credentials: FielCredentials,
        *,
        signer: SignerPort | None = None,
        login_id: str = "fiel",
        max_bootstrap_forms: int = 3,
        max_federation_forms: int = 10,
    ) -> None:
        self._signer = signer or Signer.load(credentials)
        self._login = NidpCertFormLogin(
            self._signer,
            login_id=login_id,
            max_bootstrap_forms=max_bootstrap_forms,
        )
        self._federation = OidcFederationHandler(max_forms=max_federation_forms)

    @property
    def name(self) -> str:
        return "fiel"

    @property
    def rfc(self) -> str:
        return Rfc(self._signer.rfc)

    async def authenticate(
        self,
        client: httpx.AsyncClient,
        portal: PortalConfig,
    ) -> AuthResult:
        if not self._signer.is_valid:
            raise FielCredentialsException(
                "El certificado de la FIEL esta vencido o aun no es valido."
            )

        response = await self._login.login(client, portal)
        response = await self._federation.follow(client, response)
        landing_url = str(response.url)

        if portal.verify_session:
            await self._verify_session(client, portal)

        return AuthResult(
            provider=self.name,
            authenticated=True,
            landing_url=landing_url,
            metadata={"rfc": self.rfc},
        )

    async def _verify_session(self, client: httpx.AsyncClient, portal: PortalConfig) -> None:
        response = await get_url(client, portal.entry_url)
        final_url = str(response.url)
        if (
            "/Cuenta/Login" in final_url
            or "/nidp/" in final_url
            or extract_form(response.text, form_id="certform") is not None
        ):
            raise AuthenticationException(
                "session",
                "El SAT devolvio el login despues de la federacion.",
            )
