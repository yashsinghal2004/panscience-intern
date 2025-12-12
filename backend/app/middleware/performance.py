"""Performance tracking middleware."""

import time
import logging
from typing import Callable
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware

logger = logging.getLogger(__name__)


class PerformanceMiddleware(BaseHTTPMiddleware):
    """Middleware to track request performance."""
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """Track request timing."""
        start_time = time.time()
        
        response = await call_next(request)
        
        process_time = time.time() - start_time
        process_time_ms = process_time * 1000
        
        # Add timing header
        response.headers["X-Process-Time"] = str(process_time_ms)
        
        # Log slow requests
        if process_time_ms > 1000:
            logger.warning(
                f"Slow request: {request.method} {request.url.path} "
                f"took {process_time_ms:.2f}ms"
            )
        
        return response









