# Project Plan - NewsWatcher

## Project Overview
- **Project Name:** NewsWatcher
- **Start Date:** 2026-01-14
- **Project Owner:** Pavel Borisov
- **Status:** Planning - Foundation Phase

## Objectives
- Set up a modern full-stack web application with authentication
- Create a scalable foundation for future feature development
- Implement containerized development and deployment workflow
- Build a news monitoring service that automatically filters and delivers relevant news to users

## Tech Stack

### Backend
- **Framework:** FastAPI (async)
- **Database:** PostgreSQL
- **Authentication:** fastapi-users
- **CRUD Operations:** fastCRUD
- **Package Management:** uv (already installed)
- **Language:** Python
- **Task Scheduling:** APScheduler (integrated with FastAPI lifespan)
- **AI Processing:** Google Gemini API (google-generativeai)
- **Telegram:** Telethon (with API key, hash, and session string)
- **RSS Parsing:** feedparser or similar
- **Testing:** pytest

### Frontend
- **Framework:** React with TypeScript
- **UI Library:** Chakra UI
- **State Management & API:** RTK Query
- **Package Management:** npm/yarn

### Infrastructure
- **Containerization:** Docker & Docker Compose
- **Reverse Proxy:** nginx (internal)
- **Development:** Volume mounts for hot-reload
- **Deployment:** Production Docker Compose with builds

## Scope
### In Scope - Foundation Phase
- Backend API setup with FastAPI
- PostgreSQL database configuration
- User authentication system (fastapi-users)
- Basic CRUD operations setup (fastCRUD)
- Frontend React app with TypeScript
- Login screen UI with Chakra UI
- API layer with RTK Query for authentication
- Token-based authentication (stored in cookies - more secure than localStorage)
- Docker Compose for development (mounted volumes)
- Docker Compose for production (built images)
- nginx reverse proxy configuration

### Out of Scope - Foundation Phase
- User registration UI
- Password recovery
- Role-based access control
- Email verification
- Production deployment scripts
- Advanced filtering logic
- Multi-language support

## Implementation Status

### ✅ COMPLETED (Foundation Phase)
**Phases 1-3 are fully implemented as documented in FOUNDATION_COMPLETE.md**

- **Backend**: FastAPI with async PostgreSQL, fastapi-users authentication, JWT tokens, Alembic migrations
- **Frontend**: React + TypeScript + Chakra UI + RTK Query, Login page, API service layer
- **Infrastructure**: Docker Compose (dev + prod), nginx reverse proxy, hot-reload for development
- **Documentation**: README, Makefile, .env.example, .gitignore

**Test credentials available** - documented in FOUNDATION_COMPLETE.md

### ✅ COMPLETED

**Phase 4: Database Models & Core Logic** ✅ COMPLETE
- ✅ User model extended with settings JSON field
- ✅ NewsTask model created with all fields and relationships
- ✅ Source model created (RSS/Telegram types)
- ✅ SourceNewsTask association table created
- ✅ NewsItem model created with all fields
- ✅ NewsItemSettings dataclass created
- ✅ FastCRUD operations for all models
- ✅ API endpoints for all CRUD operations
- ✅ Comprehensive test suite (26 tests)
- ✅ Alembic migration generated and applied

**Detailed documentation**: See PHASE4_COMPLETE.md

### 🚧 IN PROGRESS / TODO

**Phase 5-9**: Not started
- Producers (RSS, Telegram)
- Consumers (Gemini AI)
- APScheduler integration
- Output interfaces
- Frontend UI for news management

### 📦 Dependencies Status

**Backend** (in pyproject.toml):
- ✅ fastapi, uvicorn
- ✅ sqlalchemy, asyncpg
- ✅ fastapi-users[sqlalchemy]
- ✅ fastcrud
- ✅ alembic
- ❌ APScheduler (needs to be added)
- ❌ google-generativeai (needs to be added)
- ❌ telethon (needs to be added)
- ❌ feedparser (needs to be added)
- ❌ pytest (needs to be added)

**Frontend** (in package.json):
- ✅ react, react-dom
- ✅ @chakra-ui/react
- ✅ @reduxjs/toolkit, react-redux
- ✅ react-router-dom
- ✅ TypeScript, Vite

---

## Implementation Plan

