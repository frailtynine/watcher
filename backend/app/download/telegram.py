from __future__ import annotations

from pathlib import Path
from urllib.parse import urlparse
import shutil
import uuid

from telethon import TelegramClient
from telethon.sessions import StringSession
from telethon.tl.types import MessageMediaPhoto, MessageMediaDocument


def is_telegram_link(link: str) -> bool:
    parsed = urlparse(link)
    host = (parsed.netloc or "").lower()
    return host in {"t.me", "telegram.me", "www.t.me", "www.telegram.me"}


class TelegramDownloadService:
    def __init__(self, downloads_dir: str):
        self.downloads_dir = Path(downloads_dir)
        self.downloads_dir.mkdir(parents=True, exist_ok=True)

    @staticmethod
    def parse_message_link(link: str) -> tuple[str, int]:
        parsed = urlparse(link)
        segments = [segment for segment in parsed.path.split("/") if segment]
        if len(segments) < 2:
            raise ValueError("Invalid Telegram post link")

        channel = segments[-2]
        try:
            message_id = int(segments[-1])
        except ValueError as exc:
            raise ValueError("Invalid Telegram message id") from exc

        return channel, message_id

    async def download_from_link(
        self,
        *,
        link: str,
        api_id: str,
        api_hash: str,
        session_string: str,
    ) -> list[str]:
        channel, message_id = self.parse_message_link(link)

        session = StringSession(session_string)
        async with TelegramClient(session, int(api_id), api_hash) as client:
            message = await client.get_messages(channel, ids=message_id)
            if not message:
                return []

            target_dir = self.downloads_dir / str(uuid.uuid4())
            target_dir.mkdir(parents=True, exist_ok=True)

            media_items = await self._get_media_items_for_message(
                client=client,
                channel=channel,
                message=message,
            )
            media_urls: list[str] = []
            for media_item in media_items:
                if not getattr(media_item, "media", None):
                    continue

                file_path = await client.download_media(
                    media_item,
                    file=str(target_dir),
                )
                if file_path:
                    downloaded_path = Path(file_path)
                    unique_name = (
                        f"{uuid.uuid4()}{downloaded_path.suffix.lower()}"
                    )
                    final_path = self.downloads_dir / unique_name
                    shutil.move(str(downloaded_path), final_path)
                    media_urls.append(f"/api/download/files/{final_path.name}")

            return media_urls

    async def download_single_media_from_link(
        self,
        *,
        link: str,
        media_id: int,
        api_id: str,
        api_hash: str,
        session_string: str,
    ) -> str | None:
        channel, message_id = self.parse_message_link(link)

        session = StringSession(session_string)
        async with TelegramClient(session, int(api_id), api_hash) as client:
            message = await client.get_messages(channel, ids=message_id)
            if not message:
                return None

            media_items = await self._get_media_items_for_message(
                client=client,
                channel=channel,
                message=message,
            )

            selected_item = None
            for item in media_items:
                if getattr(item, "id", None) == media_id:
                    selected_item = item
                    break

            if not selected_item or not getattr(selected_item, "media", None):
                return None

            target_dir = self.downloads_dir / str(uuid.uuid4())
            target_dir.mkdir(parents=True, exist_ok=True)

            file_path = await client.download_media(
                selected_item,
                file=str(target_dir),
            )
            if not file_path:
                return None

            downloaded_path = Path(file_path)
            unique_name = f"{uuid.uuid4()}{downloaded_path.suffix.lower()}"
            final_path = self.downloads_dir / unique_name
            shutil.move(str(downloaded_path), final_path)
            return f"/api/download/files/{final_path.name}"

    async def get_media_previews_from_link(
        self,
        *,
        link: str,
        api_id: str,
        api_hash: str,
        session_string: str,
    ) -> list[dict]:
        channel, message_id = self.parse_message_link(link)

        session = StringSession(session_string)
        async with TelegramClient(session, int(api_id), api_hash) as client:
            message = await client.get_messages(channel, ids=message_id)
            if not message:
                return []

            media_items = await self._get_media_items_for_message(
                client=client,
                channel=channel,
                message=message,
            )

            previews: list[dict] = []
            preview_dir = self.downloads_dir / str(uuid.uuid4())
            preview_dir.mkdir(parents=True, exist_ok=True)

            for media_item in media_items:
                media_id = getattr(media_item, "id", None)
                if not isinstance(media_id, int):
                    continue

                thumbnail_url: str | None = None
                has_thumb = getattr(media_item, "photo", None) or getattr(
                    getattr(media_item, "document", None),
                    "thumbs",
                    None,
                )

                media = getattr(media_item, "media", None)
                media_type = "unknown"
                media_class_name = media.__class__.__name__ if media else ""
                if (
                    isinstance(media, MessageMediaPhoto)
                    or media_class_name == "MessageMediaPhoto"
                ):
                    media_type = "image"
                elif (
                    isinstance(media, MessageMediaDocument)
                    or media_class_name == "MessageMediaDocument"
                ):
                    mime_type = (
                        getattr(
                            getattr(media, "document", None), "mime_type", ""
                        )
                        or ""
                    )
                    if mime_type.startswith("image/"):
                        media_type = "image"
                    elif mime_type.startswith("video/"):
                        media_type = "video"
                    else:
                        media_type = "document"
                if has_thumb:
                    thumb_path = await client.download_media(
                        media_item,
                        file=str(preview_dir),
                        thumb=-1,
                    )
                    if thumb_path:
                        downloaded_path = Path(thumb_path)
                        unique_name = (
                            f"{uuid.uuid4()}{downloaded_path.suffix.lower()}"
                        )
                        final_path = self.downloads_dir / unique_name
                        shutil.move(str(downloaded_path), final_path)
                        thumbnail_url = (
                            f"/api/download/files/{final_path.name}"
                        )

                previews.append(
                    {
                        "media_id": media_id,
                        "thumbnail_url": thumbnail_url,
                        "media_type": media_type,
                    }
                )

            return previews

    async def _get_media_items_for_message(
        self,
        *,
        client: TelegramClient,
        channel: str,
        message,
    ) -> list:
        grouped_id = getattr(message, "grouped_id", None)
        if not grouped_id:
            return [message]

        message_id = getattr(message, "id", None)
        if not isinstance(message_id, int):
            return [message]

        # Telegram albums are contiguous by message id.
        nearby_ids = [
            item_id
            for item_id in range(max(1, message_id - 20), message_id + 21)
        ]
        nearby_messages = await client.get_messages(channel, ids=nearby_ids)
        nearby_messages_list: list = []
        if isinstance(nearby_messages, list):
            nearby_messages_list = nearby_messages
        elif nearby_messages is not None:
            nearby_messages_list = [nearby_messages]

        album_items = [
            item
            for item in nearby_messages_list
            if item
            and getattr(item, "grouped_id", None) == grouped_id
            and getattr(item, "media", None)
        ]

        if not album_items and getattr(message, "media", None):
            return [message]
        return album_items

    def resolve_file_path(self, filename: str) -> Path:
        if not filename or "/" in filename or "\\" in filename:
            raise ValueError("Invalid filename")

        candidate = (self.downloads_dir / filename).resolve()
        base = self.downloads_dir.resolve()
        if not str(candidate).startswith(str(base)):
            raise ValueError("Invalid filename")

        return candidate

    @staticmethod
    def extract_filename_from_download_url(url: str) -> str:
        parsed = urlparse(url)
        path_segments = [
            segment for segment in parsed.path.split("/") if segment
        ]
        if len(path_segments) < 4:
            raise ValueError("Invalid download URL")
        if path_segments[:3] != ["api", "download", "files"]:
            raise ValueError("Invalid download URL")
        return path_segments[3]
