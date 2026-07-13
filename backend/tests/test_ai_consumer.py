"""Tests for AI consumer."""

import pytest
from datetime import datetime, timedelta
from unittest.mock import AsyncMock, MagicMock

from app.ai.consumer import AIConsumer
from app.ai.base import ProcessingResult
from app.core.config import settings
from app.core.encryption import encrypt_value
from app.models.news_item import NewsItem
from app.models.news_task import NewsTask
from app.models.news_item_news_task import NewsItemNewsTask
from app.models.source import Source, SourceType
from app.models.source_news_task import SourceNewsTask
from app.models.telegram_bot import TelegramBot
from app.models.telegram_bot_news_task import TelegramBotNewsTask
from app.models.user import User


@pytest.fixture
def ai_consumer():
    """Create AI consumer instance."""
    return AIConsumer()


@pytest.fixture
def mock_user():
    """Create a mock user with Gemini API key."""
    user = MagicMock(spec=User)
    user.id = 1
    user.email = "test@example.com"
    user.settings = {
        "gemini_api_key": encrypt_value(
            "test-api-key",
            settings.ENCRYPTION_KEY,
        )
    }
    return user


@pytest.fixture
def mock_user_no_key():
    """Create a mock user without API key."""
    user = MagicMock(spec=User)
    user.id = 2
    user.email = "nokey@example.com"
    user.settings = {}
    return user


@pytest.fixture
async def test_news_item(db_session_maker, test_source):
    """Create a test news item."""
    async with db_session_maker() as session:
        news_item = NewsItem(
            source_id=test_source.id,
            title="Test News",
            content="This is test news content",
            url="https://example.com/news/1",
            published_at=datetime.now(),
        )
        session.add(news_item)
        await session.commit()
        await session.refresh(news_item)
        return news_item


@pytest.mark.anyio
async def test_get_user_api_key(ai_consumer, mock_user):
    """Test extracting API key from user settings."""
    api_key = ai_consumer._get_user_api_key(mock_user)
    assert api_key == "test-api-key"


@pytest.mark.anyio
async def test_get_user_api_key_missing(ai_consumer, mock_user_no_key):
    """Test handling missing API key."""
    api_key = ai_consumer._get_user_api_key(mock_user_no_key)
    assert api_key is None


@pytest.mark.anyio
async def test_get_user_api_key_no_settings(ai_consumer):
    """Test handling user with no settings."""
    user = MagicMock(spec=User)
    user.settings = None
    api_key = ai_consumer._get_user_api_key(user)
    assert api_key is None


@pytest.mark.anyio
async def test_get_active_tasks(
    ai_consumer, db_session_maker, test_user, test_news_task
):
    """Test fetching active tasks for a user."""
    async with db_session_maker() as session:
        tasks = await ai_consumer._get_active_tasks(session, test_user.id)
        assert len(tasks) == 1
        assert tasks[0].id == test_news_task.id
        assert tasks[0].active is True


@pytest.mark.anyio
async def test_get_active_tasks_excludes_inactive(
    ai_consumer, db_session_maker, test_user
):
    """Test that inactive tasks are excluded."""
    async with db_session_maker() as session:
        # Create active task
        active_task = NewsTask(
            user_id=test_user.id,
            name="Active Task",
            prompt="Find tech news",
            active=True,
        )
        # Create inactive task
        inactive_task = NewsTask(
            user_id=test_user.id,
            name="Inactive Task",
            prompt="Find sports news",
            active=False,
        )
        session.add(active_task)
        session.add(inactive_task)
        await session.commit()

    async with db_session_maker() as session:
        consumer = AIConsumer()
        tasks = await consumer._get_active_tasks(session, test_user.id)
        assert len(tasks) == 1
        assert tasks[0].name == "Active Task"


@pytest.mark.anyio
async def test_get_unprocessed_news(
    ai_consumer, db_session_maker, test_user, test_news_task, test_source
):
    """Test fetching unprocessed news items."""
    async with db_session_maker() as session:
        # Link source to task
        source_task_link = SourceNewsTask(
            source_id=test_source.id, news_task_id=test_news_task.id
        )
        session.add(source_task_link)

        # Create recent news item
        recent_item = NewsItem(
            source_id=test_source.id,
            title="Recent News",
            content="Recent content",
            published_at=datetime.now() - timedelta(hours=2),
        )
        session.add(recent_item)

        # Create old news item (> 4 hours)
        old_item = NewsItem(
            source_id=test_source.id,
            title="Old News",
            content="Old content",
            published_at=datetime.now() - timedelta(hours=5),
        )
        session.add(old_item)

        await session.commit()

        # Merge the task into this session
        task_in_session = await session.merge(test_news_task)

        # Fetch unprocessed news
        consumer = AIConsumer()
        news_items = await consumer._get_unprocessed_news(
            session, task_in_session
        )

        # Should only get recent item
        assert len(news_items) == 1
        assert news_items[0].title == "Recent News"


