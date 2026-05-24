# API Pulse

API uptime monitoring backend — track endpoint health, response time, and uptime.

Built step-by-step with **FastAPI**, **PostgreSQL**, **SQLAlchemy**, and **Alembic**.

---

## Step 5 — Health checker (current)

Background scheduler + httpx async checks:

- APScheduler runs every `SCHEDULER_TICK_SECONDS` (default 30s)
- Checks endpoints whose interval has elapsed
- Saves rows to `monitoring_logs`
- Updates endpoint `status`, `last_checked_at`, `consecutive_failures`
- Marks **DOWN** after `FAILURE_THRESHOLD` consecutive failures (default 3)

New routes:

| Method | Path | Action |
|--------|------|--------|
| POST | `/api/v1/endpoints/{id}/check` | Run check now |
| GET | `/api/v1/endpoints/{id}/logs` | View check history |

### Quick test

1. Create an endpoint (Step 4) with a real URL e.g. `https://api.github.com/zen`
2. **POST /api/v1/endpoints/{id}/check** — returns log with `is_up: true`, `response_time_ms`
3. **GET /api/v1/endpoints/{id}** — `status` should be `"up"`, `last_checked_at` set
4. **GET /api/v1/endpoints/{id}/logs** — history of checks
5. Wait ~30–60s — scheduler runs automatically; more logs appear

Test failure: set `expected_status_code` to `404`, call `/check` — `is_up: false`, failures increment.

---

## Step 4 — Endpoint CRUD

Protected routes (JWT required):

| Method | Path | Action |
|--------|------|--------|
| POST | `/api/v1/endpoints` | Add URL to monitor |
| GET | `/api/v1/endpoints` | List your endpoints |
| GET | `/api/v1/endpoints/{id}` | Get one |
| PATCH | `/api/v1/endpoints/{id}` | Update settings |
| DELETE | `/api/v1/endpoints/{id}` | Delete |
| POST | `/api/v1/endpoints/{id}/pause` | Pause checks |
| POST | `/api/v1/endpoints/{id}/resume` | Resume checks |

### Quick test (Swagger)

1. Login and **Authorize** (see Step 3)
2. **POST /api/v1/endpoints**:
   ```json
   {
     "name": "GitHub Zen",
     "url": "https://api.github.com/zen",
     "http_method": "GET",
     "expected_status_code": 200,
     "check_interval_seconds": 60
   }
   ```
3. **GET /api/v1/endpoints** — should list your endpoint with `"status": "unknown"`
4. Try **GET /api/v1/endpoints/999** without owning it → **404**

---

## Step 3 — Authentication

You have:

- `POST /api/v1/auth/register` — create account
- `POST /api/v1/auth/login` — get JWT (form: username=email, password=...)
- `GET /api/v1/auth/me` — protected, requires Bearer token

### Quick test (Swagger)

1. Open http://localhost:8000/docs
2. **POST /api/v1/auth/register** with `{"email":"you@example.com","password":"secret123"}`
3. **POST /api/v1/auth/login** — click "Try it out", use `username` = your email, `password` = secret123
4. Copy `access_token`, click **Authorize**, paste token
5. **GET /api/v1/auth/me** — should return your user

### Quick test (curl)

```powershell
# Register
curl -X POST http://localhost:8000/api/v1/auth/register -H "Content-Type: application/json" -d "{\"email\":\"test@example.com\",\"password\":\"secret123\"}"

# Login (note: form-urlencoded, username field = email)
curl -X POST http://localhost:8000/api/v1/auth/login -d "username=test@example.com&password=secret123"

# Me (replace TOKEN)
curl http://localhost:8000/api/v1/auth/me -H "Authorization: Bearer TOKEN"
```

---

## Step 2 — Database

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
| 3 | Authentication — register, login, JWT ✅ |
| 4 | Endpoints CRUD — add URLs to monitor ✅ |
| 5 | Health checker — httpx + background scheduler ✅ |
| 6 | Monitoring logs & alerts ← next |
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
