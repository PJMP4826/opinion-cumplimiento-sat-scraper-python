from __future__ import annotations

from urllib.parse import parse_qs

import httpx
import pytest
import respx

from opinion_scraper.auth.fiel import Signer
from opinion_scraper.auth.fiel.nidp_login import NidpCertFormLogin
from opinion_scraper.config import DEFAULT_32D
from opinion_scraper.exceptions import SatLoginException
from tests._fiel_certs import build_fiel

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
<html><body><script>top.location.href = "https://ptsc32d.clouda.sat.gob.mx/oauth2/callback";</script></body></html>
"""


async def test_login_rewrites_id_and_signs_certform() -> None:
    fixture = build_fiel()
    signer = Signer.load(fixture.credentials())

    with respx.mock:
        respx.get(url__startswith="https://ptsc32d.clouda.sat.gob.mx/?/reporte").mock(
            return_value=httpx.Response(200, text=BOOTSTRAP_HTML)
        )
        login_route = respx.post(
            url__startswith="https://loginda.sat.gob.mx/nidp/app/login"
        ).mock(
            side_effect=[
                httpx.Response(200, text=CERTFORM_HTML),
                httpx.Response(200, text=JS_REDIRECT_HTML),
            ]
        )
        client = httpx.AsyncClient(follow_redirects=True)
        try:
            response = await NidpCertFormLogin(signer).login(client, DEFAULT_32D)
        finally:
            await client.aclose()

    assert response.text == JS_REDIRECT_HTML
    assert len(login_route.calls) == 2
    assert login_route.calls[0].request.url.params["id"] == "fiel"

    certform_body = parse_qs(login_route.calls[1].request.content.decode())
    assert certform_body["guid"] == ["guid-123"]
    assert certform_body["fert"] == [signer.fert]
    assert "token" in certform_body


def test_rewrite_login_id_handles_double_slash() -> None:
    signer = Signer.load(build_fiel().credentials())
    login = NidpCertFormLogin(signer)

    assert (
        login._rewrite_login_id("https://loginda.sat.gob.mx/nidp//app/login?id=ciec&sid=0")
        == "https://loginda.sat.gob.mx/nidp//app/login?id=fiel&sid=0"
    )
    assert (
        login._rewrite_login_id("https://loginda.sat.gob.mx/otro/login?id=ciec")
        == "https://loginda.sat.gob.mx/otro/login?id=ciec"
    )


async def test_login_fails_without_certform() -> None:
    signer = Signer.load(build_fiel().credentials())

    with respx.mock:
        respx.get(url__startswith="https://ptsc32d.clouda.sat.gob.mx/?/reporte").mock(
            return_value=httpx.Response(200, text="<html></html>")
        )
        client = httpx.AsyncClient(follow_redirects=True)
        try:
            with pytest.raises(SatLoginException):
                await NidpCertFormLogin(signer).login(client, DEFAULT_32D)
        finally:
            await client.aclose()
