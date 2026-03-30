import csv
from io import StringIO
from typing import Literal

from fastapi import APIRouter, HTTPException, Request, UploadFile, status
from fastapi.openapi.docs import get_swagger_ui_html
from fastapi.responses import HTMLResponse, PlainTextResponse, RedirectResponse
from pydantic import ValidationError
from sqlmodel import SQLModel

from app.api.deps import SuperuserSession
from app.api.routes import iam, operation, ref, resource, structure
from app.core.config import settings
from app.core.enums import DocTag, ErrMsg
from app.db import models

api_router = APIRouter()
api_router.include_router(structure.router)
api_router.include_router(operation.router)
api_router.include_router(resource.router)
api_router.include_router(iam.router, tags=[DocTag.IAM_USER])
api_router.include_router(ref.router, tags=[DocTag.REF])


# ----------------------------------- Base Endpoints -----------------------------------
# Remember, all these endpoints start with the settings.API_PREFIX (set in app/main.py)


# Redirect people to the /docs page if it looks like they need help
@api_router.get("/", include_in_schema=False)
@api_router.get("/help", include_in_schema=False)
async def redirect_to_docs():
    return RedirectResponse(
        f"{settings.API_PREFIX}/docs", status.HTTP_301_MOVED_PERMANENTLY
    )


# Customizable /docs page
@api_router.get("/docs", tags=[DocTag.MISC])
def docs_page(theme: Literal["light", "dark"] = "dark"):
    """### Swagger UI docs page.
    `/`, `/help`, `api/v1/`, `/api/v1/help` all redirect here.
    """
    html = get_swagger_ui_html(
        openapi_url=f"{settings.API_PREFIX}/openapi.json",
        title=f"{settings.PROJECT_NAME} API",
        swagger_favicon_url="https://cdn.brand.illinois.edu/favicon.ico",
        swagger_ui_parameters={
            # "useUnsafeMarkdown": True,
            "persistAuthorization": True,
            "docExpansion": "none",
        },
    )

    if theme == "dark":
        cont = bytes(html.body).decode()
        cont += '<script>document.documentElement.classList.add("dark-mode");</script>'
        html = HTMLResponse(content=cont)

    return html


@api_router.get("/health-check", tags=[DocTag.MISC])
@api_router.head("/health-check", include_in_schema=False)
def health_check(_: Request):
    return PlainTextResponse("<3", status_code=status.HTTP_200_OK)


@api_router.post("/dump-csv/{table}", tags=[DocTag.MISC])
async def data_dump(db: SuperuserSession, table: str, file: UploadFile):
    Model: SQLModel | None = getattr(models, table, None)
    if not (Model and Model.__tablename__):
        raise HTTPException(status.HTTP_404_NOT_FOUND, ErrMsg.NF.format("Table", table))

    try:
        raw = await file.read()
        reader = csv.DictReader(StringIO(raw.decode("utf-8")))
        objects = [
            Model.model_validate({k: v or None for k, v in row.items()})
            for row in list(reader)
        ]
        db.add_all(objects)
    except ValidationError as e:
        db.rollback()
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_CONTENT, e.errors())
    except Exception as e:
        db.rollback()
        raise HTTPException(status.HTTP_400_BAD_REQUEST, str(e))

    return {"inserted": len(objects), "table": table}
