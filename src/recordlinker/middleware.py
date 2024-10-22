import logging
import time
import typing

import asgi_correlation_id
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request

ACCESS_LOGGER_NAME = "recordlinker.access"
DEFAULT_CORRELATION_ID_LENGTH = 12


class CorrelationIdMiddleware(asgi_correlation_id.CorrelationIdMiddleware):
    """
    Override the default ASGI correlation ID middleware to provide a
    default correlation ID length.
    """
    def __init__(self, app: typing.Callable, correlation_id_length: int = DEFAULT_CORRELATION_ID_LENGTH):
        super().__init__(app)
        self.transformer = lambda a: a[:correlation_id_length]


class AccessLogMiddleware(BaseHTTPMiddleware):
    """
    This custom access logging middleware is meant to be used instead of the default
    Uvicorn access log middleware.  As such, it provides more information about the
    request including processing time and correlation ID.
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.logger = logging.getLogger(ACCESS_LOGGER_NAME)

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
            "client_ip": request.client.host,
            "method": request.method,
            "path": request.url.path,
            "http_version": request.scope.get("http_version", "unknown"),
            "status_code": response.status_code,
        }
        msg = (
            '%(client_ip)s - "%(method)s %(path)s ',
            'HTTP/%(http_version)s" %(status_code)d %(process_time).2fms',
        )
        # Log the message
        self.logger.info(msg, data)
        return response
