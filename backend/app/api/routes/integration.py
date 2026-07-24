import logging
from uuid import UUID

from fastapi import (
    APIRouter,
    HTTPException,
    Path,
    Query,
    Request,
    Response,
    WebSocket,
    WebSocketDisconnect,
    status,
)
from fastapi.responses import RedirectResponse
from redis.asyncio import Redis

from app.api.deps import CurrentUser, JobPool, UserSession, WriteSession
from app.core.config import settings
from app.core.enums import SYNC_ACTIVE, SYNC_ORG_ERR, DocTag, ErrMsg, SyncStatus
from app.db import crud
from app.db.models import (
    AuthPublic,
    JDConnection,
    JDLinkUpdate,
    Paginated,
    SyncTreeNode,
)
from app.integrations.jd.requests import JDClient
from app.integrations.jd.sync import change_status

LIM = settings.DEFAULT_PAGE_LIMIT

logging.basicConfig(level=logging.INFO)
log = logging.getLogger(__name__)

jd_router = APIRouter(tags=[DocTag.INTEG])
router = APIRouter()  # Combine routers at the end (after endpoints are added)

# region ----------------------------- General Endpoints ------------------------------


# TODO: restrict logs by user? consider splitting into streams and/or using on_job_start
@router.websocket("/worker-logs")
async def worker_logs(
    ws: WebSocket, limit: int = Query(default=100, ge=1, le=settings.REDIS_KEEP_LOGS)
):
    await ws.accept()
    redis = Redis(
        host=settings.REDIS_HOST, port=settings.REDIS_PORT, decode_responses=True
    )

    stream = "worker_logs"
    try:
        history = await redis.xrevrange(stream, count=limit)
        for _, data in reversed(history):
            await ws.send_text(data["message"])

        last_id = "$"
        while True:
            messages = await redis.xread({stream: last_id}, block=5000)
            for _, entries in messages:
                for entry_id, data in entries:
                    last_id = entry_id
                    await ws.send_text(data["message"])

    except WebSocketDisconnect:
        pass
    finally:
        await redis.aclose()


# endregion
# region ----------------------------- JD Sync Endpoints ------------------------------


@jd_router.get(
    "/authorization-link",
    response_model=AuthPublic,
    responses={307: {"description": "Redirect to John Deere Sign-in."}},
)
async def authorize_jd(db: UserSession, redirect: bool = False):
    """### Provides authorization status and a link to John Deere sign-in page.
    Use `redirect=true` to return a RedirectResponse to the sign-in page, instead.
    """
    client = JDClient.from_session(db)
    if await client.check_connection():
        return AuthPublic(authorized=True, auth_uri=client.auth_uri())
    if redirect:
        return RedirectResponse(client.auth_uri())
    return AuthPublic(authorized=False, auth_uri=client.auth_uri())


@jd_router.delete("/authorization-link")
async def delete_connection(db: UserSession, user: CurrentUser):
    """### Removes the user's link to JD and ALL sync links and data.
    Use with caution.
    """
    conn = db.get(JDConnection, user.id)
    if conn is None:
        return HTTPException(
            status.HTTP_404_NOT_FOUND,
            ErrMsg.NF.format("Connection for User", user.email),
        )

    org_links = crud.jd_link.get_trees_paginated(db, user.id).data
    for org in org_links:
        await change_status(db, org, SyncStatus.Unsynced)
    crud.jd_connection.delete(db, conn)


@jd_router.get("/oauth-capture", include_in_schema=False)
async def capture_jd_auth_code(
    db: WriteSession,
    pool: JobPool,
    state: str,
    code: str | None = None,
    error: str | None = None,
    error_description: str | None = None,
):
    client = JDClient.from_user(db, UUID(state))
    if not code:
        log.error(f"{error}: {error_description}")
        return RedirectResponse(f"{settings.FRONTEND_HOST}?jd-connection=failed")
    await client.access_from_auth_code(code)
    if not await client.check_connection():
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, ErrMsg.UNAUTH_JD)
    job_id = f"discover:{state}"
    await pool.enqueue_job("discover_orgs", user_id=UUID(state), _job_id=job_id)
    return RedirectResponse(f"{settings.FRONTEND_HOST}?jd-connection=authorized")


# TODO: For all enqueue_job endpoints, I should return something to indicate whether the
#   job was successfulyl requested. I can use something to check that the job was posted
#   and not just skipped to determinet that (it would be skipped if there is a duplicate
#   or recent results).


