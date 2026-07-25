import pytest
from httpx import AsyncClient
from unittest.mock import AsyncMock, patch


pytestmark = pytest.mark.anyio


async def test_download_rejects_non_telegram_link(
    client: AsyncClient,
    auth_headers: dict,
):
    response = await client.post(
        "/api/download/",
        headers=auth_headers,
        json={"link": "https://example.com/video/1"},
    )

    assert response.status_code == 400
    assert (
        response.json()["detail"]
        == "Only Telegram links are supported for now."
    )


async def test_download_requires_telegram_credentials(
    client: AsyncClient,
    auth_headers: dict,
):
    response = await client.post(
        "/api/download/",
        headers=auth_headers,
        json={"link": "https://t.me/testchannel/1"},
    )

    assert response.status_code == 400
    assert "requires user Telegram credentials" in response.json()["detail"]


async def test_download_returns_urls_for_telegram_post(
    client: AsyncClient,
    auth_headers: dict,
):
    settings_response = await client.patch(
        "/api/users/me",
        headers=auth_headers,
        json={
            "settings": {
                "telegram_api_id": "12345",
                "telegram_api_hash": "test-hash",
                "telegram_session_string": "test-session",
            }
        },
    )
    assert settings_response.status_code == 200

    with patch(
        "app.api.download.TelegramDownloadService.download_from_link",
        new=AsyncMock(
            return_value=[
                "/api/download/files/video1.mp4",
                "/api/download/files/video2.mp4",
            ]
        ),
    ) as mock_download:
        response = await client.post(
            "/api/download/",
            headers=auth_headers,
            json={"link": "https://t.me/testchannel/123"},
        )

    assert response.status_code == 200
    data = response.json()
    assert len(data["urls"]) == 2
    assert data["urls"][0].endswith("video1.mp4")
    mock_download.assert_awaited_once()


async def test_download_file_returns_404_for_missing_file(
    client: AsyncClient,
    auth_headers: dict,
):
    response = await client.get(
        "/api/download/files/not-found.mp4",
        headers=auth_headers,
    )
    assert response.status_code == 404


async def test_delete_downloaded_file_rejects_invalid_url(
    client: AsyncClient,
    auth_headers: dict,
):
    response = await client.request(
        "DELETE",
        "/api/download/",
        headers=auth_headers,
        json={"url": "/api/other/files/a.mp4"},
    )
    assert response.status_code == 400


async def test_delete_downloaded_file_returns_404_for_missing_file(
    client: AsyncClient,
    auth_headers: dict,
):
    response = await client.request(
        "DELETE",
        "/api/download/",
        headers=auth_headers,
        json={"url": "/api/download/files/missing.mp4"},
    )
    assert response.status_code == 404


async def test_preview_returns_media_ids_and_thumbnails(
    client: AsyncClient,
    auth_headers: dict,
):
    settings_response = await client.patch(
        "/api/users/me",
        headers=auth_headers,
        json={
            "settings": {
                "telegram_api_id": "12345",
                "telegram_api_hash": "test-hash",
                "telegram_session_string": "test-session",
            }
        },
    )
    assert settings_response.status_code == 200

    with patch(
        "app.api.download.TelegramDownloadService.get_media_previews_from_link",
        new=AsyncMock(
            return_value=[
                {
                    "media_id": 111,
                    "thumbnail_url": "/api/download/files/thumb1.jpg",
                    "media_type": "image",
                },
                {
                    "media_id": 112,
                    "thumbnail_url": None,
                    "media_type": "video",
                },
            ]
        ),
    ) as mock_preview:
        response = await client.post(
            "/api/download/preview",
            headers=auth_headers,
            json={"link": "https://t.me/testchannel/123"},
        )

    assert response.status_code == 200
    data = response.json()
    assert len(data["items"]) == 2
    assert data["items"][0]["media_id"] == 111
    assert (
        data["items"][0]["thumbnail_url"] == "/api/download/files/thumb1.jpg"
    )
    assert data["items"][0]["media_type"] == "image"
    assert data["items"][1]["media_id"] == 112
    assert data["items"][1]["thumbnail_url"] is None
    assert data["items"][1]["media_type"] == "video"
    mock_preview.assert_awaited_once()


async def test_download_single_media_returns_url(
    client: AsyncClient,
    auth_headers: dict,
):
    settings_response = await client.patch(
        "/api/users/me",
        headers=auth_headers,
        json={
            "settings": {
                "telegram_api_id": "12345",
                "telegram_api_hash": "test-hash",
                "telegram_session_string": "test-session",
            }
        },
    )
    assert settings_response.status_code == 200

    with patch(
        "app.api.download.TelegramDownloadService.download_single_media_from_link",
        new=AsyncMock(return_value="/api/download/files/one.mp4"),
    ) as mock_single:
        response = await client.post(
            "/api/download/single",
            headers=auth_headers,
            json={"link": "https://t.me/testchannel/123", "media_id": 111},
        )

    assert response.status_code == 200
    assert response.json()["url"] == "/api/download/files/one.mp4"
    mock_single.assert_awaited_once()
