"""Tests for new message event filtering and payload."""

from types import SimpleNamespace

import pytest

homeassistant = pytest.importorskip("homeassistant.core")
pytest.importorskip("telethon")

from custom_components.telegram_client.const import (
    CHAT_FILTER_MODE_TELEGRAM_FOLDER,
    EVENT_NEW_MESSAGE,
    OPTION_CHAT_FILTER_MODE,
    OPTION_TELEGRAM_FOLDER_ID,
)
from custom_components.telegram_client.coordinator import TelegramClientCoordinator


@pytest.mark.asyncio
async def test_folder_filter_skips_non_folder_chat():
    fired = []
    coordinator = SimpleNamespace(
        _folder_chat_ids={123},
        _entry=SimpleNamespace(
            options={
                EVENT_NEW_MESSAGE: {
                    OPTION_CHAT_FILTER_MODE: CHAT_FILTER_MODE_TELEGRAM_FOLDER,
                    OPTION_TELEGRAM_FOLDER_ID: "7",
                }
            }
        ),
        _hass=SimpleNamespace(
            bus=SimpleNamespace(async_fire=lambda *args: fired.append(args))
        ),
    )
    await TelegramClientCoordinator.on_new_message(
        coordinator, SimpleNamespace(chat_id=456)
    )
    assert fired == []


@pytest.mark.asyncio
@pytest.mark.parametrize(
    ("silent", "expected"),
    [(False, True), (True, False), (None, None)],
)
async def test_new_message_payload_includes_notification_enabled(silent, expected):
    coordinator = SimpleNamespace(
        _entry=SimpleNamespace(entry_id="entry-1", options={}),
        data={"id": 42},
    )

    async def get_chat():
        return SimpleNamespace(title="Chat")

    async def get_sender():
        return SimpleNamespace(username="sender", first_name="First", last_name="Last")

    event = SimpleNamespace(
        chat_id=123,
        message=SimpleNamespace(id=10, silent=silent, date=None, fwd_from=None),
        raw_text="hello",
        out=False,
        get_chat=get_chat,
        get_sender=get_sender,
    )

    data = await TelegramClientCoordinator._new_message_event_data(
        coordinator, event, None
    )

    assert data["notification_enabled"] is expected
