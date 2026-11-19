"""Descarga del PDF de la Opinion de Cumplimiento via API 32-D."""

from __future__ import annotations

import base64
import binascii
from pathlib import Path
from typing import Any
from uuid import uuid4

import httpx

from ..config import PortalConfig
from ..exceptions.auth import SatNetworkException
from ..exceptions.download import (
    InvalidOpinionResponseException,
    OpinionNotAvailableException,
)
from ..value_objects.opinion_pdf import OpinionPdf
from ..value_objects.rfc import Rfc


class OpinionDocumentService:
    """Ejecuta el POST JSON que devuelve el PDF en base64."""

    def __init__(self, portal: PortalConfig) -> None:
        self._portal = portal

    async def download(
        self,
        client: httpx.AsyncClient,
        rfc: str,
        *,
        referer: str | None = None,
    ) -> OpinionPdf:
        validated_rfc = Rfc(rfc)
        payload = {
            "canal": "G",
            "curp": "",
            "idCorrelacion": str(uuid4()),
            "ip": "127.0.0.1",
            "rfc": str(validated_rfc),
            "tipoConsulta": "COMPLETA",
            "tipoReporte": "32D",
            "usuario": str(validated_rfc),
            "rfcCorto": str(validated_rfc),
        }
        headers = {
            "Accept": "application/json",
            "Content-Type": "application/json",
            "Origin": self._portal.portal_origin,
            "Referer": referer or f"{self._portal.portal_origin}/",
        }
        try:
            response = await client.post(
                self._portal.pdf_endpoint,
                json=payload,
                headers=headers,
                timeout=self._portal.pdf_timeout_seconds,
            )
        except httpx.HTTPError as exc:
            raise SatNetworkException(self._portal.pdf_endpoint) from exc

        if response.status_code >= 400:
            raise SatNetworkException(self._portal.pdf_endpoint, response.status_code)

        data = self._parse_json(response)
        self._validate_status(data)
        content = self._decode_content(data)
        filename = self._safe_filename(data.get("NombreArchivo"), validated_rfc)
        return OpinionPdf(content=content, filename=filename)

    @staticmethod
    def _safe_filename(raw: object, rfc: Rfc) -> str:
        if isinstance(raw, str) and raw:
            name = Path(raw.replace("\\", "/")).name
            if name:
                return name
        return f"opinion_cumplimiento_{rfc}.pdf"

    @staticmethod
    def _parse_json(response: httpx.Response) -> dict[str, Any]:
        try:
            data: object = response.json()
        except ValueError as exc:
            raise InvalidOpinionResponseException(
                "La respuesta del portal 32-D no es JSON valido."
            ) from exc
        if not isinstance(data, dict):
            raise InvalidOpinionResponseException(
                "La respuesta del portal 32-D no es un objeto JSON."
            )
        return data

    @staticmethod
    def _validate_status(data: dict[str, Any]) -> None:
        if "Respuesta" not in data:
            return
        respuesta = data["Respuesta"]
        if not isinstance(respuesta, dict):
            raise InvalidOpinionResponseException(
                "La respuesta del portal 32-D no contiene un objeto Respuesta valido."
            )
        if respuesta.get("Exito") is True:
            return
        codigo = respuesta.get("Codigo")
        mensaje = respuesta.get("Mensaje")
        raise OpinionNotAvailableException(
            str(codigo) if codigo is not None else None,
            str(mensaje) if mensaje is not None else None,
        )

    @staticmethod
    def _decode_content(data: dict[str, Any]) -> bytes:
        encoded = data.get("ContenidoBase64")
        if not isinstance(encoded, str) or not encoded:
            raise InvalidOpinionResponseException(
                "La respuesta del portal 32-D no contiene ContenidoBase64."
            )
        compact = "".join(encoded.split())
        try:
            return base64.b64decode(compact, validate=True)
        except (binascii.Error, ValueError) as exc:
            raise InvalidOpinionResponseException(
                "El contenido del PDF no es base64 valido."
            ) from exc
