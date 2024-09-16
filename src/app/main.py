import os
from contextlib import asynccontextmanager
from typing import Set

import aioredis
from fastapi import FastAPI, status
from fastapi.responses import ORJSONResponse
from fastapi.staticfiles import StaticFiles

from app import api
from app.core.config import settings
from app.core.enums import FileTypes
from app.db import init_db
from app.utils.email_processors import GmailProcessor, GmailDailyReportSearcher
from app.utils.file_processors import DocumentProcessor


@asynccontextmanager
async def lifespan(application: FastAPI):
    await init_db.init()
    application.state.redis_pool = await aioredis.from_url(
        settings.REDIS_URI,
        encoding="utf-8",
        decode_responses=True,
    )

    yield


tags_metadata = [
    {
        "name": "Daily Reports",
        "description": "The daily report send by the AFA(Agricultural Food Agency).",
    },
]

# Common response codes
responses: Set[int] = {
    status.HTTP_400_BAD_REQUEST,
    status.HTTP_401_UNAUTHORIZED,
    status.HTTP_403_FORBIDDEN,
    status.HTTP_404_NOT_FOUND,
    status.HTTP_500_INTERNAL_SERVER_ERROR,
}

app = FastAPI(
    debug=settings.DEBUG,
    title=settings.PROJECT_NAME,
    version=settings.PROJECT_VERSION,
    description="Fast and reliable support service powered by FastAPI and MongoDB.",
    # Set current documentation specs to v1
    openapi_url=f"/api/{settings.API_V1_STR}/openapi.json",
    docs_url=None,
    redoc_url=None,
    default_response_class=ORJSONResponse,
    openapi_tags=tags_metadata,
    lifespan=lifespan,
)

static_dir = os.environ.get('STATIC_DIR', 'src/app/static')
app.mount("/static", StaticFiles(directory=static_dir), name="static")

# Add the router responsible for all /api/ endpoint requests
app.include_router(api.router)


@app.get("/")
async def root():
    p = GmailProcessor(DocumentProcessor(FileTypes.PDF), GmailDailyReportSearcher)
    p.process('113年09月13日敏感性農產品產地價格日報表')

    return {"message": "Hello World"}


@app.get("/hello/{name}")
async def say_hello(name: str):
    return {"message": f"Hello {name}"}
