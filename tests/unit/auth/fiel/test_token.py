from __future__ import annotations

import base64

from cryptography import x509
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.asymmetric import padding

from opinion_scraper.auth.fiel import Signer, generate_token
from tests._fiel_certs import build_fiel


def test_generate_token_matches_sat_format() -> None:
    fixture = build_fiel()
    signer = Signer.load(fixture.credentials())

    token = generate_token(signer, "guid-123")

    outer = base64.b64decode(token)
    payload, signature = outer.split(b"#", 1)
    content = base64.b64decode(payload)
    assert content == b"guid-123|PJMP482601AB1|24680"

    public_key = x509.load_der_x509_certificate(fixture.certificate).public_key()
    public_key.verify(
        base64.b64decode(base64.b64decode(signature)),
        content,
        padding.PKCS1v15(),
        hashes.SHA1(),
    )
