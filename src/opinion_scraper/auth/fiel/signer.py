"""Adaptador de firma FIEL basado en `cryptography`."""

from __future__ import annotations

import base64
from datetime import UTC, datetime

from cryptography import x509
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import padding, rsa
from cryptography.x509.oid import NameOID

from ...exceptions.auth import FielCredentialsException
from ...value_objects.fiel_credentials import FielCredentials
from ..ports.signer_port import SignerPort


class Signer(SignerPort):
    """Carga `.cer` y `.key` en DER y expone las firmas del SAT."""

    def __init__(self, certificate: x509.Certificate, private_key: rsa.RSAPrivateKey) -> None:
        self._certificate = certificate
        self._private_key = private_key

    @classmethod
    def load(cls, credentials: FielCredentials, *, check: bool = True) -> Signer:
        try:
            certificate = x509.load_der_x509_certificate(credentials.certificate)
            private_key = serialization.load_der_private_key(
                credentials.key,
                password=credentials.password_value(),
            )
        except Exception as exc:
            raise FielCredentialsException(
                "No se pudo cargar el certificado o la llave privada de la FIEL."
            ) from exc

        if not isinstance(private_key, rsa.RSAPrivateKey):
            raise FielCredentialsException("La llave privada de la FIEL no es RSA.")

        if check and not _keys_match(certificate, private_key):
            raise FielCredentialsException(
                "La llave privada no corresponde al certificado de la FIEL."
            )
        return cls(certificate=certificate, private_key=private_key)

    @property
    def rfc(self) -> str:
        for oid in (NameOID.X500_UNIQUE_IDENTIFIER, NameOID.SERIAL_NUMBER):
            attributes = self._certificate.subject.get_attributes_for_oid(oid)
            if not attributes:
                continue
            value = str(attributes[0].value).split("/")[0].strip()
            if value:
                return value
        raise FielCredentialsException("El certificado no contiene el RFC del titular.")

    @property
    def certificate_number(self) -> str:
        return f"{self._certificate.serial_number:x}"[1::2]

    @property
    def fert(self) -> str:
        return self._certificate.not_valid_after_utc.strftime("%y%m%d%H%M%SZ")

    @property
    def is_valid(self) -> bool:
        now = datetime.now(UTC)
        return (
            self._certificate.not_valid_before_utc
            <= now
            <= self._certificate.not_valid_after_utc
        )

    def sign_sha1(self, data: bytes) -> str:
        signature = self._private_key.sign(data, padding.PKCS1v15(), hashes.SHA1())
        return base64.b64encode(signature).decode("ascii")

    def sign_sha256(self, data: bytes) -> str:
        signature = self._private_key.sign(data, padding.PKCS1v15(), hashes.SHA256())
        return base64.b64encode(signature).decode("ascii")


def _keys_match(certificate: x509.Certificate, private_key: rsa.RSAPrivateKey) -> bool:
    certificate_key = certificate.public_key().public_bytes(
        serialization.Encoding.DER,
        serialization.PublicFormat.SubjectPublicKeyInfo,
    )
    private_key_public = private_key.public_key().public_bytes(
        serialization.Encoding.DER,
        serialization.PublicFormat.SubjectPublicKeyInfo,
    )
    return certificate_key == private_key_public
