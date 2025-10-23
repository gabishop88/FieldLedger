import pytest
from fastapi import status

from app.core.config import settings


@pytest.mark.parametrize("path", ["/", "/help", "/docs"])
def test_redirect_to_docs(client, path):
    """Root, /help, /docs endpoints should redirect to /api/v1/docs page."""
    res = client.get(path, follow_redirects=False)
    assert res.status_code == status.HTTP_301_MOVED_PERMANENTLY
    assert res.headers["location"].endswith(f"{settings.API_PREFIX}/docs")


def test_redirect_to_redoc(client):
    """/redoc should redirect to /api/v1/redoc page."""
    res = client.get("/redoc", follow_redirects=False)
    assert res.status_code == status.HTTP_301_MOVED_PERMANENTLY
    assert res.headers["location"].endswith(f"{settings.API_PREFIX}/redoc")
