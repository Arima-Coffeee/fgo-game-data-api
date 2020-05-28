import logging
import time

from fastapi import FastAPI, Request, status
from fastapi.responses import RedirectResponse, Response
from fastapi.staticfiles import StaticFiles

from .data.models.common import Settings
from .routers import nice, raw


logger = logging.getLogger()
settings = Settings()


app_description = """Provide raw and processed FGO game data.

Available documentation styles: [Swagger UI](/docs), [Redoc](/redoc).

If you encounter bugs or missing data, you can report them at the [Atlas Academy Discord](https://discord.gg/TKJmuCR).
"""
export_links = """

Preprocessed nice data:
[NA servant](/export/nice_servant_NA.json),
[NA CE](/export/nice_equip_NA.json),
[JP servant](/export/nice_servant_JP.json),
[JP CE](/export/nice_equip_JP.json).
"""

if settings.export_all_nice:
    app_description += export_links


app = FastAPI(title="FGO Game data API", description=app_description, version="0.1.0",)


@app.middleware("http")
async def add_process_time_header(request: Request, call_next):
    start_time = time.time()
    response = await call_next(request)
    process_time = int((time.time() - start_time) * 1000)
    response.headers["X-Process-Time"] = str(process_time)
    logger.info(f"Processed in {process_time}ms.")
    return response


app.include_router(
    nice.router, prefix="/nice", tags=["nice"],
)


app.include_router(
    raw.router, prefix="/raw", tags=["raw"],
)


@app.get(
    "/",
    status_code=status.HTTP_307_TEMPORARY_REDIRECT,
    response_class=Response,
    summary="Redirect to /docs",
    tags=["default"],
    response_description="307 redirect to /docs",
)
async def root():
    return RedirectResponse("/docs")


if settings.export_all_nice:
    app.mount("/export", StaticFiles(directory="export"), name="export")
