"""Puerto de proveedores de autenticacion del SAT."""

from __future__ import annotations

from abc import ABC, abstractmethod

import httpx

from ...config import PortalConfig
from ...value_objects.auth_result import AuthResult


class AuthProviderPort(ABC):
    """Contrato que debe cumplir todo proveedor de autenticacion."""

    @property
    @abstractmethod
    def name(self) -> str:
        """Identificador del proveedor (por ejemplo `fiel`)."""

    @property
    @abstractmethod
    def rfc(self) -> str:
        """RFC del contribuyente autenticado."""

    @abstractmethod
    async def authenticate(
        self,
        client: httpx.AsyncClient,
        portal: PortalConfig,
    ) -> AuthResult:
        """Autentica el cliente HTTP y devuelve la sesion lista para el portal."""
