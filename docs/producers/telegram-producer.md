# TelegramProducer

**Path:** `backend/app/producers/telegram.py`

## Purpose

`TelegramProducer` listens to Telegram channels in real time and stores incoming messages as [[db/models/news-item]] records.

## Distinctive design

Unlike RSS, this producer is event-driven. The abstract `fetch()` method exists only to satisfy the base interface; the real work happens in `run_job()` and `_handle_new_message()`.

## Runtime flow

1. Load active Telegram sources.
2. Build a Telethon client from the configured session string.
3. Resolve channel entities from stored `Source.source` values.
4. Attach a `NewMessage` event handler.
5. Persist deduplicated messages as they arrive.
6. Periodically reconnect so the active source list can be refreshed.

## Message normalization

`_parse_message()`:

- prefers `message.text`
- falls back to `message.message`
- falls back to captions
- uses a media placeholder if the message only contains media
- truncates the title to 100 characters plus `...`
- uses Telegram message ID as `external_id`
- builds a public `t.me` URL when a username is available

## Operational notes

- `RECONNECT_DELAY_SECONDS = 300`
- duplicate detection still comes from [[producers/base-producer]]
- per-message persistence uses a direct session opened in the event handler

## Tests

`backend/tests/test_telegram_producer.py` covers:

- client creation
- message parsing variants
- media handling
- long-title truncation
- background loop behavior

## Related notes

- [[producers/base-producer]]
- [[db/models/source]]
- [[db/models/news-item]]
