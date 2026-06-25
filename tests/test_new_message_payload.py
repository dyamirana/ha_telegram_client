"""Tests for new message event filtering and payload."""

from types import SimpleNamespace

import pytest

from custom_components.telegram_client.const import EVENT_NEW_MESSAGE, OPTION_CHAT_FILTER_MODE, OPTION_TELEGRAM_FOLDER_ID, CHAT_FILTER_MODE_TELEGRAM_FOLDER
from custom_components.telegram_client.coordinator import TelegramClientCoordinator


@pytest.mark.asyncio
async def test_folder_filter_skips_non_folder_chat():
    fired = []
    coordinator = SimpleNamespace(
        _folder_chat_ids={123},
        _entry=SimpleNamespace(options={EVENT_NEW_MESSAGE: {OPTION_CHAT_FILTER_MODE: CHAT_FILTER_MODE_TELEGRAM_FOLDER, OPTION_TELEGRAM_FOLDER_ID: "7"}}),
        _hass=SimpleNamespace(bus=SimpleNamespace(async_fire=lambda *args: fired.append(args))),
    )
    await TelegramClientCoordinator.on_new_message(coordinator, SimpleNamespace(chat_id=456))
    assert fired == []
