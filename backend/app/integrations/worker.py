import logging

from redis.asyncio import Redis

import app.integrations.jd.sync as jd
from app.core.config import settings
from app.db.connection import get_engine

log = logging.getLogger(__name__)

# NOTE: https://arq-docs.helpmanual.io/


# TODO: Add file in ./jd/ for job functions that can be used by worker and/or startup
# NOTE: I can use _job_id in enqueue_job to make sure syncs are run once?
# TODO: Use dep function or something else to make the pool that I can enqueue to


async def health_check(ctx) -> bool:
    log.info("Worker Healthy!")
    return "engine" in ctx


# TODO: remove keep_result=10 and find another way to allow retries but not conflicts.
class WorkerSettings:
    redis_settings = settings.REDIS_SETTINGS
    keep_result = 10
    # NOTE: restart sync-worker service after a function is added or modified.
    functions = [
        health_check,
        jd.discover_orgs,
        jd.modify_sync,
        jd.handle_webhook_event,
    ]

    @staticmethod
    async def on_startup(ctx):
        log.info("Arq Worker Starting Up.")
        ctx["engine"] = get_engine()

    @staticmethod
    async def on_shutdown(ctx):
        """Currently Unused"""
        log.info("Arq Worker Shutting Down.")