### Phase 1: Backend Foundation ✅ COMPLETE
- [x] Initialize backend project structure with uv
- [x] Set up FastAPI application skeleton
- [x] Configure PostgreSQL connection
- [x] Implement fastapi-users authentication
  - [x] User model
  - [x] JWT token strategy
  - [x] Auth routes (login, logout, verify)
- [x] Integrate fastCRUD for basic operations
- [x] Create backend Dockerfile
- [x] Set up environment variables structure

### Phase 2: Frontend Foundation ✅ COMPLETE
- [x] Initialize React TypeScript project
- [x] Install and configure Chakra UI
- [x] Set up RTK Query
- [x] Create api.ts with auth endpoints
  - [x] Login mutation
  - [x] Token refresh logic
  - [x] Auth state management
- [x] Build login screen component
- [x] Implement cookie-based token storage
- [x] Create frontend Dockerfile
- [x] Set up environment variables

### Phase 3: Docker & nginx Setup ✅ COMPLETE
- [x] Create docker-compose.dev.yml
  - [x] PostgreSQL service
  - [x] Backend service (volume mounted)
  - [x] Frontend service (volume mounted)
  - [x] nginx service with dev config
- [x] Create docker-compose.prod.yml
  - [x] PostgreSQL service with volumes
  - [x] Backend service (built image)
  - [x] Frontend service (built image)
  - [x] nginx service with production config
- [x] Configure nginx routes
  - [x] `/api/*` → backend
  - [x] `/docs` → backend (Swagger)
  - [x] `/*` → frontend
- [x] Create .env.example files

### Phase 4: Database Models & Core Logic ✅ COMPLETE
- [x] Create User model (extended from fastapi-users)
  - [x] Add settings field (JSON) for API keys and Telegram data
- [x] Create NewsTask model
  - [x] Fields: user_id, name, prompt, active, created_at, updated_at
  - [x] Many-to-many relationship with Source (via association table)
- [x] Create Source model
  - [x] Fields: user_id, name, type (RSS/Telegram), source (URL/channel_id), active, last_fetched_at, created_at
  - [x] Many-to-many relationship with NewsTask
- [x] Create SourceNewsTask association table
  - [x] Fields: source_id, news_task_id (composite primary key)
- [x] Create NewsItem model
  - [x] Fields: source_id, title, content, url, external_id, published_at, fetched_at, processed (boolean), result (boolean/nullable), processed_at (nullable), ai_response (JSON/nullable), settings (JSON), raw_data (JSON)
  - [x] Settings dataclass for type safety
- [x] Set up Alembic for migrations
- [x] FastCRUD operations for all models
- [x] API endpoints with authentication
- [x] Comprehensive test suite (26 tests)

### Phase 5: News Producers (Retrieval)
- [ ] Create producer architecture
  - [ ] Base producer class/interface
  - [ ] Error handling and logging
- [ ] Implement RSS Producer
  - [ ] Fetch and parse RSS feeds
  - [ ] Store news items in database
  - [ ] Handle duplicate detection
  - [ ] Error recovery (connection issues, malformed feeds)
- [ ] Implement Telegram Producer
  - [ ] Initialize Telethon client with session string
  - [ ] Fetch messages from channels
  - [ ] Store messages as news items
  - [ ] Handle rate limits and errors
- [ ] Write pytest tests for producers
  - [ ] Mock RSS feeds
  - [ ] Mock Telegram API responses
  - [ ] Test error handling

### Phase 6: AI Consumer (Processing)
- [ ] Create consumer architecture
  - [ ] Error handling and retry logic
  - [ ] Rate limiting for API calls
- [ ] Implement Gemini AI consumer
  - [ ] Initialize client with user's API key
  - [ ] Process news items against NewsTask prompts
  - [ ] Return boolean result
  - [ ] Store results in ProcessedNews table
  - [ ] Handle API errors gracefully
- [ ] Write pytest tests for consumer
  - [ ] Mock Gemini API responses
  - [ ] Test prompt processing logic
  - [ ] Test error scenarios (API failures, quota exceeded)

### Phase 7: Task Scheduling (APScheduler)
- [ ] Integrate APScheduler with FastAPI lifespan
- [ ] Configure job scheduling
  - [ ] Producer jobs (configurable interval)
  - [ ] Consumer jobs (configurable interval)
- [ ] Implement robust error handling
  - [ ] Prevent cascading failures
  - [ ] Logging and monitoring
  - [ ] Graceful degradation
