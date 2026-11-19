"""Fachada para descargar la Opinion de Cumplimiento 32-D."""

from __future__ import annotations

import asyncio
from types import TracebackType

import httpx

from .auth.fiel.provider import FielAuthProvider
from .auth.ports.auth_provider_port import AuthProviderPort
from .config import DEFAULT_32D, PortalConfig
from .exceptions.auth import FielCredentialsException
from .http.client_factory import SatHttpClientFactory
from .services.opinion_document_service import OpinionDocumentService
from .value_objects.fiel_credentials import FielCredentials
from .value_objects.opinion_pdf import OpinionPdf
from .value_objects.rfc import Rfc


class OpinionDownloader:
    """Orquesta autenticacion FIEL y descarga del PDF 32-D."""

    def __init__(
        self,
        auth_provider: AuthProviderPort,
        client: httpx.AsyncClient,
        *,
        portal: PortalConfig = DEFAULT_32D,
        document_service: OpinionDocumentService | None = None,
        owns_client: bool = False,
    ) -> None:
        self._auth_provider = auth_provider
        self._client = client
        self._portal = portal
        self._document_service = document_service or OpinionDocumentService(portal)
        self._owns_client = owns_client

    @classmethod
    def create(
        cls,
        *,
        credentials: FielCredentials | None = None,
        auth_provider: AuthProviderPort | None = None,
        client: httpx.AsyncClient | None = None,
        portal: PortalConfig = DEFAULT_32D,
    ) -> OpinionDownloader:
        if auth_provider is not None and credentials is not None:
            raise ValueError("Proporciona credentials o auth_provider, no ambos.")
        if auth_provider is None:
            if credentials is None:
                raise ValueError("Se requieren credentials o auth_provider.")
            auth_provider = FielAuthProvider(
                credentials,
                login_id=portal.login_id,
                max_bootstrap_forms=portal.max_bootstrap_forms,
                max_federation_forms=portal.max_federation_forms,
            )

        owns_client = client is None
        if client is None:
            client = SatHttpClientFactory().create(
                trust_env=portal.trust_env,
                timeout=portal.timeout_seconds,
            )
        return cls(
            auth_provider,
            client,
            portal=portal,
            owns_client=owns_client,
        )

    @property
    def rfc(self) -> str:
        return self._auth_provider.rfc

    async def download(self, rfc: str | None = None) -> OpinionPdf:
        expected_rfc = Rfc(self._auth_provider.rfc)
        requested_rfc = expected_rfc if rfc is None else Rfc(rfc)
        if requested_rfc != expected_rfc:
            raise FielCredentialsException(
                "El RFC solicitado no corresponde al certificado de la FIEL."
            )
        try:
            auth_result = await self._auth_provider.authenticate(self._client, self._portal)
            return await self._document_service.download(
                self._client,
                str(requested_rfc),
                referer=auth_result.landing_url,
            )
        finally:
            self._client.cookies.clear()

    def download_sync(self, rfc: str | None = None) -> OpinionPdf:
        return asyncio.run(self.download(rfc))

    async def aclose(self) -> None:
        if self._owns_client:
            await self._client.aclose()

    async def __aenter__(self) -> OpinionDownloader:
        return self

    async def __aexit__(
        self,
        exc_type: type[BaseException] | None,
        exc: BaseException | None,
        traceback: TracebackType | None,
    ) -> None:
        await self.aclose()
