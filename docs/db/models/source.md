# Source model

**Path:** `backend/app/models/source.py`

## Purpose

`Source` represents an input channel that producers can watch: either an RSS/Atom feed or a Telegram channel.

## Key fields

- `id` - integer primary key
- `user_id` - owner
- `name` - display label
- `type` - `RSS` or `Telegram`
- `source` - feed URL or Telegram channel identifier
- `active`
- `last_fetched_at`
- `created_at`

## Constraints and behavior

- `source` is globally unique in the current schema.
- `last_fetched_at` is updated by producers after a successful persistence cycle.

## Relationships

- many-to-many with [[db/models/news-task]] through [[db/models/source-news-task]]
- one-to-many with [[db/models/news-item]]

## Producer relevance

- [[producers/rss-producer]] expects `source.source` to be a feed URL.
- [[producers/telegram-producer]] expects `source.source` to be a Telegram channel string it can resolve via Telethon.

## Related notes

- [[db/models/source-news-task]]
- [[db/models/news-item]]
- [[producers/rss-producer]]
- [[producers/telegram-producer]]
