import logging
import time
import traceback
import typing

import asgi_correlation_id
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request

DEFAULT_CORRELATION_ID_LENGTH = 12
ACCESS_LOGGER = logging.getLogger("recordlinker.access")
ERROR_LOGGER = logging.getLogger("recordlinker.error")


class CorrelationIdMiddleware(asgi_correlation_id.CorrelationIdMiddleware):
    """
    Override the default ASGI correlation ID middleware to provide a
    default correlation ID length.
    """

    def __init__(
        self, app: typing.Callable, correlation_id_length: int = DEFAULT_CORRELATION_ID_LENGTH
    ):
        super().__init__(app)
        self.transformer = lambda a: a[:correlation_id_length]


class AccessLogMiddleware(BaseHTTPMiddleware):
    """
    This custom access logging middleware is meant to be used instead of the default
    Uvicorn access log middleware.  As such, it provides more information about the
    request including processing time and correlation ID.
    """

    async def dispatch(self, request: Request, call_next):
        """
        Log the request and response details.
        """
        # Record the start time of the request
        start_time = time.time()
        # Process the request and get the response
        response = await call_next(request)
        data = {
            # Record the end time after the response
            "process_time": (time.time() - start_time) * 1000,
            # Record the correlation ID, if present
            "correlation_id": request.headers.get(CorrelationIdMiddleware.header_name, "-"),
            # Log details of the request
            "client_ip": getattr(request.client, "host", "-"),
            "method": request.method,
            "path": request.url.path,
            "http_version": request.scope.get("http_version", "unknown"),
            "status_code": response.status_code,
        }
        msg = (
            '[%(correlation_id)s] %(client_ip)s - "%(method)s %(path)s '
            'HTTP/%(http_version)s" %(status_code)d %(process_time).2fms'
        )
        # Log the message
        ACCESS_LOGGER.info(msg, data)
        return response


class TracebackMiddleware(BaseHTTPMiddleware):
    """
    This custom traceback middleware is meant to be used instead of the default
    Uvicorn traceback middleware.  As such, it provides more information about the
    request including processing time and correlation ID.
    """

    async def dispatch(self, request: Request, call_next):
        """
        Catch any exceptions and log them to the error logger.
        """
        try:
            return await call_next(request)
        except Exception:
            data = {
                "correlation_id": request.headers.get(CorrelationIdMiddleware.header_name, "-"),
                "traceback": traceback.format_exc(),
            }
            ERROR_LOGGER.error("uncaught exception", extra=data)
            raise
