"""Chat filtering helpers for Telegram client events."""

from __future__ import annotations

from collections.abc import AsyncIterable
from typing import Any

from homeassistant.helpers import config_validation as cv

from .const import (
    LOGGER,
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
    try:
        return await _get_dialog_folder_chat_ids(client, folder_id)
    except Exception as err:
        if not _is_folder_id_invalid_error(err):
            raise
        LOGGER.debug(
            "Telegram folder %s is not a dialog folder; trying chat folder filters",
            folder_id,
        )

    try:
        chat_ids = await _get_dialog_filter_chat_ids(client, folder_id)
    except ImportError:
        chat_ids = set()
    if not chat_ids:
        LOGGER.warning(
            "Telegram folder %s is not valid; clear or re-select the folder in the integration options",
            folder_id,
        )
    return chat_ids


async def _get_dialog_folder_chat_ids(client: Any, folder_id: int) -> set[int]:
    """Load dialog IDs from Telethon's dialog folder iterator."""
    chat_ids: set[int] = set()
    dialogs: AsyncIterable[Any] = client.iter_dialogs(folder=folder_id)
    async for dialog in dialogs:
        chat_ids.add(int(dialog.id))
    return chat_ids


async def _get_dialog_filter_chat_ids(client: Any, folder_id: int) -> set[int]:
    """Load chat IDs from Telegram chat folder filter peer lists."""
    dialog_filter = await _get_telegram_dialog_filter(client, folder_id)
    if dialog_filter is None:
        return set()

    chat_ids: set[int] = set()
    for peer in _iter_dialog_filter_peers(dialog_filter):
        chat_ids.add(_peer_id(peer))
    return chat_ids


async def _get_telegram_dialog_filter(client: Any, folder_id: int) -> Any | None:
    """Return a Telegram dialog filter by ID."""
    for dialog_filter in await _get_telegram_dialog_filters(client):
        if getattr(dialog_filter, "id", None) == folder_id:
            return dialog_filter
    return None


async def _get_telegram_dialog_filters(client: Any):
    """Return Telegram dialog filters from the API."""
    from telethon.tl.functions.messages import GetDialogFiltersRequest

    return _iter_telegram_dialog_filters(await client(GetDialogFiltersRequest()))


def _iter_dialog_filter_peers(dialog_filter: Any):
    """Iterate explicitly included peers from a Telegram dialog filter."""
    for attr in ("include_peers", "pinned_peers"):
        yield from getattr(dialog_filter, attr, ()) or ()


def _peer_id(peer: Any) -> int:
    """Return Telethon's marked peer ID for an input peer."""
    from telethon import utils

    return int(utils.get_peer_id(peer))


def _is_folder_id_invalid_error(err: Exception) -> bool:
    """Return whether err is Telethon's FolderIdInvalidError."""
    return type(err).__name__ == "FolderIdInvalidError"


async def get_telegram_folder_options(client: Any) -> dict[str, str]:
    """Return Telegram folder IDs and titles suitable for an options dropdown."""
    folders: dict[str, str] = {}
    for dialog_filter in await _get_telegram_dialog_filters(client):
        folder_id = getattr(dialog_filter, "id", None)
        title = _telegram_folder_title(dialog_filter)
        if folder_id in (None, 0) or not title:
            continue
        folders[str(folder_id)] = f"{title} ({folder_id})"
    return folders


def _iter_telegram_dialog_filters(response: Any):
    """Iterate dialog filters from Telethon response variants."""
    filters = getattr(response, "filters", None)
    if filters is not None:
        yield from filters
        return
    yield from response


def _telegram_folder_title(dialog_filter: Any) -> str | None:
    """Return a human readable Telegram folder title."""
    title = getattr(dialog_filter, "title", None)
    if title is None:
        return None
    if isinstance(title, str):
        return title
    # Some Telethon versions expose rich text titles as objects. Prefer their
    # plain text when available instead of showing an object repr in the UI.
    text = getattr(title, "text", None)
    if isinstance(text, str):
        return text
    LOGGER.debug("Unsupported Telegram folder title type: %s", type(title))
    return str(title)


def get_folder_id(options: dict[str, Any]) -> int | None:
    """Return configured Telegram folder ID, if any."""
    folder_id = options.get(OPTION_TELEGRAM_FOLDER_ID)
    if folder_id in (None, ""):
        return None
    return int(folder_id)
