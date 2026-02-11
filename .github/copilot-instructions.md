# NewsWatcher - Copilot Instructions

## Project Overview

NewsWatcher is an AI-powered news monitoring service that fetches news from RSS feeds and Telegram channels, processes them through AI filters (Google Gemini), and delivers relevant news to users.

**Tech Stack:**
- Backend: FastAPI (async), PostgreSQL, SQLAlchemy, APScheduler
- Frontend: React + TypeScript, Chakra UI, RTK Query, Vite
- Infrastructure: Docker Compose, nginx
- AI: Google Gemini API (planned)
- Messaging: Telethon (planned)

## Build, Test, and Lint Commands

### Development Environment
```bash
# Start all services (backend, frontend, database, nginx)
make dev

# Stop services
make down

# View logs
make logs              # All services
make logs-backend      # Backend only
make logs-frontend     # Frontend only
```

### Backend Testing
```bash
# Run all tests
make test

# Run specific test file
make test-unit FILE=tests/test_models.py

# Run with coverage report (generates htmlcov/index.html)
make test-coverage

# Run only model tests
make test-models
```

Tests are configured via `backend/pytest.ini` and use markers: `@pytest.mark.unit`, `@pytest.mark.integration`, `@pytest.mark.slow`.

### Code Quality
```bash
# Run ruff linter with autofix
make lint
```

Ruff is configured in `backend/pyproject.toml` with line-length=79 and ignores F821 (SQLAlchemy relationships).

### Database Migrations
```bash
# Create new migration
make migrate-create MSG="description of changes"

# Apply pending migrations
make migrate-upgrade

# Rollback last migration
make migrate-downgrade

# View migration history
make migrate-history
```

Migrations use Alembic and are auto-applied on container startup via the `migrate` service in docker-compose.

### Frontend
```bash
# Development server (runs automatically in make dev)
npm run dev

# Production build
npm run build

# Type checking
tsc
```

## Architecture

### Data Flow

**Producers → NewsItems → AI Consumer → Results → Output**

1. **Producers** (RSS/Telegram) fetch news and create `NewsItem` records
2. **AI Consumer** processes items through user-defined `NewsTask` prompts
3. Results stored in `NewsItemNewsTask` (many-to-many with processing results)
4. **Output Interface** sends notifications for items where `result=True`

### Database Models

**Core Models:**
- `User` - fastapi-users base with JWT auth, `settings` JSON field for API keys
- `NewsTask` - User-defined AI prompts for filtering news
- `Source` - RSS feeds or Telegram channels (enum type)
- `NewsItem` - Individual articles/messages
- `NewsItemNewsTask` - Association table with processing results (processed, result, ai_response)
- `SourceNewsTask` - Links sources to tasks

**Key Relationships:**
- One NewsItem can be processed by multiple NewsTasks independently
- Each NewsItem-NewsTask combination has its own processing result
- Sources linked to NewsTasks determine which items get processed by which tasks

**Unique Constraints:**
- `Source.source` - Prevents duplicate sources
- `(NewsItem.source_id, NewsItem.url)` - Deduplicates RSS entries
- `(NewsItem.source_id, NewsItem.external_id)` - Deduplicates Telegram messages

### Task Scheduling

APScheduler (AsyncIOScheduler) runs in FastAPI lifespan context:
- RSS producer job: runs every `RSS_FETCH_INTERVAL_MINUTES` (env var, default: 15)
- Jobs configured with `max_instances=1` and `replace_existing=True`
- Error isolation: individual source failures don't stop the job

### API Structure

All API endpoints require JWT authentication (Authorization: Bearer token).

**Endpoints using fastCRUD:**
- `/api/news-tasks/*` - CRUD for news tasks
- `/api/sources/*` - CRUD for sources
- `/api/source-news-tasks/*` - Link sources to tasks
- `/api/news-items/*` - View fetched news

**Authentication (fastapi-users):**
- `POST /api/auth/jwt/login` - Returns JWT token
- `POST /api/auth/jwt/logout` - Logout
- `POST /api/auth/register` - Register new user
- `GET /api/users/me` - Get current user

### Frontend Architecture

