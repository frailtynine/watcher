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


async def test_audio_transcription_debug_returns_videoflow_captions(
    client: AsyncClient,
    auth_headers: dict,
    monkeypatch: pytest.MonkeyPatch,
):
    from app.api import ai_debug

    async def fake_transcribe(self, audio_url: str, output_dir: str):
        return (
            [
                {
                    "caption": "Hello",
                    "startTime": 0.0,
                    "endTime": 1.2,
                },
                {
                    "caption": "world",
                    "startTime": 1.2,
                    "endTime": 2.4,
                },
            ],
            "/api/download/files/captions_test.json",
        )

    monkeypatch.setattr(
        ai_debug, "_resolve_gemini_api_key", lambda _u: "test-key"
    )
    monkeypatch.setattr(
        ai_debug.GeminiClient,
        "transcribe_audio_to_videoflow_captions",
        fake_transcribe,
    )

    response = await client.post(
        "/api/debug/ai/audio-transcription",
        headers=auth_headers,
        data={"audio_url": "https://example.com/audio.mp3"},
    )

    assert response.status_code == 200
    data = response.json()
    assert data["captions_count"] == 2
    assert data["captions"][0]["caption"] == "Hello"
    assert data["captions"][0]["startTime"] == 0.0
    assert data["captions"][0]["endTime"] == 1.2
    assert all("\n" not in item["caption"] for item in data["captions"])
    assert all(len(item["caption"]) <= 25 for item in data["captions"])
    assert (
        data["captions_file_url"] == "/api/download/files/captions_test.json"
    )


async def test_audio_transcription_debug_accepts_local_upload(
    client: AsyncClient,
    auth_headers: dict,
    monkeypatch: pytest.MonkeyPatch,
):
    from app.api import ai_debug

    async def fake_transcribe_file(
        self,
        audio_bytes: bytes,
        *,
        filename: str,
        content_type: str | None,
        output_dir: str,
    ):
        assert filename == "sample.mp3"
        assert content_type == "audio/mpeg"
        assert audio_bytes == b"fake-audio-content"
        return (
            [
                {
                    "caption": "Uploaded",
                    "startTime": 0.0,
                    "endTime": 1.0,
                }
            ],
            "/api/download/files/captions_uploaded.json",
        )

    monkeypatch.setattr(
        ai_debug, "_resolve_gemini_api_key", lambda _u: "test-key"
    )
    monkeypatch.setattr(
        ai_debug.GeminiClient,
        "transcribe_audio_file_to_videoflow_captions",
        fake_transcribe_file,
    )

    response = await client.post(
        "/api/debug/ai/audio-transcription",
        headers=auth_headers,
        data={"audio_url": ""},
        files={
            "audio_file": (
                "sample.mp3",
                b"fake-audio-content",
                "audio/mpeg",
            )
        },
    )

    assert response.status_code == 200
    data = response.json()
    assert data["captions_count"] == 1
    assert data["captions"][0]["caption"] == "Uploaded"
    assert (
        data["captions_file_url"]
        == "/api/download/files/captions_uploaded.json"
    )


async def test_audio_transcription_debug_accepts_wav_upload(
    client: AsyncClient,
    auth_headers: dict,
    monkeypatch: pytest.MonkeyPatch,
):
    from app.api import ai_debug

    async def fake_transcribe_file(
        self,
        audio_bytes: bytes,
        *,
        filename: str,
        content_type: str | None,
        output_dir: str,
    ):
        assert filename == "sample.wav"
        assert content_type == "audio/wav"
        assert audio_bytes == b"fake-wav-content"
        return (
            [
                {
                    "caption": "Wav",
                    "startTime": 0.0,
                    "endTime": 1.0,
                }
            ],
            "/api/download/files/captions_wav.json",
        )

    monkeypatch.setattr(
        ai_debug, "_resolve_gemini_api_key", lambda _u: "test-key"
    )
    monkeypatch.setattr(
        ai_debug.GeminiClient,
        "transcribe_audio_file_to_videoflow_captions",
        fake_transcribe_file,
    )

    response = await client.post(
        "/api/debug/ai/audio-transcription",
        headers=auth_headers,
        data={"audio_url": ""},
        files={
            "audio_file": (
                "sample.wav",
                b"fake-wav-content",
                "audio/wav",
            )
        },
    )

    assert response.status_code == 200
    data = response.json()
    assert data["captions_count"] == 1
    assert data["captions"][0]["caption"] == "Wav"
    assert data["captions_file_url"] == "/api/download/files/captions_wav.json"
