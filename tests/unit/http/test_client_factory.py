from __future__ import annotations

from opinion_scraper.http import SatHttpClientFactory, create_sat_ssl_context


async def test_client_factory_sets_browser_defaults() -> None:
    client = SatHttpClientFactory().create()

    try:
        assert client.headers["User-Agent"].startswith("Mozilla/5.0")
        assert client.follow_redirects is True
        assert client.trust_env is False
    finally:
        await client.aclose()


def test_ssl_context_is_created() -> None:
    context = create_sat_ssl_context()
    assert context.verify_mode.name == "CERT_REQUIRED"
