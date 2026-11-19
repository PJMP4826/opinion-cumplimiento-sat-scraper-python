"""Value objects del dominio."""

from __future__ import annotations

from .auth_result import AuthResult
from .fiel_credentials import FielCredentials
from .opinion_pdf import OpinionPdf
from .rfc import Rfc

__all__ = ["AuthResult", "FielCredentials", "OpinionPdf", "Rfc"]
