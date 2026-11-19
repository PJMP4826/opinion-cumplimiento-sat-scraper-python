"""Extraccion de formularios HTML y redirecciones JavaScript."""

from __future__ import annotations

import html as html_module
import re
from dataclasses import dataclass
from urllib.parse import urljoin

from bs4 import BeautifulSoup
from bs4.element import Tag

_JS_REDIRECT_PATTERN = re.compile(
    r"(?:window|top)\.location(?:\.href)?\s*=\s*[\"']([^\"']+)[\"']",
    re.IGNORECASE,
)


@dataclass(frozen=True, slots=True)
class FormExtractionResult:
    """Formulario HTML listo para reenviarse."""

    action: str | None
    method: str
    fields: dict[str, str]


def _field_value(element: Tag) -> str | None:
    name = element.get("name")
    if not isinstance(name, str) or not name:
        return None
    if element.name == "textarea":
        return element.get_text()
    if element.name == "select":
        selected = element.find("option", selected=True) or element.find("option")
        if selected is None:
            return ""
        value = selected.get("value")
        return value if isinstance(value, str) else selected.get_text(strip=True)
    input_type = str(element.get("type", "text")).lower()
    if input_type in {"checkbox", "radio"} and not element.has_attr("checked"):
        return None
    value = element.get("value")
    return value if isinstance(value, str) else ""


def extract_form(
    html: str,
    *,
    form_id: str | None = None,
    index: int = 0,
    base_url: str | None = None,
    action_contains: str | None = None,
) -> FormExtractionResult | None:
    """Devuelve el formulario solicitado con todos sus campos."""
    soup = BeautifulSoup(html, "lxml")
    form: Tag | None
    if form_id is not None:
        form = soup.find("form", id=form_id)
    elif action_contains is not None:
        form = None
        for candidate in soup.find_all("form"):
            raw_action = candidate.get("action")
            if isinstance(raw_action, str) and action_contains in raw_action:
                form = candidate
                break
    else:
        forms = soup.find_all("form")
        form = forms[index] if len(forms) > index else None
    if form is None:
        return None

    raw_action = form.get("action")
    action: str | None = None
    if isinstance(raw_action, str) and raw_action.strip():
        action = urljoin(base_url, raw_action) if base_url else raw_action
    method = str(form.get("method", "GET")).upper()

    fields: dict[str, str] = {}
    for element in form.find_all(["input", "textarea", "select"]):
        name = element.get("name")
        value = _field_value(element)
        if isinstance(name, str) and value is not None:
            fields[name] = value
    return FormExtractionResult(action=action, method=method, fields=fields)


def extract_js_redirect(html: str) -> str | None:
    """Extrae la URL de una asignacion `window/top.location.href`."""
    match = _JS_REDIRECT_PATTERN.search(html)
    if match is None:
        return None
    return html_module.unescape(match.group(1))
