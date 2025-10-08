from enum import StrEnum

from fastapi import APIRouter, Request, status
from fastapi.openapi.docs import (
    get_swagger_ui_html,
    get_swagger_ui_oauth2_redirect_html,
)
from fastapi.responses import PlainTextResponse, RedirectResponse

from app.api.routes import assets
from app.core.config import settings


class DocTags(StrEnum):
    ASSET = "Farm Assets"
    USER = "User Information and Authentication"
    OP = "Field Operations"
    REF = "Reference Tables"


api_router = APIRouter()
api_router.include_router(assets.router, prefix="/farm-data", tags=[DocTags.ASSET])


# ----------------------------------- Base Endpoints -----------------------------------


# Redirect people to the /docs page if it looks like they need help
@api_router.get("/", include_in_schema=False)
@api_router.get("/help", include_in_schema=False)
async def redirect_to_docs():
    return RedirectResponse(
        f"{settings.API_V1_STR}/docs", status.HTTP_301_MOVED_PERMANENTLY
    )


# Customizable /docs page
@api_router.get("/docs", include_in_schema=False)
def docs_page():
    return get_swagger_ui_html(
        openapi_url=f"{settings.API_V1_STR}/openapi.json",
        title=f"{settings.PROJECT_NAME} API",
        swagger_ui_parameters={
            "useUnsafeMarkdown": True,
            "docExpansion": "none",
            "persistAuthorization": True,
        },
        swagger_favicon_url="https://illinois.edu/favicon.ico"
    )


@api_router.get(f"{settings.API_V1_STR}/docs/oauth2-redirect", include_in_schema=False)
async def swagger_ui_redirect():
    return get_swagger_ui_oauth2_redirect_html()


@api_router.get("/health-check")
@api_router.head("/health-check", include_in_schema=False)
def health_check(_: Request):
    return PlainTextResponse("<3", status_code=status.HTTP_200_OK)
