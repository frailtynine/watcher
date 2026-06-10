from typing import Any

from app.core.config import settings
from app.core.encryption import encrypt_value

SENSITIVE_SETTINGS_FIELDS = {
    "gemini_api_key",
    "telegram_api_id",
    "telegram_api_hash",
    "telegram_session_string",
}
LEGACY_TELEGRAM_BOTS_FIELD = "telegram_bots"


def settings_presence(values: dict[str, Any] | None) -> dict[str, Any]:
    """Return safe settings values for the API response."""
    if not values:
        return {}

    visible_settings = {
        field: True for field in SENSITIVE_SETTINGS_FIELDS if values.get(field)
    }

    telegram_bots = values.get(LEGACY_TELEGRAM_BOTS_FIELD)
    if isinstance(telegram_bots, list):
        visible_settings[LEGACY_TELEGRAM_BOTS_FIELD] = telegram_bots

    return visible_settings


def merge_settings_for_storage(
    current_settings: dict[str, Any] | None,
    incoming_settings: dict[str, Any] | None,
) -> dict[str, Any]:
    """Merge plaintext updates into stored settings, encrypting secrets."""
    merged_settings = dict(current_settings or {})

    if not incoming_settings:
        return merged_settings

    for key, value in incoming_settings.items():
        if key == LEGACY_TELEGRAM_BOTS_FIELD:
            merged_settings.pop(LEGACY_TELEGRAM_BOTS_FIELD, None)
            continue

        if value is None:
            merged_settings.pop(key, None)
            continue

        if key in SENSITIVE_SETTINGS_FIELDS:
            if not isinstance(value, str):
                continue

            trimmed = value.strip()
            if not trimmed:
                merged_settings.pop(key, None)
                continue

            merged_settings[key] = encrypt_value(
                trimmed,
                settings.ENCRYPTION_KEY,
            )
            continue

        merged_settings[key] = value

    return merged_settings
