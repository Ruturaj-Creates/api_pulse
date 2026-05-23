# API Pulse

API uptime monitoring backend — track endpoint health, response time, and uptime.

Built step-by-step with **FastAPI**, **PostgreSQL**, **SQLAlchemy**, and **Alembic**.

---

## Step 2 — Database (current)

You have:

- SQLAlchemy models: `User`, `Endpoint`, `MonitoringLog`, `Alert`
- Async DB session (`app/db/session.py`) with `get_db` dependency
- Alembic migrations in `alembic/versions/`
- `/health` reports database `connected` / `disconnected`

### Run migrations (after pulling new code)

```powershell
cd e:\projects\api_pulse
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
alembic upgrade head
```

### Verify tables in PostgreSQL

```sql
\dt
-- or in pgAdmin: api_pulse → Schemas → public → Tables
```

Expected tables: `users`, `endpoints`, `monitoring_logs`, `alerts`, `alembic_version`

---

## Step 1 — Project foundation

You have:

- FastAPI app with `/` and `/health`
- Environment-based config (`app/core/config.py`)
- Docker Compose for PostgreSQL (optional if you use local Postgres)
- `requirements.txt` and `.env.example`

### Prerequisites

- Python 3.11+ ([python.org](https://www.python.org/downloads/))
- Docker Desktop ([docker.com](https://www.docker.com/products/docker-desktop/))
- Git (optional but recommended)

### Setup

```powershell
# 1. Go to the project
cd e:\projects\api_pulse

# 2. Create a virtual environment
python -m venv .venv

# 3. Activate it (Windows PowerShell)
.\.venv\Scripts\Activate.ps1

# 4. Install dependencies
pip install -r requirements.txt

# 5. Copy environment file
copy .env.example .env

# 6. Ensure PostgreSQL is running (local install OR: docker compose up -d)
# 7. Apply database migrations
alembic upgrade head

# 8. Run the API
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

Open:

- API root: http://localhost:8000/
- Health: http://localhost:8000/health
- Swagger docs: http://localhost:8000/docs

### First Git commit (suggested)

```powershell
git init
git add .
git commit -m "chore: scaffold API Pulse with FastAPI, config, and Docker Postgres"
```

---

## Roadmap (upcoming steps)

| Step | Topic |
|------|--------|
| 2 | Database — SQLAlchemy models, async session, Alembic ✅ |
| 3 | Authentication — register, login, JWT ← next |
| 4 | Endpoints CRUD — users add URLs to monitor |
| 5 | Health checker — httpx + background scheduler |
| 6 | Monitoring logs & alerts |
| 7 | Dashboard APIs |

---

## Project layout

```
backend/   (repo root: api_pulse)
├── app/
│   ├── api/          # HTTP routes (routers)
│   ├── core/         # Config, security constants
│   ├── models/       # Database tables (ORM)
│   ├── schemas/      # API input/output (Pydantic)
│   ├── services/     # Business logic
│   ├── db/           # Engine, sessions, migrations
│   ├── utils/        # Helpers
│   ├── workers/      # Scheduled health checks
│   └── main.py       # App entry point
├── alembic/          # (Step 2) DB migrations
├── docker-compose.yml
├── Dockerfile
├── requirements.txt
└── .env.example
```

---

## License

MIT (add your own license if needed)
