import logging
from uuid import UUID

from fastapi import APIRouter, Request, Response, status

from app.api.deps import CurrentUser, JobPool
from app.core.enums import DocTag

logging.basicConfig(level=logging.INFO)
log = logging.getLogger(__name__)

router = APIRouter(tags=[DocTag.INTEG])


# TODO: Can I replace request with just the events body? maybe need pydantic?
# TODO: Should I use the Authorization header (CurrentUser) or token in body for user?
@router.post("/jd/recieve-webhook-events")
async def recieve_jd_webhook(request: Request, user: CurrentUser, pool: JobPool) -> Response:
    """Handle webhook callback. Must return status 204 within 5s as per JD docs."""
    events = await request.json()
    for event in events:
        # TODO: Should I handle the subscriptionVerification events here immediately?
        await pool.enqueue_job("handle_webhook_event", user_id=user.id, event=event)

    return Response(None, status.HTTP_204_NO_CONTENT)


@router.post("jd/sync/{jd_org_id}")
async def jd_sync_org(user: CurrentUser, pool: JobPool, jd_org_id: UUID):
    log.info(f"Manual Sync Triggered for {jd_org_id=}")
    await pool.enqueue_job("initial_sync", org_id=jd_org_id, user_id=user.id)
    # TODO: Determine a better response, such as getting the sync tree from the task
    return {"status": "syncing", "org_id": str(jd_org_id)}


# TODO: Add endpoints to modify sync states within the sync tree?
#   I think make an endpoint to get sync tree for org_id (+ return it from jd_sync_org?)
#   Probably also make endpoints to modify sync state for specific records or bulk?

# TODO: Add col to JDRecordLink to indicate when it should be deleted if link is
