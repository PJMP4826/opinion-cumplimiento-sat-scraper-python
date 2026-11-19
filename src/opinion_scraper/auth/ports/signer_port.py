"""Puerto de firma con la llave privada de la FIEL."""

from __future__ import annotations

from abc import ABC, abstractmethod


class SignerPort(ABC):
    """Operaciones criptograficas requeridas por el flujo NIDP."""

    @property
    @abstractmethod
    def rfc(self) -> str:
        """RFC contenido en el certificado."""

    @property
    @abstractmethod
    def certificate_number(self) -> str:
        """Numero de serie en el formato que espera el SAT."""

    @property
    @abstractmethod
    def fert(self) -> str:
        """Fecha de expiracion del certificado en formato `YYMMDDHHMMSSZ`."""

    @property
    @abstractmethod
    def is_valid(self) -> bool:
        """Indica si el certificado esta vigente en este momento."""

    @abstractmethod
    def sign_sha1(self, data: bytes) -> str:
        """Firma RSA PKCS#1 v1.5 con SHA-1, codificada en base64."""

    @abstractmethod
    def sign_sha256(self, data: bytes) -> str:
        """Firma RSA PKCS#1 v1.5 con SHA-256, codificada en base64."""
