"""Device automation triggers for Telegram client."""

from __future__ import annotations

import voluptuous as vol

from homeassistant.components.device_automation import DEVICE_TRIGGER_BASE_SCHEMA
from homeassistant.const import CONF_DEVICE_ID, CONF_DOMAIN, CONF_PLATFORM, CONF_TYPE
from homeassistant.core import CALLBACK_TYPE, HomeAssistant, callback
from homeassistant.helpers import config_validation as cv, device_registry as dr
from homeassistant.helpers.typing import ConfigType

from .const import DOMAIN, EVENT_NEW_MESSAGE, KEY_CHAT_ID, KEY_SENDER_ID, KEY_FOLDER_ID

TRIGGER_TYPE_NEW_MESSAGE = "new_message"
CONF_CHAT_ID = "chat_id"
CONF_SENDER_ID = "sender_id"
CONF_MESSAGE_CONTAINS = "message_contains"
CONF_FOLDER_ID = "folder_id"

TRIGGER_SCHEMA = DEVICE_TRIGGER_BASE_SCHEMA.extend(
    {
        vol.Required(CONF_TYPE): vol.In({TRIGGER_TYPE_NEW_MESSAGE}),
        vol.Optional(CONF_CHAT_ID): int,
        vol.Optional(CONF_SENDER_ID): int,
        vol.Optional(CONF_MESSAGE_CONTAINS): cv.string,
        vol.Optional(CONF_FOLDER_ID): int,
    }
)


async def async_get_triggers(hass: HomeAssistant, device_id: str) -> list[dict]:
    """Return supported Telegram client device triggers."""
    registry = dr.async_get(hass)
    device = registry.async_get(device_id)
    if device is None or not any(identifier[0] == DOMAIN for identifier in device.identifiers):
        return []
    return [
        {
            CONF_PLATFORM: "device",
            CONF_DOMAIN: DOMAIN,
            CONF_DEVICE_ID: device_id,
            CONF_TYPE: TRIGGER_TYPE_NEW_MESSAGE,
        }
    ]


async def async_validate_trigger_config(hass: HomeAssistant, config: ConfigType) -> ConfigType:
    """Validate trigger config."""
    return TRIGGER_SCHEMA(config)


async def async_attach_trigger(
    hass: HomeAssistant,
    config: ConfigType,
    action,
    trigger_info,
) -> CALLBACK_TYPE:
    """Attach a Telegram new message trigger."""

    @callback
    def _handle_event(event):
        data = event.data
        if CONF_CHAT_ID in config and data.get(KEY_CHAT_ID) != config[CONF_CHAT_ID]:
            return
        if CONF_SENDER_ID in config and data.get(KEY_SENDER_ID) != config[CONF_SENDER_ID]:
            return
        if CONF_FOLDER_ID in config and data.get(KEY_FOLDER_ID) != config[CONF_FOLDER_ID]:
            return
        if CONF_MESSAGE_CONTAINS in config and config[CONF_MESSAGE_CONTAINS] not in (data.get("raw_text") or data.get("message") or ""):
            return
        hass.async_create_task(action({"trigger": {**trigger_info, "event": event}}))

    return hass.bus.async_listen(f"{DOMAIN}_{EVENT_NEW_MESSAGE}", _handle_event)
