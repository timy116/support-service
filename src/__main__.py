import uvicorn

from app.core.config import settings


def run_dev_server() -> None:
    """Run the uvicorn server in development environment."""
    uvicorn.run(
        "app.main:create_app",  # path to the ASGI application
        host=settings.UVICORN_HOST,
        port=settings.UVICORN_PORT,
        reload=settings.DEBUG,
        factory=True,
    )


if __name__ == "__main__":
    run_dev_server()