- [ ] Configure job persistence (optional)
- [ ] Write tests for scheduler
  - [ ] Test job execution
  - [ ] Test error isolation

### Phase 8: Output Interface (Telegram) - TBD
- [ ] Design output interface architecture
- [ ] Implementation details to be defined later

### Phase 9: Testing & Documentation
- [ ] Integration tests for full workflow
  - [ ] Source → Producer → Consumer → Output
- [ ] Test development workflow
- [ ] Test production build
- [ ] Verify authentication flow end-to-end
- [ ] Document setup instructions (README.md)
- [ ] Document environment variables
- [ ] Document API endpoints
- [ ] Document testing procedures

## Project Structure
```
newswatcher/
├── backend/
│   ├── app/
│   │   ├── main.py
│   │   ├── models/
│   │   ├── schemas/
│   │   ├── api/
│   │   ├── core/
│   │   └── db/
│   ├── pyproject.toml
│   ├── Dockerfile
│   └── .env.example
├── frontend/
│   ├── src/
│   │   ├── components/
│   │   ├── features/
│   │   │   └── auth/
│   │   ├── services/
│   │   │   └── api.ts
│   │   ├── App.tsx
│   │   └── main.tsx
│   ├── package.json
│   ├── Dockerfile
│   └── .env.example
├── nginx/
│   └── nginx.conf
├── docker-compose.dev.yml
├── docker-compose.prod.yml
├── .gitignore
├── README.md
└── PROJECT_PLAN.md
```

## Resources Required
- **Team Members:** 1 (Full-stack developer)
- **Tools/Technologies:** Docker, uv, Node.js, PostgreSQL
- **External Services:** None for foundation phase

## Technical Decisions

### Authentication Token Storage
- **Decision:** HTTP-only cookies
- **Rationale:** 
  - More secure than localStorage (immune to XSS attacks)
  - Automatic transmission with requests
  - Can set secure and SameSite flags

### Package Management
- **Backend:** uv (fast, modern Python package manager)
- **Frontend:** npm/yarn (standard for React)

### Development Workflow
- Hot-reload enabled via volume mounts
- Backend uvicorn auto-reload
- Frontend Vite/webpack dev server

## Risks & Mitigation
| Risk | Impact | Mitigation Strategy |
|------|--------|---------------------|
| CORS issues with nginx | Medium | Configure nginx and FastAPI CORS properly from start |
| Cookie authentication cross-domain | Medium | Use proxy approach, all traffic through nginx |
| Database migration conflicts | Low | Use Alembic from the beginning |
| Docker volume permissions | Low | Set correct user permissions in Dockerfiles |
| API rate limits (Gemini, Telegram) | High | Implement exponential backoff, rate limiting, and queue management |
| Telegram session expiration | Medium | Handle re-authentication gracefully, log errors clearly |
| Producer/Consumer crashes | High | Isolate errors, use try-except blocks, continue on failure |
| Duplicate news items | Medium | Implement deduplication based on URL/message_id |
| User API key security | High | Encrypt API keys in database, validate before use |
| Scheduler job failures | Medium | Implement job monitoring, alerting, and automatic recovery |

## Success Criteria

### Foundation Phase
- [ ] User can access login screen
- [ ] User can successfully authenticate
- [ ] Token is stored securely in cookies
- [ ] Protected routes return 401 when not authenticated
- [ ] Development environment starts with single command
- [ ] Production build completes successfully
- [ ] nginx correctly routes traffic to frontend/backend

### Core Functionality Phase
- [ ] Users can create and manage NewsTask entries
- [ ] Users can create and manage Source entries (RSS and Telegram)
- [ ] RSS producer successfully fetches and stores news items
- [ ] Telegram producer successfully fetches and stores channel messages
- [ ] Gemini consumer processes news items and returns boolean results
- [ ] APScheduler runs producers and consumers on schedule
- [ ] System continues operating after individual job failures
- [ ] All producers have >80% test coverage
- [ ] All consumers have >80% test coverage
- [ ] No single error breaks the entire system

## Architecture Details

### News Processing Flow
1. **Producers** (scheduled via APScheduler)
   - RSS Producer: Polls RSS feeds every N minutes
   - Telegram Producer: Fetches new messages from channels every N minutes
   - Each producer runs independently, failures are isolated
   - Store fetched items in NewsItem table with `processed=False`