@pytest.mark.anyio
async def test_save_result_creates_new_record(
    ai_consumer, db_session_maker, test_user
):
    """Test saving result creates new record."""
    # Create test data
    async with db_session_maker() as session:
        source = Source(
            user_id=test_user.id,
            name="Test Source",
            source="https://test.com/feed",
            type=SourceType.RSS,
        )
        session.add(source)
        await session.commit()
        await session.refresh(source)

        news_item = NewsItem(
            source_id=source.id,
            title="Test News",
            content="Test content",
            published_at=datetime.now(),
        )
        session.add(news_item)

        news_task = NewsTask(
            user_id=test_user.id,
            name="Test Task",
            prompt="Test prompt",
            active=True,
        )
        session.add(news_task)
        await session.commit()
        await session.refresh(news_item)
        await session.refresh(news_task)

        result = ProcessingResult(
            result=True, thinking="Matches criteria", tokens_used=150
        )

        consumer = AIConsumer()
        await consumer._save_result(session, news_item, news_task, result)
        # Commit happens at higher level now
        await session.commit()

    # Verify record was created
    async with db_session_maker() as session:
        from sqlalchemy import select

        stmt = select(NewsItemNewsTask).where(
            NewsItemNewsTask.news_item_id == news_item.id,
            NewsItemNewsTask.news_task_id == news_task.id,
        )
        db_result = await session.execute(stmt)
        record = db_result.scalar_one()

        assert record.processed is True
        assert record.result is True
        assert record.ai_response["thinking"] == "Matches criteria"
        assert record.ai_response["tokens_used"] == 150


@pytest.mark.anyio
async def test_save_result_updates_existing_record(
    ai_consumer, db_session_maker, test_user
):
    """Test saving result updates existing record."""
    # Create test data
    async with db_session_maker() as session:
        source = Source(
            user_id=test_user.id,
            name="Test Source",
            source="https://test.com/feed",
            type=SourceType.RSS,
        )
        session.add(source)
        await session.commit()
        await session.refresh(source)

        news_item = NewsItem(
            source_id=source.id,
            title="Test News",
            content="Test content",
            published_at=datetime.now(),
        )
        session.add(news_item)

        news_task = NewsTask(
            user_id=test_user.id,
            name="Test Task",
            prompt="Test prompt",
            active=True,
        )
        session.add(news_task)
        await session.commit()
        await session.refresh(news_item)
        await session.refresh(news_task)

        # Create initial record
        initial_record = NewsItemNewsTask(
            news_item_id=news_item.id,
            news_task_id=news_task.id,
            processed=False,
            result=None,
        )
        session.add(initial_record)
        await session.commit()

    # Update with processing result
    result = ProcessingResult(
        result=False, thinking="Does not match", tokens_used=100
    )

    async with db_session_maker() as session:
        consumer = AIConsumer()
        item_in_session = await session.merge(news_item)
        task_in_session = await session.merge(news_task)
        await consumer._save_result(
            session, item_in_session, task_in_session, result
        )
        # Commit happens at higher level now
        await session.commit()

    # Verify record was updated
    async with db_session_maker() as session:
        from sqlalchemy import select

        stmt = select(NewsItemNewsTask).where(
            NewsItemNewsTask.news_item_id == news_item.id,
            NewsItemNewsTask.news_task_id == news_task.id,
        )
        db_result = await session.execute(stmt)
        record = db_result.scalar_one()

        assert record.processed is True
        assert record.result is False
        assert record.ai_response["thinking"] == "Does not match"


@pytest.mark.anyio
async def test_process_user_news_no_api_key(
    ai_consumer, db_session_maker, mock_user_no_key
):
    """Test processing handles missing API key."""
    result = await ai_consumer.process_user_news(mock_user_no_key.id)

    assert result["processed"] == 0
    assert result["errors"] == 0


