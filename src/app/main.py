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


tags_metadata = [
    {
        "name": "Fruits Origin Products",
        "description": "The daily report of fruits origin products send by the AFA(Agricultural Food Agency).",
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

app.mount("/static", StaticFiles(directory="src/app/static"), name="static")

# Add the router responsible for all /api/ endpoint requests
app.include_router(api.router)


@app.get("/")
async def root():
    return {"message": "Hello World"}


@app.get("/hello/{name}")
async def say_hello(name: str):
    return {"message": f"Hello {name}"}
