# AI Module Rework TODO

## Goals
- Split orchestration, AI evaluation, persistence, and delivery responsibilities.
- Shorten DB session lifetimes and avoid holding sessions during external I/O.
- Make behavior explicit and testable for retries, partial failures, and notifications.

## Current Module Snapshot
- `consumer.py`: mixes orchestration, DB reads/writes, AI calls, newspaper generation, and Telegram delivery.
- `base.py`: good shared contract for AI providers (`ProcessingResult`, `BaseAIClient`).
- `gemini_client.py`: provider implementation + newspaper generation helper.
- `nova_client.py`: provider implementation for Bedrock.
- `__init__.py`: exports `GeminiClient` and `AIConsumer` only.
- `README.md`: partially outdated examples and model names.

## Priority 1: Restructure `consumer.py`
- Create a lightweight job coordinator (`run_ai_consumer_job`) that only resolves active user IDs and dispatches work.
- Split user processing into staged phases:
  - Phase A (read): load active task IDs and required user settings.
  - Phase B (compute): run AI evaluation without DB session.
  - Phase C (write): persist results in short transaction.
  - Phase D (side effects): trigger newspaper/Telegram after successful commit.
- Remove nested `async for get_async_session()` loops inside utility methods.
- Ensure every method has a single responsibility and clear inputs/outputs.

## Priority 2: Session and Transaction Boundaries
- Do not keep one session for the full user lifecycle.
- Open short-lived sessions per phase (read or write), then close.
- Never hold an active DB transaction while waiting on external APIs (Gemini/Telegram).
- Keep commit/rollback only in write-focused methods.

## Priority 3: Service Boundaries
- Extract `TaskSelectionService` (unprocessed items, active tasks).
- Extract `TaskResultService` (upsert `NewsItemNewsTask`, stats derivation).
- Extract `NotificationService` facade (task bot mapping + message dispatch).
- Keep `TelegramSender` transport-only; no DB access there.
- Keep `TelegramService` as lookup/selection logic only.

## Priority 4: Provider Layer Cleanup
- Keep `BaseAIClient` as the single interface for providers.
- Decide whether newspaper generation belongs in provider (`GeminiClient.process_newspaper`) or separate use-case service.
- Make provider selection configurable (Gemini/Nova) instead of directly constructing `GeminiClient` in consumer.

## Priority 5: Data Contracts and Types
- Introduce typed DTOs for processing pipeline stages:
  - task context
  - queued news payload
  - evaluation outcome
  - notification payload
- Remove ambiguous `dict` returns where practical.
- Tighten method return annotations in `consumer.py` to satisfy static checks.

## Priority 6: Reliability and Idempotency
- Guarantee idempotent writes for repeated runs of the same task/news pair.
- Define policy for notification retries/failures (log + continue; optional retry queue later).
- Add clear correlation identifiers in logs (`user_id`, `task_id`, `news_item_id`).

## Priority 7: Tests
- Add unit tests per extracted service (selection, result persistence, notifications).
- Add integration test for pipeline order:
  - evaluate -> persist commit -> notify.
- Add regression tests for:
  - missing API key
  - empty task set
  - AI provider exception on one item
  - notification failure should not rollback persisted AI result.

## Priority 8: Documentation
- Update `README.md` to match actual model name and current scheduler integration.
- Document the new phased workflow and session lifecycle.
- Add a short architecture section with module boundaries.

## Suggested Execution Order
1. Extract selection and persistence services from `consumer.py`.
2. Refactor consumer to phased execution with short DB sessions.
3. Move notification orchestration behind service facade.
4. Add/adjust tests for each extracted boundary.
5. Update README and exports in `__init__.py` if new public services are introduced.
