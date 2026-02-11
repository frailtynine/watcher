# AI Consumer Module

This module handles AI-powered news processing using Google Gemini API.

## Overview

The AI consumer processes news items by:
1. Fetching unprocessed news items (published within the last 4 hours)
2. Running them through user-defined prompts via Gemini API
3. Storing results (match/no-match) with AI reasoning

## Components

### `gemini_client.py`

Wrapper around Google Gemini API:
- **Model**: `gemini-2.0-flash-lite`
- **Input**: News title, content, and user prompt
- **Output**: Structured JSON with:
  - `result`: Boolean (matches criteria or not)
  - `thinking`: AI's explanation
  - `tokens_used`: Token count for the request

**Example usage:**
```python
client = GeminiClient(api_key="your-key")
result = await client.process_news(
    news_id=123,
    title="Breaking News",
    content="Full article text...",
    prompt="Find news about technology"
)
# result.result -> True/False
# result.thinking -> "This article discusses..."
# result.tokens_used -> 150
```

### `consumer.py`

Main consumer logic:
- **Per-user processing**: Creates separate Gemini client for each user's API key
- **Active tasks only**: Only processes tasks marked as `active=True`
- **Time window**: Only processes news published within last 4 hours
- **Deduplication**: Skips already-processed item-task combinations
- **Error isolation**: Errors for one item don't stop processing others

**Example usage:**
```python
consumer = AIConsumer()
stats = await consumer.process_user_news(db, user)
# stats -> {"processed": 10, "errors": 1}
```

## Database Schema

Results stored in `news_item_news_task` table:
- `news_item_id`, `news_task_id` - Composite primary key
- `processed` - Boolean flag
- `result` - True if news matches task prompt
- `ai_response` - Full JSON response from Gemini:
  ```json
  {
    "thinking": "This article discusses AI advancements...",
    "tokens_used": 150,
    "processed_at": "2024-01-15T10:30:00"
  }
  ```

## Configuration

Users must set their Gemini API key in user settings:
```json
{
  "gemini_api_key": "YOUR_GOOGLE_API_KEY"
}
```

## Error Handling

- **Missing API key**: Skips processing, logs warning
- **API errors**: Logged but don't stop processing other items
- **Invalid responses**: Defaults to `result=False`, empty thinking

## Testing

Tests use mocked Gemini API responses:
```bash
# Run all AI tests
make test-unit FILE=tests/test_gemini_client.py
make test-unit FILE=tests/test_ai_consumer.py
```

## Future Integration

To integrate into the scheduler:
1. Import in `app/main.py`:
   ```python
   from app.ai.consumer import AIConsumer
   ```
2. Add scheduled job:
   ```python
   async def ai_consumer_job():
       async for db in get_async_session():
           # Get all users
           users = await get_all_users(db)
           consumer = AIConsumer()
           for user in users:
               await consumer.process_user_news(db, user)
   ```
3. Schedule it:
   ```python
   scheduler.add_job(
       ai_consumer_job,
       'interval',
       minutes=10,  # Run every 10 minutes
       id='ai_consumer',
       replace_existing=True
   )
   ```
