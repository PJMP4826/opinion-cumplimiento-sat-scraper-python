"""Configuracion del portal a consultar."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class PortalConfig:
    """Endpoints y parametros de navegacion de un portal SAT."""

    entry_url: str
    pdf_endpoint: str
    portal_origin: str
    login_id: str = "fiel"
    max_bootstrap_forms: int = 3
    max_federation_forms: int = 10
    timeout_seconds: float = 30.0
    pdf_timeout_seconds: float = 60.0
    trust_env: bool = False
    verify_session: bool = True


DEFAULT_32D = PortalConfig(
    entry_url="https://ptsc32d.clouda.sat.gob.mx/?/reporteOpinion32DContribuyente",
    pdf_endpoint=(
        "https://ptsc32d.clouda.sat.gob.mx/RespuestaCompleta/ObtenerRespuestaCompletaPdf"
    ),
    portal_origin="https://ptsc32d.clouda.sat.gob.mx",
)
