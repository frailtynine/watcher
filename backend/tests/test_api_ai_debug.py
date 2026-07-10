import pytest
from httpx import AsyncClient


pytestmark = pytest.mark.anyio


async def test_summary_debug_uses_defaults_when_task_not_selected(
    client: AsyncClient,
    auth_headers: dict,
    monkeypatch: pytest.MonkeyPatch,
):
    from app.api import ai_debug

    async def fake_summarize_article(self, article, prompt: str, api_key: str):
        return f"summary::{prompt}::{api_key}"

    monkeypatch.setattr(
        ai_debug, "_resolve_gemini_api_key", lambda _u: "test-key"
    )
    monkeypatch.setattr(
        ai_debug.SummaryService,
        "get_article",
        lambda self, _url: object(),
    )
    monkeypatch.setattr(
        ai_debug.SummaryService,
        "summarize_article",
        fake_summarize_article,
    )

    response = await client.post(
        "/api/debug/ai/summary",
        headers=auth_headers,
        json={
            "link": "https://example.com/test-article",
        },
    )

    assert response.status_code == 200
    data = response.json()
    assert data["language"] == "en"
    assert data["task_id"] is None
    assert (
        data["prompt_used"]
        == "Retell the news article in a neutral way in a short form, "
        "no more than three sentences\n\nSummarize in en language"
    )
    assert "test-key" in data["summary"]


async def test_summary_debug_uses_task_prompt_and_language(
    client: AsyncClient,
    auth_headers: dict,
    test_user,
    db_session_maker,
    monkeypatch: pytest.MonkeyPatch,
):
    from app.api import ai_debug
    from app.models import NewsTask

    async with db_session_maker() as session:
        task = NewsTask(
            user_id=test_user.id,
            name="Summary Task",
            prompt="Find relevant fintech updates",
            active=True,
            settings={
                "delivery": {
                    "telegram": {
                        "summary": True,
                        "lang": "de",
                        "prompt": "Rewrite in a neutral short German style",
                    }
                }
            },
        )
        session.add(task)
        await session.commit()
        await session.refresh(task)
        task_id = task.id

    async def fake_summarize_article(self, article, prompt: str, api_key: str):
        return prompt

    monkeypatch.setattr(
        ai_debug, "_resolve_gemini_api_key", lambda _u: "test-key"
    )
    monkeypatch.setattr(
        ai_debug.SummaryService,
        "get_article",
        lambda self, _url: object(),
    )
    monkeypatch.setattr(
        ai_debug.SummaryService,
        "summarize_article",
        fake_summarize_article,
    )

    response = await client.post(
        "/api/debug/ai/summary",
        headers=auth_headers,
        json={
            "link": "https://example.com/task-article",
            "task_id": task_id,
        },
    )

    assert response.status_code == 200
    data = response.json()
    assert data["task_id"] == task_id
    assert data["language"] == "de"
    assert (
        data["prompt_used"] == "Rewrite in a neutral short German style\n\n"
        "Summarize in de language"
    )
    assert data["summary"] == data["prompt_used"]
