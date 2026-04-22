# Database runtime

**Path:** `backend/app/db/database.py`

## Purpose

This module defines the SQLAlchemy base class, creates the async engine, and exposes the `get_async_session()` generator used throughout the app.

## Main pieces

- `Base` - declarative base for every model
- `engine` - async engine created from `settings.DATABASE_URL`
- `async_session_maker` - `async_sessionmaker` configured with `expire_on_commit=False`
- `get_async_session()` - async generator that yields one `AsyncSession`

## How it is used

- FastAPI route dependencies import `get_async_session`.
- Producers open short-lived sessions while fetching and persisting content.
- The AI consumer and delivery layer open sessions directly through the same generator.

## Related notes

- [[db/README]]
- [[db/models/news-item]]
- [[consumer/ai-consumer]]
- [[producers/base-producer]]
