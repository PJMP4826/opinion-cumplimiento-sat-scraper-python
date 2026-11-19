"""Credenciales de e.firma / FIEL."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from pydantic import SecretStr

from ..exceptions.auth import FielCredentialsException


@dataclass(frozen=True, slots=True)
class FielCredentials:
    """Contenedor inmutable de `.cer`, `.key` y contrasena de la FIEL."""

    certificate: bytes
    key: bytes
    password: SecretStr | None = None

    def __post_init__(self) -> None:
        if not self.certificate:
            raise FielCredentialsException("El certificado de la FIEL esta vacio.")
        if not self.key:
            raise FielCredentialsException("La llave privada de la FIEL esta vacia.")

    @classmethod
    def from_bytes(
        cls,
        certificate: bytes,
        key: bytes,
        password: str | None = None,
    ) -> FielCredentials:
        return cls(
            certificate=certificate,
            key=key,
            password=SecretStr(password) if password is not None else None,
        )

    @classmethod
    def from_files(
        cls,
        certificate_path: str | Path,
        key_path: str | Path,
        password: str | None = None,
    ) -> FielCredentials:
        certificate = Path(certificate_path).read_bytes()
        key = Path(key_path).read_bytes()
        return cls.from_bytes(certificate=certificate, key=key, password=password)

    def password_value(self) -> bytes | None:
        if self.password is None:
            return None
        return self.password.get_secret_value().encode()
