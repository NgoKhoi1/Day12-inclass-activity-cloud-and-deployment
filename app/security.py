import hmac
import time
from collections import defaultdict, deque
from fastapi import Header, HTTPException, Request, status
from .settings import get_settings

# In-memory rate limiter for classroom/demo only.
# Production should use Redis or API Gateway level rate limiting.
_REQUESTS = defaultdict(deque)


def require_api_key(x_api_key: str | None = Header(default=None, alias="X-API-Key")) -> str:
    settings = get_settings()
    if not x_api_key or not hmac.compare_digest(x_api_key, settings.app_api_key):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing or invalid X-API-Key",
        )
    return x_api_key


def enforce_rate_limit(request: Request, api_key: str) -> None:
    settings = get_settings()
    now = time.time()
    window_start = now - 60
    key = f"{api_key}:{request.client.host if request.client else 'unknown'}"
    bucket = _REQUESTS[key]
    while bucket and bucket[0] < window_start:
        bucket.popleft()
    if len(bucket) >= settings.rate_limit_per_minute:
        raise HTTPException(status_code=429, detail="Rate limit exceeded. Try again later.")
    bucket.append(now)
