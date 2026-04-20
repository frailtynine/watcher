# RSSProducer

**Path:** `backend/app/producers/rss.py`

## Purpose

`RSSProducer` ingests RSS and Atom feeds and turns valid entries into [[db/models/news-item]] records.

## Entry points

- `RSSProducer.fetch(source)`
- `rss_producer_job()`

## Fetch behavior

- uses `feedparser.parse`
- wraps parsing in `run_in_executor()` because `feedparser` is synchronous
- logs `bozo` parsing warnings but still attempts to process entries

## Entry parsing rules

`_parse_entry()` requires:

- `title`
- `link`
- `description`

Entries missing any of those are skipped.

## News item mapping

- `title` -> news item title
- `description` -> content
- `link` -> URL
- `id` or URL -> `external_id`
- parsed publication date -> `published_at`
- a small payload snapshot -> `raw_data`

## Scheduling

`rss_producer_job()` calls `BaseProducer.run_job()` with:

- `source_type=SourceType.RSS`
- `concurrency_limit=settings.RSS_FETCH_CONCURRENCY`

## Tests

`backend/tests/test_rss_producer.py` covers:

- successful parsing
- malformed feeds
- fetch failures
- date parsing
- required field filtering

## Related notes

- [[producers/base-producer]]
- [[db/models/source]]
- [[db/models/news-item]]
