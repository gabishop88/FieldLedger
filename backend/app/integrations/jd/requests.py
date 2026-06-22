import logging
from datetime import UTC, datetime, timedelta
from typing import Any, Literal, overload
from uuid import UUID

import httpx
from fastapi import HTTPException, status
from rich.logging import RichHandler
from sqlmodel import Session

from app.core.config import settings
from app.core.enums import ErrMsg
from app.db import crud
from app.db.models import AppUser, JDConnection, JDConnectionUpdate
from app.integrations.jd.models import JDModel, JDOrg

log_handler = RichHandler(rich_tracebacks=True, show_time=False)
logging.basicConfig(level=logging.INFO, format="%(message)s", handlers=[log_handler])
log = logging.getLogger(__name__)

Method = Literal["get", "post", "put", "patch", "delete"]
GrantType = Literal["authorization_code", "refresh_token"]
REDIRECT_URI = f"localhost:8000{settings.API_PREFIX}/jd/oauth-capture"


class JDClient:
    """### A Client for handling requests to John Deere servers.
    `client = JDClient(db, connection)` is valid as long as the Session (db) is active.
    Client will be able to make requests as long as connection has a valid access_token.

    `JDClient(db, user_id)` will fetch the connection from the database or create one.
    If a new JDConnection is created with this method, it will not have an access_token.

    Use `client.auth_url()` to get a url that will allow the user to sign in to JD.
    Once they sign in via this url, the auth_code will be captured and used to fill in
    the access_token and refresh_token of the connection associated with the user, which
    means clients made with that user_id (or associated connection) will be authorized.

    Use `client.ensure_fresh_access()` to refresh access_token if it is near expiration.

    Use `client.is_authorized()` to check whether the client has an access_token.
    Request helper functions will call `ensure_fresh_access` internally. `is_authorized`
    therefore does not check for an expired access_token, only a missing one.
    """

    def __init__(self, db: Session, connection: JDConnection):
        self.db = db
        self.conn = connection

    @classmethod
    def from_user(cls, db: Session, user_id: UUID):
        if not db.get(AppUser, user_id):
            raise HTTPException(
                status.HTTP_404_NOT_FOUND, ErrMsg.NF.format("AppUser", user_id)
            )
        new_conn = JDConnection(user_id=user_id)
        conn = db.get(JDConnection, user_id) or crud.jd_connection.create(db, new_conn)
        return cls(db, conn)

    async def _request_token(self, grant: GrantType, code: str | None) -> None:
        assert self.conn.refresh_token if (refr := grant == "refresh_token") else code
        head = {"Content-Type": "application/x-www-form-urlencoded"}
        data = {
            "grant_type": grant,
            "redirect_uri": REDIRECT_URI,
            "client_id": settings.JD_CLIENT_ID,
            "client_secret": settings.JD_CLIENT_SECRET,
            **({"refresh_token": self.conn.refresh_token} if refr else {"code": code}),
        }
        async with httpx.AsyncClient() as cli:
            url = f"{settings.JD_AUTH_BASE}/token"
            res = await cli.request("POST", url, headers=head, data=data)
        tkn = res.raise_for_status().json()
        tkn["expires_at"] = datetime.now(UTC) + timedelta(seconds=tkn["expires_in"])
        if not refr and self.conn.first_established is None:
            tkn["first_established"] = datetime.now(UTC)
        crud.jd_connection.update(self.db, self.conn, JDConnectionUpdate(**tkn))

    def auth_url(self) -> str:
        params = {
            "response_type": "code",
            "scope": "ag2 offline-access eq1",
            "client_id": settings.JD_CLIENT_ID,
            "state": self.conn.user_id,
            "redirect_uri": REDIRECT_URI,
        }
        req = httpx.Request("GET", f"{settings.JD_AUTH_BASE}/authorize", params=params)
        return str(req.url)

    async def access_from_auth_code(self, code: str) -> None:
        await self._request_token("authorization_code", code)

    async def ensure_fresh_access(self, buffer_min=10) -> None:
        if self.conn.access_expires_at is None:
            raise HTTPException(status.HTTP_401_UNAUTHORIZED, ErrMsg.UNAUTH_JD)
        cutoff = datetime.now(UTC) + timedelta(minutes=buffer_min)
        if self.conn.access_expires_at < cutoff:
            await self._request_token("refresh_token", None)

    def has_token(self) -> bool:
        return bool(self.conn.access_token)

    async def check_connection(self) -> bool:
        if not self.has_token():
            return False
        try:
            await self.get(f"{settings.JD_API_BASE}/organizations")
            return True
        except httpx.HTTPStatusError:
            return False

    async def request(self, method: str, uri: str, **kwargs) -> httpx.Response:
        await self.ensure_fresh_access()
        headers = {
            "Authorization": f"Bearer {self.conn.access_token}",
            "Accept": "application/vnd.deere.axiom.v3+json",
            "Accept-Language": "en",
        }
        headers.update(kwargs.pop("headers", {}))
        async with httpx.AsyncClient() as client:
            response = await client.request(method, uri, headers=headers, **kwargs)
        return response.raise_for_status()

    @overload
    async def get(self, uri: str, **kwargs) -> dict[str, Any]: ...

    @overload
    async def get[T: JDModel](self, uri: str, model: type[T], **kwargs) -> T: ...

    async def get[T: JDModel](
        self, uri: str, model: type[T] | None = None, **kwargs
    ) -> dict[str, Any] | T:
        """Get data at url. If you pass `model`, data is returned validated by it."""
        data = (await self.request("GET", uri, **kwargs)).json()
        return data if model is None else model.model_validate(data)

    async def post(self, uri: str, **kwargs) -> dict[str, Any]:
        return (await self.request("POST", uri, **kwargs)).json()

    async def get_org(self, uri: str, **kwargs) -> JDOrg | None:
        """Extract the org part from the url, then make request."""
        base, _, tail = uri.partition("/organizations/")
        org_id = tail.split("/", 1)[0]
        if not org_id:
            log.warning(f"<uri {uri}> does not contain an organization.")
            return None
        return await self.get(f"{base}/organizations/{org_id}", JDOrg, **kwargs)

    async def orgs(self, member_only=True) -> list[JDOrg]:
        data = await self.get(f"{settings.JD_API_BASE}/organizations")
        orgs = list(map(JDOrg.model_validate, data["values"]))
        return [org for org in orgs if not member_only or org.member]
