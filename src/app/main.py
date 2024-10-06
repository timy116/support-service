import os
from contextlib import asynccontextmanager
from http import HTTPStatus
from typing import Set

from fastapi import FastAPI, status
from fastapi.exceptions import RequestValidationError
from fastapi.responses import ORJSONResponse
from fastapi.staticfiles import StaticFiles
from redis import asyncio as aioredis
from starlette.exceptions import HTTPException as StarletteHTTPException

from app import api
from app.core.config import settings
from app.core.logging import configure_logging
from app.db import init_db
from app.schemas.error import APIValidationError, CommonHTTPError


@asynccontextmanager
async def lifespan(application: FastAPI):
    configure_logging()
    await init_db.init()
    application.state.redis_pool = await aioredis.from_url(settings.REDIS_URI)

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


def create_app():
    application = FastAPI(
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
        responses={
            status.HTTP_422_UNPROCESSABLE_ENTITY: {
                "description": "Validation Error",
                "model": APIValidationError,  # Adds OpenAPI schema for 422 errors
            },
            **{
                code: {
                    "description": HTTPStatus(code).phrase,
                    "model": CommonHTTPError,
                }
                for code in responses
            },
        },
    )
    static_dir = os.environ.get('STATIC_DIR', 'src/app/static')
    application.mount("/static", StaticFiles(directory=static_dir), name="static")
    # Add the router responsible for all /api/ endpoint requests
    application.include_router(api.router)
    if settings.USE_CORRELATION_ID:
        from app.middlewares.correlation import CorrelationMiddleware

        application.add_middleware(CorrelationMiddleware)

    # Custom HTTPException handler
    @application.exception_handler(StarletteHTTPException)
    async def http_exception_handler(_, exc: StarletteHTTPException) -> ORJSONResponse:
        return ORJSONResponse(
            content={
                "message": exc.detail,
            },
            status_code=exc.status_code,
            headers=exc.headers,
        )

    @application.exception_handler(RequestValidationError)
    async def custom_validation_exception_handler(
            _,
            exc: RequestValidationError,
    ) -> ORJSONResponse:
        return ORJSONResponse(
            content=APIValidationError.from_pydantic(exc).dict(exclude_none=True),
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        )

    return application


if __name__ == "__main__":
    app = create_app()
