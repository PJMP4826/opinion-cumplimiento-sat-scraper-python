"""Errores de autenticacion, red y formularios del portal SAT."""

from __future__ import annotations

from . import OpinionScraperException


class FielCredentialsException(OpinionScraperException):
    """La e.firma no pudo cargarse o no es consistente."""


class AuthenticationException(OpinionScraperException):
    """La autenticacion no llego a una sesion valida."""

    def __init__(self, stage: str, message: str | None = None) -> None:
        self.stage = stage
        self.detail = message
        super().__init__(f"Authentication failed at stage '{stage}': {message or 'unknown error'}")


class SatLoginException(AuthenticationException):
    """El formulario de login FIEL no esta disponible o no puede resolverse."""

    def __init__(self, message: str | None = None) -> None:
        super().__init__("login", message)


class FederationException(AuthenticationException):
    """La cadena de formularios SAML/OIDC no pudo completarse."""

    def __init__(self, message: str | None = None) -> None:
        super().__init__("federation", message)


class SatNetworkException(OpinionScraperException):
    """Fallo de transporte al comunicarse con el SAT."""

    def __init__(self, url: str, status_code: int | None = None) -> None:
        self.url = url
        self.status_code = status_code
        suffix = f" (HTTP {status_code})" if status_code is not None else ""
        super().__init__(f"Network error while requesting {url}{suffix}")


class SatFormNotFoundException(OpinionScraperException):
    """No se encontro el formulario HTML esperado en la respuesta del SAT."""
