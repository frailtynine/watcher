import pytest

from app.delivery.telegram import telegram_service as telegram_service_module
from app.delivery.telegram.telegram_service import TelegramService
from app.models import TelegramBot, TelegramBotNewsTask


pytestmark = pytest.mark.anyio


@pytest.fixture
def telegram_service_test_db(db_session_maker, monkeypatch):
    async def override_get_async_session():
        async with db_session_maker() as session:
            yield session

    monkeypatch.setattr(
        telegram_service_module,
        "get_async_session",
        override_get_async_session,
    )


async def test_get_chat_subscriptions_for_bot(
    telegram_service_test_db,
    db_session_maker,
    test_telegram_bot,
    test_news_task,
):
    async with db_session_maker() as session:
        bot = await session.get(TelegramBot, test_telegram_bot.id)
        bot.chats = [
            {"chat_id": "555", "task_id": test_news_task.id},
            {"chat_id": "777", "task_id": test_news_task.id},
        ]
        session.add(
            TelegramBotNewsTask(
                telegram_bot_id=test_telegram_bot.id,
                news_task_id=test_news_task.id,
            )
        )
        await session.commit()

    service = TelegramService()

    subscriptions = await service.get_chat_subscriptions_for_bot(
        telegram_bot_id=test_telegram_bot.id,
        chat_id="555",
    )

    assert subscriptions == [{"id": test_news_task.id, "name": "Test Task"}]


async def test_remove_chat_subscription(
    telegram_service_test_db,
    db_session_maker,
    test_telegram_bot,
    test_news_task,
):
    async with db_session_maker() as session:
        bot = await session.get(TelegramBot, test_telegram_bot.id)
        bot.chats = [
            {"chat_id": "555", "task_id": test_news_task.id},
            {"chat_id": "555", "task_id": 999},
        ]
        await session.commit()

    service = TelegramService()

    removed = await service.remove_chat_subscription(
        telegram_bot_id=test_telegram_bot.id,
        chat_id="555",
        task_id=test_news_task.id,
    )

    assert removed is True

    async with db_session_maker() as session:
        bot = await session.get(TelegramBot, test_telegram_bot.id)

    assert bot.chats == [{"chat_id": "555", "task_id": 999}]


async def test_remove_chat_subscription_returns_false_when_missing(
    telegram_service_test_db,
    test_telegram_bot,
    test_news_task,
):
    service = TelegramService()

    removed = await service.remove_chat_subscription(
        telegram_bot_id=test_telegram_bot.id,
        chat_id="555",
        task_id=test_news_task.id,
    )

    assert removed is False
