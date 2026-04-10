"""Интеграционные тесты OpenAPI security-схемы."""

import pytest


@pytest.mark.integration
def test_openapi_contains_bearer_security_scheme(api_client) -> None:
    """Проверяет наличие Bearer security scheme для Swagger Authorize."""
    response = api_client.get("/openapi.json")

    assert response.status_code == 200
    payload = response.json()
    security_schemes = payload["components"]["securitySchemes"]
    assert "HTTPBearer" in security_schemes
    assert security_schemes["HTTPBearer"]["type"] == "http"
    assert security_schemes["HTTPBearer"]["scheme"] == "bearer"


@pytest.mark.integration
def test_openapi_marks_protected_routes(api_client) -> None:
    """Проверяет, что защищенные роуты имеют security-требование."""
    response = api_client.get("/openapi.json")
    payload = response.json()

    media_upload_security = payload["paths"]["/api/v1/media/upload"]["post"]["security"]
    create_post_security = payload["paths"]["/api/v1/posts"]["post"]["security"]

    assert {"HTTPBearer": []} in media_upload_security
    assert {"HTTPBearer": []} in create_post_security
