import time
import logging
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint

logger = logging.getLogger(__name__)


class RequestLoggingMiddleware(BaseHTTPMiddleware):
    """Middleware for logging request details"""

    async def dispatch(
        self, request: Request, call_next: RequestResponseEndpoint
    ) -> Response:
        # Log request details
        logger.info(
            f"Request: {request.method} {request.url.path} "
            f"Client: {request.client.host if request.client else 'Unknown'}"
        )

        try:
            response = await call_next(request)
            # Log response status
            logger.info(
                f"Response: {request.method} {request.url.path} "
                f"Status: {response.status_code}"
            )
            return response
        except Exception as e:
            logger.error(
                f"Error processing request: {request.method} {request.url.path} "
                f"Error: {str(e)}"
            )
            raise


class ResponseTimeMiddleware(BaseHTTPMiddleware):
    """Middleware for measuring and logging response times"""

    async def dispatch(
        self, request: Request, call_next: RequestResponseEndpoint
    ) -> Response:
        start_time = time.time()

        try:
            response = await call_next(request)

            # Calculate and log response time
            process_time = time.time() - start_time
            response.headers["X-Process-Time"] = str(process_time)

            # Log if response time exceeds threshold
            if process_time > 1.0:  # 1 second threshold
                logger.warning(
                    f"Slow response: {request.method} {request.url.path} "
                    f"Time: {process_time:.2f}s"
                )

            return response
        except Exception as e:
            process_time = time.time() - start_time
            logger.error(
                f"Error in request: {request.method} {request.url.path} "
                f"Time: {process_time:.2f}s Error: {str(e)}"
            )
            raise
