# app/services/embeddings.py
import logging
from typing import Optional, Dict, Any, List
from app.core.config import settings

_logger = logging.getLogger(__name__)

try:
    import openai
except Exception:
    openai = None


EMBEDDING_MODEL = "text-embedding-3-small"  # reasonable default; change if desired


async def generate_openai_embedding(text: str) -> List[float]:
    if openai is None:
        raise RuntimeError("openai package not installed")

    if not settings.OPENAI_API_KEY:
        raise RuntimeError("OPENAI_API_KEY not set")
    openai.api_key = settings.OPENAI_API_KEY

    # Use the new OpenAI python client or the older one; this uses openai.Embedding.create
    resp = openai.Embedding.create(input=text, model=EMBEDDING_MODEL)
    emb = resp["data"][0]["embedding"]
    return emb


def ensure_embedding_for_feedback(supabase_client, feedback_row: Dict[str, Any]) -> Optional[List[float]]:
    """
    Ensure an embedding exists for a given feedback row.
    If embedding already exists in DB, returns it.
    If missing and OPENAI_API_KEY available, generate and insert, then return it.
    If missing and no OPENAI_API_KEY, returns None.
    """
    feedback_id = feedback_row["id"]
    # check if present
    res = supabase_client.table("feedback_embeddings").select("embedding").eq("feedback_id", feedback_id).limit(1).execute()
    if res.error:
        _logger.error("Supabase error checking embeddings: %s", res.error)
    rows = res.data or []
    if rows:
        return rows[0].get("embedding")

    # missing -> try to generate
    text = feedback_row.get("comments") or ""
    text_for_embedding = f"{text}"  # could concat rating etc later

    if settings.OPENAI_API_KEY:
        try:
            emb = None
            # If caller runs in async loop but openai is synchronous, generate in sync
            emb = __import__("asyncio").get_event_loop().run_in_executor(None, lambda: generate_openai_embedding_sync(text_for_embedding))
            # but generate_openai_embedding_sync uses the sync openai client; for simplicity
        except Exception:
            # fallback to synchronous call if using blocking environment
            emb = generate_openai_embedding_sync(text_for_embedding)
        # insert into supabase
        insert_res = supabase_client.table("feedback_embeddings").insert({
            "feedback_id": feedback_id,
            "embedding": emb,
        }).execute()
        if insert_res.error:
            _logger.error("Failed to insert embedding for feedback %s: %s", feedback_id, insert_res.error)
        else:
            _logger.info("Inserted embedding for feedback %s", feedback_id)
        return emb
    else:
        _logger.info("OPENAI_API_KEY not set; skipping embedding for feedback %s", feedback_id)
        return None


def generate_openai_embedding_sync(text: str) -> List[float]:
    """Synchronous embedding helper for environments where async is not used."""
    if openai is None:
        raise RuntimeError("openai package not installed")
    if not settings.OPENAI_API_KEY:
        raise RuntimeError("OPENAI_API_KEY not set")
    openai.api_key = settings.OPENAI_API_KEY
    resp = openai.Embedding.create(input=text, model=EMBEDDING_MODEL)
    return resp["data"][0]["embedding"]
