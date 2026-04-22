# BaseAIClient

**Path:** `backend/app/ai/base.py`

## Purpose

`BaseAIClient` defines the common prompt contract for AI providers and the normalized `ProcessingResult` return type.

## Core pieces

- `ProcessingResult` dataclass
  - `result`
  - `thinking`
  - `tokens_used`
- `process_news()` template method
- abstract `_generate()` method for provider-specific API calls

## Prompt structure

`process_news()` builds:

- a system instruction from the task prompt
- a user message from the news title and content

It then expects a JSON response with:

- `result`
- `thinking`

## Why it matters

This abstraction lets the rest of the system treat Gemini and Nova similarly even though their transport and SDK behavior differ.

## Related notes

- [[consumer/gemini-client]]
- [[consumer/nova-client]]
- [[consumer/ai-consumer]]
