# RAG Analysis Backend (Phase 1)


FastAPI scaffold with Supabase SDK, protected `/analyze` stub, health endpoint, and Docker setup.


## Quick Start (Local)


```bash
cd backend
cp .env.example .env # fill values
python -m venv .venv && source .venv/bin/activate # Windows: .venv\\Scripts\\activate
pip install -r requirements.txt
make run