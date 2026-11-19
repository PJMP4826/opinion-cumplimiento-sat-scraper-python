from __future__ import annotations

import httpx
import respx

from opinion_scraper.auth.fiel.oidc_federation import OidcFederationHandler

JS_REDIRECT_HTML = """
<html><body><script>window.location.href = "https://ptsc32d.clouda.sat.gob.mx/oauth2/callback?code=abc&amp;state=xyz";</script></body></html>
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


async def test_follows_js_redirect_and_form_post() -> None:
    with respx.mock:
        respx.get(url__startswith="https://ptsc32d.clouda.sat.gob.mx/oauth2/callback").mock(
            return_value=httpx.Response(200, text=CALLBACK_FORM_HTML)
        )
        callback_post = respx.post(
            url__startswith="https://ptsc32d.clouda.sat.gob.mx/oauth2/callback"
        ).mock(return_value=httpx.Response(200, text=PORTAL_READY_HTML))

        initial = httpx.Response(
            200,
            text=JS_REDIRECT_HTML,
            request=httpx.Request("GET", "https://loginda.sat.gob.mx/nidp/app/login"),
        )
        client = httpx.AsyncClient(follow_redirects=True)
        try:
            response = await OidcFederationHandler().follow(client, initial)
        finally:
            await client.aclose()

    assert response.text == PORTAL_READY_HTML
    assert len(callback_post.calls) == 1
