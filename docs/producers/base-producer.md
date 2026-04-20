# BaseProducer

**Path:** `backend/app/producers/base.py`

## Purpose

`BaseProducer` is the shared contract and persistence workflow for content ingestors.

## Main responsibilities

- declare the abstract `fetch(source)` method
- create normalized `NewsItem` instances with `_create_news_item()`
- deduplicate by URL or external ID with `_is_duplicate()`
- persist items and update `source.last_fetched_at`
- select active sources that are attached to active tasks
- run concurrent source processing jobs with a semaphore

## Important methods

- `process_source()` - fetch + deduplicate + persist one source
- `get_sources()` - joins `Source`, `SourceNewsTask`, and `NewsTask`
- `run_job()` - fan-out runner for multiple sources
- `process_source_safe()` - semaphore wrapper with broad job safety

## Design notes

- Producers do not trust external sources, so fetch errors are logged and isolated.
- Deduplication happens before insert rather than relying only on database constraint errors.
- Timestamps are normalized to naive UTC for compatibility with the schema.

## Related notes

- [[producers/rss-producer]]
- [[producers/telegram-producer]]
- [[db/models/source]]
- [[db/models/news-item]]
