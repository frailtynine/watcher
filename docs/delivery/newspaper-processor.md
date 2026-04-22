# NewsPaperProcessor

**Path:** `backend/app/delivery/web.py`

## Purpose

`NewsPaperProcessor` builds and updates the newspaper JSON for a task.

## Main methods

- `get_newspaper(news_task)` - load or create the task newspaper
- `create_newspaper(news_task)` - build a first version from positive items
- `process_newspaper(news_item, news_task)` - insert a new item into the current layout
- `_build_body_from_items(news_task)` - bootstrap layout from recent positive results
- `_update_newspaper_body(newspaper, new_body)` - persist the JSON body

## Input query

When building from scratch, the processor:

- joins `NewsItem` with [[db/models/news-item-news-task]]
- filters to `processed=True` and `result=True`
- orders by `NewsItem.updated_at.desc()`
- limits to 10 items

## AI contract

The prompt asks Gemini to:

- write a concise headline
- write a short summary
- place the new item in the layout
- reposition surviving existing items
- keep the newspaper within 10 rows/items of interest

The response is validated against `NewsItemNewspaperAIResponse` from `backend/app/schemas/newspaper.py`.

## Output shape

`NewspaperBody.rows` is a list of `NewsItemNewspaper` objects with:

- generated title
- generated summary
- linked `news_item_id`
- `position` tuple `(row, col)`
- source metadata and link

## API exposure

`backend/app/api/newspapers.py` exposes:

- `GET /api/newspapers/{news_task_id}`
- `POST /api/newspapers/{news_task_id}/regenerate`

## Notes

- If the stored newspaper body does not validate, the processor rebuilds it from positive items.
- Newspaper update failures are logged but are downstream of AI classification persistence.

## Related notes

- [[db/models/newspaper]]
- [[consumer/gemini-client]]
- [[consumer/ai-consumer]]
