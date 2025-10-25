"""
FastAPI middleware for logging HTTP requests and responses.
"""

import time
from typing import Callable

from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware

from app.utils.logger import log_request_response


class LoggingMiddleware(BaseHTTPMiddleware):
    """
    Middleware to log HTTP requests and responses.

    Logs request method, path, status code, duration, and user context if available.
    """

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """
        Process the request and log the details.

        Args:
            request: The incoming HTTP request
            call_next: The next middleware or route handler

        Returns:
            The HTTP response
        """
        # Record start time
        start_time = time.time()

        # Extract user ID from request if available (from auth middleware)
        user_id = getattr(request.state, "user_id", None)

        # Process the request
        response = await call_next(request)

        # Calculate duration
        duration_ms = (time.time() - start_time) * 1000

        # Log the request/response
        log_request_response(
            method=request.method,
            path=str(request.url.path),
            status_code=response.status_code,
            duration_ms=duration_ms,
            user_id=user_id,
            query_params=dict(request.query_params) if request.query_params else None,
            user_agent=request.headers.get("user-agent"),
            remote_addr=request.client.host if request.client else None,
        )

        return response
