"""Generacion del token que consume el formulario NIDP del SAT."""

from __future__ import annotations

import base64

from ..ports.signer_port import SignerPort


def generate_token(signer: SignerPort, guid: str) -> str:
    """Construye `base64(base64(guid|rfc|serie)#base64(firma))`."""
    content = f"{guid}|{signer.rfc}|{signer.certificate_number}".encode()
    signature = base64.b64encode(signer.sign_sha1(content).encode("ascii"))
    payload = base64.b64encode(content)
    return base64.b64encode(payload + b"#" + signature).decode("ascii")
