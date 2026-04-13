from fastapi import HTTPException, status

from app.services.cache_service import delete_key, get_counter, increment_counter


async def enforce_rate_limit(
    key: str, limit: int, window_seconds: int, detail: str = "Too many requests"
) -> None:
    count = await increment_counter(key, window_seconds)
    if count > limit:
        raise HTTPException(status_code=status.HTTP_429_TOO_MANY_REQUESTS, detail=detail)


async def ensure_login_not_locked(phone: str) -> None:
    failures = await get_counter(f"auth:failures:{phone}")
    if failures >= 100:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Too many failed login attempts. Try again later.",
        )


async def record_login_failure(phone: str) -> int:
    return await increment_counter(f"auth:failures:{phone}", ttl_seconds=900)


async def clear_login_failures(phone: str) -> None:
    await delete_key(f"auth:failures:{phone}")
