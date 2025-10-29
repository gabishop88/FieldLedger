import csv
from enum import StrEnum
from io import StringIO

from fastapi import APIRouter, HTTPException, Request, UploadFile, status
from fastapi.openapi.docs import get_swagger_ui_html
from fastapi.responses import PlainTextResponse, RedirectResponse
from pydantic import ValidationError
from sqlmodel import SQLModel

from app.api.deps import CurrentSuperuser, UserSession
from app.api.messages import ExeMsg
from app.api.routes import asset, iam
from app.core.config import settings
from app.db import models


class DocTags(StrEnum):
    ASSET = "Farm Assets"
    USER = "User Information and Authentication"
    OP = "Field Operations"
    REF = "Reference Tables"
    MISC = "Miscellaneous"


api_router = APIRouter()
api_router.include_router(asset.router, tags=[DocTags.ASSET])
api_router.include_router(iam.router, tags=[DocTags.USER])


# ----------------------------------- Base Endpoints -----------------------------------
# Remember, all of these endpoints start with the settings.API_PREFIX (set in app/main.py)


# Redirect people to the /docs page if it looks like they need help
@api_router.get("/", include_in_schema=False)
@api_router.get("/help", include_in_schema=False)
async def redirect_to_docs():
    return RedirectResponse(
        f"{settings.API_PREFIX}/docs", status.HTTP_301_MOVED_PERMANENTLY
    )


# Customizable /docs page
@api_router.get("/docs", include_in_schema=False)
def docs_page():
    return get_swagger_ui_html(
        openapi_url=f"{settings.API_PREFIX}/openapi.json",
        title=f"{settings.PROJECT_NAME} API",
        swagger_favicon_url="https://illinois.edu/favicon.ico",
        swagger_ui_parameters={
            "useUnsafeMarkdown": True,
            "docExpansion": "none",
            "persistAuthorization": True,
        },
    )


@api_router.get("/health-check", tags=[DocTags.MISC])
@api_router.head("/health-check", include_in_schema=False)
def health_check(_: Request):
    return PlainTextResponse("<3", status_code=status.HTTP_200_OK)


@api_router.post("/dump-csv/{table}", tags=[DocTags.MISC])
async def data_dump(db: UserSession, _: CurrentSuperuser, table: str, file: UploadFile):
    Model: SQLModel | None= getattr(models, table, None)
    if not (Model and Model.__tablename__):
        raise HTTPException(status.HTTP_404_NOT_FOUND, ExeMsg.NF_TABLE.format(table))

    try:
        raw = await file.read()
        reader = csv.DictReader(StringIO(raw.decode("utf-8")))
        objects = [
            Model.model_validate({k: v or None for k, v in row.items()})
            for row in list(reader)
        ]
        db.add_all(objects)
        db.commit()
    except ValidationError as e:
        db.rollback()
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_CONTENT, e.errors())
    except Exception as e:
        db.rollback()
        raise HTTPException(status.HTTP_400_BAD_REQUEST, str(e))

    return {"inserted": len(objects), "table": table}
