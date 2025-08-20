from fastapi import APIRouter
from app.core.config import settings


router = APIRouter()


@router.get("/health")
async def health():
    return {
        "status": "ok",
        "env": settings.APP_ENV,
        "supabase_url_present": bool(settings.SUPABASE_URL),
    }