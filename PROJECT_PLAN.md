# NewsWatcher - Project Plan

## Project Status: Foundation + RSS Producer Complete

### Completed Phases ✅
- **Phase 1-3**: Authentication, Docker infrastructure, Frontend basics
- **Phase 4**: Database models (User, NewsTask, Source, NewsItem, SourceNewsTask)
- **Phase 5**: RSS Producer with APScheduler integration
  - [x] Testing/Debug News Items Viewer (frontend-only, easily detachable)

### Current Implementation
See **IMPLEMENTATION_GUIDE.md** for detailed architecture and logic explanation.

### In Progress / TODO

**Phase 6: AI Consumer (Gemini)** ⚠️ Not Started
- [ ] Install google-generativeai library
- [ ] Create Gemini consumer class
- [ ] Implement news processing logic:
  - Query unprocessed NewsItems
  - Get associated NewsTasks via Source
  - Call Gemini API for each task
  - Store results in NewsItem (result, ai_response)
- [ ] Add consumer job to APScheduler
- [ ] Error handling and rate limiting

**Phase 7: Telegram Producer** ⚠️ Not Started
- [ ] Install Telethon library
- [ ] Implement Telegram producer
- [ ] Use session string from User.settings
- [ ] Fetch messages from channels
- [ ] Store as NewsItems with external_id
- [ ] Add to scheduler

**Phase 8: Output Interface** ⚠️ Not Started
- [ ] Design output architecture
- [ ] Telegram notification sender
- [ ] Query NewsItems where result=True
- [ ] Send to users via Telegram

**Phase 9: Testing** ⚠️ Not Started
- [ ] Install pytest
- [ ] Unit tests for producers
- [ ] Unit tests for consumer
- [ ] Integration tests
- [ ] Mock external APIs
- [ ] Achieve >80% coverage

**Phase 10: Frontend Features** ⚠️ Partial
- [x] Login/Signup pages
- [x] NewsTasks CRUD
- [x] Sources CRUD
- [x] Source-Task associations
- [x] NewsItems debug viewer (testing feature)
- [ ] Filtered results page (production feature)
- [ ] User settings page (API keys)

## Tech Stack

**Backend**: FastAPI (async), PostgreSQL, fastapi-users, fastCRUD, APScheduler, feedparser, Alembic  
**Frontend**: React + TypeScript, Chakra UI, RTK Query  
**Infrastructure**: Docker Compose, nginx  
**Testing**: pytest (planned)  
**AI**: Google Gemini (planned)  
**Messaging**: Telethon (planned)

## Database Models

See IMPLEMENTATION_GUIDE.md for detailed field descriptions.

- **User** - Authentication + settings (API keys)
- **NewsTask** - AI prompts for filtering
- **Source** - RSS/Telegram sources
- **NewsItem** - Fetched news articles
- **SourceNewsTask** - Many-to-many association

## Architecture

**Producers** → Fetch news → **NewsItem** (processed=false)  
**Consumer** → Process via AI → **NewsItem** (processed=true, result=true/false)  
**Output** → Query results → Send notifications

## Quick Start

```bash
make dev          # Start all services
make down         # Stop services
make logs         # View logs
make test-user    # Create test user
```

## Configuration

Environment variables in `.env`:
- `DATABASE_URL` - PostgreSQL connection
- `SECRET_KEY` - JWT secret
- `RSS_FETCH_INTERVAL_MINUTES` - Producer schedule (default: 15)
- `BACKEND_CORS_ORIGINS` - CORS whitelist

## Next Steps

1. Implement Gemini consumer for AI processing
2. Add Telegram producer
3. Build output notification system
4. Create comprehensive test suite
5. Add frontend pages for viewing filtered news
