# NewsItem model

**Path:** `backend/app/models/news_item.py`

## Purpose

`NewsItem` stores a concrete article or Telegram message fetched by a producer.

## Key fields

- `id`
- `source_id`
- `title`
- `content`
- `url`
- `external_id`
- `published_at`
- `fetched_at`
- `settings` - JSON extension point
- `raw_data` - original source payload snapshot
- `created_at`, `updated_at`

## Deduplication rules

The table uses two unique constraints:

- `(source_id, url)`
- `(source_id, external_id)`

This lets producers treat RSS links and Telegram message IDs as stable identity keys.

## Relationships

- belongs to [[db/models/source]]
- has many [[db/models/news-item-news-task]] processing result rows

## Notes

- `published_at` is the timestamp used by [[consumer/ai-consumer]] to enforce its 4-hour processing window.
- `raw_data` is intentionally lightweight for RSS and more message-specific for Telegram.

## Related notes

- [[producers/rss-producer]]
- [[producers/telegram-producer]]
- [[db/models/news-item-news-task]]
