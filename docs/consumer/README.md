# Consumer

This folder documents the AI-processing side of the system.

## Package purpose

`backend/app/ai/` evaluates fetched news against active tasks and stores per-task results.

## Modules

- [[consumer/base-ai-client]] - shared prompt/result contract
- [[consumer/ai-consumer]] - orchestration and persistence
- [[consumer/gemini-client]] - Google Gemini implementation
- [[consumer/nova-client]] - Amazon Nova / Bedrock implementation

## Flow summary

1. `run_ai_consumer_job()` loads all active users.
2. `AIConsumer.process_user_news()` loads the user, task list, and provider key.
3. The consumer queries recent unprocessed items linked to each task.
4. An AI client returns a structured relevance decision.
5. The consumer writes [[db/models/news-item-news-task]] rows.
6. The delivery layer is asked to refresh the task newspaper.

## Provider status

- Gemini is the client wired into the current consumer and newspaper processor.
- Nova exists as an alternative provider wrapper, but is not the default execution path yet.

## Related notes

- [[db/models/news-task]]
- [[db/models/news-item-news-task]]
- [[delivery/newspaper-processor]]