@jd_router.post("/recieve-webhook-events", include_in_schema=False)
async def recieve_jd_webhook(request: Request, user: CurrentUser, pool: JobPool):
    """Handle webhook callback. Must return status 204 within 5s as per JD docs."""
    events = await request.json()
    for event in events:
        await pool.enqueue_job("handle_webhook_event", user_id=user.id, event=event)
    return Response(None, status.HTTP_204_NO_CONTENT)


@jd_router.get("/sync-trees", response_model=Paginated[SyncTreeNode])
async def get_sync_trees(db: UserSession, skip=0, limit: int | None = LIM):
    """Get the sync trees for each org the user can access."""
    client = JDClient.from_session(db)
    if not await client.check_connection():
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, ErrMsg.UNAUTH_JD)

    trees = crud.jd_link.get_trees_paginated(db, client.conn.user_id, skip, limit)
    return Paginated[SyncTreeNode](
        count=trees.count, data=[SyncTreeNode.model_validate(t) for t in trees.data]
    )


# TODO: Change job name or id in pool using resource path and/or user.id?
@jd_router.patch("/resource/{resource_uri:path}")
async def jd_modify_sync(
    db: UserSession,
    pool: JobPool,
    data_in: JDLinkUpdate,
    resource_uri: str = Path(description="e.g. `platform/organizations/{id}`"),
):
    """### Modifies the Sync State of a John Deere Resource Link."""
    log.info("Modifying a Sync Resource.")
    log.info(f"{data_in=}")
    log.info(f"{resource_uri=}")
    if data_in.status and data_in.status in SYNC_ORG_ERR:
        msg = ErrMsg.INVLD_STATUS.format(data_in.status)
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_CONTENT, msg)

    client = JDClient.from_session(db)
    if not await client.check_connection():
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, ErrMsg.UNAUTH_JD)

    link = crud.jd_link.get_by_user_and_uri(db, client.conn.user_id, resource_uri)
    if not link:
        msg = ErrMsg.NF.format("Resource Link", resource_uri)
        raise HTTPException(status.HTTP_404_NOT_FOUND, msg)
    if link.parent and link.parent.status not in SYNC_ACTIVE:
        msg = ErrMsg.INACTIVE_PARENT.format(link.uri, link.parent.uri)
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_CONTENT, msg)

    # TODO: remove once completed
    # if link.table_name in ("field_op",):
    #     raise HTTPException(
    #         status.HTTP_501_NOT_IMPLEMENTED, f"{link.table_name} sync unimplemneted."
    #     )

    args = {"user_id": client.conn.user_id, "uri": resource_uri, "update": data_in}
    j = await pool.enqueue_job("modify_sync", **args, _job_id=f"modify:{resource_uri}")
    if j is None:
        msg = ErrMsg.JOB_EXISTS.format(resource_uri)
        raise HTTPException(status.HTTP_409_CONFLICT, msg)
    return status.HTTP_202_ACCEPTED


@jd_router.get("/resource/prepare-operation/{op_uri:path}")
async def jd_prepare_operation_for_sync(db: UserSession, pool: JobPool, op_uri: str):
    """### Get data that syncing an operation would produce.
    Useful for checking the operation data before calling `PATCH /resource/{path}` on it

    Returns the new links that would be created as a result of syncing this op.
    """
    log.info("Preparing operation sync data.")
    client = JDClient.from_session(db)
    if not await client.check_connection():
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, ErrMsg.UNAUTH_JD)

    link = crud.jd_link.get_by_user_and_uri(db, client.conn.user_id, op_uri)
    if not link:
        msg = ErrMsg.NF.format("Resource Link", op_uri)
        raise HTTPException(status.HTTP_404_NOT_FOUND, msg)
    if link.table_name != "field_op":
        msg = ErrMsg.LINK_TYPE.format(op_uri, "Field Operation.")
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_CONTENT, msg)

    args = {"user_id": client.conn.user_id, "uri": op_uri}
    job = await pool.enqueue_job("prepare_op", **args, _job_id=f"prepare:{op_uri}")
    if job is None:
        raise HTTPException(status.HTTP_409_CONFLICT, ErrMsg.JOB_EXISTS.format(op_uri))
    org_children, op_children = await job.result()
    return {"new_org_children": org_children, "new_op_children": op_children}


# endregion

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
