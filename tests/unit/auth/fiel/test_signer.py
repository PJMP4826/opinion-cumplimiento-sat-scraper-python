from __future__ import annotations

import base64

import pytest
from cryptography import x509
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.asymmetric import padding

from opinion_scraper.auth.fiel import Signer
from opinion_scraper.exceptions import FielCredentialsException
from opinion_scraper.value_objects import FielCredentials
from tests._fiel_certs import DEFAULT_RFC, build_fiel


def test_signer_exposes_sat_fields() -> None:
    fixture = build_fiel()
    signer = Signer.load(fixture.credentials())

    assert signer.rfc == DEFAULT_RFC
    assert signer.certificate_number == "24680"
    assert len(signer.fert) == 13
    assert signer.fert.endswith("Z")
    assert signer.is_valid is True


def test_signer_loads_encrypted_key() -> None:
    fixture = build_fiel(password="secreto")

    signer = Signer.load(fixture.credentials())

    assert signer.rfc == DEFAULT_RFC


def test_signer_rejects_wrong_password() -> None:
    fixture = build_fiel(password="correcto")
    credentials = FielCredentials.from_bytes(
        certificate=fixture.certificate,
        key=fixture.key,
        password="incorrecto",
    )

    with pytest.raises(FielCredentialsException):
        Signer.load(credentials)


def test_signer_rejects_mismatched_key() -> None:
    first = build_fiel(serial_number=1)
    second = build_fiel(serial_number=2)
    credentials = FielCredentials.from_bytes(first.certificate, second.key)

    with pytest.raises(FielCredentialsException):
        Signer.load(credentials)


def test_signer_rejects_invalid_der() -> None:
    credentials = FielCredentials.from_bytes(b"no-cert", b"no-key")

    with pytest.raises(FielCredentialsException):
        Signer.load(credentials)


def test_expired_certificate_is_not_valid() -> None:
    signer = Signer.load(build_fiel(expired=True).credentials())

    assert signer.is_valid is False


def test_signatures_are_verifiable() -> None:
    fixture = build_fiel()
    signer = Signer.load(fixture.credentials())
    public_key = x509.load_der_x509_certificate(fixture.certificate).public_key()
    data = b"contenido a firmar"

    sha1_signature = base64.b64decode(signer.sign_sha1(data))
    sha256_signature = base64.b64decode(signer.sign_sha256(data))

    public_key.verify(sha1_signature, data, padding.PKCS1v15(), hashes.SHA1())
    public_key.verify(sha256_signature, data, padding.PKCS1v15(), hashes.SHA256())
