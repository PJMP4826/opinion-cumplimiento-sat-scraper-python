# opinion-cumplimiento-sat-scraper-python

Librería en Python para **descargar la Opinión de Cumplimiento del SAT (32-D)**
autenticándose con **e.firma / FIEL** (`.cer`, `.key` y contraseña).

El paquete emula el flujo web oficial: login NIDP con el formulario `certform`,
federación OAuth2/OIDC y `POST` al endpoint que entrega el PDF en base64.
**No parsea el contenido del PDF**; solo lo descarga y lo entrega en memoria.

## Requisitos

- Python 3.11 o superior.
- e.firma vigente en formato **DER** (`.cer` y `.key`).
- RFC del titular incluido en el certificado.

## Instalación

```bash
pip install "opinion-cumplimiento-sat-scraper-python[fiel]"
```

Para desarrollo local:

```bash
python -m venv .venv
.venv/bin/pip install -e ".[dev,fiel]"
```

## Uso

### Asíncrono

```python
import asyncio

from opinion_scraper import FielCredentials, OpinionDownloader


async def main() -> None:
    credentials = FielCredentials.from_files(
        certificate_path="certificado.cer",
        key_path="llave.key",
        password="mi-contrasena",
    )
    async with OpinionDownloader.create(credentials=credentials) as downloader:
        pdf = await downloader.download()
        pdf.save("opinion.pdf")
        print(pdf.filename, pdf.size, pdf.sha256)


asyncio.run(main())
```

### Síncrono

```python
from opinion_scraper import FielCredentials, OpinionDownloader

credentials = FielCredentials.from_files("certificado.cer", "llave.key", "mi-contrasena")
downloader = OpinionDownloader.create(credentials=credentials)
try:
    pdf = downloader.download_sync()
    pdf.save("opinion.pdf")
finally:
    downloader.close_sync()
```

`download()` usa el RFC del certificado. También acepta un RFC explícito, que
debe coincidir con el certificado:

```python
pdf = await downloader.download("PJMP482601AB1")
```

## API principal

| Símbolo | Descripción |
|---|---|
| `FielCredentials` | Contenedor inmutable de `.cer`, `.key` y contraseña (`SecretStr`). |
| `OpinionDownloader` | Fachada que autentica y descarga el PDF. |
| `OpinionPdf` | PDF validado con `as_bytes()`, `size`, `sha256` y `save()`. |
| `PortalConfig` / `DEFAULT_32D` | Endpoints y parámetros del portal. |
| `FielAuthProvider` | Proveedor FIEL (NIDP + federación OIDC). |
| `AuthProviderPort` | Puerto ABC para futuros proveedores de autenticación. |

## Flujo de descarga

1. `GET` al portal 32-D y seguimiento de la cadena OIDC hasta el login NIDP.
2. Reescritura de `id=ciec` a `id=fiel` en la acción del formulario de login.
3. Firma del `certform` con la FIEL:
   `token = base64(base64(guid|RFC|serie)#base64(firma SHA-1))` y `fert`.
4. Seguimiento de los formularios `form_post` de la federación OIDC/SAML.
5. Validación de sesión con un `GET` al portal.
6. `POST` JSON a `ObtenerRespuestaCompletaPdf` con `tipoReporte="32D"`.
7. Validación de `Respuesta.Exito`, decodificación de `ContenidoBase64` y
   verificación de la firma `%PDF-`.

## Errores

Todas las excepciones heredan de `OpinionScraperException`.

| Excepción | Cuándo ocurre |
|---|---|
| `FielCredentialsException` | Certificado/llave inválidos, contraseña incorrecta, llave que no corresponde, certificado vencido o RFC distinto. |
| `SatLoginException` | No se encontró el formulario `certform` o el campo `guid`. |
| `FederationException` | La federación OIDC no terminó dentro del límite de formularios. |
| `AuthenticationException` | La sesión no quedó autenticada tras la federación. |
| `SatNetworkException` | Error de red, timeout o HTTP 4xx/5xx. |
| `OpinionNotAvailableException` | El SAT respondió `Exito=false`; conserva `codigo` y `mensaje`. |
| `InvalidOpinionResponseException` | Respuesta sin JSON válido, sin `ContenidoBase64` o con base64 inválido. |
| `InvalidPdfException` | El contenido descargado no es un PDF. |
| `InvalidRfcException` | El RFC no tiene formato válido. |

## Seguridad

- La contraseña se guarda en `pydantic.SecretStr` y no aparece en `repr`.
- No se escriben cookies, tokens ni credenciales en logs.
- Las cookies de sesión se limpian al terminar cada descarga.
- `trust_env=False` por defecto para no tomar proxies del entorno.
- La verificación TLS permanece habilitada; solo se ajustan los cifrados
  requeridos por los hosts legacy del SAT.

## Alcance actual

- Autenticación **solo con FIEL**. El puerto `AuthProviderPort` queda listo
  para un futuro proveedor CIEC, que no está implementado.
- **No** se parsea el contenido del PDF de la opinión.
- El portal del SAT puede cambiar sin aviso; los endpoints viven en
  `PortalConfig` para facilitar ajustes.

## Desarrollo

```bash
.venv/bin/ruff check src tests
.venv/bin/mypy
.venv/bin/pytest
```

Las pruebas no contactan al SAT: usan `respx` y certificados autofirmados. El
marcador `live` está reservado para pruebas manuales con credenciales reales.

## Atribuciones

Ver [NOTICE.md](NOTICE.md). Este proyecto no está afiliado ni respaldado por el SAT.
