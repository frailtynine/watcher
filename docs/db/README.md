# Database layer

This folder documents the persistence layer: engine/session setup plus the SQLAlchemy models that define the news pipeline.

## Key files

- [[db/database]] - async engine, session maker, session dependency
- `backend/app/models/__init__.py` - exported model surface
- `backend/app/models/utils.py` - shared UTC timestamp helper

## Model graph

- [[db/models/user]] owns many [[db/models/news-task]] and [[db/models/source]] records by foreign key.
- [[db/models/source]] connects to [[db/models/news-task]] through [[db/models/source-news-task]].
- [[db/models/source]] produces many [[db/models/news-item]] records.
- [[db/models/news-item]] connects to [[db/models/news-task]] through [[db/models/news-item-news-task]], which stores AI results.
- [[db/models/news-task]] has a one-to-one presentation artifact in [[db/models/newspaper]].

## Notes

- The database layer uses async SQLAlchemy sessions from `backend/app/db/database.py`.
- Timestamp columns mostly use `utcnow_naive()` because the schema stores naive UTC datetimes.
- Tests covering model creation and constraints live in `backend/tests/test_models.py` and `backend/tests/test_newspaper_model.py`.

## Model notes

- [[db/models/user]]
- [[db/models/news-task]]
- [[db/models/source]]
- [[db/models/source-news-task]]
- [[db/models/news-item]]
- [[db/models/news-item-news-task]]
- [[db/models/newspaper]]
