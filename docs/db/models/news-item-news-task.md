# NewsItemNewsTask model

**Path:** `backend/app/models/news_item_news_task.py`

## Purpose

`NewsItemNewsTask` is the result table for AI evaluation. It links one news item to one task and stores the processing outcome.

## Key fields

- `news_item_id`, `news_task_id` - composite primary key
- `processed` - whether this pair has been evaluated
- `result` - `True`, `False`, or `None`
- `processed_at`
- `ai_response` - JSON payload with reasoning and token counts
- `created_at`, `updated_at`

## Why it is central

This table turns the system from “collected news” into “task-specific relevance judgments”.

## Current writer

[[consumer/ai-consumer]] creates or updates these rows in `_save_result()`.

The current `ai_response` payload contains:

- `thinking`
- `tokens_used`
- `processed_at`

## Downstream use

- The delivery layer queries rows where `processed=True` and `result=True`.
- Reprocessing is possible per `(news_item_id, news_task_id)` pair.

## Related notes

- [[db/models/news-item]]
- [[db/models/news-task]]
- [[consumer/ai-consumer]]
- [[delivery/newspaper-processor]]
