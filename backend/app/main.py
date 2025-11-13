import re

from fastapi import FastAPI, status
from fastapi.responses import RedirectResponse
from fastapi.routing import APIRoute
from starlette.middleware.cors import CORSMiddleware

from app.api.router import DocTags, api_router
from app.core.config import settings

SNAKIFIER = re.compile(r"(?<=[a-z])(?=[A-Z])|(?<=[A-Z])(?=[A-Z][a-z])")


def custom_route_id(route: APIRoute) -> str:
    tag = route.tags[0] if route.tags else "default"
    tag = str(tag).strip().replace(" ", "_")
    tag = SNAKIFIER.sub("_", tag).lower()
    return f"{tag}_{route.name}"


app = FastAPI(
    title=f"{settings.PROJECT_NAME} API",
    contact={"role": "Developer", "email": settings.FIRST_SUPERUSER},
    generate_unique_id_function=custom_route_id,
    openapi_tags=[{"name": str(tag)} for tag in DocTags],
    openapi_url=f"{settings.API_PREFIX}/openapi.json",
    swagger_ui_oauth2_redirect_url=f"{settings.API_PREFIX}/docs/oauth2-redirect",
    docs_url=None,  # I registered a custom docs page in `app/api/router.py`
    redoc_url=f"{settings.API_PREFIX}/redoc",
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
    return RedirectResponse(
        f"{settings.API_PREFIX}/docs", status.HTTP_301_MOVED_PERMANENTLY
    )


@app.get("/redoc", include_in_schema=False)
def redirect_to_redoc():
    return RedirectResponse(
        f"{settings.API_PREFIX}/redoc", status.HTTP_301_MOVED_PERMANENTLY
    )
