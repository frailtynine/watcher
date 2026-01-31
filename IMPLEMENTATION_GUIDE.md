# NewsWatcher - Implementation Guide

## Architecture Overview

NewsWatcher is a news monitoring service built with FastAPI (async) backend and React/TypeScript frontend. It fetches news from RSS feeds and Telegram channels, processes them through AI filters, and delivers relevant news to users.

## Core Components

### 1. Database Models

**User** (`app/models/user.py`)
- FastAPI-users base model with JWT authentication
- `settings` JSON field stores user API keys (Gemini, Telegram credentials)
- Primary key: integer ID

**NewsTask** (`app/models/news_task.py`)
- User-defined AI prompts for filtering news
- Fields: `name`, `prompt`, `active`, timestamps
- Many-to-many relationship with Sources (via `source_news_task` table)

**Source** (`app/models/source.py`)
- News sources (RSS feeds or Telegram channels)
- Type: enum (RSS | Telegram)
- `source` field: URL for RSS, channel ID for Telegram
- Tracks `last_fetched_at`, `active` status
- Unique constraint on `source` field (prevents duplicates)

**NewsItem** (`app/models/news_item.py`)
- Individual news articles/messages
- Fields: `title`, `content`, `url`, `external_id`, `published_at`
- Processing status: `processed` (bool), `result` (bool/null), `processed_at`, `ai_response` (JSON)
- `settings` (JSON) and `raw_data` (JSON) for extensibility
- Unique constraints: (`source_id`, `url`) and (`source_id`, `external_id`)

**SourceNewsTask** (`app/models/source_news_task.py`)
- Association table linking Sources to NewsTasks
- Composite primary key: (`source_id`, `news_task_id`)

### 2. Producers (News Fetchers)

**Base Producer** (`app/producers/base.py`)
- Abstract base class for all producers
- Defines `fetch()` interface
- Error handling and logging utilities

**RSS Producer** (`app/producers/rss.py`)
- Fetches RSS/Atom feeds using `feedparser`
- Parses entries: title, link, description, published date
- Handles malformed feeds gracefully (continues on errors)
- Deduplication via unique constraints (source_id + url)
- Updates `source.last_fetched_at` after successful fetch

**Telegram Producer** (`app/producers/telegram.py`)
- Uses Telethon library with session string
- Fetches messages from Telegram channels
- Extracts message text, media info
- Deduplication via unique constraints (source_id + external_id)

### 3. Task Scheduling

