# RSSProducer

**Path:** `backend/app/producers/rss.py`

## Purpose

`RSSProducer` ingests RSS and Atom feeds and turns valid entries into [[db/models/news-item]] records.

## Entry points

- `RSSProducer.fetch(source)`
- `rss_producer_job()`

## Fetch behavior

- downloads feeds with cancellable HTTP requests, bounded by `RSS_FETCH_TIMEOUT_SECONDS` (default 30 seconds)
- parses downloaded content with `feedparser.parse` in a worker thread
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

Only one RSS job runs at a time. Runs exceeding `RSS_JOB_TIMEOUT_SECONDS`
(default 300 seconds) are cancelled so a later scheduled run can proceed.
An interval may still be skipped if a healthy run takes longer than the
configured interval. Cancellation cannot stop a parsing thread already running.

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
