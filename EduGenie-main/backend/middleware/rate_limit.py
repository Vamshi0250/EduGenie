"""
EduGenie — Basic Rate Limiting Middleware
In-memory sliding-window limiter per client IP. Good enough for a single-
process deployment (Render free tier, one uvicorn worker); if you scale to
multiple workers/instances, swap the backing store for Redis.
"""

import time
from collections import defaultdict, deque
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse

# Paths that should be rate-limited — /api/* endpoints plus the top-level
# alias routes that also hit Gemini (/qa, /explain, /quiz, /summarize,
# /learn/recommendations). Health checks, static files, and the root page
# are intentionally excluded.
_RATE_LIMITED_PREFIXES = ("/api/", "/qa", "/explain", "/quiz", "/summarize", "/learn/")


class RateLimitMiddleware(BaseHTTPMiddleware):
    def __init__(self, app, max_requests: int = 30, window_seconds: int = 60):
        super().__init__(app)
        self.max_requests = max_requests
        self.window_seconds = window_seconds
        self._hits: dict[str, deque] = defaultdict(deque)

    async def dispatch(self, request, call_next):
        # Only rate-limit AI-backed endpoints — health, root, static, and auth are free.
        path = request.url.path
        if path.startswith("/api/auth/"):
            return await call_next(request)
        if not any(path.startswith(prefix) for prefix in _RATE_LIMITED_PREFIXES):
            return await call_next(request)

        client_ip = request.client.host if request.client else "unknown"
        now = time.monotonic()
        hits = self._hits[client_ip]

        while hits and now - hits[0] > self.window_seconds:
            hits.popleft()

        if len(hits) >= self.max_requests:
            retry_after = int(self.window_seconds - (now - hits[0]))
            return JSONResponse(
                status_code=429,
                content={"detail": "Too many requests. Please slow down."},
                headers={"Retry-After": str(max(retry_after, 1))},
            )

        hits.append(now)
        return await call_next(request)
