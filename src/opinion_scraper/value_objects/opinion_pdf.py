"""PDF descargado de la Opinion de Cumplimiento."""

from __future__ import annotations

import hashlib
from dataclasses import dataclass
from pathlib import Path

from ..exceptions.download import InvalidPdfException

DEFAULT_FILENAME = "opinion_cumplimiento.pdf"


@dataclass(frozen=True, slots=True)
class OpinionPdf:
    """PDF validado, en memoria, con utilidades de guardado."""

    content: bytes
    filename: str = DEFAULT_FILENAME

    def __post_init__(self) -> None:
        if not self.content:
            raise InvalidPdfException("El contenido del PDF esta vacio.")
        if not self.content.startswith(b"%PDF-"):
            raise InvalidPdfException("El contenido descargado no es un PDF.")

    def as_bytes(self) -> bytes:
        return self.content

    @property
    def size(self) -> int:
        return len(self.content)

    @property
    def sha256(self) -> str:
        return hashlib.sha256(self.content).hexdigest()

    def save(self, path: str | Path) -> Path:
        target = Path(path)
        if target.is_dir():
            target = target / self.filename
        target.write_bytes(self.content)
        return target

    def __len__(self) -> int:
        return len(self.content)
