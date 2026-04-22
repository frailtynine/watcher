# SourceNewsTask model

**Path:** `backend/app/models/source_news_task.py`

## Purpose

`SourceNewsTask` is the join table that says which sources feed which tasks.

## Key fields

- `source_id` - part of the composite primary key
- `news_task_id` - part of the composite primary key
- `created_at`

## Why it matters

- Producers only fetch sources that are linked to at least one active task.
- The AI consumer uses this join to discover which tasks should process a news item from a given source.

## Pipeline role

`Source` -> `SourceNewsTask` -> `NewsTask`

Without this association, fetched content exists in the database but has no downstream task to evaluate it.

## Related notes

- [[db/models/source]]
- [[db/models/news-task]]
- [[consumer/ai-consumer]]
- [[producers/base-producer]]
