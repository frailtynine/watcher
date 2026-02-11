# AI Consumer Flow Diagram

```
┌─────────────────────────────────────────────────────────────────┐
│                    AI CONSUMER WORKFLOW                         │
└─────────────────────────────────────────────────────────────────┘

1. ENTRY POINT
   ┌──────────────────────────┐
   │ process_user_news(db, user)│
   └──────────┬───────────────┘
              │
              ├─ Check user.settings['gemini_api_key']
              │  └─ If missing: return {"processed": 0, "errors": 0}
              │
              └─ Create GeminiClient(api_key)
              
2. TASK PROCESSING
   ┌──────────────────────────┐
   │ _get_active_tasks(user_id)│
   └──────────┬───────────────┘
              │
              └─ SELECT * FROM news_task
                 WHERE user_id = ? AND active = TRUE
              
   For each task:
   ┌──────────────────────────────────┐
   │ _process_task_news(task, client) │
   └──────────┬───────────────────────┘
              │
3. NEWS FETCHING
   ┌────────────────────────────┐
   │ _get_unprocessed_news(task)│
   └──────────┬─────────────────┘
              │
              └─ Query:
                 SELECT DISTINCT news_item.*
                 FROM news_item
                 JOIN source_news_task 
                   ON news_item.source_id = source_news_task.source_id
                 LEFT JOIN news_item_news_task
                   ON news_item.id = news_item_news_task.news_item_id
                   AND news_item_news_task.news_task_id = ?
                 WHERE source_news_task.news_task_id = ?
                   AND news_item.published_at >= NOW() - INTERVAL '4 hours'
                   AND (news_item_news_task IS NULL 
                        OR news_item_news_task.processed = FALSE)

4. AI PROCESSING
   For each news_item:
   ┌─────────────────────────────────────────┐
   │ gemini_client.process_news(             │
   │   news_id=item.id,                      │
   │   title=item.title,                     │
   │   content=item.content,                 │
   │   prompt=task.prompt                    │
   │ )                                       │
   └──────────┬──────────────────────────────┘
              │
              ├─ Build system instruction from prompt
              ├─ Build user message from title + content
              └─ Call Gemini API
                 │
                 ├─ Model: gemini-2.0-flash-lite
                 ├─ Temperature: 0.1
                 ├─ Response format: JSON
                 └─ Schema: {result: boolean, thinking: string}
              
              Returns:
              ┌──────────────────────────┐
              │ ProcessingResult         │
              ├──────────────────────────┤
              │ • news_id: 123           │
              │ • result: True/False     │
              │ • thinking: "..."        │
              │ • tokens_used: 150       │
              └──────────────────────────┘

5. RESULT STORAGE
   ┌────────────────────────────────┐
   │ _save_result(item_id, task_id) │
   └──────────┬─────────────────────┘
              │
              ├─ Check if NewsItemNewsTask exists
              │  (composite key: item_id, task_id)
              │
              ├─ If exists: UPDATE
              │  └─ processed = TRUE
              │     result = <boolean>
              │     processed_at = NOW()
              │     ai_response = {
              │       "thinking": "...",
              │       "tokens_used": 150,
              │       "processed_at": "2024-01-15T10:30:00"
              │     }
              │
              └─ If not exists: INSERT
                 └─ Same fields as above

6. RETURN STATISTICS
   ┌──────────────────────────┐
   │ {"processed": 10,        │
   │  "errors": 1}            │
   └──────────────────────────┘

┌─────────────────────────────────────────────────────────────────┐
│                       ERROR HANDLING                            │
└─────────────────────────────────────────────────────────────────┘

• Missing API key → Skip user (log warning)
• API error → Log error, increment error count, continue
• DB error → Log error, rollback, increment error count, continue
• Invalid response → Default to result=False, thinking=""

Each item processed independently - errors don't cascade!

┌─────────────────────────────────────────────────────────────────┐
│                     DATA FLOW EXAMPLE                           │
└─────────────────────────────────────────────────────────────────┘

User: test@example.com
Settings: {"gemini_api_key": "AIza..."}

Task: "Find news about AI and machine learning"
Sources: RSS Feed (TechCrunch), RSS Feed (Wired)

News Items (< 4 hours old):
  1. "OpenAI releases new model" [TechCrunch]
  2. "Recipe for chocolate cake" [Wired] 
  3. "Google's AI breakthrough" [TechCrunch]

Processing:
  Item 1 + Task → Gemini → result: TRUE ✓
  Item 2 + Task → Gemini → result: FALSE ✗
  Item 3 + Task → Gemini → result: TRUE ✓

Database Result:
  news_item_news_task:
  ┌────────┬─────────┬──────────┬────────┬───────────────────┐
  │ item_id│ task_id │ processed│ result │ ai_response       │
  ├────────┼─────────┼──────────┼────────┼───────────────────┤
  │   1    │    1    │   TRUE   │  TRUE  │ {"thinking": ..., │
  │        │         │          │        │  "tokens": 142}   │
  ├────────┼─────────┼──────────┼────────┼───────────────────┤
  │   2    │    1    │   TRUE   │ FALSE  │ {"thinking": ..., │
  │        │         │          │        │  "tokens": 98}    │
  ├────────┼─────────┼──────────┼────────┼───────────────────┤
  │   3    │    1    │   TRUE   │  TRUE  │ {"thinking": ..., │
  │        │         │          │        │  "tokens": 156}   │
  └────────┴─────────┴──────────┴────────┴───────────────────┘

User sees only items 1 and 3 in their filtered news feed!
```
