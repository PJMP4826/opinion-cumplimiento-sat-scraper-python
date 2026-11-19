from __future__ import annotations

import base64

import httpx
import pytest
import respx

from opinion_scraper.config import DEFAULT_32D
from opinion_scraper.exceptions import (
    InvalidOpinionResponseException,
    InvalidPdfException,
    OpinionNotAvailableException,
)
from opinion_scraper.services import OpinionDocumentService

RFC = "PJMP482601AB1"
PDF_BYTES = b"%PDF-1.4 opinion"


def _json_response(payload: object) -> httpx.Response:
    return httpx.Response(200, json=payload)


async def test_download_returns_pdf() -> None:
    payload = {
        "Respuesta": {"Exito": True, "Codigo": "0", "Mensaje": ""},
        "ContenidoBase64": base64.b64encode(PDF_BYTES).decode(),
        "NombreArchivo": "opinion.pdf",
    }
    with respx.mock:
        route = respx.post(DEFAULT_32D.pdf_endpoint).mock(return_value=_json_response(payload))
        client = httpx.AsyncClient()
        try:
            pdf = await OpinionDocumentService(DEFAULT_32D).download(
                client, RFC, referer="https://ptsc32d.clouda.sat.gob.mx/"
            )
        finally:
            await client.aclose()

    assert pdf.content == PDF_BYTES
    assert pdf.filename == "opinion.pdf"
    assert route.calls[0].request.url == DEFAULT_32D.pdf_endpoint


async def test_download_uses_default_filename() -> None:
    payload = {
        "ContenidoBase64": base64.b64encode(PDF_BYTES).decode(),
    }
    with respx.mock:
        respx.post(DEFAULT_32D.pdf_endpoint).mock(return_value=_json_response(payload))
        client = httpx.AsyncClient()
        try:
            pdf = await OpinionDocumentService(DEFAULT_32D).download(client, RFC)
        finally:
            await client.aclose()

    assert pdf.filename == f"opinion_cumplimiento_{RFC}.pdf"


async def test_download_sanitizes_filename_and_whitespace() -> None:
    encoded = base64.b64encode(PDF_BYTES).decode()
    payload = {
        "ContenidoBase64": f"  {encoded[:10]}\n{encoded[10:]}  ",
        "NombreArchivo": "../../etc/opinion.pdf",
    }
    with respx.mock:
        respx.post(DEFAULT_32D.pdf_endpoint).mock(return_value=_json_response(payload))
        client = httpx.AsyncClient()
        try:
            pdf = await OpinionDocumentService(DEFAULT_32D).download(client, RFC)
        finally:
            await client.aclose()

    assert pdf.content == PDF_BYTES
    assert pdf.filename == "opinion.pdf"


async def test_download_raises_when_sat_rejects() -> None:
    payload = {
        "Respuesta": {"Exito": False, "Codigo": "32D-01", "Mensaje": "Sin obligaciones"},
    }
    with respx.mock:
        respx.post(DEFAULT_32D.pdf_endpoint).mock(return_value=_json_response(payload))
        client = httpx.AsyncClient()
        try:
            with pytest.raises(OpinionNotAvailableException) as error:
                await OpinionDocumentService(DEFAULT_32D).download(client, RFC)
        finally:
            await client.aclose()

    assert error.value.codigo == "32D-01"
    assert error.value.mensaje == "Sin obligaciones"


@pytest.mark.parametrize(
    "response",
    [
        httpx.Response(200, text="<html>login</html>"),
        httpx.Response(200, json=["no", "objeto"]),
        httpx.Response(200, json={"Respuesta": {"Exito": True}}),
        httpx.Response(200, json={"ContenidoBase64": "%%%"}),
        httpx.Response(200, json={"ContenidoBase64": "aG9sYQ=="}),
    ],
)
async def test_download_rejects_invalid_responses(response: httpx.Response) -> None:
    with respx.mock:
        respx.post(DEFAULT_32D.pdf_endpoint).mock(return_value=response)
        client = httpx.AsyncClient()
        try:
            with pytest.raises((InvalidOpinionResponseException, InvalidPdfException)):
                await OpinionDocumentService(DEFAULT_32D).download(client, RFC)
        finally:
            await client.aclose()
