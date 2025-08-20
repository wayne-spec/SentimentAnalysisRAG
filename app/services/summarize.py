# app/services/summarize.py
import logging
from typing import List, Dict, Optional
from app.core.config import settings

_logger = logging.getLogger(__name__)

try:
    import openai
except Exception:
    openai = None


MAX_COMMENTS_FOR_PROMPT = 50
MAX_CHARS = 3000


def _truncate_comments(comments: List[str], max_chars: int = MAX_CHARS) -> List[str]:
    out = []
    total = 0
    for c in comments:
        if total + len(c) > max_chars:
            break
        out.append(c)
        total += len(c)
    return out


def summarise_with_fallback(comments: List[str]) -> Dict[str, str]:
    """
    If OPENAI_API_KEY available, call Chat API to get a structured summary + insights.
    Otherwise return a simple concatenated/short extractive summary.
    """
    comments = comments[:MAX_COMMENTS_FOR_PROMPT]
    if not comments:
        return {"summary": "", "insights": ""}

    if settings.OPENAI_API_KEY and openai is not None:
        try:
            openai.api_key = settings.OPENAI_API_KEY
            prompt = build_prompt_for_comments(comments)
            resp = openai.ChatCompletion.create(
                model="gpt-4o-mini",  # If unavailable change to gpt-4o or gpt-4o-mini-preview etc.
                messages=[
                    {"role": "system", "content": "You are a helpful summarizer that produces a short summary and 2-3 actionable insights."},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=512,
                temperature=0.0,
            )
            text = resp["choices"][0]["message"]["content"].strip()
            # Try to split into summary and insights by delimiter
            # Expect user to structure output like:
            # Summary:
            # ...
            # Insights:
            # - ...
            if "Insights:" in text:
                parts = text.split("Insights:", 1)
                summary = parts[0].replace("Summary:", "").strip()
                insights = parts[1].strip()
            else:
                # best-effort
                summary = text[:1000]
                insights = text[1000:2000]
            return {"summary": summary, "insights": insights}
        except Exception as e:
            _logger.exception("OpenAI summarization failed, falling back: %s", e)

    # Fallback simple summarization: top N non-empty comments concatenated
    truncated = _truncate_comments([c.strip() for c in comments if c.strip()])
    summary = " | ".join(truncated[:5])
    insights = ""
    # heuristic insights:
    lc = " ".join(truncated).lower()
    if "interactive" in lc or "particip" in lc:
        insights += "Students appreciate interactive teaching. "
    if "late" in lc or "delay" in lc or "slow" in lc:
        insights += "Students mention delays or slowness in course delivery. "
    return {"summary": summary, "insights": insights.strip()}
    

def build_prompt_for_comments(comments: List[str]) -> str:
    # Build a compact user prompt for the LLM
    sample = "\n".join([f"- {c}" for c in comments[:MAX_COMMENTS_FOR_PROMPT]])
    prompt = f"""Here are student feedback comments. Produce:
1) A concise 2-3 sentence SUMMARY describing overall sentiment and themes.
2) 3 short ACTIONABLE INSIGHTS (bullet points).
Keep output labeled clearly like:
Summary:
<two sentences>

Insights:
- ...
- ...
- ...
Comments:
{sample}
"""
    return prompt
