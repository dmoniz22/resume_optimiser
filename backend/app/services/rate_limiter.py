from fastapi import Request, HTTPException, status
from valkey import Valkey
from app.config import settings

redis_client = Valkey.from_url(settings.REDIS_URL)


async def check_rate_limit(user_id: str, max_requests: int = 10, window_seconds: int = 1) -> bool:
    key = f"rate_limit:{user_id}"
    current = redis_client.get(key)
    if current and int(current) >= max_requests:
        return False
    pipe = redis_client.pipeline()
    pipe.incr(key)
    pipe.expire(key, window_seconds)
    pipe.execute()
    return True


async def rate_limit_dependency(request: Request):
    user_id = getattr(request.state, "user_id", None)
    if not user_id:
        token = request.headers.get("authorization", "").replace("Bearer ", "")
        if token:
            key = f"rate_limit:token:{token[:20]}"
        else:
            key = f"rate_limit:ip:{request.client.host if request.client else 'unknown'}"
    else:
        key = f"rate_limit:{user_id}"

    allowed = await check_rate_limit(key)
    if not allowed:
        raise HTTPException(status_code=status.HTTP_429_TOO_MANY_REQUESTS, detail="Rate limit exceeded")
