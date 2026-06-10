import logging
from datetime import UTC, datetime, timedelta
from typing import Any, Literal
from uuid import UUID

import httpx
from fastapi import HTTPException, status
from rich.logging import RichHandler
from sqlmodel import Session

from app.core.config import settings
from app.core.enums import ErrMsg
from app.db import crud
from app.db.models import AppUser, JDConnection, JDConnectionUpdate
from app.integrations.jd.models import JDOrg

log_handler = RichHandler(rich_tracebacks=True, show_time=False)
logging.basicConfig(level=logging.INFO, format="%(message)s", handlers=[log_handler])
log = logging.getLogger(__name__)

Method = Literal["get", "post", "put", "patch", "delete"]
GrantType = Literal["authorization_code", "refresh_token"]
REDIRECT_URI = f"localhost:8000{settings.API_PREFIX}/jd/oauth-capture"


# def rq(m: Method, url: str, pram=None, head=None, json=None, data=None) -> Response:
#     """Make and print request, return response."""
#     res = request(m, url, params=pram, headers=head, data=data, json=json)
#     u, status = urlparse(res.request.url), res.status_code
#     log.info(f'{u.hostname} "{m.upper()} {u.path}?{u.query} HTTP/1.1" {status} -')
#     assert status in (200, 304, 404, 409), f"{status}: {res.text}"
#     return res


# https://developer.deere.com/dev-docs/webhook#events:~:text=Post%20authorization%20redirect%20to%20enable%20organization%20access
# TODO: Check user has enabled org access per org when orgs are requested


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
            await self.orgs(False)
            return True
        except httpx.HTTPStatusError:
            return False


    async def request(self, method: str, url: str, **kwargs) -> httpx.Response:
        await self.ensure_fresh_access()
        headers = {
            "Authorization": f"Bearer {self.conn.access_token}",
            "Accept": "application/vnd.deere.axiom.v3+json",
            "Accept-Language": "en",
        }
        headers.update(kwargs.pop("headers", {}))
        async with httpx.AsyncClient() as client:
            response = await client.request(method, url, headers=headers, **kwargs)
        return response.raise_for_status()

    async def get(self, url: str, **kwargs) -> dict[str, Any]:
        response = await self.request("GET", url, **kwargs)
        return response.json()

    async def post(self, url: str, **kwargs) -> dict[str, Any]:
        response = await self.request("POST", url, **kwargs)
        return response.json()

    async def orgs(self, member_only=True) -> list[JDOrg]:
        data = await self.get(f"{settings.JD_API_BASE}/organizations")
        orgs = list(map(JDOrg.model_validate, data["values"]))
        return [org for org in orgs if not member_only or org.member]

    # TODO: Since my endpoint may use a resource path, I may only really need self.get

    # async def add_orgs(self, member_only=True):
    #     """Add org links available to connection. Basically, create org-tree roots."""
    #     log.info(f"Adding initial orgs to {self.conn=}")
    #     data = await self.get(f"{settings.JD_API_BASE}/organizations")
    #     orgs = filter(lambda org: member_only and org["member"], data["values"])
    #     for org in orgs:
    #         links = org["links"]  # TODO: conn_link in data, so I can get it to user
    #         conn_link = next(filter(lambda ln: ln["rel"] == "connections", links), None)
    #         self_link = next(filter(lambda ln: ln["rel"] == "self", links))
    #         conn_status = SyncStatus.NORG if conn_link else None
    #         match = crud.org.get_paginated(self.db, 0, None, Org.name == org["name"])
    #         org_link = JDRecordLink(
    #             link=self_link["uri"],
    #             data=org,
    #             status=conn_status or (SyncStatus.NOSYNC, SyncStatus.SYNC)[match.count],
    #             persistent=bool(match.count),
    #             table_name="org",
    #             table_key={"id": match.data[0].id} if match.count else None,
    #             parent_id=None,
    #             user_id=self.conn.user_id,
    #         )
    #         filters = [
    #             JDRecordLink.link == self_link["uri"],
    #             JDRecordLink.user_id == self.conn.user_id,
    #         ]
    #         existing = crud.jd_link.get_paginated(self.db, 0, None, *filters)
    #         assert existing.count < 2, existing
    #         existing_link = existing.data[0] if existing.count else None
    #         if existing_link:  # TODO: Validate and ensure this can replace org_link
    #             assert (
    #                 existing_link.table_name == "org"
    #                 and existing_link.parent_id is None
    #             ), existing_link
    #             if existing_link.status == SyncStatus.PAUSE:
    #                 continue
    #             existing_link.data = org
    #             if existing_link.table_key is None:
    #                 if match.count:
    #                     existing_link.table_key = {"id": match.data[0].id}
    #                     existing_link.persistent = True
    #                     existing_link.status = SyncStatus.SYNC
    #                 else:
    #                     existing_link.status = SyncStatus.NOSYNC
    #             if conn_link:
    #                 existing_link.status = SyncStatus.NORG

    #         org_link = existing_link or org_link
    #         self.db.add(org_link)
    #         self.db.flush()
    #         if existing.count or match.count:
    #             assert org_link.table_key and org_link.table_name == "org"
    #             db_org = self.db.get(Org, org_link.table_key)
    #             if db_org and db_org.name != org["name"]:
    #                 crud.org.update(self.db, db_org, OrgUpdate(name=org["name"]))

    #             # TODO: if there was a match or existing link, update farms