@pytest.mark.anyio
async def test_process_task_news_with_error(
    ai_consumer, db_session_maker, test_news_task, test_source
):
    """Test error handling during processing."""
    # Setup: Link source to task and create news item
    async with db_session_maker() as session:
        source_task_link = SourceNewsTask(
            source_id=test_source.id, news_task_id=test_news_task.id
        )
        session.add(source_task_link)

        news_item = NewsItem(
            source_id=test_source.id,
            title="Test News",
            content="Test content",
            published_at=datetime.utcnow() - timedelta(hours=1),
        )
        session.add(news_item)
        await session.commit()

    # Mock Gemini client that raises error
    mock_client = MagicMock()
    mock_client.process_news = AsyncMock(side_effect=Exception("API Error"))

    async with db_session_maker() as session:
        consumer = AIConsumer()
        task_in_session = await session.merge(test_news_task)
        user = MagicMock(spec=User)
        user.id = 1
        user.email = "test@example.com"
        stats = await consumer._process_task_news(
            session,
            mock_client,
            task_in_session,
            user,
        )

        assert stats["processed"] == 0
        assert stats["errors"] == 1


@pytest.mark.anyio
async def test_process_task_news_success(
    ai_consumer, db_session_maker, test_news_task, test_source
):
    """Test successful processing of news items."""
    # Setup: Link source to task and create news item
    async with db_session_maker() as session:
        source_task_link = SourceNewsTask(
            source_id=test_source.id, news_task_id=test_news_task.id
        )
        session.add(source_task_link)

        news_item = NewsItem(
            source_id=test_source.id,
            title="Test News",
            content="Test content",
            published_at=datetime.utcnow() - timedelta(hours=1),
        )
        session.add(news_item)
        await session.commit()

    # Mock Gemini client
    mock_client = MagicMock()
    mock_client.process_news = AsyncMock(
        return_value=ProcessingResult(
            result=True, thinking="Test thinking", tokens_used=200
        )
    )

    async with db_session_maker() as session:
        consumer = AIConsumer()
        task_in_session = await session.merge(test_news_task)
        user = MagicMock(spec=User)
        user.id = 1
        user.email = "test@example.com"
        stats = await consumer._process_task_news(
            session,
            mock_client,
            task_in_session,
            user,
        )

        assert stats["processed"] == 1
        assert stats["errors"] == 0


@pytest.mark.anyio
async def test_get_task_bot_ids_returns_associated_ids(
    ai_consumer,
    db_session_maker,
    test_user,
    test_news_task,
    test_telegram_bot,
):
    async with db_session_maker() as session:
        second_bot = TelegramBot(
            user_id=test_user.id,
            bot_token="encrypted-token-2",
            bot_name="test_news_bot_2",
            bot_tg_id="987654321",
            chats=[],
            is_active=True,
        )
        session.add(second_bot)
        await session.commit()
        await session.refresh(second_bot)

        session.add_all(
            [
                TelegramBotNewsTask(
                    telegram_bot_id=test_telegram_bot.id,
                    news_task_id=test_news_task.id,
                ),
                TelegramBotNewsTask(
                    telegram_bot_id=second_bot.id,
                    news_task_id=test_news_task.id,
                ),
            ]
        )
        await session.commit()

        bot_ids = await ai_consumer._get_task_bot_ids(
            session, test_news_task.id
        )

        assert set(bot_ids) == {test_telegram_bot.id, second_bot.id}


@pytest.mark.anyio
async def test_process_task_news_sends_message_for_each_bot_on_match(
    db_session_maker,
    test_news_task,
    test_source,
):
    async with db_session_maker() as session:
        session.add(
            SourceNewsTask(
                source_id=test_source.id,
                news_task_id=test_news_task.id,
            )
        )
        session.add(
            NewsItem(
                source_id=test_source.id,
                title="Matched News",
                content="Matched content",
                url="https://example.com/matched",
                published_at=datetime.utcnow() - timedelta(hours=1),
            )
        )
        await session.commit()

    mock_client = MagicMock()
    mock_client.process_news = AsyncMock(
        return_value=ProcessingResult(
            result=True,
            thinking="Matches",
            tokens_used=50,
        )
    )

    async with db_session_maker() as session:
        consumer = AIConsumer()
        consumer._get_task_bot_ids = AsyncMock(return_value=[10, 20])
        consumer._send_message = AsyncMock()

        task_in_session = await session.merge(test_news_task)
        user = MagicMock(spec=User)
        user.id = 1
        user.email = "test@example.com"

        await consumer._process_task_news(
            session,
            mock_client,
            task_in_session,
            user,
        )

        assert consumer._send_message.await_count == 2


