# Newspaper model

**Path:** `backend/app/models/newspaper.py`

## Purpose

`Newspaper` is the presentation artifact for a task. It stores the AI-shaped front page for one `NewsTask`.

## Key fields

- `id`
- `news_task_id` - unique foreign key, enforcing one newspaper per task
- `title`
- `body` - JSON document representing layout and rendered items
- `updated_at`

## Relationship

- belongs to exactly one [[db/models/news-task]]

## Body format

The shape is validated by `backend/app/schemas/newspaper.py`:

- `NewspaperBody`
- `NewsItemNewspaper`
- `NewsItemNewspaperAIResponse`

The current format stores a flat list of items with a `position` tuple `(row, col)` rather than a nested matrix.

## Current writer

[[delivery/newspaper-processor]] creates and updates these rows.

## Tests

`backend/tests/test_newspaper_model.py` covers:

- creation
- one-to-one uniqueness
- task back-population
- cascade delete
- arbitrary nested JSON in `body`

## Related notes

- [[delivery/newspaper-processor]]
- [[db/models/news-task]]