2. **Consumers** (scheduled via APScheduler)
   - Query unprocessed NewsItems (`processed=False`) from database
   - For each NewsItem, get associated NewsTasks via Source → SourceNewsTask → NewsTask
   - If source has associated tasks, process the item:
     - Call Gemini API with each task's prompt + news content
     - Aggregate results: if ANY task returns true, set `result=True`
     - Store all task results in `ai_response` JSON field
     - Set `processed=True` and `processed_at`
   - If source has no associated tasks, mark as processed but skip AI processing
   - Handle API errors gracefully (retry, skip, log)

3. **Output** (TBD - to be designed later)
   - Query NewsItems where `result=True`
   - Send notifications via configured channels

### Database Models Detail

#### User (extends fastapi-users)
- `id`: UUID (primary key)
- `email`: String (unique)
- `hashed_password`: String
- `is_active`: Boolean
- `is_verified`: Boolean
- `settings`: JSON (stores: gemini_api_key, telegram_session, etc.)

#### NewsTask
- `id`: UUID (primary key)
- `user_id`: UUID (foreign key)
- `name`: String
- `prompt`: Text (AI prompt to evaluate news)
- `active`: Boolean
- `created_at`: DateTime
- `updated_at`: DateTime
- Relationship: many-to-many with Source

#### Source
- `id`: UUID (primary key)
- `user_id`: UUID (foreign key)
- `name`: String
- `type`: Enum (RSS, Telegram)
- `source`: String (RSS URL or Telegram channel ID)
- `active`: Boolean
- `last_fetched_at`: DateTime (nullable)
- `created_at`: DateTime
- Relationship: many-to-many with NewsTask

#### SourceNewsTask (Association Table)
- `source_id`: UUID (foreign key, part of composite primary key)
- `news_task_id`: UUID (foreign key, part of composite primary key)
- `created_at`: DateTime

#### NewsItem
- `id`: UUID (primary key)
- `source_id`: UUID (foreign key)
- `title`: String
- `content`: Text
- `url`: String (nullable, unique constraint)
- `external_id`: String (nullable, for Telegram message_id, unique per source)
- `published_at`: DateTime
- `fetched_at`: DateTime
- `processed`: Boolean (default: False)
- `result`: Boolean (nullable, true if news matches ANY associated task)
- `processed_at`: DateTime (nullable)
- `ai_response`: JSON (nullable, stores all task results)
- `settings`: JSON (typed with dataclass for validation)
- `raw_data`: JSON (full original data)

#### NewsItemSettings (Dataclass for NewsItem.settings)
```python
@dataclass
class NewsItemSettings:
    language: Optional[str] = None
    priority: Optional[int] = None
    custom_fields: Optional[Dict[str, Any]] = None
```

### Error Handling Strategy
- **Producers**: Wrap each source fetch in try-except, log errors, continue to next source
- **Consumers**: Wrap each news item processing in try-except, log errors, continue to next item
- **Scheduler**: Use APScheduler's error handling, don't crash on job failure
- **API Calls**: Exponential backoff for rate limits, max retries, then skip
- **Logging**: Structured logging with levels (DEBUG, INFO, WARNING, ERROR)

### Testing Strategy
- **Unit Tests**: Test individual functions with mocked dependencies
- **Integration Tests**: Test full flow with test database
- **Fixtures**: Use pytest fixtures for common test data
- **Mocking**: Mock external APIs (Gemini, Telegram, RSS feeds)
- **Coverage**: Aim for >80% code coverage
- **CI/CD**: Run tests automatically on commits (future)

## Next Steps After Foundation
- Implement user registration UI
- Add password recovery
- Build frontend interfaces for NewsTask and Source management
- Implement Output interface (Telegram notifications)
- Add role-based permissions
- Implement refresh token rotation
- Add comprehensive logging and monitoring
- Build admin dashboard

## Notes
- Keep it simple for foundation - focus on getting authentication working
- Ensure hot-reload works properly in development
- Document any deviations from the plan
- Security best practices for token handling
- **User API keys are sensitive**: Encrypt in database, never log them
- **Telegram session string is sensitive**: Store securely in user settings
- Each module (producer/consumer) must be fault-tolerant
- APScheduler jobs must not block each other
- Consider adding a job status/health check endpoint 