**APScheduler Integration** (`app/main.py`)
- AsyncIOScheduler runs in FastAPI lifespan
- RSS producer job: runs every N minutes (configurable via `RSS_FETCH_INTERVAL_MINUTES`)
- Each job configured with:
  - `max_instances=1` (prevent concurrent runs)
  - `replace_existing=True` (safe restarts)
  - Error isolation (job failures don't crash scheduler)

**Producer Jobs** (`app/producers/rss.py:rss_producer_job`)
```python
async def rss_producer_job():
    # 1. Get all active RSS sources
    # 2. For each source:
    #    - Fetch feed
    #    - Parse entries into NewsItem objects
    #    - Save to database (ignoring duplicates)
    #    - Update source.last_fetched_at
    # 3. Error handling: continue on individual source failures
```

### 4. API Endpoints

**Authentication** (`app/api/auth.py`)
- FastAPI-users routes: `/auth/jwt/login`, `/auth/jwt/logout`, `/auth/register`
- JWT token strategy with Bearer authentication

**CRUD Endpoints** (using fastCRUD)
- `/api/news-tasks/*` - Create, read, update, delete news tasks
- `/api/sources/*` - Manage news sources
- `/api/source-news-tasks/*` - Link sources to tasks
- `/api/news-items/*` - View fetched news items

All endpoints require authentication (JWT token in Authorization header).

### 5. Frontend

**Authentication Flow**
- Login form → POST `/api/auth/jwt/login` → store token in localStorage
- RTK Query prepares headers: adds `Authorization: Bearer {token}` to all requests
- PrivateRoute component protects authenticated pages

**State Management**
- RTK Query (`@reduxjs/toolkit/query`) for API calls and caching
- Auto-generated hooks: `useLoginMutation`, `useGetNewsTasksQuery`, etc.
- Tag-based cache invalidation (e.g., creating a task invalidates 'NewsTasks' tag)

**Key Pages**
- `/login` - Login form (Chakra UI)
- `/signup` - Registration form
- `/news-tasks` - List/create/edit news tasks
- `/sources` - List/create/edit sources
- Dashboard layout with navigation

**API Service** (`frontend/src/services/api.ts`)
- Single RTK Query API definition
- Base URL: `/api` (proxied through nginx)
- Endpoints grouped by resource type

### 6. Infrastructure

**Docker Compose - Development** (`docker-compose.dev.yml`)
- PostgreSQL 16 with health checks
- Backend: volume mounts `/app/app` for hot-reload (uvicorn --reload)
- Frontend: volume mounts `/app/src` for Vite HMR
- nginx: routes `/api/*` → backend:8000, `/*` → frontend:3000
- Migrate service: runs Alembic migrations on startup

**Docker Compose - Production** (`docker-compose.prod.yml`)
- Same services, but builds Docker images (no volume mounts)
- Frontend: static build served by nginx
- All services communicate via internal Docker network

**nginx Configuration** (`nginx/nginx.conf`)
```
/api/*  → backend:8000 (FastAPI)
/docs   → backend:8000 (Swagger UI)
/*      → frontend:3000 (dev) or frontend:80 (prod)
```

## Data Flow

### News Fetching Flow
1. **Scheduler triggers** RSS producer job (every N minutes)
2. **Producer queries** active RSS sources from database
3. **For each source:**
   - Fetch and parse feed
   - Create NewsItem objects
   - Insert into database (duplicate URLs/external_ids are skipped)
   - Update `source.last_fetched_at`
4. **Errors are logged** but don't stop processing other sources

### Processing Flow (Not Yet Implemented)
1. Consumer job queries NewsItems where `processed=False`
2. For each NewsItem:
   - Get associated NewsTasks via Source → SourceNewsTask
   - Call Gemini API for each task's prompt
   - Aggregate results (if ANY task returns true, set `result=True`)
   - Store AI responses in `ai_response` JSON field
   - Mark `processed=True`, set `processed_at`

### User Interaction Flow
1. User logs in → JWT token stored
2. User creates NewsTask (defines AI prompt)
3. User adds Sources (RSS feeds/Telegram channels)
4. User links Sources to NewsTasks (via SourceNewsTask)
5. Producers automatically fetch news from active sources
6. Consumer (when implemented) processes news and flags relevant items
7. User views filtered news items (result=true)

## Key Design Decisions

**1. Combined Processing Model**
- No separate ProcessedNews table
- NewsItem has `processed`, `result`, `ai_response` fields
- Simplifies queries, reduces joins

**2. Many-to-Many Source-Task Relationship**
- Allows one source to be filtered by multiple tasks
- Consumer only processes NewsItems from sources with linked tasks

**3. Error Isolation**
- Each source fetch wrapped in try-except
- Job failures don't crash scheduler
- `max_instances=1` prevents concurrent duplicate jobs

**4. Deduplication Strategy**
- Unique constraints on (source_id, url) and (source_id, external_id)
- Database handles duplicates (INSERT IGNORE or ON CONFLICT DO NOTHING)

**5. Token Storage**
- localStorage (not HTTP-only cookies as initially planned)
- Simpler implementation for SPA architecture

**6. JSON Fields for Extensibility**
- `User.settings` - API keys, credentials
- `NewsItem.settings` - per-item configuration
- `NewsItem.raw_data` - original feed/message data
- `NewsItem.ai_response` - full AI processing results

## Configuration

**Environment Variables** (`.env`)
```bash
# Database
DATABASE_URL=postgresql+asyncpg://...

# Auth
SECRET_KEY=your-secret-key

# Scheduling
RSS_FETCH_INTERVAL_MINUTES=15

# CORS
BACKEND_CORS_ORIGINS=["http://localhost"]
```

## Not Yet Implemented

- **AI Consumer** (Gemini integration)
- **Telegram Producer** (Telethon integration)
- **Output Interface** (sending notifications)
- **pytest Test Suite**
- **Consumer Scheduler** (only RSS producer is scheduled)
- **Frontend pages** for viewing NewsItems and results

## Quick Commands

```bash
# Start development environment
make dev

# Stop all services
make down

# View logs
make logs

# Create database migration
make migrate-create MSG="add new field"

# Apply migrations
make migrate-upgrade

# Create test user
make test-user
```

## File Structure

```
backend/app/
├── main.py                 # FastAPI app, scheduler setup
├── crud.py                 # fastCRUD configuration
├── models/                 # SQLAlchemy models
│   ├── user.py
│   ├── news_task.py
│   ├── source.py
│   ├── news_item.py
│   └── source_news_task.py
├── schemas/                # Pydantic schemas for API
├── api/                    # FastAPI route handlers
├── producers/              # News fetchers
│   ├── base.py
│   ├── rss.py
│   └── telegram.py
├── core/                   # Config, auth utilities
└── db/                     # Database session management

frontend/src/
├── features/               # Page components
│   ├── auth/              # Login, Signup
│   ├── newsTasks/         # Task management
│   └── sources/           # Source management
├── services/api.ts         # RTK Query API definitions
└── components/             # Shared components
```

## Testing Approach (Planned)

- **Unit Tests**: Mock database, test individual functions
- **Integration Tests**: Test database with pytest fixtures
- **Producer Tests**: Mock RSS feeds, Telegram API
- **Consumer Tests**: Mock Gemini API responses
- **Coverage Target**: >80%
