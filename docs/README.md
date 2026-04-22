# NewsWatcher vault

This folder is the Obsidian-facing map of the repository. The notes stay close to the code layout so you can connect them later in canvas without re-translating the architecture.

## Start here

- [[project-structure]] - repository-level map
- [[db/README]] - database layer, sessions, and model graph
- [[producers/README]] - RSS and Telegram ingestion
- [[consumer/README]] - AI filtering and provider clients
- [[delivery/README]] - newspaper generation and presentation layer

## Runtime chain

`Source` -> `NewsItem` -> `NewsItemNewsTask` -> `Newspaper`

- Producers pull content from sources and persist [[db/models/news-item]] records.
- The AI consumer evaluates each item against [[db/models/news-task]] prompts.
- Positive results feed the delivery layer, which builds one [[db/models/newspaper]] per task.

## Source material used for these notes

- `README.md`
- `IMPLEMENTATION_GUIDE.md`
- `IMPLEMENTATION_AI_CONSUMER.md`
- `AI_CONSUMER_FLOW.md`
- `backend/app/**/*`
- `backend/tests/**/*`
