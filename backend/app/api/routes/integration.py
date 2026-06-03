import logging
from uuid import UUID

from fastapi import APIRouter, HTTPException, Request, Response, status
from fastapi.responses import RedirectResponse

from app.api.deps import CurrentUser, JobPool, UserSession, WriteSession
from app.core.config import settings
from app.core.enums import DocTag, ErrMsg
from app.db.models import JDRecordLinkUpdate, Paginated, SyncTreeNode
from app.integrations.jd.requests import JDClient

LIM = settings.DEFAULT_PAGE_LIMIT

logging.basicConfig(level=logging.INFO)
log = logging.getLogger(__name__)

router = APIRouter(tags=[DocTag.INTEG])


@router.get("jd/authorize-integration")
def authorize_jd(db: UserSession, user: CurrentUser):
    client = JDClient.from_user(db, user.id)
    if client.refresh_check_auth():
        return Response()
    return RedirectResponse(client._get_auth_url())


@router.post("jd/oauth-capture")
def capture_jd_auth_code(db: WriteSession, code: str, state: str):
    client = JDClient.from_user(db, UUID(state))
    client._req_tokens("authorization_code", code)


# TODO: Can I replace request with just the events body? maybe need pydantic?
# TODO: Should I use the Authorization header (CurrentUser) or token in body for user?
# TODO: try to reject these if the user is not authorized? Does it matter for this?
@router.post("jd/recieve-webhook-events")
async def recieve_jd_webhook(request: Request, user: CurrentUser, pool: JobPool):
    """Handle webhook callback. Must return status 204 within 5s as per JD docs."""
    events = await request.json()
    for event in events:
        await pool.enqueue_job("handle_webhook_event", user_id=user.id, event=event)
    return Response(None, status.HTTP_204_NO_CONTENT)


@router.get("jd/sync-trees", response_model=Paginated[SyncTreeNode])
def get_sync_trees(db: UserSession, user: CurrentUser, skip=0, limit: int | None = LIM):
    """Get the sync trees for each org the user can access."""
    client = JDClient.from_user(db, user.id)
    if not client.refresh_check_auth():
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, ErrMsg.UNAUTH_JD)
    nodes = client.get_org_trees(skip, limit)
    return Paginated(count=len(nodes), data=nodes)


# TODO: remove this
@router.post("jd/sync/{jd_org_id}")
async def jd_sync_org(db: UserSession, user: CurrentUser, pool: JobPool, jd_org: UUID):
    log.info(f"Manual Sync Triggered for {jd_org=}")
    client = JDClient.from_user(db, user.id)
    if not client.refresh_check_auth():
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, ErrMsg.UNAUTH_JD)

    await pool.enqueue_job("initial_sync", org_id=jd_org, user_id=user.id)
    return {"status": "job queued", "org_id": str(jd_org)}


@router.patch("jd/sync/{resource_link:path}")
async def jd_modify_sync(
    db: UserSession,
    user: CurrentUser,
    pool: JobPool,
    resource_path: str,
    updates: JDRecordLinkUpdate,
):
    client = JDClient.from_user(db, user.id)
    if not client.refresh_check_auth():
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, ErrMsg.UNAUTH_JD)
    # TODO: Preliminary sanity check for the values in `updates`
    # TODO: Change job name or id in pool using resource path and/or user.id?
    await pool.enqueue_job(
        "modify_sync", user_id=user.id, resource_path=resource_path, updates=updates
    )
    return {"status": "job queued", "resource": resource_path}


# TODO: Add endpoints to modify sync states within the sync tree?
#   I think make an endpoint to get sync tree for org_id (+ return it from jd_sync_org?)
#   Probably also make endpoints to modify sync state for specific records or bulk?

# TODO: Add col to JDRecordLink to indicate when it should be deleted if link is
