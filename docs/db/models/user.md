# User model

**Path:** `backend/app/models/user.py`

## Purpose

`User` is the authentication root entity. It comes from `fastapi-users` and adds project-specific settings storage.

## Key fields

- `id` - integer primary key
- `email` - unique, indexed login identifier
- `hashed_password`
- `is_active`, `is_superuser`, `is_verified`
- `settings` - PostgreSQL JSON field for per-user configuration

## Important role in the system

- Users own [[db/models/news-task]] records.
- Users own [[db/models/source]] records.
- The AI layer reads API keys from `user.settings`, with the current consumer primarily looking for `gemini_api_key`.

## Notes

- The model extends `SQLAlchemyBaseUserTable[int]`.
- `settings` is the extensibility point for provider credentials and other user-specific runtime options.

## Related notes

- [[db/models/news-task]]
- [[db/models/source]]
- [[consumer/ai-consumer]]
