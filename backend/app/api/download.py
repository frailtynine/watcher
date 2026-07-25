from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import FileResponse
from typing import Any, cast

from app.api.auth import current_active_user
from app.core.config import settings
from app.core.encryption import decrypt_value
from app.download import TelegramDownloadService, is_telegram_link
from app.models import User
from app.schemas import (
    DownloadDeleteRequest,
    DownloadPreviewItem,
    DownloadPreviewResponse,
    DownloadRequest,
    DownloadResponse,
    DownloadSingleRequest,
    DownloadSingleResponse,
)


router = APIRouter()


def _resolve_telegram_credentials(user: User) -> tuple[str, str, str]:
    encrypted_settings = user.settings or {}
    encrypted_api_id = encrypted_settings.get("telegram_api_id")
    encrypted_api_hash = encrypted_settings.get("telegram_api_hash")
    encrypted_session = encrypted_settings.get("telegram_session_string")

    if not isinstance(encrypted_api_id, str):
        encrypted_api_id = None
    if not isinstance(encrypted_api_hash, str):
        encrypted_api_hash = None
    if not isinstance(encrypted_session, str):
        encrypted_session = None

    if not all([encrypted_api_id, encrypted_api_hash, encrypted_session]):
        raise HTTPException(
            status_code=400,
            detail=(
                "Telegram download requires user Telegram credentials in "
                "settings."
            ),
        )

    encrypted_api_id_str = cast(str, encrypted_api_id)
    encrypted_api_hash_str = cast(str, encrypted_api_hash)
    encrypted_session_str = cast(str, encrypted_session)

    try:
        api_id = decrypt_value(encrypted_api_id_str, settings.ENCRYPTION_KEY)
        api_hash = decrypt_value(
            encrypted_api_hash_str, settings.ENCRYPTION_KEY
        )
        session_string = decrypt_value(
            encrypted_session_str,
            settings.ENCRYPTION_KEY,
        )
    except Exception as exc:
        raise HTTPException(
            status_code=400,
            detail="Invalid Telegram credentials in user settings.",
        ) from exc

    return api_id, api_hash, session_string


@router.get("/files/{filename}")
async def get_downloaded_file(filename: str):
    service = TelegramDownloadService(settings.DOWNLOADS_DIR)
    try:
        file_path = service.resolve_file_path(filename)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    if not file_path.exists() or not file_path.is_file():
        raise HTTPException(status_code=404, detail="File not found")

    return FileResponse(file_path)


@router.post("/", response_model=DownloadResponse)
async def download_media(
    payload: DownloadRequest,
    user: User = Depends(current_active_user),
):
    if not is_telegram_link(payload.link):
        raise HTTPException(
            status_code=400,
            detail="Only Telegram links are supported for now.",
        )

    api_id, api_hash, session_string = _resolve_telegram_credentials(user)

    service = TelegramDownloadService(settings.DOWNLOADS_DIR)
    try:
        urls = await service.download_from_link(
            link=payload.link,
            api_id=api_id,
            api_hash=api_hash,
            session_string=session_string,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail=f"Telegram download failed: {exc}",
        ) from exc

    return DownloadResponse(urls=urls)


@router.post("/preview", response_model=DownloadPreviewResponse)
async def preview_media(
    payload: DownloadRequest,
    user: User = Depends(current_active_user),
):
    if not is_telegram_link(payload.link):
        raise HTTPException(
            status_code=400,
            detail="Only Telegram links are supported for now.",
        )

    api_id, api_hash, session_string = _resolve_telegram_credentials(user)

    service = TelegramDownloadService(settings.DOWNLOADS_DIR)
    try:
        items = await service.get_media_previews_from_link(
            link=payload.link,
            api_id=api_id,
            api_hash=api_hash,
            session_string=session_string,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail=f"Telegram preview failed: {exc}",
        ) from exc

    typed_items = cast(list[dict[str, Any]], items)
    return DownloadPreviewResponse(
        items=[DownloadPreviewItem(**item) for item in typed_items]
    )


@router.post("/single", response_model=DownloadSingleResponse)
async def download_single_media(
    payload: DownloadSingleRequest,
    user: User = Depends(current_active_user),
):
    if not is_telegram_link(payload.link):
        raise HTTPException(
            status_code=400,
            detail="Only Telegram links are supported for now.",
        )

    api_id, api_hash, session_string = _resolve_telegram_credentials(user)

    service = TelegramDownloadService(settings.DOWNLOADS_DIR)
    try:
        url = await service.download_single_media_from_link(
            link=payload.link,
            media_id=payload.media_id,
            api_id=api_id,
            api_hash=api_hash,
            session_string=session_string,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail=f"Telegram single download failed: {exc}",
        ) from exc

    if not url:
        raise HTTPException(status_code=404, detail="Media not found")

    return DownloadSingleResponse(url=url)


@router.delete("/")
async def delete_downloaded_file(
    payload: DownloadDeleteRequest,
    user: User = Depends(current_active_user),
):
    service = TelegramDownloadService(settings.DOWNLOADS_DIR)

    try:
        filename = service.extract_filename_from_download_url(payload.url)
        file_path = service.resolve_file_path(filename)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    if not file_path.exists() or not file_path.is_file():
        raise HTTPException(status_code=404, detail="File not found")

    file_path.unlink(missing_ok=False)
    return {"deleted": True}
