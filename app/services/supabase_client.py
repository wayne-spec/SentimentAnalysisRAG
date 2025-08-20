from typing import Optional
from supabase import create_client, Client
from app.core.config import settings
import logging


_logger = logging.getLogger(__name__)


_client: Optional[Client] = None


def get_supabase() -> Client:
    global _client
    if _client is None:
        if not settings.SUPABASE_URL or not settings.SUPABASE_SERVICE_ROLE_KEY:
            raise RuntimeError("Supabase env vars missing: SUPABASE_URL or SUPABASE_SERVICE_ROLE_KEY")
        _client = create_client(settings.SUPABASE_URL, settings.SUPABASE_SERVICE_ROLE_KEY)
        _logger.info("Supabase client initialized")
    return _client