@pytest.mark.anyio
async def test_process_task_news_uses_title_when_news_url_missing(
    db_session_maker,
    test_news_task,
    test_source,
):
    async with db_session_maker() as session:
        session.add(
            SourceNewsTask(
                source_id=test_source.id,
                news_task_id=test_news_task.id,
            )
        )
        session.add(
            NewsItem(
                source_id=test_source.id,
                title="Title As Fallback",
                content="Matched content",
                url=None,
                published_at=datetime.utcnow() - timedelta(hours=1),
            )
        )
        await session.commit()

    mock_client = MagicMock()
    mock_client.process_news = AsyncMock(
        return_value=ProcessingResult(
            result=True,
            thinking="Matches",
            tokens_used=50,
        )
    )

    async with db_session_maker() as session:
        consumer = AIConsumer()
        consumer._get_task_bot_ids = AsyncMock(return_value=[10])
        consumer._send_message = AsyncMock()

        task_in_session = await session.merge(test_news_task)
        user = MagicMock(spec=User)
        user.id = 1
        user.email = "test@example.com"

        await consumer._process_task_news(
            session,
            mock_client,
            task_in_session,
            user,
        )

        consumer._send_message.assert_awaited_once_with(
            user_id=1,
            bot_id=10,
            newstask_id=test_news_task.id,
            news_url="Title As Fallback",
        )


@pytest.mark.anyio
async def test_get_task_telegram_delivery_settings_defaults(ai_consumer):
    task = MagicMock(spec=NewsTask)
    task.settings = None

    settings_dict = ai_consumer._get_task_telegram_delivery_settings(task)

    assert settings_dict["summary"] is False
    assert settings_dict["lang"] == "en"
    assert (
        settings_dict["prompt"]
        == "Retell the news article in a neutral way in a short form, "
        "no more than three sentences"
    )


@pytest.mark.anyio
async def test_process_task_news_uses_summary_service_when_enabled(
    db_session_maker,
    test_news_task,
    test_source,
    monkeypatch: pytest.MonkeyPatch,
):
    async with db_session_maker() as session:
        session.add(
            SourceNewsTask(
                source_id=test_source.id,
                news_task_id=test_news_task.id,
            )
        )
        session.add(
            NewsItem(
                source_id=test_source.id,
                title="Matched News",
                content="Matched content",
                url="https://example.com/matched-summary",
                published_at=datetime.now() - timedelta(hours=1),
            )
        )
        await session.commit()

    mock_client = MagicMock()
    mock_client.process_news = AsyncMock(
        return_value=ProcessingResult(
            result=True,
            thinking="Matches",
            tokens_used=50,
        )
    )

    summarize_news_item_mock = AsyncMock(
        return_value="SUMMARY TEXT\n\nhttps://example.com/matched-summary"
    )

    from app.ai import consumer as consumer_module

    monkeypatch.setattr(
        consumer_module.SummaryService,
        "summarize_news_item",
        summarize_news_item_mock,
    )

    async with db_session_maker() as session:
        consumer = AIConsumer()
        consumer._get_task_bot_ids = AsyncMock(return_value=[10])
        consumer._send_message = AsyncMock()
        consumer.notification_service.is_new_relevant_news_item = AsyncMock(
            return_value=(True, "new")
        )

        task_in_session = await session.merge(test_news_task)
        task_in_session.settings = {
            "delivery": {
                "telegram": {
                    "summary": True,
                    "lang": "de",
                    "prompt": "Rewrite neutrally in short form",
                }
            }
        }

        user = MagicMock(spec=User)
        user.id = 1
        user.email = "test@example.com"

        await consumer._process_task_news(
            session,
            mock_client,
            task_in_session,
            user,
            gemini_api_key="test-api-key",
        )

        summarize_news_item_mock.assert_awaited_once()
        summarize_kwargs = summarize_news_item_mock.await_args_list[0].kwargs
        assert summarize_kwargs["prompt"] == "Rewrite neutrally in short form"
        assert summarize_kwargs["language"] == "de"

        consumer._send_message.assert_awaited_once_with(
            user_id=1,
            bot_id=10,
            newstask_id=test_news_task.id,
            news_url=("SUMMARY TEXT\n\nhttps://example.com/matched-summary"),
        )


