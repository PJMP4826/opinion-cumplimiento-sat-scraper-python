"""RFC validado del contribuyente."""

from __future__ import annotations

import re

from ..exceptions.value_objects import InvalidRfcException

_RFC_PATTERN = re.compile(r"^[A-Z&Ñ]{3,4}\d{6}[A-Z0-9]{3}$")


class Rfc(str):
    """RFC normalizado (mayusculas, sin espacios) y validado."""

    def __new__(cls, value: str) -> Rfc:
        if not isinstance(value, str):
            raise InvalidRfcException("El RFC debe ser una cadena de texto.")
        normalized = value.strip().upper()
        if not _RFC_PATTERN.fullmatch(normalized):
            raise InvalidRfcException(f"El RFC '{value}' no tiene un formato valido.")
        return super().__new__(cls, normalized)
