from __future__ import annotations

from pathlib import Path

import pytest

from opinion_scraper import (
    FielCredentialsException,
    InvalidPdfException,
    InvalidRfcException,
    OpinionPdf,
    Rfc,
)
from opinion_scraper.value_objects import FielCredentials


def test_rfc_normalizes_and_validates() -> None:
    assert Rfc("  pjmp482601ab1 ") == "PJMP482601AB1"
    with pytest.raises(InvalidRfcException):
        Rfc("NO-ES-RFC")


def test_fiel_credentials_from_files(tmp_path: Path) -> None:
    certificate = tmp_path / "cert.cer"
    key = tmp_path / "key.key"
    certificate.write_bytes(b"cert")
    key.write_bytes(b"key")

    credentials = FielCredentials.from_files(certificate, key, "secret")

    assert credentials.certificate == b"cert"
    assert credentials.password_value() == b"secret"
    assert "secret" not in repr(credentials)


def test_fiel_credentials_rejects_empty() -> None:
    with pytest.raises(FielCredentialsException):
        FielCredentials.from_bytes(b"", b"key")
    with pytest.raises(FielCredentialsException):
        FielCredentials.from_bytes(b"cert", b"")


def test_opinion_pdf_validates_and_saves(tmp_path: Path) -> None:
    pdf = OpinionPdf(b"%PDF-1.4 content", filename="opinion.pdf")

    assert pdf.size == len(pdf.content)
    assert len(pdf) == pdf.size
    assert len(pdf.sha256) == 64
    assert pdf.save(tmp_path) == tmp_path / "opinion.pdf"
    assert (tmp_path / "opinion.pdf").read_bytes() == pdf.content


@pytest.mark.parametrize("content", [b"", b"no es pdf"])
def test_opinion_pdf_rejects_invalid_content(content: bytes) -> None:
    with pytest.raises(InvalidPdfException):
        OpinionPdf(content)
