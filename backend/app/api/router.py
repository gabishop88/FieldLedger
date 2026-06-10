import csv
from io import StringIO
from typing import Literal

from fastapi import APIRouter, HTTPException, UploadFile, status
from fastapi.openapi.docs import get_swagger_ui_html
from fastapi.responses import HTMLResponse, PlainTextResponse, RedirectResponse
from pydantic import ValidationError
from sqlmodel import Column, ForeignKey, SQLModel, Table, select

from app.api.deps import JobPool, ReadSession, SuperuserSession
from app.api.routes import iam, integration, operation, ref, resource, structure
from app.core.config import settings
from app.core.enums import DocTag, ErrMsg
from app.db import models

api_router = APIRouter()
api_router.include_router(structure.router)
api_router.include_router(operation.router)
api_router.include_router(resource.router)
api_router.include_router(iam.router, tags=[DocTag.IAM_USER])
api_router.include_router(ref.router, tags=[DocTag.REF])
api_router.include_router(integration.router)


# ----------------------------------- Base Endpoints -----------------------------------
# NOTE: All of these endpoints start with the settings.API_PREFIX (set in app/main.py)


@api_router.get("/health-check", tags=[DocTag.MISC])
@api_router.head("/health-check", include_in_schema=False)
def api_health_check(db: ReadSession):
    try:
        db.exec(select(1)).one()
    except Exception as e:
        raise HTTPException(status.HTTP_503_SERVICE_UNAVAILABLE, str(e))
    return PlainTextResponse("<3", status.HTTP_200_OK)


@api_router.get("/health-check/sync-worker", tags=[DocTag.MISC])
@api_router.head("/health-check/sync-worker", include_in_schema=False)
async def sync_health_check(pool: JobPool, timeout_sec: int = 10):
    job = await pool.enqueue_job("health_check")
    if job is None:
        raise HTTPException(status.HTTP_503_SERVICE_UNAVAILABLE, ErrMsg.NO_QUEUE)

    try:
        if await job.result(timeout=timeout_sec):
            return PlainTextResponse("<3", status.HTTP_200_OK)
    except TimeoutError:
        pass
    raise HTTPException(status.HTTP_503_SERVICE_UNAVAILABLE, ErrMsg.NO_WORKER)


# Redirect people to the /docs page if it looks like they need help
@api_router.get("/", include_in_schema=False)
@api_router.get("/help", include_in_schema=False)
async def redirect_to_docs():
    return RedirectResponse(
        f"{settings.API_PREFIX}/docs", status.HTTP_301_MOVED_PERMANENTLY
    )


# Customized /docs page
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


def mermaid_erd(include_cols=True) -> str:
    def tname(t: Table) -> str:  # NOTE: construct node name for a table
        return "".join(seg.capitalize() for seg in t.name.split("_"))

    def ctxt(c: Column) -> str:  # NOTE: get "type name FK/PK" for col def in table
        keys = " ".join(["PK"] * c.primary_key + ["FK"] * bool(c.foreign_keys))
        return f'\t\t{str(c.type).upper().split("(")[0]} {c.name} "{keys}"'

    def tblines(t: Table) -> list[str]:  # NOTE: define table node (w or w/o col lines)
        node = f"\t{tname(t)}:::{t.schema}"
        return [f"{node} {{", *map(ctxt, t.columns), "\t}"] if include_cols else [node]

    def conn(t: Table, fk: ForeignKey) -> str:  # NOTE: Draw 1:M conn from t using fk
        return f'\t\t{tname(fk.column.table)} ||--o{{ {tname(t)} : ""'

    def incl(fk: ForeignKey) -> bool:  # NOTE: Filter most unit fks, there are too many.
        skip_unit = fk.column.table.name != "unit" or fk.parent.table.name == "crop"
        skip_self = fk.parent.table.name != fk.column.table.name
        return skip_unit and skip_self

    def rels(t: Table) -> list[str]:  # NOTE: Output all fks that connect to t
        return [conn(t, fk) for c in t.columns for fk in c.foreign_keys if incl(fk)]

    schemas = {  # NOTE: determines table colors and the output order by schema.
        "iam": "#03b7bf",
        "integration": "#ffde00",
        "ref": "#eb6156",
        "structure": "#55a1ff",
        "resource": "#ff7d35",
        "operation": "#00b572",
    }
    for sch in SQLModel.metadata._schemas - set(schemas.keys()):
        schemas[sch] = "#cccccc"
    colors = [f"\tclassDef {s} stroke:{c}" for (s, c) in schemas.items()]
    ts = SQLModel.metadata.tables.values()
    ts = sorted(ts, key=lambda t: list(schemas.keys()).index(t.schema or ""))
    lines = ["erDiagram"] + colors + [ln for t in ts for ln in tblines(t) + rels(t)]
    return "\n\t\t".join(lines)


@api_router.get("/erd", tags=[DocTag.MISC], response_class=HTMLResponse)
def get_database_diagram(simple: bool = False):
    return f"""
<!doctype html><html>
<head>
    <meta charset="utf-8">
    <title>FieldLedger ERD</title>
    <style>
        body {{
            box-sizing: border-box;
            max-width: 1460px;
            margin: 0 auto;
            padding: 8px;
            font-family: sans-serif;
            background: #1c2022;
            color: #d2d6d8;
        }}
    </style>
</head>
<body>
    <h1 style="{{font-size: 36px; margin: 50px 20px;}}">FieldLedger ERD</h1>
    <button id="svg-btn">Download SVG</button>
    <button id="png-btn">Download PNG</button>
    <pre class="mermaid">
        {mermaid_erd(not simple)}
    </pre>
    <script type="module">
        import mermaid from 'https://cdn.jsdelivr.net/npm/mermaid@11/dist/mermaid.esm.min.mjs';
        mermaid.initialize({{theme: "dark", look: "handDrawn"}});
    </script>
<script src="https://cdn.jsdelivr.net/npm/canvg/dist/browser/canvg.min.js"></script>

<script>
document.getElementById("svg-btn").onclick=()=>{{
    const svg=document.querySelector(".mermaid svg");
    const data=new XMLSerializer().serializeToString(svg);
    const a=document.createElement("a");
    a.href=URL.createObjectURL(new Blob([data],{{type:"image/svg+xml"}}));
    a.download="fieldledger-erd.svg";
    a.click();
}};

document.getElementById("png-btn").onclick=async()=>{{
    const svg=document.querySelector(".mermaid svg");
    const data=new XMLSerializer().serializeToString(svg);

    const canvas=document.createElement("canvas");
    const ctx=canvas.getContext("2d");

    canvas.width=svg.viewBox.baseVal.width||svg.getBBox().width;
    canvas.height=svg.viewBox.baseVal.height||svg.getBBox().height;

    const v=await Canvg.fromString(ctx,data);
    await v.render();

    const a=document.createElement("a");
    a.href=canvas.toDataURL("image/png");
    a.download="fieldledger-erd.png";
    a.click();
}};
</script>
</body>
</html>
"""


# @api_router.post("/erd/layout")
# async def save_layout(data: dict):
#     save_erd_layout(data)
#     return {"ok": True}


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
