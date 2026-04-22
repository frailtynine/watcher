# Project structure

This note is the top-level map of the repository.

## Root layout

- `backend/` - FastAPI app, SQLAlchemy models, producers, AI, delivery, tests
- `frontend/` - React + TypeScript UI
- `nginx/` - reverse proxy template used by Docker Compose
- `docker-compose.dev.yml` / `docker-compose.prod.yml` - runtime topology
- `docker/` - PostgreSQL init scripts
- root `*.md` files - implementation notes and planning documents

## Backend map

The most important backend folders for the news pipeline are:

- `backend/app/db/` -> [[db/README]]
- `backend/app/models/` -> [[db/README]]
- `backend/app/producers/` -> [[producers/README]]
- `backend/app/ai/` -> [[consumer/README]]
- `backend/app/delivery/` -> [[delivery/README]]

Supporting backend folders:

- `backend/app/api/` - authenticated CRUD routes plus newspaper endpoints
- `backend/app/core/` - settings, auth, and user management glue
- `backend/app/schemas/` - Pydantic request/response and AI payload schemas
- `backend/app/validators/` - source validation helpers

## Frontend map

The frontend is not decomposed into vault notes yet, but structurally it is:

- `frontend/src/features/` - route-level features such as auth, tasks, sources, news items
- `frontend/src/services/api.ts` - RTK Query API client
- `frontend/src/components/` - shared UI pieces
- `frontend/src/store.ts` - Redux store setup

## Runtime entry points

- `backend/app/main.py` creates the FastAPI app, configures CORS, and starts the scheduler.
- `rss_producer_job()` is scheduled on an interval.
- `run_ai_consumer_job()` is scheduled every minute.
- `telegram_producer_job()` runs as a long-lived background task in the FastAPI lifespan.

## Main data flow

1. [[producers/README]] load items from configured sources.
2. [[db/models/news-item]] records are stored and deduplicated.
3. [[consumer/ai-consumer]] evaluates recent items against active tasks.
4. [[db/models/news-item-news-task]] stores per-task AI results.
5. [[delivery/newspaper-processor]] rebuilds or updates [[db/models/newspaper]] output for each task.
