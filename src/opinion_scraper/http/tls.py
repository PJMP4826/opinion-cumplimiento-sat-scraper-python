"""Contexto TLS compatible con los hosts legacy del SAT."""

from __future__ import annotations

import ssl

SAT_CIPHERS = (
    "ECDHE+AESGCM:ECDHE+CHACHA20:DHE+AESGCM:DHE+CHACHA20:"
    "ECDH+AESGCM:DH+AESGCM:ECDH+AES:DH+AES:RSA+AESGCM:RSA+AES:"
    "!aNULL:!eNULL:!MD5:!DSS:HIGH:!DH"
)


def create_sat_ssl_context() -> ssl.SSLContext:
    """Crea un contexto con verificacion habilitada y cifrados compatibles."""
    context = ssl.create_default_context()
    context.set_ciphers(SAT_CIPHERS)
    return context
