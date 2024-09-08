from contextlib import asynccontextmanager
from http import HTTPStatus
from typing import Set

from fastapi import FastAPI, status
from fastapi.exceptions import RequestValidationError
from fastapi.responses import ORJSONResponse
from fastapi.staticfiles import StaticFiles
from starlette.exceptions import HTTPException as StarletteHTTPException

from src.app import api
from src.app.core.config import settings
from src.app.db import init_db

@asynccontextmanager
async def lifespan(application: FastAPI):
    await init_db.init()
    yield


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
    lifespan=lifespan,
)


@app.get("/")
async def root():
    return {"message": "Hello World"}


@app.get("/hello/{name}")
async def say_hello(name: str):
    return {"message": f"Hello {name}"}
