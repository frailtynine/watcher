# NewsTask model

**Path:** `backend/app/models/news_task.py`

## Purpose

`NewsTask` is the user-defined filtering rule. Each task wraps a natural-language prompt that the AI consumer uses to judge relevance.

## Key fields

- `id` - integer primary key
- `user_id` - owner of the task
- `name` - human-readable task name
- `prompt` - AI filter instruction
- `active` - enables or disables processing
- `created_at`, `updated_at`

## Relationships

- many-to-many with [[db/models/source]] through [[db/models/source-news-task]]
- one-to-many with [[db/models/news-item-news-task]] as stored AI results
- one-to-one with [[db/models/newspaper]] as rendered output

## Role in the pipeline

1. A user creates a task.
2. Sources are linked to it.
3. [[consumer/ai-consumer]] evaluates recent news items against its prompt.
4. Positive results can be surfaced in [[db/models/newspaper]].

## Notes

- The SQLAlchemy relationship to `newspaper` is configured with `uselist=False`, so operationally it behaves as one-to-one.
- Cascade rules remove dependent result rows and the newspaper when the task is deleted.

## Related notes

- [[db/models/source-news-task]]
- [[db/models/news-item-news-task]]
- [[db/models/newspaper]]
- [[consumer/ai-consumer]]
