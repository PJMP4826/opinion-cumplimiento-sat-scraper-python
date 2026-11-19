from __future__ import annotations

import base64
import json

import httpx
import pytest
import respx

from opinion_scraper import OpinionDownloader
from opinion_scraper.config import DEFAULT_32D
from opinion_scraper.exceptions import FielCredentialsException
from tests._fiel_certs import DEFAULT_RFC, build_fiel

PDF_BYTES = b"%PDF-1.4 opinion de cumplimiento"

BOOTSTRAP_HTML = """
<html><body>
<form method="post" action="https://loginda.sat.gob.mx/nidp/app/login?id=ciec&sid=0">
  <input type="hidden" name="option" value="credential">
  <input type="hidden" name="target" value="abc">
</form>
</body></html>
"""

CERTFORM_HTML = """
<html><body>
<form id="certform" method="post">
  <input type="hidden" name="guid" value="guid-123">
  <input type="hidden" name="txtCertificate" value="">
  <input type="hidden" name="txtPrivateKey" value="">
  <input type="hidden" name="privateKeyPassword" value="">
  <input type="hidden" name="credentialsRequired" value="CERT">
</form>
</body></html>
"""

JS_REDIRECT_HTML = """
<html><body><script>top.location.href = "https://ptsc32d.clouda.sat.gob.mx/oauth2/callback?code=abc&amp;state=xyz";</script></body></html>
"""

CALLBACK_FORM_HTML = """
<html><body>
<form method="post" action="https://ptsc32d.clouda.sat.gob.mx/oauth2/callback">
  <input type="hidden" name="code" value="abc">
  <input type="hidden" name="state" value="xyz">
</form>
</body></html>
"""

PORTAL_READY_HTML = "<html><body>Portal listo</body></html>"


async def test_downloader_end_to_end_with_fiel() -> None:
    fixture = build_fiel()
    pdf_payload = {
        "Respuesta": {"Exito": True, "Codigo": "0", "Mensaje": ""},
        "ContenidoBase64": base64.b64encode(PDF_BYTES).decode(),
        "NombreArchivo": "opinion.pdf",
    }

    with respx.mock:
        entry_route = respx.get(
            url__startswith="https://ptsc32d.clouda.sat.gob.mx/?/reporte"
        ).mock(
            side_effect=[
                httpx.Response(200, text=BOOTSTRAP_HTML),
                httpx.Response(200, text=PORTAL_READY_HTML),
            ]
        )
        login_route = respx.post(
            url__startswith="https://loginda.sat.gob.mx/nidp/app/login"
        ).mock(
            side_effect=[
                httpx.Response(200, text=CERTFORM_HTML),
                httpx.Response(200, text=JS_REDIRECT_HTML),
            ]
        )
        respx.get(url__startswith="https://ptsc32d.clouda.sat.gob.mx/oauth2/callback").mock(
            return_value=httpx.Response(200, text=CALLBACK_FORM_HTML)
        )
        respx.post(url__startswith="https://ptsc32d.clouda.sat.gob.mx/oauth2/callback").mock(
            return_value=httpx.Response(200, text=PORTAL_READY_HTML)
        )
        pdf_route = respx.post(DEFAULT_32D.pdf_endpoint).mock(
            return_value=httpx.Response(200, json=pdf_payload)
        )

        client = httpx.AsyncClient(follow_redirects=True)
        downloader = OpinionDownloader.create(
            credentials=fixture.credentials(),
            client=client,
        )
        try:
            pdf = await downloader.download()
        finally:
            await client.aclose()

    assert pdf.content == PDF_BYTES
    assert pdf.filename == "opinion.pdf"
    assert len(entry_route.calls) == 2
    assert login_route.calls[0].request.url.params["id"] == "fiel"

    payload = json.loads(pdf_route.calls[0].request.content)
    assert payload["rfc"] == DEFAULT_RFC
    assert payload["tipoReporte"] == "32D"
    assert payload["tipoConsulta"] == "COMPLETA"
    assert payload["canal"] == "G"


def test_downloader_end_to_end_sync() -> None:
    fixture = build_fiel()
    pdf_payload = {
        "Respuesta": {"Exito": True},
        "ContenidoBase64": base64.b64encode(PDF_BYTES).decode(),
        "NombreArchivo": "opinion.pdf",
    }

    with respx.mock:
        respx.get(url__startswith="https://ptsc32d.clouda.sat.gob.mx/?/reporte").mock(
            side_effect=[
                httpx.Response(200, text=BOOTSTRAP_HTML),
                httpx.Response(200, text=PORTAL_READY_HTML),
            ]
        )
        respx.post(url__startswith="https://loginda.sat.gob.mx/nidp/app/login").mock(
            side_effect=[
                httpx.Response(200, text=CERTFORM_HTML),
                httpx.Response(200, text=JS_REDIRECT_HTML),
            ]
        )
        respx.get(url__startswith="https://ptsc32d.clouda.sat.gob.mx/oauth2/callback").mock(
            return_value=httpx.Response(200, text=CALLBACK_FORM_HTML)
        )
        respx.post(url__startswith="https://ptsc32d.clouda.sat.gob.mx/oauth2/callback").mock(
            return_value=httpx.Response(200, text=PORTAL_READY_HTML)
        )
        respx.post(DEFAULT_32D.pdf_endpoint).mock(
            return_value=httpx.Response(200, json=pdf_payload)
        )

        downloader = OpinionDownloader.create(credentials=fixture.credentials())
        pdf = downloader.download_sync()

    assert pdf.content == PDF_BYTES
    assert pdf.filename == "opinion.pdf"


async def test_downloader_rejects_rfc_mismatch() -> None:
    client = httpx.AsyncClient()
    downloader = OpinionDownloader.create(
        credentials=build_fiel().credentials(),
        client=client,
    )
    try:
        with pytest.raises(FielCredentialsException):
            await downloader.download("XAXX010101000")
    finally:
        await client.aclose()


async def test_downloader_rejects_expired_certificate() -> None:
    client = httpx.AsyncClient()
    downloader = OpinionDownloader.create(
        credentials=build_fiel(expired=True).credentials(),
        client=client,
    )
    try:
        with pytest.raises(FielCredentialsException):
            await downloader.download()
    finally:
        await client.aclose()
