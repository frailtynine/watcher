# AIConsumer

**Path:** `backend/app/ai/consumer.py`

## Purpose

`AIConsumer` is the orchestrator that turns recent fetched news into task-specific AI decisions.

## Main entry points

- `process_user_news(user_id)`
- `run_ai_consumer_job()`

## Current execution flow

1. Load the user by ID.
2. Resolve an API key from `user.settings` or fall back to `settings.BACKEND_GEMINI_API_KEY`.
3. Load active tasks for that user.
4. For each task, query recent unprocessed news linked through [[db/models/source-news-task]].
5. Process items concurrently with `GeminiClient.process_news()`.
6. Upsert [[db/models/news-item-news-task]] rows in `_save_result()`.
7. After a task batch, invoke [[delivery/newspaper-processor]] to refresh presentation output.

## Query logic

`_get_unprocessed_news()`:

- uses a 4-hour lookback window
- joins `NewsItem` to `SourceNewsTask`
- outer-joins `NewsItemNewsTask`
- keeps items with no result row yet or `processed=False`
- eager-loads the source relation

## Persistence details

`_save_result()` stores:

- `processed=True`
- boolean `result`
- `processed_at`
- JSON `ai_response` with reasoning and token counts

## Current caveats worth remembering

- The consumer currently instantiates `GeminiClient` directly.
- `run_ai_consumer_job()` fans out per-user processing with `asyncio.gather`.
- Newspaper generation is attempted after task processing but delivery failures are logged and do not roll back AI results.

## Tests

`backend/tests/test_ai_consumer.py` covers:

- API-key extraction
- active task filtering
- 4-hour unprocessed item query
- result row creation and update

## Related notes

- [[consumer/gemini-client]]
- [[db/models/news-item-news-task]]
- [[delivery/newspaper-processor]]