**State Management:**
- RTK Query for all API calls and caching
- Auto-generated hooks: `useLoginMutation`, `useGetNewsTasksQuery`, etc.
- Tag-based cache invalidation (e.g., creating a task invalidates 'NewsTasks' tag)
- Auth token stored in localStorage, added to all requests via `prepareHeaders`

**Routing:**
- React Router with `PrivateRoute` component for auth protection
- Base URL: `/api` (proxied through nginx)

**Key Pages:**
- `/login`, `/signup` - Authentication
- `/news-tasks` - List/create/edit tasks
- `/sources` - List/create/edit sources
- Dashboard layout with navigation

### Infrastructure

**nginx Routing:**
```
/api/*  → backend:8000 (FastAPI)
/docs   → backend:8000 (Swagger UI)
/*      → frontend:3000 (dev) or frontend:80 (prod)
```

**Docker Compose - Development:**
- Volume mounts for hot-reload: `/app/app` (backend), `/app/src` (frontend)
- Backend runs with `uvicorn --reload`
- Frontend runs with Vite HMR
- Auto-migration on startup via `migrate` service

**Docker Compose - Production:**
- Builds static images (no volume mounts)
- Frontend served as static files by nginx

## Key Conventions

### Error Handling in Producers
```python
# Each source fetch is wrapped in try-except
# Errors are logged but don't stop processing other sources
for source in sources:
    try:
        await fetch_and_save(source)
    except Exception as e:
        logger.error(f"Error fetching {source.id}: {e}")
        continue  # Continue with next source
```

### Deduplication Pattern
Database handles duplicates via unique constraints. Producers insert normally and rely on constraint violations being ignored:
```python
# NewsItem has unique constraint on (source_id, url)
# Duplicate inserts are silently skipped by database
```

### Many-to-Many Processing
Each NewsItem-NewsTask combination stores independent processing results:
```python
# NewsItemNewsTask fields:
# - processed: bool (has this task processed this item?)
# - result: bool | null (did it match the filter?)
# - ai_response: JSON (full AI response for debugging)
# - processed_at: datetime
```

### JSON Fields for Extensibility
- `User.settings` - Stores API keys (Gemini, Telegram credentials)
- `NewsItem.settings` - Per-item configuration
- `NewsItem.raw_data` - Original feed/message data
- `NewsItemNewsTask.ai_response` - Full AI processing results

### Database Session Management
All CRUD operations use async sessions from `app.db.session.get_async_session()`. FastCRUD handles session lifecycle automatically.

### Testing Patterns
- Use `@pytest.mark.asyncio` for async tests
- Mock external APIs (RSS feeds, Telegram, Gemini)
- Use pytest fixtures for database setup
- Target: >80% coverage

## Current Implementation Status

**Implemented:**
- ✅ Authentication (fastapi-users, JWT)
- ✅ Docker infrastructure (dev + prod)
- ✅ Database models (all tables)
- ✅ RSS Producer with APScheduler
- ✅ Frontend: Login, NewsTasks CRUD, Sources CRUD
- ✅ Testing framework setup (pytest, ruff)

**Not Yet Implemented:**
- ⚠️ AI Consumer (Gemini integration)
- ⚠️ Telegram Producer (Telethon)
- ⚠️ Output Interface (notifications)
- ⚠️ Frontend: NewsItems viewer, results page
- ⚠️ Comprehensive test coverage

See `PROJECT_PLAN.md` and `IMPLEMENTATION_GUIDE.md` for detailed architecture and future work.

## Common Utilities

```bash
# Create test user (test@example.com / password123)
make test-user

# Access PostgreSQL shell
make db-shell

# Access backend container shell
make backend-shell

# Check service status
make status

# Clean everything (removes volumes)
make clean

# Rebuild from scratch
make rebuild
```

## Environment Configuration

All config in single `.env` file in repository root:
- `DATABASE_URL` - PostgreSQL connection string
- `SECRET_KEY` - JWT secret (min 32 chars)
- `RSS_FETCH_INTERVAL_MINUTES` - Producer schedule (default: 15)
- `BACKEND_CORS_ORIGINS` - JSON array of allowed origins
- `VITE_API_URL` - Frontend API base URL (use `/api`)

Copy `.env.example` to `.env` before starting development.
