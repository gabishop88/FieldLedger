from fastapi import status

from app.core.config import settings


def test_docs_page(client):
    res = client.get(f"{settings.API_PREFIX}/docs")
    assert res.status_code == status.HTTP_200_OK
    assert "text/html" in res.headers["content-type"]
    assert settings.PROJECT_NAME in res.text


def test_health_check(client):
    res = client.get(f"{settings.API_PREFIX}/health-check")
    assert res.status_code == status.HTTP_200_OK
    assert res.text == "<3"

# TODO: test data-dump endpoint
