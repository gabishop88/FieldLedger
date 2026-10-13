import asyncio
import contextlib
import logging
from typing import cast

from redis.asyncio import Redis
from rich.logging import RichHandler

import app.integrations.jd.sync as jd
from app.core.config import settings
from app.db.connection import get_engine

log_handler = RichHandler(show_time=False)
logging.basicConfig(level=logging.INFO, format="%(message)s", handlers=[log_handler])
log = logging.getLogger(__name__)

# NOTE: https://arq-docs.helpmanual.io/


async def health_check(ctx) -> bool:
    log.info("Worker Healthy!")
    return "engine" in ctx


class RedisLogHandler(logging.Handler):
    def __init__(self, redis: Redis):
        super().__init__()
        self.redis = redis

    async def _publish(self, msg) -> None:
        await self.redis.xadd(
            "worker_logs",
            {"message": msg},
            maxlen=settings.REDIS_KEEP_LOGS,
            approximate=True,
        )

    def emit(self, record: logging.LogRecord):
        with contextlib.suppress(RuntimeError):
            asyncio.get_running_loop().create_task(self._publish(self.format(record)))


# TODO: remove `keep_result` and find another way to allow retries but not conflicts.
# NOTE: restart sync-worker service after a function is added or modified.
class WorkerSettings:
    redis_settings = settings.REDIS_SETTINGS
    keep_result = 5
    functions = [
        health_check,
        jd.discover_orgs,
        jd.modify_sync,
        jd.prepare_op,
        jd.handle_webhook_event,
    ]

    @staticmethod
    async def on_startup(ctx):
        log.info("Arq Worker Starting Up.")
        ctx["engine"] = get_engine()

        redis = Redis(host=settings.REDIS_HOST, port=settings.REDIS_PORT)
        ctx["log_redis"] = redis

        handler = RedisLogHandler(redis)
        handler.setFormatter(
            logging.Formatter("[%(asctime)s] %(levelname)s %(name)s: %(message)s")
        )
        root = logging.getLogger()
        if not any(isinstance(h, RedisLogHandler) for h in root.handlers):
            root.addHandler(handler)

    @staticmethod
    async def on_shutdown(ctx):
        """Currently Unused"""
        log.info("Arq Worker Shutting Down.")
        await cast(Redis, ctx["log_redis"]).aclose()
