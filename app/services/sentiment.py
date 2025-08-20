# app/services/sentiment.py
import logging
from typing import Optional

_logger = logging.getLogger(__name__)

POSITIVE_KEYWORDS = {"good", "great", "excellent", "well", "enjoy", "love", "helpful", "clear", "interactive"}
NEGATIVE_KEYWORDS = {"bad", "poor", "terrible", "boring", "hate", "confusing", "slow", "late", "delay", "unprepared"}


def classify_sentiment(comments: Optional[str], overall_rating: Optional[int] = None) -> str:
    """
    Deterministic sentiment classifier for MVP:
    - If overall_rating is present: >=4 -> positive, ==3 -> neutral, <=2 -> negative
    - Else, keyword scan on comments: if more positive than negative -> positive, etc.
    - Defaults to neutral.
    Returns: "positive" | "neutral" | "negative"
    """
    if overall_rating is not None:
        try:
            r = int(overall_rating)
            if r >= 4:
                return "positive"
            if r == 3:
                return "neutral"
            return "negative"
        except Exception:
            pass

    if not comments:
        return "neutral"

    text = comments.lower()
    pos = sum(1 for k in POSITIVE_KEYWORDS if k in text)
    neg = sum(1 for k in NEGATIVE_KEYWORDS if k in text)
    if pos > neg:
        return "positive"
    if neg > pos:
        return "negative"
    return "neutral"
