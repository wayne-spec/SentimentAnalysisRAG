from fastapi import Depends, Header, HTTPException, status
from app.core.config import settings


async def require_shared_secret(authorization: str | None = Header(default=None)) -> None:
    """Simple bearer token check for Edge Function -> FastAPI calls.
    Expect: Authorization: Bearer <ANALYZE_SHARED_SECRET>
    """
    if not authorization or not authorization.lower().startswith("bearer "):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Missing bearer token")

    token = authorization.split(" ", 1)[1].strip()
    if token != settings.ANALYZE_SHARED_SECRET:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")

    return None