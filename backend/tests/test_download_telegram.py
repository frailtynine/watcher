import pytest
from unittest.mock import AsyncMock, MagicMock

from app.download.telegram import TelegramDownloadService, is_telegram_link


def test_is_telegram_link_accepts_supported_hosts():
    assert is_telegram_link("https://t.me/mychannel/123") is True
    assert is_telegram_link("https://telegram.me/mychannel/123") is True
    assert is_telegram_link("https://www.t.me/mychannel/123") is True


def test_is_telegram_link_rejects_other_hosts():
    assert is_telegram_link("https://example.com/mychannel/123") is False
    assert is_telegram_link("https://youtube.com/watch?v=1") is False


def test_parse_message_link():
    channel, message_id = TelegramDownloadService.parse_message_link(
        "https://t.me/some_channel/456"
    )
    assert channel == "some_channel"
    assert message_id == 456


def test_parse_message_link_raises_for_invalid_path():
    with pytest.raises(ValueError, match="Invalid Telegram post link"):
        TelegramDownloadService.parse_message_link("https://t.me/some_channel")


def test_resolve_file_path_rejects_path_traversal(tmp_path):
    service = TelegramDownloadService(str(tmp_path))
    with pytest.raises(ValueError, match="Invalid filename"):
        service.resolve_file_path("../secret.txt")


def test_extract_filename_from_download_url():
    filename = TelegramDownloadService.extract_filename_from_download_url(
        "/api/download/files/a1b2c3.mp4"
    )
    assert filename == "a1b2c3.mp4"


def test_extract_filename_from_download_url_rejects_invalid_url():
    with pytest.raises(ValueError, match="Invalid download URL"):
        TelegramDownloadService.extract_filename_from_download_url(
            "/api/other/files/a1b2c3.mp4"
        )


@pytest.mark.anyio
async def test_get_media_items_for_message_returns_single_when_not_grouped(
    tmp_path,
):
    service = TelegramDownloadService(str(tmp_path))
    client = MagicMock()
    message = MagicMock()
    message.grouped_id = None

    result = await service._get_media_items_for_message(
        client=client,
        channel="testchannel",
        message=message,
    )

    assert result == [message]
    client.get_messages.assert_not_called()


@pytest.mark.anyio
async def test_get_media_items_for_message_returns_album_items(tmp_path):
    service = TelegramDownloadService(str(tmp_path))
    client = MagicMock()

    main_message = MagicMock()
    main_message.id = 100
    main_message.grouped_id = 777

    item_a = MagicMock()
    item_a.grouped_id = 777
    item_a.media = object()

    item_b = MagicMock()
    item_b.grouped_id = 777
    item_b.media = object()

    not_album = MagicMock()
    not_album.grouped_id = 888
    not_album.media = object()

    client.get_messages = AsyncMock(return_value=[item_a, item_b, not_album])

    result = await service._get_media_items_for_message(
        client=client,
        channel="testchannel",
        message=main_message,
    )

    assert result == [item_a, item_b]
    client.get_messages.assert_awaited_once()


@pytest.mark.anyio
async def test_get_media_previews_from_link_returns_ids_and_thumbnails(
    tmp_path,
    monkeypatch: pytest.MonkeyPatch,
):
    service = TelegramDownloadService(str(tmp_path))

    media_item = MagicMock()
    media_item.id = 123
    media_item.media = MagicMock()
    media_item.media.__class__.__name__ = "MessageMediaPhoto"
    media_item.photo = object()

    message = MagicMock()
    message.id = 123
    message.grouped_id = None

    client_instance = MagicMock()
    client_instance.get_messages = AsyncMock(return_value=message)
    client_instance.download_media = AsyncMock(
        return_value=str(tmp_path / "thumb.jpg")
    )

    import app.download.telegram as telegram_module

    PathClass = telegram_module.Path
    PathClass(str(tmp_path / "thumb.jpg")).write_bytes(b"thumb")

    class FakeClientContext:
        async def __aenter__(self):
            return client_instance

        async def __aexit__(self, exc_type, exc, tb):
            return False

    monkeypatch.setattr(
        telegram_module,
        "TelegramClient",
        lambda *args, **kwargs: FakeClientContext(),
    )
    monkeypatch.setattr(
        telegram_module,
        "StringSession",
        lambda _session: object(),
    )
    monkeypatch.setattr(
        service,
        "_get_media_items_for_message",
        AsyncMock(return_value=[media_item]),
    )

    items = await service.get_media_previews_from_link(
        link="https://t.me/test/123",
        api_id="1",
        api_hash="hash",
        session_string="session",
    )

    assert len(items) == 1
    assert items[0]["media_id"] == 123
    assert items[0]["thumbnail_url"].startswith("/api/download/files/")
    assert items[0]["media_type"] == "image"
