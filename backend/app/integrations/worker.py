import logging

from arq.connections import RedisSettings

import app.integrations.jd.sync as jd
from app.core.config import settings
from app.db.connection import get_engine

log = logging.getLogger(__name__)

# NOTE: https://arq-docs.helpmanual.io/

# NOTE: port is set to 6379 by default. Change here if docker-compose changes redis port
REDIS_SETTINGS = RedisSettings(host=settings.REDIS_HOST, port=settings.REDIS_PORT)


# TODO: Add file in ./jd/ for job functions that can be used by worker and/or startup
# NOTE: I can use _job_id in enqueue_job to make sure syncs are run once?
# TODO: Use dep function or something else to make the pool that I can enqueue to

async def health_check(ctx) -> bool:
    log.info("Worker Healthy!")
    return "engine" in ctx


class WorkerSettings:
    redis_settings = REDIS_SETTINGS
    # NOTE: restart the sync-worker service after a function is added or modified.
    functions = [health_check, jd.modify_sync, jd.handle_webhook_event]

    @staticmethod
    async def on_startup(ctx):
        ctx["engine"] = get_engine()
        log.info("Arq Worker Starting Up.")

    @staticmethod
    async def on_shutdown(ctx):
        """Currently Unused"""
        log.info("Arq Worker Shutting Down.")
