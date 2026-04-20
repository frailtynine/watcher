# Producers

This folder documents the ingestion side of the system.

## Package purpose

`backend/app/producers/` is responsible for turning external inputs into stored [[db/models/news-item]] records.

## Modules

- [[producers/base-producer]] - shared workflow and persistence behavior
- [[producers/rss-producer]] - interval-based RSS/Atom fetcher
- [[producers/telegram-producer]] - event-driven Telegram watcher

## Shared flow

1. Load active sources that are connected to active tasks.
2. Fetch or receive raw content.
3. Normalize it into [[db/models/news-item]] objects.
4. Deduplicate before insert.
5. Update `source.last_fetched_at` when applicable.

## Scheduler integration

- RSS is scheduled by `backend/app/main.py`.
- Telegram runs as a long-lived background task started from the FastAPI lifespan.

## Related notes

- [[db/models/source]]
- [[db/models/news-item]]
- [[consumer/ai-consumer]]
