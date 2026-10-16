# GEIDIMCP-102 — Geidi AI Spend Manager (COSTRA)

AI cost tracking and billing integration for Anthropic/Claude and OpenAI/ChatGPT.

## Quick start

### Backend

```bash
cd backend
python -m venv .venv
# Windows:
.venv\Scripts\activate
pip install -r requirements.txt

# Copy and configure env
cp ../backend.env .env
# Edit .env: set DATABASE_URL and JWT_SECRET_KEY

# Apply migrations
alembic upgrade head

# Seed admin user
python seed_admin.py

# Start API
uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

### Frontend

```bash
cd frontend
npm install

# Copy and configure env
cp ../frontend.env .env

npm run dev
```

Open http://localhost:5173 and sign in with `admin@geidi.com` / `changeme`.

## Running tests

```bash
cd backend
pytest tests/unit/ -v --cov=app/services --cov-report=term-missing
```

## Architecture

See `tasks/plan.md` for the full implementation plan and architecture decisions.  
Core requirements: `Core Docs/BRD.md`, `Core Docs/TDD.md`, `Core Docs/GEIDIMCP-102_FER_BER.md`.

## Key invariants

- All monetary amounts stored as `DECIMAL(20,6)` — zero float usage
- Idempotent ingestion: re-running a sync or re-uploading a file produces the same DB state
- Coverage metadata per month: unavailable months are explicit, never silently zero
- AuditEvent written in the same transaction as every write operation
- No API keys or secrets in any HTTP response body
