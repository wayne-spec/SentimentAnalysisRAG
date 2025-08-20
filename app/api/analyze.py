# app/api/analyze.py
from fastapi import APIRouter, Depends, status
from app.core.security import require_shared_secret
from app.services.supabase_client import get_supabase
from app.services.embeddings import ensure_embedding_for_feedback
from app.services.sentiment import classify_sentiment
from app.services.summarize import summarise_with_fallback
import logging
from collections import defaultdict

router = APIRouter()
_logger = logging.getLogger(__name__)


@router.post("/analyze", status_code=status.HTTP_202_ACCEPTED, dependencies=[Depends(require_shared_secret)])
async def analyze():
    """
    Full pipeline (MVP):
    - Fetch feedback rows not present in feedback_embeddings
    - Ensure embeddings for new rows (if provider configured)
    - Classify sentiment for each feedback row
    - Group feedback by course_id where user role = 'lecturer'
    - Insert analysis_results row per course with counts and summary
    """
    supabase = get_supabase()

    # 1) get all feedback with course and user information, filtering for lecturer role
    fb_resp = supabase.table("feedback").select("*, courses!inner(*, users!inner(*))").eq("courses.users.role", "lecturer").execute()
    if fb_resp.error:
        _logger.error("Failed to fetch feedback: %s", fb_resp.error)
        return {"status": "error", "message": "failed to fetch feedback"}

    all_feedback = fb_resp.data or []
    _logger.info("Fetched %d feedback rows for lecturer courses", len(all_feedback))

    # 2) find which feedback ids lack embeddings
    emb_resp = supabase.table("feedback_embeddings").select("feedback_id").execute()
    existing = {r["feedback_id"] for r in (emb_resp.data or [])}
    to_process = [r for r in all_feedback if r["id"] not in existing]
    _logger.info("New feedback (no embeddings): %d", len(to_process))

    # 3) generate embeddings (best-effort)
    for fb in to_process:
        try:
            ensure_embedding_for_feedback(supabase, fb)
        except Exception as e:
            _logger.exception("Embedding generation failed for %s: %s", fb.get("id"), e)

    # 4) run sentiment classification for all feedback (we will upsert into a local list)
    sentiments = {}
    for fb in all_feedback:
        sid = fb["id"]
        sentiment = classify_sentiment(fb.get("comments"), fb.get("overall_rating"))
        sentiments[sid] = sentiment

    # 5) group by course_id (only for courses taught by lecturers)
    grouping = defaultdict(list)
    for fb in all_feedback:
        course_id = fb["course_id"]
        grouping[course_id].append(fb)

    # 6) for each group, compute counts, summary, insights, and insert to analysis_results
    results_inserted = 0
    for course_id, feedbacks in grouping.items():
        pos = sum(1 for f in feedbacks if sentiments.get(f["id"]) == "positive")
        neu = sum(1 for f in feedbacks if sentiments.get(f["id"]) == "neutral")
        neg = sum(1 for f in feedbacks if sentiments.get(f["id"]) == "negative")

        comments = [f.get("comments") or "" for f in feedbacks]
        summary_ins = summarise_with_fallback(comments)
        summary = summary_ins.get("summary", "")
        insights = summary_ins.get("insights", "")

        # insert result
        payload = {
            "course_id": course_id,
            "analysis_type": "sentiment",  # Added required field from schema
            "result_data": {  # Changed to match schema structure
                "positive_count": pos,
                "neutral_count": neu,
                "negative_count": neg,
                "summary": summary,
                "insights": insights,
            },
            "confidence_score": None  # Optional field
        }
        insert_res = supabase.table("analysis_results").insert(payload).execute()
        if insert_res.error:
            _logger.error("Failed to insert analysis_results for course %s: %s", course_id, insert_res.error)
        else:
            results_inserted += 1

    return {
        "status": "ok",
        "feedback_count": len(all_feedback),
        "groups_processed": len(grouping),
        "analysis_inserted": results_inserted,
    }
