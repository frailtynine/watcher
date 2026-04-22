# GeminiClient

**Path:** `backend/app/ai/gemini_client.py`

## Purpose

`GeminiClient` is the current Google provider implementation for both relevance classification and newspaper layout generation.

## Model

- `MODEL_NAME = "gemini-2.5-flash-lite"`

## Responsibilities

- implement `_generate()` for [[consumer/base-ai-client]]
- count prompt and candidate tokens from Gemini usage metadata
- generate newspaper layout JSON with `process_newspaper()`
- translate unsupported `prefixItems` schema fragments for the Gemini SDK

## News classification path

`_generate()` sends:

- `system_instruction`
- `user_message`
- a JSON response schema requiring `result` and `thinking`

It returns `(response.text, tokens_used)`.

## Newspaper path

`process_newspaper()` sends a prompt plus the `NewsItemNewspaperAIResponse` schema so the model can place a new item into the current layout.

## Notes

- This client is used directly by [[consumer/ai-consumer]] and [[delivery/newspaper-processor]].
- Token counting is approximate to whatever Gemini returns in `usage_metadata`.

## Tests

`backend/tests/test_gemini_client.py` covers:

- initialization
- positive/negative results
- prompt building
- token counting
- error propagation

## Related notes

- [[consumer/base-ai-client]]
- [[consumer/ai-consumer]]
- [[delivery/newspaper-processor]]
