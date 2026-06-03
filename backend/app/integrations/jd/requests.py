import logging
from datetime import UTC, datetime, timedelta
from typing import Any, Literal
from urllib.parse import urlparse
from uuid import UUID

import httpx
from fastapi import HTTPException, status
from requests import Response, request
from rich.logging import RichHandler
from sqlmodel import Session, select

from app.core.config import settings
from app.core.enums import ErrMsg
from app.db import crud
from app.db.models import JDConnection, JDRecordLink

log_handler = RichHandler(rich_tracebacks=True, show_time=False)
logging.basicConfig(level=logging.INFO, format="%(message)s", handlers=[log_handler])
log = logging.getLogger(__name__)

Method = Literal["get", "post", "put", "patch", "delete"]
GrantType = Literal["authorization_code", "refresh_token"]
REDIRECT_URI = f"localhost:8000{settings.API_PREFIX}/jd/oauth-capture"


def rq(m: Method, url: str, pram=None, head=None, json=None, data=None) -> Response:
    """Make and print request, return response."""
    res = request(m, url, params=pram, headers=head, data=data, json=json)
    u, status = urlparse(res.request.url), res.status_code
    log.info(f'{u.hostname} "{m.upper()} {u.path}?{u.query} HTTP/1.1" {status} -')
    assert status in (200, 304, 404, 409), f"{status}: {res.text}"
    return res


# https://developer.deere.com/dev-docs/webhook#events:~:text=Post%20authorization%20redirect%20to%20enable%20organization%20access
# TODO: Check user has enabled org access per org when orgs are requested


class JDClient:
    def __init__(self, db: Session, connection: JDConnection):
        self.db = db
        self.conn = connection

    @classmethod
    def from_user(cls, db: Session, user_id: UUID) -> "JDClient":
        new_conn = JDConnection(user_id=user_id)
        conn = db.get(JDConnection, user_id) or crud.jd_connection.create(db, new_conn)
        return JDClient(db, conn)

    def _get_auth_url(self) -> str:
        params = {
            "response_type": "code",
            "scope": "ag2 offline-access eq1",
            "client_id": settings.JD_CLIENT_ID,
            "state": self.conn.user_id,
            "redirect_uri": REDIRECT_URI,
        }
        req = httpx.Request("GET", f"{settings.JD_AUTH_BASE}/authorize", params=params)
        return str(req.url)

    def _req_tokens(self, grant: GrantType, code: str | None = None) -> None:
        data = {
            "grant_type": grant,
            "redirect_uri": REDIRECT_URI,
            "client_id": settings.JD_CLIENT_ID,
            "client_secret": settings.JD_CLIENT_SECRET,
        }
        if grant == "authorization_code":
            assert code
            data["code"] = code
        else:
            assert self.conn.refresh_token
            data["refresh_token"] = self.conn.refresh_token

        response = httpx.post(
            f"{settings.JD_AUTH_BASE}/token",
            headers={"Content-Type": "application/x-www-form-urlencoded"},
            data=data,
        )
        response.raise_for_status()
        tkn = response.json()
        expires_at = datetime.now(UTC) + timedelta(seconds=tkn["expires_in"])
        self.conn.access_token = tkn["access_token"]
        self.conn.access_expires_at = expires_at
        self.conn.refresh_token = tkn["refresh_token"]
        self.db.add(self.conn)
        self.db.flush()
        self.db.refresh(self.conn)

    def refresh_check_auth(self, authorized_for_min=10) -> bool:
        """Ensures JDClient is authorized. Attempts to refresh token if expired."""
        if self.conn.access_expires_at is None:
            return False

        cutoff = datetime.now(UTC) + timedelta(minutes=authorized_for_min)
        if self.conn.access_expires_at < cutoff:
            self._req_tokens("refresh_token")

        return True

    def get_org_trees(self, skip: int, limit: int | None) -> list[JDRecordLink]:
        return list(self.db.exec(
            select(JDRecordLink).where(
                JDRecordLink.connection == self.conn, JDRecordLink.parent is None
            ).offset(skip).limit(limit)
        ).all())

    async def request(self, method: str, url: str, **kwargs) -> httpx.Response:
        if not self.refresh_check_auth():
            raise HTTPException(status.HTTP_401_UNAUTHORIZED, ErrMsg.UNAUTH_JD)

        headers = {
            "Authorization": f"{self.conn.access_token}",
            "Accept": "application/vnd.deere.axiom.v3+json",
            "Accept-Language": "en",
        }
        headers.update(kwargs.pop("headers", {}))
        async with httpx.AsyncClient() as client:
            response = await client.request(method, url, headers=headers, **kwargs)
        response.raise_for_status()
        return response

    async def get(self, url: str, **kwargs) -> dict[str, str] | list[Any]:
        response = await self.request("GET", url, **kwargs)
        return response.json()

    async def post(self, url: str, **kwargs) -> dict[str, Any]:
        response = await self.request("POST", url, **kwargs)
        return response.json()
