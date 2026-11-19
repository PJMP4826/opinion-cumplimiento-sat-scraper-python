from __future__ import annotations

from opinion_scraper.form_utils import extract_form, extract_js_redirect

FORM_HTML = """
<html><body>
<form id="certform" method="post">
  <input type="hidden" name="guid" value="guid-123">
  <input type="text" name="rfc" value="PJMP482601AB1">
  <input type="checkbox" name="unchecked">
  <input type="checkbox" name="checked" value="si" checked>
  <input type="radio" name="radio" value="a">
  <select name="opcion">
    <option value="1">Uno</option>
    <option value="2" selected>Dos</option>
  </select>
  <textarea name="notas">hola</textarea>
</form>
<form action="relativo" method="get"><input name="otro" value="x"></form>
<script>top.location.href = "https://sat.gob.mx/cb?a=1&amp;b=2";</script>
</body></html>
"""


def test_extract_form_by_id() -> None:
    form = extract_form(FORM_HTML, form_id="certform", base_url="https://base/path")

    assert form is not None
    assert form.action is None
    assert form.method == "POST"
    assert form.fields == {
        "guid": "guid-123",
        "rfc": "PJMP482601AB1",
        "checked": "si",
        "opcion": "2",
        "notas": "hola",
    }


def test_extract_form_by_index_resolves_action() -> None:
    form = extract_form(FORM_HTML, index=1, base_url="https://base/path/page")

    assert form is not None
    assert form.action == "https://base/path/relativo"
    assert form.method == "GET"
    assert form.fields == {"otro": "x"}


def test_extract_form_missing() -> None:
    assert extract_form("<html></html>") is None
    assert extract_form(FORM_HTML, form_id="noexiste") is None


def test_extract_js_redirect_unescapes() -> None:
    assert extract_js_redirect(FORM_HTML) == "https://sat.gob.mx/cb?a=1&b=2"
    assert extract_js_redirect("<html></html>") is None
