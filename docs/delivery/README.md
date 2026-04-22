# Delivery

This folder documents the layer that turns positive AI matches into a readable newspaper-style output.

## Package purpose

`backend/app/delivery/` currently contains one concrete processor:

- [[delivery/newspaper-processor]]

## Delivery artifact

The delivery layer writes [[db/models/newspaper]] rows, one per [[db/models/news-task]].

## Input assumptions

- the task already has processed news results
- only `NewsItemNewsTask.result=True` rows are relevant
- Gemini is used to rewrite headlines, summarize items, and reposition layout

## Related notes

- [[consumer/ai-consumer]]
- [[db/models/newspaper]]
- [[db/models/news-item-news-task]]
