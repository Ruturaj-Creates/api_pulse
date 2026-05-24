# API Pulse

API uptime monitoring backend. Add URLs, run scheduled health checks,
track response time & uptime, get alerts when endpoints go down.

## Features
- JWT auth (register / login)
- CRUD for monitored endpoints
- Background health checks (httpx + APScheduler)
- Monitoring logs & email alerts (mock)
- Dashboard: uptime %, avg response time, incidents

## Tech stack
FastAPI · PostgreSQL · SQLAlchemy · Alembic · JWT · httpx · APScheduler

## Quick start
1. Clone repo
2. python -m venv .venv && activate
3. pip install -r requirements.txt
4. copy .env.example ..env  (set DATABASE_URL)
5. alembic upgrade head
6. uvicorn app.main:app --reload

Docs: http://localhost:8000/docs