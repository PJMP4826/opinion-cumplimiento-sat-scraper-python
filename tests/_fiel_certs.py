"""Fixtures de certificados FIEL autofirmados para pruebas."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime, timedelta

from cryptography import x509
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.x509.oid import NameOID

from opinion_scraper.value_objects import FielCredentials

DEFAULT_RFC = "PJMP482601AB1"


@dataclass(frozen=True, slots=True)
class FielFixture:
    certificate: bytes
    key: bytes
    password: str | None
    rfc: str
    serial_number: int

    def credentials(self) -> FielCredentials:
        return FielCredentials.from_bytes(
            certificate=self.certificate,
            key=self.key,
            password=self.password,
        )


def build_fiel(
    *,
    rfc: str = DEFAULT_RFC,
    password: str | None = None,
    serial_number: int = 0x1234567890,
    expired: bool = False,
) -> FielFixture:
    private_key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    subject = x509.Name(
        [
            x509.NameAttribute(NameOID.X500_UNIQUE_IDENTIFIER, f"{rfc} / CURPDEMO"),
            x509.NameAttribute(NameOID.COMMON_NAME, rfc),
        ]
    )
    now = datetime.now(UTC)
    if expired:
        not_before = now - timedelta(days=400)
        not_after = now - timedelta(days=1)
    else:
        not_before = now - timedelta(days=1)
        not_after = now + timedelta(days=365)

    certificate = (
        x509.CertificateBuilder()
        .subject_name(subject)
        .issuer_name(subject)
        .public_key(private_key.public_key())
        .serial_number(serial_number)
        .not_valid_before(not_before)
        .not_valid_after(not_after)
        .sign(private_key, hashes.SHA256())
    )
    encryption: serialization.KeySerializationEncryption
    if password is None:
        encryption = serialization.NoEncryption()
    else:
        encryption = serialization.BestAvailableEncryption(password.encode())

    return FielFixture(
        certificate=certificate.public_bytes(serialization.Encoding.DER),
        key=private_key.private_bytes(
            serialization.Encoding.DER,
            serialization.PrivateFormat.PKCS8,
            encryption,
        ),
        password=password,
        rfc=rfc,
        serial_number=serial_number,
    )
