from typing import Any

from app.core.config import settings
from app.core.encryption import encrypt_value

SENSITIVE_SETTINGS_FIELDS = {
    "gemini_api_key",
    "telegram_api_id",
    "telegram_api_hash",
    "telegram_session_string",
    "telegram_bot_token",
}


def settings_presence(values: dict[str, Any] | None) -> dict[str, bool]:
    """Return presence flags for sensitive settings fields."""
    if not values:
        return {}

    return {
        field: True
        for field in SENSITIVE_SETTINGS_FIELDS
        if values.get(field)
    }


def merge_settings_for_storage(
    current_settings: dict[str, Any] | None,
    incoming_settings: dict[str, Any] | None,
) -> dict[str, Any]:
    """Merge plaintext updates into stored settings, encrypting secrets."""
    merged_settings = dict(current_settings or {})

    if not incoming_settings:
        return merged_settings

    for key, value in incoming_settings.items():
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
