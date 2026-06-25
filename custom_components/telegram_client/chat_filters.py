"""Chat filtering helpers for Telegram client events."""

from __future__ import annotations

from collections.abc import AsyncIterable
from typing import Any

from homeassistant.helpers import config_validation as cv

from .const import (
    CHAT_FILTER_MODE_MANUAL_BLACKLIST,
    CHAT_FILTER_MODE_MANUAL_WHITELIST,
    CHAT_FILTER_MODE_TELEGRAM_FOLDER,
    OPTION_BLACKLIST_CHATS,
    OPTION_CHAT_FILTER_MODE,
    OPTION_CHATS,
    OPTION_TELEGRAM_FOLDER_ID,
)


def parse_chat_ids_csv(value: Any) -> list[int]:
    """Parse a comma-separated Telegram chat ID list."""
    return [int(item) for item in cv.ensure_list_csv(value) if str(item).strip()]


def migrate_chat_filter_options(options: dict[str, Any]) -> dict[str, Any]:
    """Add chat_filter_mode to old event options without changing behavior."""
    migrated = dict(options)
    if migrated.get(OPTION_CHAT_FILTER_MODE):
        return migrated
    chats = parse_chat_ids_csv(migrated.get(OPTION_CHATS))
    if migrated.get(OPTION_BLACKLIST_CHATS):
        migrated[OPTION_CHAT_FILTER_MODE] = CHAT_FILTER_MODE_MANUAL_BLACKLIST
    elif chats:
        migrated[OPTION_CHAT_FILTER_MODE] = CHAT_FILTER_MODE_MANUAL_WHITELIST
    else:
        migrated[OPTION_CHAT_FILTER_MODE] = CHAT_FILTER_MODE_MANUAL_WHITELIST
    return migrated


def get_manual_chat_filter(options: dict[str, Any]) -> tuple[list[int] | None, bool]:
    """Return Telethon chats and blacklist_chats arguments for manual modes."""
    mode = options.get(OPTION_CHAT_FILTER_MODE)
    chats = parse_chat_ids_csv(options.get(OPTION_CHATS)) or None
    if mode == CHAT_FILTER_MODE_MANUAL_BLACKLIST:
        return chats, True
    if mode == CHAT_FILTER_MODE_TELEGRAM_FOLDER:
        return None, False
    return chats, False


async def get_folder_chat_ids(client: Any, folder_id: int) -> set[int]:
    """Load Telegram dialog IDs from a folder."""
    chat_ids: set[int] = set()
    dialogs: AsyncIterable[Any] = client.iter_dialogs(folder=folder_id)
    async for dialog in dialogs:
        chat_ids.add(int(dialog.id))
    return chat_ids


def get_folder_id(options: dict[str, Any]) -> int | None:
    """Return configured Telegram folder ID, if any."""
    folder_id = options.get(OPTION_TELEGRAM_FOLDER_ID)
    if folder_id in (None, ""):
        return None
    return int(folder_id)
