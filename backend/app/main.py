import re
from contextlib import asynccontextmanager

from arq import create_pool
from fastapi import FastAPI
from fastapi.responses import RedirectResponse
from fastapi.routing import APIRoute
from starlette.middleware.cors import CORSMiddleware

from app.api.router import api_router
from app.core.config import settings
from app.core.enums import DocTag

SNAKIFIER = re.compile(r"(?<=[a-z])(?=[A-Z])|(?<=[A-Z])(?=[A-Z][a-z])")


def custom_route_id(route: APIRoute) -> str:
    """### Provide each endpoint with a unique route id.
    Take the first tag (or 'default'), put it in snake_case and append the route name.
    """
    tag = route.tags[0] if route.tags else "default"
    tag = str(tag).strip().replace(" ", "_")
    tag = SNAKIFIER.sub("_", tag).lower()
    return f"{tag}_{route.name}"


@asynccontextmanager
async def lifespan(app):
    """Set up a job pool whose life span is tied to the API."""
    app.state.job_pool = await create_pool(settings.REDIS_SETTINGS)
    yield
    await app.state.job_pool.close()


app = FastAPI(
    title=f"{settings.PROJECT_NAME} API",
    openapi_url=f"{settings.API_PREFIX}/openapi.json",
    openapi_tags=[{"name": str(tag)} for tag in DocTag],
    docs_url=None,  # I registered a custom docs page in `app/api/router.py`
    redoc_url=f"{settings.API_PREFIX}/redoc",
    swagger_ui_oauth2_redirect_url=f"{settings.API_PREFIX}/docs/oauth2-redirect",
    lifespan=lifespan,
    contact={"role": "Developer", "email": settings.FIRST_SUPERUSER},
    generate_unique_id_function=custom_route_id,
)

if settings.all_cors_origins:
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.all_cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

# Add all of the main endpoints to the router.
app.include_router(api_router, prefix=settings.API_PREFIX)


# redirect some expected base urls to use the settings.API_PREFIX.
@app.get("/", include_in_schema=False)
@app.get("/help", include_in_schema=False)
@app.get("/docs", include_in_schema=False)
def redirect_to_docs():
    return RedirectResponse(f"{settings.API_PREFIX}/docs")


@app.get("/redoc", include_in_schema=False)
def redirect_to_redoc():
    return RedirectResponse(f"{settings.API_PREFIX}/redoc")
