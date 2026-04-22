# NovaClient

**Path:** `backend/app/ai/nova_client.py`

## Purpose

`NovaClient` is the Amazon Bedrock implementation of the shared AI client contract.

## Model

- default `MODEL_ID = "amazon.nova-lite-v1:0"`

## Responsibilities

- create a Bedrock runtime client with boto3
- implement `_generate()` using the `converse` API
- extract response text from Bedrock payloads
- sum input and output token counts

## Request shape

The current implementation sends:

- one system instruction block
- one user message block
- `maxTokens=1024`
- `temperature=0.1`

## Current status in the project

- The class is implemented and tested.
- The main consumer currently uses [[consumer/gemini-client]] directly, so Nova is available but not the default pipeline.

## Tests

`backend/tests/test_nova_client.py` covers:

- initialization
- custom model IDs
- positive and negative classification
- missing usage metadata
- Bedrock request structure

## Related notes

- [[consumer/base-ai-client]]
- [[consumer/ai-consumer]]
