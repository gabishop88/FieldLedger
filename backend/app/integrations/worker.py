import inspect
import logging
import os
from typing import Literal

from arq import create_pool
from arq.connections import RedisSettings

import app.integrations.jd.sync as jd

log = logging.getLogger(__name__)

# NOTE: https://arq-docs.helpmanual.io/

# NOTE: port is set to 6379 by default. Change here if docker-compose changes redis port
REDIS_SETTINGS = RedisSettings(host=os.getenv("REDIS_HOST") or "localhost")


# TODO: Add file in ./jd/ for job functions that can be used by worker and/or startup
# NOTE: I can use _job_id in enqueue_job to make sure syncs are run once?
# TODO: Use dep function or something else to make the pool that I can enqueue to

class WorkerSettings:
    redis_settings = REDIS_SETTINGS
    functions = [jd.initial_sync, jd.handle_webhook_event]

    @staticmethod
    async def on_startup(ctx):
        """Currently Unused"""
        log.info("Arq Worker Starting Up.")

    @staticmethod
    async def on_shutdown(ctx):
        """Currently Unused"""
        log.info("Arq Worker Shutting Down.")
