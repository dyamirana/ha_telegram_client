"""Tests for Telegram chat filtering helpers."""

from types import SimpleNamespace

import asyncio

import pytest

from custom_components.telegram_client.chat_filters import (
    get_folder_chat_ids,
    get_telegram_folder_options,
    migrate_chat_filter_options,
    parse_chat_ids_csv,
)
from custom_components.telegram_client.const import (
    CHAT_FILTER_MODE_MANUAL_BLACKLIST,
    CHAT_FILTER_MODE_MANUAL_WHITELIST,
    OPTION_BLACKLIST_CHATS,
    OPTION_CHAT_FILTER_MODE,
    OPTION_CHATS,
)


def test_parse_chat_ids_csv_ignores_empty_items():
    assert parse_chat_ids_csv("2074448263,, -1001234567890") == [
        2074448263,
        -1001234567890,
    ]


def test_parse_chat_ids_csv_rejects_invalid_id():
    with pytest.raises(ValueError):
        parse_chat_ids_csv("2074448263,not-a-chat")


def test_migrate_old_blacklist_config():
    assert migrate_chat_filter_options(
        {OPTION_BLACKLIST_CHATS: True, OPTION_CHATS: "1,2"}
    )[OPTION_CHAT_FILTER_MODE] == CHAT_FILTER_MODE_MANUAL_BLACKLIST


def test_migrate_old_whitelist_config():
    assert migrate_chat_filter_options(
        {OPTION_BLACKLIST_CHATS: False, OPTION_CHATS: "1,2"}
    )[OPTION_CHAT_FILTER_MODE] == CHAT_FILTER_MODE_MANUAL_WHITELIST


class _Client:
    async def iter_dialogs(self, folder):
        assert folder == 7
        for dialog_id in (1, -1001234567890):
            yield SimpleNamespace(id=dialog_id)


def test_folder_chat_id_loading():
    assert asyncio.run(get_folder_chat_ids(_Client(), 7)) == {1, -1001234567890}


def test_get_telegram_folder_options(monkeypatch):
    import sys
    import types

    class GetDialogFiltersRequest:
        pass

    telethon = types.ModuleType("telethon")
    tl = types.ModuleType("telethon.tl")
    functions = types.ModuleType("telethon.tl.functions")
    messages = types.ModuleType("telethon.tl.functions.messages")
    messages.GetDialogFiltersRequest = GetDialogFiltersRequest
    monkeypatch.setitem(sys.modules, "telethon", telethon)
    monkeypatch.setitem(sys.modules, "telethon.tl", tl)
    monkeypatch.setitem(sys.modules, "telethon.tl.functions", functions)
    monkeypatch.setitem(sys.modules, "telethon.tl.functions.messages", messages)

    class Client:
        async def __call__(self, request):
            assert isinstance(request, GetDialogFiltersRequest)
            return [
                SimpleNamespace(id=0, title="Default"),
                SimpleNamespace(id=2, title="Home Assistant"),
            ]

    assert asyncio.run(get_telegram_folder_options(Client())) == {
        "2": "Home Assistant (2)"
    }
