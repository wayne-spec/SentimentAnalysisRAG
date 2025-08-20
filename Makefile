.PHONY: run test docker-build docker-run fmt


run:
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000


test:
pytest -q


docker-build:
docker build -t rag-backend:dev .


docker-run:
docker run --rm -p 8000:8000 --env-file .env rag-backend:dev