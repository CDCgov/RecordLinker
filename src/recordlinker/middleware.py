import logging
import time

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request

# Initialize logger
logger = logging.getLogger("recordlinker.access")


class AccessLogMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        """
        Log the details of the request and response. This custom middleware is meant to
        be used instead of the default Uvicorn access log middleware.  As such, it provides
        more information about the request including processing time and correlation ID.
        """
        # Record the start time of the request
        start_time = time.time()
        # Process the request and get the response
        response = await call_next(request)
        data = {
            # Record the end time after the response
            "process_time": (time.time() - start_time) * 1000,
            # Record the correlation ID, if present
            "correlation_id": request.headers.get("X-Request-ID", "-"),
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
        logger.info(msg, data)
        return response