@pytest.mark.anyio
async def test_process_task_news_uses_rss_content_when_article_download_fails(
    db_session_maker,
    test_news_task,
    test_source,
    monkeypatch: pytest.MonkeyPatch,
):
    async with db_session_maker() as session:
        session.add(
            SourceNewsTask(
                source_id=test_source.id,
                news_task_id=test_news_task.id,
            )
        )
        session.add(
            NewsItem(
                source_id=test_source.id,
                title="RSS Title",
                content="RSS content body",
                url="https://example.com/failing-download",
                published_at=datetime.utcnow() - timedelta(hours=1),
            )
        )
        await session.commit()

    mock_client = MagicMock()
    mock_client.process_news = AsyncMock(
        return_value=ProcessingResult(
            result=True,
            thinking="Matches",
            tokens_used=50,
        )
    )

    from app.ai import consumer as consumer_module

    summarize_news_item_mock = AsyncMock(
        return_value="SUMMARY FROM RSS\n\nhttps://example.com/failing-download"
    )
    monkeypatch.setattr(
        consumer_module.SummaryService,
        "summarize_news_item",
        summarize_news_item_mock,
    )

    async with db_session_maker() as session:
        consumer = AIConsumer()
        consumer._get_task_bot_ids = AsyncMock(return_value=[10])
        consumer._send_message = AsyncMock()
        consumer.notification_service.is_new_relevant_news_item = AsyncMock(
            return_value=(True, "new")
        )

        task_in_session = await session.merge(test_news_task)
        task_in_session.settings = {
            "delivery": {
                "telegram": {
                    "summary": True,
                    "lang": "en",
                    "prompt": "Use neutral short summary",
                }
            }
        }

        user = MagicMock(spec=User)
        user.id = 1
        user.email = "test@example.com"

        await consumer._process_task_news(
            session,
            mock_client,
            task_in_session,
            user,
            gemini_api_key="test-api-key",
        )

        summarize_news_item_mock.assert_awaited_once()
        consumer._send_message.assert_awaited_once_with(
            user_id=1,
            bot_id=10,
            newstask_id=test_news_task.id,
            news_url=(
                "SUMMARY FROM RSS\n\nhttps://example.com/failing-download"
            ),
        )


@pytest.mark.anyio
async def test_process_task_news_falls_back_to_url_when_summary_fails(
    db_session_maker,
    test_news_task,
    test_source,
    monkeypatch: pytest.MonkeyPatch,
):
    async with db_session_maker() as session:
        session.add(
            SourceNewsTask(
                source_id=test_source.id,
                news_task_id=test_news_task.id,
            )
        )
        session.add(
            NewsItem(
                source_id=test_source.id,
                title="Fallback Title",
                content="RSS fallback content",
                url="https://example.com/fallback-url",
                published_at=datetime.now() - timedelta(hours=1),
            )
        )
        await session.commit()

    mock_client = MagicMock()
    mock_client.process_news = AsyncMock(
        return_value=ProcessingResult(
            result=True,
            thinking="Matches",
            tokens_used=50,
        )
    )

    from app.ai import consumer as consumer_module

    monkeypatch.setattr(
        consumer_module.SummaryService,
        "summarize_news_item",
        AsyncMock(side_effect=Exception("summary failed")),
    )

    async with db_session_maker() as session:
        consumer = AIConsumer()
        consumer._get_task_bot_ids = AsyncMock(return_value=[10])
        consumer._send_message = AsyncMock()
        consumer.notification_service.is_new_relevant_news_item = AsyncMock(
            return_value=(True, "new")
        )

        task_in_session = await session.merge(test_news_task)
        task_in_session.settings = {
            "delivery": {
                "telegram": {
                    "summary": True,
                    "lang": "en",
                    "prompt": "Use neutral short summary",
                }
            }
        }

        user = MagicMock(spec=User)
        user.id = 1
        user.email = "test@example.com"

        await consumer._process_task_news(
            session,
            mock_client,
            task_in_session,
            user,
            gemini_api_key="test-api-key",
        )

        consumer._send_message.assert_awaited_once_with(
            user_id=1,
            bot_id=10,
            newstask_id=test_news_task.id,
            news_url="https://example.com/fallback-url",
        )
