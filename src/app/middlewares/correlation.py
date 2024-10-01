from contextvars import ContextVar
from typing import Callable, Optional, TypeAlias
from uuid import UUID, uuid4

import structlog
from starlette.datastructures import Headers, MutableHeaders
from starlette.types import ASGIApp, Message, Receive, Scope, Send
from structlog.stdlib import BoundLogger

"""
Correlation ID middleware implementation inspired from asgi-correlation-id project:
https://github.com/snok/asgi-correlation-id
"""

logger: BoundLogger = structlog.get_logger()

# Context variable to store the correlation ID
correlation_id: ContextVar[Optional[str]] = ContextVar("correlation_id", default=None)

IDGenerator: TypeAlias = Callable[[], str]
IDValidator: TypeAlias = Callable[[str], bool]
IDTransformer: TypeAlias = Callable[[str], str]


def is_valid_uuid4(uuid_string: str) -> bool:
    try:
        UUID(uuid_string, version=4)
    except ValueError:
        return False
    return True


class CorrelationMiddleware:
    __slots__ = (
        "app",
        "header",
        "id_generator",
        "id_validator",
        "id_transformer",
    )

    def __init__(
            self,
            app: ASGIApp,
            *,
            header: str = "X-Request-ID",
            id_generator: IDGenerator = lambda: uuid4().hex,
            id_validator: Optional[IDValidator] = is_valid_uuid4,
            id_transformer: Optional[IDTransformer] = lambda x: x,
    ):
        self.app = app
        self.header = header
        self.id_generator = id_generator
        self.id_validator = id_validator
        self.id_transformer = id_transformer

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        """
        This method will be called whenever an ASGI request is received by the middleware.
        It acts as the entry point for processing each request and is invoked by the ASGI server
        as part of the request handling pipeline.

        In any case, ASGI middleware must be callables that accept three arguments: scope, receive, and send.
        - scope is a dict holding information about the connection, where scope["type"] may be:
            - "http": for HTTP requests.
            - "websocket": for WebSocket connections.
            - "lifespan": for ASGI lifespan messages.
        - receive and send can be used to exchange ASGI event messages with the ASGI server.
          The type and contents of these messages depend on the scope type.

        You can see the more detailed explanation of the ASGI middleware in the  Starlette's official documentation:
        https://www.starlette.io/middleware/#writing-pure-asgi-middleware

        :param scope: ASGI scope dict.
        :param receive: ASGI receive callable.
        :param send: ASGI send callable.
        """

        # If the ASGI message is not an HTTP request, the middleware will pass the message to the next application.
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        header_value = Headers(scope=scope).get(self.header)

        if not header_value:
            id_ = self.id_generator()
        elif self.id_validator and not self.id_validator(header_value):
            id_ = self.id_generator()
            await logger.awarning(
                "Generated new correlation ID because the provided one was invalid",
                correlation_id=id_,
            )
        else:
            id_ = header_value

        if self.id_transformer:
            id_ = self.id_transformer(id_)

        correlation_id.set(id_)

        async def send_wrapper(message: Message):
            """
            This method is to add the correlation ID to the response headers.
            It is called when the response starts, ensuring the correlation ID is included in the response.

            :param message: ASGI message.
            """

            # check if the ASGI message being processed is the start of an HTTP response.
            if message["type"] == "http.response.start" and (
                    cid := correlation_id.get()
            ):
                headers = MutableHeaders(scope=message)
                headers[self.header] = cid
                headers["Access-Control-Expose-Headers"] = self.header
            await send(message)

        # Calls the next application in the ASGI stack, passing the `send_wrapper` function to handle the response.
        await self.app(scope, receive, send_wrapper)
