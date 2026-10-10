import pytest
from httpx import AsyncClient


pytestmark = pytest.mark.anyio


async def test_jev_debug_runs_all_cases(
    client: AsyncClient,
    auth_headers: dict,
    monkeypatch: pytest.MonkeyPatch,
):
    from app.api import ai_debug

    async def fake_is_news_relevant(self, title, content, prompt):
        return "strikes" in title.lower()

    monkeypatch.setattr(
        ai_debug.OpenRouterClient,
        "is_news_relevant",
        fake_is_news_relevant,
    )

    response = await client.post(
        "/api/debug/ai/jev",
        headers=auth_headers,
        json={"criteria": "Return news about war in Iran."},
    )

    assert response.status_code == 200
    data = response.json()
    assert len(data["cases"]) == 3
    assert data["cases"][0]["is_relevant"] is True
    assert data["cases"][1]["is_relevant"] is False
    assert data["cases"][2]["is_relevant"] is False


async def test_summary_debug_uses_defaults_when_task_not_selected(
    client: AsyncClient,
    auth_headers: dict,
    monkeypatch: pytest.MonkeyPatch,
):
    from app.api import ai_debug

    async def fake_summarize_article(self, article, prompt: str):
        return f"summary::{prompt}"

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
    assert data["summary"].startswith("summary::")


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

    async def fake_summarize_article(self, article, prompt: str):
        return prompt

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
