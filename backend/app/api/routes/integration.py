import logging
from uuid import UUID

from fastapi import APIRouter, HTTPException, Path, Request, Response, status
from fastapi.responses import RedirectResponse

from app.api.deps import CurrentUser, JobPool, UserSession, WriteSession
from app.core.config import settings
from app.core.enums import DocTag, ErrMsg
from app.db import crud
from app.db.models import JDLinkUpdate, Paginated, SyncTreeNode
from app.integrations.jd.requests import JDClient

LIM = settings.DEFAULT_PAGE_LIMIT

logging.basicConfig(level=logging.INFO)
log = logging.getLogger(__name__)

jd_router = APIRouter(tags=[DocTag.INTEG])

router = APIRouter()  # Combine routers at the end (after endpoints are added)


@jd_router.get(
    "/authorize-integration",
    responses={
        200: {"description": "Already Authenticated"},
        307: {"description": "Redirect to John Deere Sign-in."},
    },
)
def authorize_jd(db: UserSession, user: CurrentUser):
    """### Redirects user to John Deere sign-in page to authorize syncing"""
    client = JDClient.from_user(db, user.id)
    if client.check_connection():
        return {"status": "authorized"}
    return RedirectResponse(client.auth_url())


@jd_router.post("/oauth-capture", include_in_schema=False)
async def capture_jd_auth_code(
    db: WriteSession, user: CurrentUser, pool: JobPool, code: str, state: str
):
    client = JDClient.from_user(db, UUID(state))
    await client.access_from_auth_code(code)
    if not await client.check_connection():
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, ErrMsg.UNAUTH_JD)
    await pool.enqueue_job("discover_orgs", user_id=user.id)


# TODO: Can I replace request with just the events body? maybe need pydantic?
# TODO: Should I use the Authorization header (CurrentUser) or token in body for user?
# TODO: try to reject these if the user is not authorized? Does it matter for this?
@jd_router.post("/recieve-webhook-events", include_in_schema=False)
async def recieve_jd_webhook(request: Request, user: CurrentUser, pool: JobPool):
    """Handle webhook callback. Must return status 204 within 5s as per JD docs."""
    events = await request.json()
    for event in events:
        await pool.enqueue_job("handle_webhook_event", user_id=user.id, event=event)
    return Response(None, status.HTTP_204_NO_CONTENT)


@jd_router.get("/sync-trees", response_model=Paginated[SyncTreeNode])
def get_sync_trees(db: UserSession, user: CurrentUser, skip=0, limit: int | None = LIM):
    """Get the sync trees for each org the user can access."""
    return crud.jd_link.get_trees_paginated(db, user.id, skip, limit)


# TODO: Change job name or id in pool using resource path and/or user.id?
@jd_router.patch("/sync/{resource_link:path}")
async def jd_modify_sync(
    db: UserSession,
    user: CurrentUser,
    pool: JobPool,
    updates: JDLinkUpdate,
    resource_path: str = Path(description="e.g. `organizations/{id}/farms/{id}`"),
):
    """### Modifies the Sync State of a John Deere Resource Link."""
    if not JDClient.from_user(db, user.id).check_connection():
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, ErrMsg.UNAUTH_JD)
    link = f"{settings.JD_API_BASE}/{resource_path}"
    if not crud.jd_link.get_by_link(db, user.id, link):
        raise HTTPException(
            status.HTTP_404_NOT_FOUND, ErrMsg.NF.format("Resource", resource_path)
        )
    # TODO: Preliminary sanity check for the values in `updates`?
    await pool.enqueue_job("modify_sync", user_id=user.id, link=link, updates=updates)
    return {"status": "job queued", "resource": resource_path}


# TODO: If someone attempts to modify the sync status of a resource, first check that
#   they have access to the org that it is contained in, with the status SYNC.
# If they are trying to change the sync status of an org, then make sure that all other
#   (if any) links to that org are NOSYNC, then set this user's to SYNC and all others
#   to CONFLICT


# TODO: Add endpoints to modify sync states within the sync tree?
#   I think make an endpoint to get sync tree for org_id (+ return it from jd_sync_org?)
#   Probably also make endpoints to modify sync state for specific records or bulk?

# TODO: Add col to JDRecordLink to indicate when it should be deleted if link is

router.include_router(jd_router, prefix="/jd")
