import logging
from uuid import UUID

from fastapi import APIRouter, HTTPException, Request, status

from app.api.deps import UserSession
from app.core.enums import DocTag, ErrMsg
from app.integrations.worker import add_task

logging.basicConfig(level=logging.INFO)
log = logging.getLogger(__name__)

router = APIRouter(tags=[DocTag.INTEG])


# TODO: How to ensure caller is John Deere API and get which user's webhook called?
@router.post("/jd/webhook-callback")  # TODO: Look up webhook expected response
async def recieve_jd_webhook(request: Request):
    payload = await request.json()
    if not payload:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, ErrMsg.BAD_PAYLOAD)
    log.info(f"Recieved Webhook from John Deere: {payload.get('eventType')}")
    await add_task("handle_webhook_event", payload)
    return {"status": "accepted"}


@router.post("jd/sync/{org_id}")
async def jd_sync_org(db: UserSession, org_id: UUID):
    log.info(f"Manual Sync Triggered for {org_id=}")
    await add_task("initial_sync", db, org_id)
    return {"status": "syncing", "org_id": str(org_id)}


# TODO: Add endpoints to modify sync states within the sync tree?
#   I think make an endpoint to get sync tree for org_id (+ return it from jd_sync_org)
#   Probably also make endpoints to modify sync state for specific records or bulk?
