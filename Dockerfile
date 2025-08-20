# syntax=docker/dockerfile:1


# ===== builder =====
FROM python:3.11-slim AS builder
WORKDIR /app
ENV PYTHONDONTWRITEBYTECODE=1 \
PYTHONUNBUFFERED=1


RUN apt-get update && apt-get install -y --no-install-recommends build-essential && rm -rf /var/lib/apt/lists/*


COPY requirements.txt .
RUN pip install --upgrade pip && pip wheel --wheel-dir /wheels -r requirements.txt


# ===== runtime =====
FROM python:3.11-slim
WORKDIR /app
ENV PYTHONDONTWRITEBYTECODE=1 \
PYTHONUNBUFFERED=1 \
PORT=8000


COPY --from=builder /wheels /wheels
RUN pip install --no-index --find-links=/wheels -r /wheels/requirements.txt || pip install --no-index --find-links=/wheels fastapi uvicorn[standard] pydantic pydantic-settings httpx supabase pytest pytest-asyncio


COPY app ./app
COPY requirements.txt ./requirements.txt


EXPOSE 8000
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]